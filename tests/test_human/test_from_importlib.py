import os

from metametameta import generate_from_importlib


def test_generate_from_importlib(tmp_path, mocker):
    # Simulated package name and metadata
    package_name = "SimulatedPackage"
    simulated_metadata = {
        "name": package_name,
        "version": "1.0.2",
        "author": "Author Name",
        "author-email": "author@example.com",
        # Add more metadata fields as needed
    }

    # Mock the importlib.metadata.metadata function
    _mocked_metadata = mocker.patch("importlib.metadata.metadata", return_value=simulated_metadata)

    # Store the original cwd and temporarily change cwd to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Execution: Call the function
        generate_from_importlib(package_name)

        # Expected output file path
        expected_file_path = tmp_path / "__about__.py"

        # Assertion: Check if the file is created at the correct location
        assert os.path.isfile(expected_file_path), "File was not created at the expected location"

        # Assertion: Check the content of the file
        with open(expected_file_path, encoding="utf-8") as file:
            content = file.read()
        # Define the expected content based on the simulated metadata
        expected_content = '''"""Metadata for SimulatedPackage."""

__all__ = [
    "__title__",
    "__version__",
    "__author__",
    "__author_email__"
]

__title__ = "SimulatedPackage"
__version__ = "1.0.2"
__author__ = "Author Name"
__author_email__ = "author@example.com"'''
        assert content == expected_content, "Content of the file does not match the expected content"
    finally:
        # Revert the cwd back to the original
        os.chdir(original_cwd)
