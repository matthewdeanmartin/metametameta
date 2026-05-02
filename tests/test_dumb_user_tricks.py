from __future__ import annotations

from textwrap import dedent

import pytest

from metametameta.__main__ import main as cli_main


def write_pep621_pyproject(tmp_path, name: str = "demo-app", version: str = "1.2.3") -> None:
    (tmp_path / "pyproject.toml").write_text(
        dedent(
            f"""
            [project]
            name = "{name}"
            version = "{version}"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def test_cli_typo_suggests_closest_subcommand(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli_main(["pep62"])

    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "Did you mean: pep621?" in captured.err


def test_cli_gibberish_does_not_offer_a_bad_suggestion(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli_main(["totally-wrong-command"])

    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "invalid choice" in captured.err
    assert "Did you mean:" not in captured.err


def test_auto_reports_missing_metadata_source(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        cli_main(["auto"])

    captured = capsys.readouterr()

    assert excinfo.value.code == 1
    assert "Auto-generation failed" in captured.err
    assert "Could not find a viable metadata source" in captured.err


def test_auto_reports_ambiguous_metadata_sources(tmp_path, monkeypatch, capsys):
    (tmp_path / "setup.cfg").write_text("[metadata]\nname = demo-app\n", encoding="utf-8")
    (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup(name='demo-app')\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        cli_main(["auto"])

    captured = capsys.readouterr()

    assert excinfo.value.code == 1
    assert "Auto-generation failed" in captured.err
    assert "Multiple viable metadata sources found: setup_cfg, setup_py" in captured.err


def test_pep621_errors_when_package_dir_missing(tmp_path, monkeypatch, capsys):
    """When the project name does not match a real folder, error out instead of inventing one."""
    write_pep621_pyproject(tmp_path, name="weirdname-xyz", version="0.0.1")
    monkeypatch.chdir(tmp_path)

    exit_code = cli_main(["pep621"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Could not locate a package directory" in captured.err
    assert "--output" in captured.err
    # The bogus folder must not have been created on disk.
    assert not (tmp_path / "weirdname-xyz").exists()
    assert not (tmp_path / "weirdname_xyz").exists()


def test_sync_check_reports_missing_metadata_file(tmp_path, monkeypatch, capsys):
    write_pep621_pyproject(tmp_path)
    (tmp_path / "demo_app").mkdir()
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        cli_main(["sync-check"])

    captured = capsys.readouterr()

    assert excinfo.value.code == 1
    assert "Sync check failed" in captured.out
    assert "File is missing:" in captured.out
    assert "__about__.py" in captured.out


def test_sync_check_accepts_hyphenated_name_with_underscored_package_dir(tmp_path, monkeypatch, capsys):
    write_pep621_pyproject(tmp_path, name="demo-app", version="2.0.0")
    package_dir = tmp_path / "demo_app"
    package_dir.mkdir()
    (package_dir / "__about__.py").write_text(
        '__title__ = "demo-app"\n__version__ = "2.0.0"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = cli_main(["sync-check"])
    captured = capsys.readouterr()

    assert result == 0
    assert "Sync check passed" in captured.out
