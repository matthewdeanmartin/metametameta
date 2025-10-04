"""
This module contains the function to generate the __about__.py file from the pyproject.toml file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

import toml

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


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
    # must be dict for 3.8 support
    return cast(dict, project_data)


# pylint: disable=unused-argument
def generate_from_pep621(
    name: str = "", source: str = "pyproject.toml", output: str = "__about__.py", validate: bool = False
) -> str:
    """
    Generate the __about__.py file from the pyproject.toml file.

    Args:
        validate:
        name (str): Name of the project.
        source (str): Path to the pyproject.toml file.
        output (str): Name of the file to write to.
        validate (bool): Validate file

    Returns:
        str: Path to the file that was written.
    """
    project_data = read_pep621_metadata(source)
    if project_data:
        # Extract the project name and create a directory
        project_name = project_data.get("name", "")
        if not project_name:
            raise TypeError("Project name not found in [project] section of pyproject.toml.")
        if output != "__about__.py" and "/" in output or "\\" in output:
            dir_path = "./"
        else:
            dir_path = f"./{project_name}"

        # if the dir_path does not exist check if project_name.replace("-", "_") exists
        if not Path(dir_path).exists():
            project_name = project_name.replace("-", "_")
            dir_path = f"./{project_name}"

        if not Path(dir_path).exists():
            project_name = project_name.replace("_", "-")
            dir_path = f"./{project_name}"

        result_tuple = None
        try:
            result_tuple = any_metadict(project_data)
            about_content, names = result_tuple
        except Exception:
            print(result_tuple)
            raise
        about_content = merge_sections(names, project_name or "", about_content)
        file_path = write_to_file(dir_path, about_content, output)

        if validate:
            validate_about_file(file_path, project_data)

        return file_path
    logger.debug("No [project] section found in pyproject.toml.")
    return "No [project] section found in pyproject.toml."


if __name__ == "__main__":
    print(generate_from_pep621(source="../pyproject.toml"))
