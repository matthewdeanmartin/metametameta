from __future__ import annotations

from pathlib import Path

import pytest

from metametameta.filesystem import PackageDirectoryNotFoundError, write_to_file


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
    # Prepare the directory path; pre-create it because the writer no longer
    # invents package directories from a guessed name.
    dir_path = tmp_path / directory
    dir_path.mkdir(parents=True, exist_ok=True)
    result_path = write_to_file(str(dir_path), about_content, output)

    # Assert that the file was created
    assert Path(result_path).exists()
    # Assert that the content written to the file is as expected
    with open(result_path, encoding="utf-8") as file:
        content = file.read()
        assert content == expected_content


def test_write_to_file_happy_path(tmp_path):
    directory = tmp_path / "example_dir"
    directory.mkdir()
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
    directory.mkdir()
    about_content = "Custom output content."
    output = "custom_output.py"

    file_path = write_to_file(str(directory), about_content, output)

    # Verify that the file is created at the expected path
    assert Path(file_path).is_file()

    # Verify file content
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
        assert content == about_content


def test_write_to_file_raises_when_dir_missing(tmp_path, monkeypatch):
    """If the guessed package dir does not exist, refuse rather than create it."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(PackageDirectoryNotFoundError) as exc_info:
        write_to_file("not_a_real_package", "content")
    msg = str(exc_info.value)
    assert "not_a_real_package" in msg
    assert "--output" in msg
    assert not (tmp_path / "not_a_real_package").exists()
