from __future__ import annotations

import pytest
import toml

from metametameta.from_poetry import generate_from_poetry, read_poetry_metadata


def test_generate_from_poetry_file_not_found(tmp_path):
    # A non-existent file path
    non_existent_file = tmp_path / "non_existent_pyproject.toml"

    with pytest.raises(FileNotFoundError):
        generate_from_poetry(source=str(non_existent_file))


def test_read_poetry_metadata_zero_dependencies(tmp_path):
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        toml.dumps(
            {
                "tool": {
                    "poetry": {
                        "name": "demo-app",
                        "version": "0.1.0",
                        "description": "Demo package",
                        "dependencies": {"python": ">=3.11"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    metadata = read_poetry_metadata(source=str(pyproject_file))

    assert metadata["name"] == "demo-app"
    assert metadata["dependencies"] == []


def test_generate_from_poetry_with_no_dependencies_writes_typed_empty_list(tmp_path, monkeypatch):
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        toml.dumps(
            {
                "tool": {
                    "poetry": {
                        "name": "demo-app",
                        "version": "0.1.0",
                        "description": "Demo package",
                        "dependencies": {"python": ">=3.11"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "demo-app").mkdir()
    monkeypatch.chdir(tmp_path)

    generated_path = generate_from_poetry(source=str(pyproject_file), validate=True)
    generated_content = (tmp_path / "demo-app" / "__about__.py").read_text(encoding="utf-8")

    assert generated_path.endswith("__about__.py")
    assert "__dependencies__: list[str] = []" in generated_content
