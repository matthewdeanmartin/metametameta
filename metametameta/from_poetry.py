"""
This module contains the functions to generate the __about__.py file from the [tool.poetry] section of the
pyproject.toml file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import toml

from metametameta import filesystem
from metametameta.general import any_metadict, merge_sections

logger = logging.getLogger(__name__)


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


# pylint: disable=unused-argument
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
        candidate_packages = []
        packages_data_list = poetry_data.get("packages")
        if packages_data_list:
            for package_data in packages_data_list:
                include_part = None
                from_part = None  # subfolder(s)
                _format_part = None  # can be dist, i.e not a folder
                for key, value in package_data.items():
                    if key == "include":
                        include_part = value
                    elif key == "from":
                        from_part = value
                    elif key == "format":
                        pass
                candidate_path = ""
                if include_part:
                    candidate_path = include_part
                if include_part and from_part:
                    candidate_from_path = Path(candidate_path) / from_part
                    if candidate_from_path.exists():
                        candidate_path = candidate_from_path
                if Path(candidate_path).exists():
                    candidate_packages.append(candidate_path)

        project_name = poetry_data.get("name")
        if not candidate_packages:
            candidate_packages.append(project_name)
        written = []
        for candidate in candidate_packages:
            if output != "__about__.py" and "/" in output or "\\" in output:
                dir_path = "./"
            else:
                dir_path = f"./{candidate}"
            result_tuple = any_metadict(poetry_data)
            about_content, names = result_tuple
            about_content = merge_sections(names, candidate or "", about_content)
            # Define the content to write to the __about__.py file
            result = filesystem.write_to_file(dir_path, about_content, output)
            written.append(result)
    logger.debug("No [tool.poetry] section found in pyproject.toml.")
    return "No [tool.poetry] section found in pyproject.toml."


if __name__ == "__main__":
    generate_from_poetry()
