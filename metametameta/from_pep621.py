"""
This module contains the function to generate the __about__.py file from the pyproject.toml file.
"""

from typing import Any, cast

import toml

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections


def read_pep621_metadata(source: str = "pyproject.toml") -> dict[str, Any]:
    """
    Read the pyproject.toml file and extract the [project] section.
    Args:
        source (str): Path to the pyproject.toml file.

    Returns:
        dict: The [project] section of the pyproject.toml file.
    """
    # Read the pyproject.toml file
    with open(source, encoding="utf-8") as file:
        data = toml.load(file)

    # Extract the [project] section
    project_data = data.get("project", {})
    return cast(dict[str, Any], project_data)


def generate_from_pep621(name: str = "", source: str = "pyproject.toml", output: str = "__about__.py") -> str:
    """
    Generate the __about__.py file from the pyproject.toml file.

    Args:
        name (str): Name of the project.
        source (str): Path to the pyproject.toml file.
        output (str): Name of the file to write to.

    Returns:
        str: Path to the file that was written.
    """
    project_data = read_pep621_metadata(source)
    if project_data:
        # Extract the project name and create a directory
        project_name = project_data.get("name")
        if output != "__about__.py" and "/" in output or "\\" in output:
            dir_path = "./"
        else:
            dir_path = f"./{project_name}"

        result_tuple = None
        try:
            result_tuple = any_metadict(project_data)
            about_content, names = result_tuple
        except Exception:
            print(result_tuple)
            raise
        about_content = merge_sections(names, project_name or "", about_content)
        return write_to_file(dir_path, about_content, output)
    return "No [project] section found in pyproject.toml."


if __name__ == "__main__":
    generate_from_pep621()
