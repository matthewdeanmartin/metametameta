from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

repo_root = Path(__file__).resolve().parents[1]
pyproject_path = repo_root / "pyproject.toml"
pylint_config_path = repo_root / ".pylintrc"


def run_subprocess(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and capture text output for assertions."""
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def assert_subprocess_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    """Fail with captured output when a subprocess exits unsuccessfully."""
    message = "\n".join(
        [
            f"{label} failed with exit code {result.returncode}",
            f"stdout:\n{result.stdout}",
            f"stderr:\n{result.stderr}",
        ]
    )
    assert result.returncode == 0, message


def read_all_entries(about_path: Path) -> list[str]:
    """Read the generated __all__ entries from an about file."""
    module = ast.parse(about_path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return [element.value for element in node.value.elts if isinstance(element, ast.Constant)]
    raise AssertionError(f"Could not find __all__ in {about_path}")


@pytest.mark.parametrize(
    ("source_name", "cli_args", "source_content"),
    [
        (
            "pyproject.toml",
            ["pep621", "--source", "pyproject.toml"],
            textwrap.dedent("""
                [project]
                name = "demo-app"
                version = "0.1.0"
                description = "Demo package"
                requires-python = ">=3.11"
                keywords = ["demo", "metadata"]
                dependencies = ["click>=8", "rich>=13"]
                classifiers = ["Development Status :: 4 - Beta"]
                authors = [{name = "Demo Dev", email = "dev@example.com"}]
                """).strip() + "\n",
        ),
        (
            "setup.cfg",
            ["setup_cfg", "--source", "setup.cfg"],
            textwrap.dedent("""
                [metadata]
                name = demo-app
                version = 0.1.0
                description = Demo package
                classifiers =
                    Development Status :: 4 - Beta
                keywords =
                    demo
                    metadata

                [options]
                install_requires =
                    click>=8
                    rich>=13
                """).strip() + "\n",
        ),
    ],
)
def test_generated_about_cli_output_passes_quality_gates(tmp_path, source_name, cli_args, source_content):
    """Generated about files should pass formatting, linting, and type checks unchanged."""
    (tmp_path / source_name).write_text(source_content, encoding="utf-8")
    (tmp_path / "demo_app").mkdir()

    cli_result = run_subprocess([sys.executable, "-m", "metametameta", *cli_args], cwd=tmp_path)
    assert_subprocess_ok(cli_result, "CLI generation")

    about_path = tmp_path / "demo_app" / "__about__.py"
    assert about_path.exists()
    assert read_all_entries(about_path) == sorted(read_all_entries(about_path))

    commands = [
        (
            "ruff format",
            [sys.executable, "-m", "ruff", "format", "--config", str(pyproject_path), "--check", str(about_path)],
        ),
        ("ruff check", [sys.executable, "-m", "ruff", "check", "--config", str(pyproject_path), str(about_path)]),
        ("pylint", [sys.executable, "-m", "pylint", "--rcfile", str(pylint_config_path), str(about_path)]),
        (
            "isort",
            [sys.executable, "-m", "isort", "--settings-path", str(pyproject_path), "--check-only", str(about_path)],
        ),
        ("black", [sys.executable, "-m", "black", "--config", str(pyproject_path), "--check", str(about_path)]),
        (
            "mypy",
            [
                sys.executable,
                "-m",
                "mypy",
                "--config-file",
                str(pyproject_path),
                str(about_path),
                "--ignore-missing-imports",
                "--check-untyped-defs",
            ],
        ),
    ]
    for label, command in commands:
        assert_subprocess_ok(run_subprocess(command, cwd=repo_root), label)
