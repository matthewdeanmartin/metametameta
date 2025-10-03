from __future__ import annotations

from pathlib import Path

import pytest

from metametameta.filesystem import write_to_file


@pytest.mark.parametrize(
    "directory, about_content, output, expected_content",
    [
        ("test_dir", "This is a test.", "__about__.py", "This is a test."),
        ("another_test_dir", "Another test content.", "my_about.py", "Another test content."),
        ("dir-with- hyphen", "Testing hyphen in directory.", "__about__.py", "Testing hyphen in directory."),
        ("src/test_src", "Inside src directory.", "__about__.py", "Inside src directory."),
    ],
)
def test_write_to_file(tmp_path, directory, about_content, output, expected_content):
    # Prepare the directory path
    dir_path = tmp_path / directory
    result_path = write_to_file(str(dir_path), about_content, output)

    # Assert that the file was created
    assert Path(result_path).exists()
    # Assert that the content written to the file is as expected
    with open(result_path, encoding="utf-8") as file:
        content = file.read()
        assert content == expected_content


def test_write_to_file_happy_path(tmp_path):
    directory = tmp_path / "example_dir"
    about_content = "This is the __about__.py content."
    output = "__about__.py"

    file_path = write_to_file(str(directory), about_content, output)

    # Verify that the file is created at the expected path
    assert Path(file_path).is_file()

    # Verify file content
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
        assert content == about_content


def test_write_to_file_with_custom_output(tmp_path):
    directory = tmp_path / "another_dir"
    about_content = "Custom output content."
    output = "custom_output.py"

    file_path = write_to_file(str(directory), about_content, output)

    # Verify that the file is created at the expected path
    assert Path(file_path).is_file()

    # Verify file content
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
        assert content == about_content
