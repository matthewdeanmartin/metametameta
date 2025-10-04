"""
Tests for high-risk areas: metadata parsing (general.py) and the CLI (__main__.py).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from metametameta.__main__ import main as cli_main
from metametameta.general import any_metadict, merge_sections, safe_quote

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
        # Test case 9: Unsupported value type (dict) should be skipped
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
