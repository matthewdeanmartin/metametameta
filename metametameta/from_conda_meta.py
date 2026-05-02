"""
Generate metadata from a conda recipe meta.yaml file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


def strip_matching_quotes(value: str) -> str:
    """Strip matching single or double quotes from a string."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def strip_comment(value: str) -> str:
    """Strip YAML-style comments from a line."""
    if " #" in value:
        return value.split(" #", maxsplit=1)[0].rstrip()
    return value.rstrip()


def infer_project_name(source_path: Path) -> str:
    """Infer a project name from the recipe location."""
    parent = source_path.resolve().parent
    if parent.name == "conda" and parent.parent.name:
        return parent.parent.name
    return parent.name


def read_conda_meta_metadata(source: str = "conda/meta.yaml", name: str = "") -> dict[str, Any]:
    """
    Read metadata from a conda recipe.

    Args:
        source: Path to the conda meta.yaml file.
        name: Optional explicit project name override.

    Returns:
        A metadata dictionary with the supported fields extracted.
    """
    source_path = Path(source)
    parsed: dict[str, Any] = {"package": {}, "about": {}, "requirements": {"run": []}}
    current_section = ""
    current_subsection = ""

    for raw_line in source_path.read_text(encoding="utf-8").splitlines():
        without_comment = strip_comment(raw_line)
        stripped = without_comment.strip()
        if not stripped or stripped.startswith("{%"):
            continue

        indent = len(without_comment) - len(without_comment.lstrip(" "))

        if stripped.endswith(":") and not stripped.startswith("- "):
            section_name = stripped[:-1].strip()
            if indent == 0:
                current_section = section_name
                current_subsection = ""
            else:
                current_subsection = section_name
            continue

        if stripped.startswith("- "):
            item = strip_matching_quotes(stripped[2:].strip())
            if current_section == "requirements" and current_subsection:
                parsed["requirements"].setdefault(current_subsection, []).append(item)
            continue

        if ":" not in stripped:
            continue

        key, value = stripped.split(":", maxsplit=1)
        cleaned_value = strip_matching_quotes(value.strip())
        if current_section in {"package", "about"}:
            parsed[current_section][key.strip()] = cleaned_value

    package_data = parsed.get("package", {})
    about_data = parsed.get("about", {})
    run_dependencies = parsed.get("requirements", {}).get("run", [])

    project_name = name or package_data.get("name") or infer_project_name(source_path)

    metadata: dict[str, Any] = {"name": project_name}
    if package_data.get("version"):
        metadata["version"] = package_data["version"]
    if about_data.get("summary"):
        metadata["summary"] = about_data["summary"]
    elif about_data.get("description"):
        metadata["description"] = about_data["description"]
    if about_data.get("license"):
        metadata["license"] = about_data["license"]
    if about_data.get("home"):
        metadata["homepage"] = about_data["home"]
    metadata["dependencies"] = run_dependencies

    return metadata


def generate_from_conda_meta(
    name: str = "", source: str = "conda/meta.yaml", output: str = "__about__.py", validate: bool = False
) -> str:
    """
    Generate the metadata file from conda/meta.yaml.

    Args:
        name: Explicit project name override.
        source: Path to the conda recipe.
        output: Name of the file to write to.
        validate: Validate file after writing.

    Returns:
        Path to the file that was written.
    """
    metadata = read_conda_meta_metadata(source=source, name=name)
    project_name = metadata.get("name", "")
    if not project_name:
        raise ValueError("Project name could not be determined from conda/meta.yaml.")

    if output != "__about__.py" and ("/" in output or "\\" in output):
        dir_path = "./"
    else:
        dir_path = f"./{project_name}"

    about_content, names = any_metadict(metadata)
    about_content = merge_sections(names, project_name, about_content)
    file_path = write_to_file(dir_path, about_content, output)
    if validate:
        validate_about_file(file_path, metadata)
    return file_path
