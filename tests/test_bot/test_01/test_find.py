from __future__ import annotations

import pytest

from metametameta.find import get_meta


@pytest.mark.parametrize(
    "file_content, expected_output",
    [
        ("__title__ = 'My Package'\n__version__ = '1.0.0'\n", {"title": "My Package", "version": "1.0.0"}),
        ("No metadata here.\n", {}),
        (
            "__title__ = 'Invalid Example'\n__version__ = '1.0.0'\n__malformed__ = 'missing quotes\n",
            {"title": "Invalid Example", "version": "1.0.0"},
        ),
        (None, {}),  # Simulating non-existent file
    ],
)
def test_get_meta(tmp_path, file_content, expected_output):
    if file_content is not None:
        # Create a temporary file with the given content
        module_file = tmp_path / "test_module.py"
        module_file.write_text(file_content, encoding="utf-8")
        result = get_meta(str(module_file))
    else:
        result = get_meta("non_existent_file.py")

    assert result == expected_output


def test_get_meta_file_not_found(tmp_path):
    """Test handling when the file does not exist."""
    non_existent_file = tmp_path / "non_existent_module.py"
    result = get_meta(str(non_existent_file))

    # Expecting an empty dict since the file doesn't exist
    assert not result


# Happy path test
def test_get_meta_happy_path(tmp_path):
    """Test the extraction of valid metadata from a file."""
    metadata_file = tmp_path / "module_with_metadata.py"
    content = "__title__ = 'Test Package'\n__version__ = '1.0.0'\n"
    metadata_file.write_text(content, encoding="utf-8")

    result = get_meta(metadata_file)
    expected = {"title": "Test Package", "version": "1.0.0"}
    assert result == expected


# Edge Case: Empty file
def test_get_meta_empty_file(tmp_path):
    """Test handling an empty file."""
    empty_file = tmp_path / "empty_module.py"
    empty_file.write_text("", encoding="utf-8")

    result = get_meta(empty_file)
    assert not result


# Edge Case: File with invalid content
def test_get_meta_file_with_invalid_content(tmp_path):
    """Test handling a file with content that does not match expected metadata pattern."""
    invalid_file = tmp_path / "invalid_module.py"
    invalid_content = "This is not metadata at all\nSome other text"
    invalid_file.write_text(invalid_content, encoding="utf-8")

    result = get_meta(invalid_file)
    assert not result


# Non-existent file (for completeness, but previously covered)
def test_get_meta_file_not_found2(tmp_path):
    """Test handling when the file does not exist."""
    non_existent_file = tmp_path / "non_existent_module.py"
    result = get_meta(non_existent_file)

    # Expecting an empty dict since the file doesn't exist
    assert not result
