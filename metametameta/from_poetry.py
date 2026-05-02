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
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


def format_poetry_dependency(name: str, spec: Any) -> str | None:
    """Convert a poetry dependency entry into a string requirement."""
    if name == "python":
        return None
    if isinstance(spec, str):
        return name if spec == "*" else f"{name}{spec}"
    if not isinstance(spec, dict):
        return name

    extras = spec.get("extras", [])
    extras_suffix = f"[{','.join(extras)}]" if isinstance(extras, list) and extras else ""

    if "version" in spec and isinstance(spec["version"], str):
        version = spec["version"]
        return f"{name}{extras_suffix}" if version == "*" else f"{name}{extras_suffix}{version}"
    if "git" in spec and isinstance(spec["git"], str):
        return f"{name}{extras_suffix} @ {spec['git']}"
    if "url" in spec and isinstance(spec["url"], str):
        return f"{name}{extras_suffix} @ {spec['url']}"
    if "path" in spec and isinstance(spec["path"], str):
        return f"{name}{extras_suffix} @ {spec['path']}"
    return f"{name}{extras_suffix}"


def read_poetry_metadata(
    source: str = "pyproject.toml",
) -> dict[str, Any]:
    """
    Read the pyproject.toml file and extract the [tool.poetry] section.

    Args:
        source: Path to the pyproject.toml file.

    Returns:
        The [tool.poetry] section of the pyproject.toml file.
    """
    # Read the pyproject.toml file
    with open(source, encoding="utf-8") as file:
        data = toml.load(file)

    # Extract the [tool.poetry] section
    poetry_data = data.get("tool", {}).get("poetry", {})
    normalized_data = dict(poetry_data)
    dependencies = poetry_data.get("dependencies")
    if isinstance(dependencies, dict):
        normalized_dependencies: list[str] = []
        for dependency_name, dependency_spec in dependencies.items():
            requirement = format_poetry_dependency(dependency_name, dependency_spec)
            if isinstance(requirement, str):
                normalized_dependencies.append(requirement)
        normalized_data["dependencies"] = normalized_dependencies
    return normalized_data


# pylint: disable=unused-argument
def generate_from_poetry(
    name: str = "", source: str = "pyproject.toml", output: str = "__about__.py", validate: bool = True
) -> str:
    """
    Generate the __about__.py file from the pyproject.toml file.

    Args:
        name: Name of the project.
        source: Path to the pyproject.toml file.
        output: Name of the file to write to.
        validate: Check if top level values are in about file after written.

    Returns:
        Path to the file that was written.
    """
    poetry_data = read_poetry_metadata(source)
    if poetry_data:
        candidate_packages: list[str] = []
        packages_data_list = poetry_data.get("packages")
        if packages_data_list:
            for package_data in packages_data_list:
                include_part = None
                from_part = None  # subfolder(s)

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
            if not isinstance(project_name, str) or not project_name:
                raise ValueError("Project name not found in [tool.poetry] section of pyproject.toml.")
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
            file_path = filesystem.write_to_file(dir_path, about_content, output)

            if validate:
                validate_about_file(file_path, poetry_data)

            written.append(file_path)
        if len(written) == 1:
            return written[0]
        return ", ".join(written)
    logger.debug("No [tool.poetry] section found in pyproject.toml.")
    return "No [tool.poetry] section found in pyproject.toml."


if __name__ == "__main__":
    generate_from_poetry()
