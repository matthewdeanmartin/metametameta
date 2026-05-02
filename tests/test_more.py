"""
Tests for high-risk areas: metadata parsing (general.py) and the CLI (__main__.py).
"""

from __future__ import annotations

import importlib
import importlib.metadata as md
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metametameta.__main__ import main as cli_main
from metametameta.find_it import find_metadata_in_module
from metametameta.find_it import main as find_it_main
from metametameta.from_importlib import generate_from_importlib, get_package_metadata
from metametameta.from_setup_cfg import generate_from_setup_cfg, read_setup_cfg_metadata
from metametameta.general import any_metadict, merge_sections, safe_quote
from metametameta.validate_sync import check_sync, normalize_sync_value, read_about_file_ast

# --- Tests for general.py ---


@pytest.mark.parametrize(
    "metadata, expected_lines, expected_names",
    [
        # Test case 1: Basic metadata
        (
            {"name": "my-lib", "version": "1.2.3", "description": "A cool library."},
            ['__title__ = "my-lib"', '__version__ = "1.2.3"', '__description__ = "A cool library."'],
            ["__title__", "__version__", "__description__"],
        ),
        # Test case 2: Single author with email
        (
            {"authors": ["First Last <user@example.com>"]},
            ['__author__ = "First Last"', '__author_email__ = "user@example.com"'],
            ["__author__", "__author_email__"],
        ),
        # Test case 3: Single author without email
        ({"authors": ["Just A. Name"]}, ['__author__ = "Just A. Name"'], ["__author__"]),
        # Test case 4: Multiple authors become credits
        ({"authors": ["Dev One", "Dev Two"]}, ["__credits__ = ['Dev One', 'Dev Two']"], ["__credits__"]),
        # Test case 5: Empty authors list should be ignored
        ({"authors": []}, [], []),
        # Test case 6: Classifiers for status
        (
            {"classifiers": ["Development Status :: 4 - Beta", "License :: OSI Approved :: MIT License"]},
            ['__status__ = "4 - Beta"'],
            ["__status__"],
        ),
        # Test case 7: Keywords list
        ({"keywords": ["one", "two"]}, ["__keywords__ = ['one', 'two']"], ["__keywords__"]),
        # Test case 8: Empty keywords list should be ignored
        ({"keywords": []}, [], []),
        # Test case 9: Empty dependency list should stay typed for mypy/sync checks
        ({"dependencies": []}, ["__dependencies__: list[str] = []"], ["__dependencies__"]),
        # Test case 10: install_requires should normalize to dependencies
        ({"install_requires": []}, ["__dependencies__: list[str] = []"], ["__dependencies__"]),
        # Test case 11: Unsupported value type (dict) should be skipped
        ({"unsupported": {"a": 1}}, [], []),
    ],
)
def test_any_metadict(metadata, expected_lines, expected_names):
    """Tests the any_metadict function with various metadata inputs."""
    about_content, names = any_metadict(metadata)
    # Check that all expected lines are present in the generated content
    for line in expected_lines:
        assert line in about_content
    # Check that the names list matches exactly
    assert sorted(names) == sorted(expected_names)


def test_merge_sections():
    """Tests the merging of docstring, __all__, and content."""
    names = ["__title__", "__version__"]
    project_name = "my-project"
    about_content = '__title__ = "my-project"'
    result = merge_sections(names, project_name, about_content)

    assert '"""Metadata for my-project."""' in result
    assert "__all__ = [" in result
    assert '"__title__"' in result
    assert '"__version__"' in result
    assert '__title__ = "my-project"' in result


@pytest.mark.parametrize(
    "value, expected",
    [
        ("hello", '"hello"'),
        (123, "123"),
        (1.23, "1.23"),
        ("hello\nworld", '"""hello\nworld"""'),
        ('contains """ quotes', '"""contains \\"\\"\\" quotes"""'),
    ],
)
def test_safe_quote(value, expected):
    """Tests the safe_quote function."""
    assert safe_quote(value) == expected


# --- Tests for __main__.py ---


