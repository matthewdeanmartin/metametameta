"""
This module contains the functions to generate the __about__.py file from the [tool.poetry] section of the
pyproject.toml file.
"""
from typing import Any

import toml

from metametameta import filesystem, general


def read_poetry_metadata(
    source: str = "pyproject.toml",
) -> Any:
    """
    Read the pyproject.toml file and extract the [tool.poetry] section.
    Args:
        source (str): Path to the pyproject.toml file.

    Returns:
        dict: The [tool.poetry] section of the pyproject.toml file.
    """
    # Read the pyproject.toml file
    with open(source, encoding="utf-8") as file:
        data = toml.load(file)

    # Extract the [tool.poetry] section
    poetry_data = data.get("tool", {}).get("poetry", {})
    return poetry_data


def generate_from_poetry(name: str = "", source: str = "pyproject.toml", output: str = "__about__.py") -> str:
    """
    Generate the __about__.py file from the pyproject.toml file.
    Args:
        name (str): Name of the project.
        source (str): Path to the pyproject.toml file.
        output (str): Name of the file to write to.

    Returns:
        str: Path to the file that was written.
    """
    poetry_data = read_poetry_metadata(source)
    if poetry_data:
        project_name = poetry_data.get("name")
        if output != "__about__.py" and "/" in output or "\\" in output:
            dir_path = "./"
        else:
            dir_path = f"./{project_name}"
        about_content, names = general.any_metadict(poetry_data)
        about_content = general.merge_sections(names, project_name or "", about_content)
        # Define the content to write to the __about__.py file
        return filesystem.write_to_file(dir_path, about_content, output)
    return "No [tool.poetry] section found in pyproject.toml."


if __name__ == "__main__":
    generate_from_poetry()
