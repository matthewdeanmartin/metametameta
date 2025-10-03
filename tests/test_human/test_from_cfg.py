from __future__ import annotations

import os

from metametameta import generate_from_setup_cfg


def test_generate_from_setup_cfg(tmp_path):
    # Create a minimal setup.cfg in the tmp_path directory
    setup_cfg_path = tmp_path / "setup.cfg"
    with open(setup_cfg_path, "w", encoding="utf-8") as file:
        file.write("[metadata]\n")
        file.write("name = MyProject\n")
        file.write("version = 1.0.0\n")
        # Add more metadata fields as needed

    # Store the original cwd and temporarily change cwd to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Execution: Call the function
        generate_from_setup_cfg()

        # Expected output file path
        expected_file_path = tmp_path / "MyProject/__about__.py"

        # Assertion: Check if the file is created at the correct location
        assert os.path.isfile(expected_file_path), "File was not created at the expected location"

        # Assertion: Check the content of the file
        with open(expected_file_path, encoding="utf-8") as file:
            content = file.read()
        # Define the expected content based on the metadata in setup.cfg
        expected_content = '''"""Metadata for MyProject."""

__all__ = [
    "__title__",
    "__version__"
]

__title__ = "MyProject"
__version__ = "1.0.0"'''
        assert content == expected_content, "Content of the file does not match the expected content"
    finally:
        # Revert the cwd back to the original
        os.chdir(original_cwd)