@patch("metametameta.__main__.generate_from_pep621")
def test_cli_pep621_subcommand(mock_generate: MagicMock):
    """Tests if the 'pep621' subcommand calls the correct function."""
    cli_main(["pep621", "--source", "test.toml", "--output", "test_about.py"])
    mock_generate.assert_called_once_with(name="", source="test.toml", output="test_about.py")


@patch("metametameta.__main__.generate_from_poetry")
def test_cli_poetry_subcommand(mock_generate: MagicMock):
    """Tests if the 'poetry' subcommand calls the correct function."""
    cli_main(["poetry"])
    mock_generate.assert_called_once_with(name="", source="pyproject.toml", output="__about__.py")


@patch("metametameta.__main__.generate_from_setup_cfg")
def test_cli_setup_cfg_subcommand(mock_generate: MagicMock):
    """Tests if the 'setup_cfg' subcommand calls the correct function."""
    cli_main(["setup_cfg"])
    mock_generate.assert_called_once_with(name="", source="setup.cfg", output="__about__.py")


@patch("metametameta.__main__.generate_from_importlib")
def test_cli_importlib_subcommand(mock_generate: MagicMock):
    """Tests if the 'importlib' subcommand calls the correct function."""
    cli_main(["importlib", "--name", "my-package"])
    mock_generate.assert_called_once_with(name="my-package", output="__about__.py")


# @patch('logging.config.dictConfig')
# def test_cli_verbose_flag(mock_config: MagicMock):
#     """Tests if --verbose sets the log level to DEBUG."""
#     # Using a subcommand that requires no file I/O mocks
#     with patch('metametameta.__main__.generate_from_importlib'):
#         cli_main(['importlib', '--name', 'pkg', '--verbose'])
#
#     # Check the config passed to dictConfig
#     final_config = mock_config.call_args[0][0]
#     assert final_config['handlers']['default']['level'] == 'DEBUG'
#     assert final_config['loggers']['metametameta']['level'] == 'DEBUG'


@patch("argparse.ArgumentParser.print_help")
def test_cli_no_subcommand(mock_print_help: MagicMock):
    """Tests if running with no subcommand prints help."""
    cli_main([])
    mock_print_help.assert_called_once()


# --- Additional Coverage Gap Tests ---


def test_get_package_metadata_not_found():
    """Test get_package_metadata when package is not found."""
    with patch("importlib.metadata.metadata") as mock_metadata:
        mock_metadata.side_effect = md.PackageNotFoundError
        result = get_package_metadata("non_existent_package_12345")
        assert result == {}


def test_generate_from_importlib_not_found():
    """Test generate_from_importlib when package is not found."""
    with patch("metametameta.from_importlib.get_package_metadata") as mock_get:
        mock_get.return_value = {}
        result = generate_from_importlib("non_existent_package_12345")
        assert "No metadata found for package 'non_existent_package_12345' via importlib." in result


def test_read_setup_cfg_metadata_none():
    """Test read_setup_cfg_metadata with None (defaults to setup.cfg)."""
    with patch("configparser.ConfigParser.read") as mock_read:
        read_setup_cfg_metadata(None)
        mock_read.assert_called_with(Path("setup.cfg"))


def test_read_setup_cfg_metadata_preserves_empty_install_requires(tmp_path):
    """Test read_setup_cfg_metadata keeps empty dependency lists."""
    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.write_text(
        "[metadata]\nname = myproject\nversion = 0.1.0\n\n[options]\ninstall_requires =\n",
        encoding="utf-8",
    )

    metadata = read_setup_cfg_metadata(setup_cfg)

    assert metadata["dependencies"] == []


def test_generate_from_setup_cfg_with_no_dependencies_writes_typed_empty_list(tmp_path, monkeypatch):
    """Test generate_from_setup_cfg writes typed empty dependency lists."""
    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.write_text(
        "[metadata]\nname = myproject\nversion = 0.1.0\n\n[options]\ninstall_requires =\n",
        encoding="utf-8",
    )
    (tmp_path / "myproject").mkdir()
    monkeypatch.chdir(tmp_path)

    generated_path = generate_from_setup_cfg(source=str(setup_cfg), validate=True)
    generated_content = (tmp_path / "myproject" / "__about__.py").read_text(encoding="utf-8")

    assert generated_path.endswith("__about__.py")
    assert "__dependencies__: list[str] = []" in generated_content


