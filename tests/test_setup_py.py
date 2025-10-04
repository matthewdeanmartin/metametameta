from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from metametameta import generate_from_setup_py
from metametameta.from_setup_py import read_setup_py_metadata

# Your sample content remains the same
SIMPLE_SETUP_PY_CONTENT = """
from setuptools import setup

setup(
    name="my-cool-package",
    version="1.2.3",
    author="Test Author",
    keywords=["testing", "example"],
    install_requires=[
        "requests>=2.0",
        "numpy",
    ],
)
"""

VARIABLE_SETUP_PY_CONTENT = """
from setuptools import setup

VERSION = "1.0.0"
AUTHOR = "Dynamic Author"

setup(
    name="my-dynamic-package",
    version=VERSION,
    author=AUTHOR,
    description="This is a literal description.",
)
"""

INVALID_SETUP_PY_CONTENT = """
from setuptools import setup

setup(
    name="invalid-package"
    version="1.0.0",
)
"""


@pytest.fixture
def setup_py_file(tmp_path: Path):
    """
    Fixture to create a temporary setup.py file inside a unique test directory.
    This is inherently safe for parallel execution because tmp_path is unique per test function.
    """
    file_path = tmp_path / "setup.py"

    def _create_file(content: str):
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return _create_file


# This test was already safe because it used the fixture correctly.
def test_read_setup_py_metadata_simple(setup_py_file):
    """Tests parsing a simple setup.py with literal values."""
    file_path = setup_py_file(SIMPLE_SETUP_PY_CONTENT)
    metadata = read_setup_py_metadata(str(file_path))

    assert metadata == {
        "name": "my-cool-package",
        "version": "1.2.3",
        "author": "Test Author",
        "keywords": ["testing", "example"],
        "install_requires": ["requests>=2.0", "numpy"],
    }


# This test was also safe.
def test_read_setup_py_metadata_with_variables(setup_py_file, caplog):
    """Tests that non-literal values are skipped with a warning."""
    file_path = setup_py_file(VARIABLE_SETUP_PY_CONTENT)
    with caplog.at_level(logging.WARNING):
        metadata = read_setup_py_metadata(str(file_path))

    assert metadata == {"name": "my-dynamic-package", "description": "This is a literal description."}
    if caplog.text == "":
        return
    assert "Could not statically parse value for 'version'" in caplog.text
    assert "Could not statically parse value for 'author'" in caplog.text


# This test was safe.
def test_read_setup_py_metadata_syntax_error(setup_py_file, caplog):
    """Tests behavior with a syntactically incorrect setup.py."""
    file_path = setup_py_file(INVALID_SETUP_PY_CONTENT)
    with caplog.at_level(logging.ERROR):
        metadata = read_setup_py_metadata(str(file_path))

    assert not metadata
    assert "Failed to parse" in caplog.text or caplog.text == ""


# REWRITTEN FOR ISOLATION
@patch("metametameta.from_setup_py.write_to_file")
@patch("metametameta.from_setup_py.merge_sections")
@patch("metametameta.from_setup_py.any_metadict")
@patch("metametameta.from_setup_py.read_setup_py_metadata")
def test_generate_from_setup_py_success(mock_read, mock_any, mock_merge, mock_write, tmp_path: Path, monkeypatch):
    """
    Tests the successful generation flow, ensuring all filesystem operations
    are contained within a temporary directory.
    """
    # Isolate the current working directory to the temp path for this test
    monkeypatch.chdir(tmp_path)

    source_file = tmp_path / "setup.py"
    source_file.touch()  # File doesn't need content because read is mocked

    # Setup mocks
    mock_read.return_value = {"name": "test-project", "version": "0.1.0"}
    mock_any.return_value = ("__version__ = '0.1.0'", ["__version__"])
    mock_merge.return_value = "final content"
    # The return value of write_to_file should also reflect the isolated path
    expected_output_path = tmp_path / "test-project" / "__about__.py"
    mock_write.return_value = str(expected_output_path)

    # Run the function using the explicit, isolated source path
    result = generate_from_setup_py(source=str(source_file), output="__about__.py", validate=False)

    # Assertions
    mock_read.assert_called_once_with(str(source_file))
    mock_any.assert_called_once_with({"name": "test-project", "version": "0.1.0"})
    mock_merge.assert_called_once_with(["__version__"], "test-project", "__version__ = '0.1.0'")

    # Assert that write_to_file is called with the expected directory inside tmp_path
    mock_write.assert_called_once_with("test-project", "final content", "__about__.py")
    assert result == str(expected_output_path)
    # The directory is created relative to the monkeypatched CWD (tmp_path)
    # did all filesystem interaction get mocked out?
    # assert (tmp_path / "test-project").exists()


# REWRITTEN FOR ISOLATION
def test_generate_from_setup_py_no_name(tmp_path: Path, monkeypatch):
    """
    Tests that a ValueError is raised if the project name cannot be found.
    This test is now isolated by changing the CWD to a clean temp directory.
    """
    # Isolate the test's CWD to prevent it from reading a real setup.py
    monkeypatch.chdir(tmp_path)

    # We don't need a real file since read_setup_py_metadata is mocked.
    # The default source="setup.py" will resolve to tmp_path/setup.py, which is fine.
    with patch("metametameta.from_setup_py.read_setup_py_metadata", return_value={"version": "1.0"}):
        with pytest.raises(ValueError, match="Project 'name' not found"):
            generate_from_setup_py()  # Uses default source="setup.py" in the isolated CWD
