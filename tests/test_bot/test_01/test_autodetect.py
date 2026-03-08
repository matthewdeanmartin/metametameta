from __future__ import annotations

import pytest

from metametameta.autodetect import detect_source


def test_detect_source_uses_requirements_txt_as_fallback(tmp_path):
    (tmp_path / "requirements.txt").write_text("click>=8\n", encoding="utf-8")

    assert detect_source(tmp_path) == "requirements_txt"


def test_detect_source_uses_conda_meta_as_fallback(tmp_path):
    conda_dir = tmp_path / "conda"
    conda_dir.mkdir()
    (conda_dir / "meta.yaml").write_text("package:\n  name: demo-app\n", encoding="utf-8")

    assert detect_source(tmp_path) == "conda_meta"


def test_detect_source_prefers_primary_sources_over_fallbacks(tmp_path):
    (tmp_path / "requirements.txt").write_text("click>=8\n", encoding="utf-8")
    (tmp_path / "setup.cfg").write_text("[metadata]\nname = demo-app\n", encoding="utf-8")

    assert detect_source(tmp_path) == "setup_cfg"


def test_detect_source_ignores_empty_requirements_txt(tmp_path):
    (tmp_path / "requirements.txt").write_text("# no dependencies yet\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        detect_source(tmp_path)


def test_detect_source_reports_multiple_primary_sources(tmp_path):
    (tmp_path / "setup.cfg").write_text("[metadata]\nname = demo-app\n", encoding="utf-8")
    (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup(name='demo-app')\n", encoding="utf-8")

    with pytest.raises(ValueError, match="setup_cfg, setup_py"):
        detect_source(tmp_path)


def test_detect_source_reports_multiple_fallback_sources(tmp_path):
    (tmp_path / "requirements.txt").write_text("click>=8\n", encoding="utf-8")
    conda_dir = tmp_path / "conda"
    conda_dir.mkdir()
    (conda_dir / "meta.yaml").write_text("about:\n  summary: demo\n", encoding="utf-8")

    with pytest.raises(ValueError, match="requirements_txt, conda_meta"):
        detect_source(tmp_path)
