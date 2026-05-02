from __future__ import annotations

import pytest

from metametameta.from_requirements_txt import generate_from_requirements_txt, read_requirements_txt_metadata


def test_read_requirements_txt_metadata(tmp_path):
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text(
        "click>=8\n# comment\nrich==13.0\n-r other.txt\n-e git+https://example.com/pkg.git#egg=editable-pkg\n",
        encoding="utf-8",
    )

    metadata = read_requirements_txt_metadata(source=str(requirements_path), name="demo-app")

    assert metadata == {
        "name": "demo-app",
        "dependencies": ["click>=8", "rich==13.0", "editable-pkg"],
    }


def test_generate_from_requirements_txt(tmp_path, monkeypatch):
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text("click>=8\nrich\n", encoding="utf-8")
    (tmp_path / "demo_app").mkdir()
    monkeypatch.chdir(tmp_path)

    generated_path = generate_from_requirements_txt(name="demo-app", source=str(requirements_path), validate=True)
    generated_content = (tmp_path / "demo_app" / "__about__.py").read_text(encoding="utf-8")

    assert generated_path.endswith("__about__.py")
    assert '__title__ = "demo-app"' in generated_content
    assert "__dependencies__ = ['click>=8', 'rich']" in generated_content


@pytest.mark.parametrize(
    "requirements_text, expected_dependencies",
    [
        (
            '--index-url "https://example.com/simple"\n"click>=8"  # keep this dep\n--trusted-host example.com\n',
            ["click>=8"],
        ),
        (
            "--editable git+https://example.com/pkg.git#egg=quoted-pkg\ncolorama>=0.4\n",
            ["quoted-pkg", "colorama>=0.4"],
        ),
    ],
)
def test_read_requirements_txt_metadata_skips_options_and_strips_quotes(
    tmp_path, requirements_text, expected_dependencies
):
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text(requirements_text, encoding="utf-8")

    metadata = read_requirements_txt_metadata(source=str(requirements_path))

    assert metadata["name"] == tmp_path.name
    assert metadata["dependencies"] == expected_dependencies


def test_read_requirements_txt_metadata_without_dependencies_returns_only_name(tmp_path):
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text("# comment only\n--find-links https://example.com/wheels\n", encoding="utf-8")

    metadata = read_requirements_txt_metadata(source=str(requirements_path), name="demo-app")

    assert metadata == {"name": "demo-app"}


def test_generate_from_requirements_txt_supports_custom_output_path(tmp_path, monkeypatch):
    requirements_path = tmp_path / "requirements.txt"
    nested_output = tmp_path / "artifacts" / "about.py"
    requirements_path.write_text("click>=8\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    generated_path = generate_from_requirements_txt(
        name="demo-app", source=str(requirements_path), output=str(nested_output), validate=True
    )

    assert generated_path == str(nested_output)
    assert "__dependencies__ = ['click>=8']" in nested_output.read_text(encoding="utf-8")
