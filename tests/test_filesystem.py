import os

from metametameta.filesystem import write_to_file


def test_write_to_file(tmp_path):
    # Test setup: Define directory, content, and expected output file
    directory = tmp_path / "test_package"
    about_content = "__version__ = '1.0.0'"
    output_file_name = "__about__.py"

    # Execution: Call the function
    write_to_file(str(directory), about_content, output_file_name)

    # Expected output file path
    expected_file_path = directory / output_file_name

    # Assertion: Check if the file is created at the correct location
    assert os.path.isfile(expected_file_path), "File was not created at the expected location"

    # Assertion: Check if the content of the file is as expected
    with open(expected_file_path, encoding="utf-8") as file:
        content = file.read()
    assert content == about_content, "Content of the file does not match the expected content"