def test_generate_from_setup_cfg_no_metadata(tmp_path):
    """Test generate_from_setup_cfg when no [metadata] section is found."""
    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.write_text("[other]\nkey = value", encoding="utf-8")
    result = generate_from_setup_cfg(source=str(setup_cfg))
    assert "No [metadata] section found in setup.cfg." in result


def test_generate_from_setup_cfg_with_slash(tmp_path):
    """Test generate_from_setup_cfg when output has a slash."""
    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.write_text("[metadata]\nname = myproject\nversion = 0.1.0", encoding="utf-8")

    with patch("metametameta.from_setup_cfg.write_to_file") as mock_write:
        mock_write.return_value = "sub/__about__.py"
        generate_from_setup_cfg(source=str(setup_cfg), output="sub/__about__.py", validate=False)
        mock_write.assert_called()
        args, _ = mock_write.call_args
        assert args[0] == "./"


def test_find_it_main():
    """Test main function of find_it."""
    # Test with metametameta itself
    find_it_main(["metametameta"])

    # Direct check of the core logic
    module = importlib.import_module("metametameta")
    assert module.__file__ is not None
    module_path = Path(module.__file__).parent
    results = find_metadata_in_module(module_path)
    assert "__about__" in results
    assert "version" in results["__about__"]


def test_generate_from_setup_cfg_exception(tmp_path):
    """Test generate_from_setup_cfg when any_metadict raises an exception."""
    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.write_text("[metadata]\nname = myproject\nversion = 0.1.0", encoding="utf-8")

    with patch("metametameta.from_setup_cfg.any_metadict") as mock_any:
        mock_any.side_effect = Exception("Parsing error")
        with pytest.raises(Exception, match="Parsing error"):
            generate_from_setup_cfg(source=str(setup_cfg))


def test_find_it_main_no_file():
    """Test main function of find_it with a module that has no file."""
    with patch("importlib.import_module") as mock_import:
        mock_mod = MagicMock()
        mock_mod.__file__ = None
        mock_import.return_value = mock_mod
        with pytest.raises(ValueError, match="has no file attribute"):
            find_it_main(["sys"])


def test_normalize_sync_value_other():
    """Test normalize_sync_value with other types."""
    assert normalize_sync_value(123) == 123


def test_read_about_file_ast_annotated(tmp_path):
    """Test read_about_file_ast with annotated assignments."""
    about_file = tmp_path / "__about__.py"
    about_file.write_text(
        '__version__: str = "1.2.3"\n__title__: str = "test"\n__ignored__ = lambda x: x', encoding="utf-8"
    )
    result = read_about_file_ast(about_file)
    assert result["__version__"] == "1.2.3"
    assert result["__title__"] == "test"
    assert "__ignored__" not in result


def test_read_about_file_ast_non_literal(tmp_path):
    """Test read_about_file_ast with non-literal assignments."""
    about_file = tmp_path / "__about__.py"
    about_file.write_text(
        '__version__ = "1.2.3"\n__title__ = some_func()\n__annotated__: str = other_func()', encoding="utf-8"
    )
    result = read_about_file_ast(about_file)
    assert result["__version__"] == "1.2.3"
    assert "__title__" not in result
    assert "__annotated__" not in result


def test_check_sync_non_string_source(tmp_path):
    """Test check_sync with non-string source value."""
    about_file = tmp_path / "__about__.py"
    about_file.write_text('__title__ = "test"\n', encoding="utf-8")
    source_metadata = {"name": {"not": "a string"}}
    result = check_sync(source_metadata, about_file)
    assert result == []


def test_check_sync_missing_about_value(tmp_path):
    """Test check_sync with missing value in about file."""
    about_file = tmp_path / "__about__.py"
    about_file.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    source_metadata = {"name": "test", "version": "1.2.3"}
    result = check_sync(source_metadata, about_file)
    assert any("__title__" in m and "missing" in m for m in result)
