from __future__ import annotations

from metametameta.from_conda_meta import generate_from_conda_meta, read_conda_meta_metadata


def test_read_conda_meta_metadata(tmp_path):
    conda_dir = tmp_path / "conda"
    conda_dir.mkdir()
    meta_path = conda_dir / "meta.yaml"
    meta_path.write_text(
        """
package:
  name: demo-app
  version: "1.2.3"

about:
  summary: Demo package
  license: MIT
  home: https://example.com/demo

requirements:
  run:
    - click>=8
    - rich
""".strip(),
        encoding="utf-8",
    )

    metadata = read_conda_meta_metadata(source=str(meta_path))

    assert metadata == {
        "name": "demo-app",
        "version": "1.2.3",
        "summary": "Demo package",
        "license": "MIT",
        "homepage": "https://example.com/demo",
        "dependencies": ["click>=8", "rich"],
    }


def test_generate_from_conda_meta(tmp_path, monkeypatch):
    conda_dir = tmp_path / "conda"
    conda_dir.mkdir()
    meta_path = conda_dir / "meta.yaml"
    meta_path.write_text(
        """
package:
  name: demo-app
  version: 1.2.3

about:
  summary: Demo package
  license: MIT
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "demo_app").mkdir()
    monkeypatch.chdir(tmp_path)

    generated_path = generate_from_conda_meta(source=str(meta_path), validate=True)
    generated_content = (tmp_path / "demo_app" / "__about__.py").read_text(encoding="utf-8")

    assert generated_path.endswith("__about__.py")
    assert '__version__ = "1.2.3"' in generated_content
    assert '__description__ = "Demo package"' in generated_content


def test_read_conda_meta_metadata_uses_description_and_name_override(tmp_path):
    conda_dir = tmp_path / "conda"
    conda_dir.mkdir()
    meta_path = conda_dir / "meta.yaml"
    meta_path.write_text(
        """
{% set version = "9.9.9" %}
package:
  version: "9.9.9"

about:
  description: "Long form description"
  home: https://example.com/demo # comment

requirements:
  run:
    - "python>=3.10"
    - "requests"
""".strip(),
        encoding="utf-8",
    )

    metadata = read_conda_meta_metadata(source=str(meta_path), name="override-name")

    assert metadata == {
        "name": "override-name",
        "version": "9.9.9",
        "description": "Long form description",
        "homepage": "https://example.com/demo",
        "dependencies": ["python>=3.10", "requests"],
    }


def test_read_conda_meta_metadata_infers_name_from_parent_folder(tmp_path):
    project_root = tmp_path / "sample-project"
    conda_dir = project_root / "conda"
    conda_dir.mkdir(parents=True)
    meta_path = conda_dir / "meta.yaml"
    meta_path.write_text(
        """
about:
  summary: Demo package
""".strip(),
        encoding="utf-8",
    )

    metadata = read_conda_meta_metadata(source=str(meta_path))

    assert metadata == {"name": "sample-project", "summary": "Demo package"}


def test_generate_from_conda_meta_supports_custom_output_path(tmp_path, monkeypatch):
    conda_dir = tmp_path / "conda"
    conda_dir.mkdir()
    meta_path = conda_dir / "meta.yaml"
    nested_output = tmp_path / "artifacts" / "conda_about.py"
    meta_path.write_text(
        """
package:
  name: demo-app

about:
  summary: Demo package
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    generated_path = generate_from_conda_meta(source=str(meta_path), output=str(nested_output), validate=True)

    assert generated_path == str(nested_output)
    assert '__description__ = "Demo package"' in nested_output.read_text(encoding="utf-8")
