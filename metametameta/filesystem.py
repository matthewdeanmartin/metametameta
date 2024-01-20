"""
This module contains functions for working with the filesystem.
"""
import os
from pathlib import Path


def write_to_file(directory: str, about_content: str, output: str = "__about__.py") -> str:
    """
    Write the content to the __about__.py file.
    Args:
        directory (str): Directory to write the file to.
        about_content (str): Content to write to the file.
        output (str): Name of the file to write to.

    Returns:
        str: Path to the file that was written.
    """
    # Define the path for the __about__.py file
    about_file_path = os.path.join(directory, output)

    if output.endswith(".py"):
        combined_directory = Path(about_file_path).parent
    else:
        combined_directory = Path(about_file_path)

    os.makedirs(str(combined_directory), exist_ok=True)

    # Write the content to the __about__.py file
    with open(about_file_path, "w", encoding="utf-8") as file:
        file.write(about_content)
    return about_file_path
