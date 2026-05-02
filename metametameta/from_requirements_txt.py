"""
Generate metadata from a requirements.txt file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)

SKIPPED_PREFIXES = (
    "-r",
    "--requirement",
    "-c",
    "--constraint",
    "-i",
    "--index-url",
    "--extra-index-url",
    "-f",
    "--find-links",
    "--trusted-host",
)


def strip_matching_quotes(value: str) -> str:
    """Strip matching single or double quotes from a string."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def strip_inline_comment(line: str) -> str:
    """Strip trailing comments while preserving URL fragments like #egg."""
    if " #" in line:
        return line.split(" #", maxsplit=1)[0].rstrip()
    return line.rstrip()


def parse_requirement_line(line: str) -> str | None:
    """Parse a single requirements.txt line into a dependency string."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if stripped.startswith(SKIPPED_PREFIXES):
        return None

    if stripped.startswith(("-e ", "--editable ")):
        parts = stripped.split(maxsplit=1)
        stripped = parts[1].strip() if len(parts) == 2 else ""

    stripped = strip_inline_comment(stripped)
    if not stripped:
        return None

    if "#egg=" in stripped:
        return strip_matching_quotes(stripped.split("#egg=", maxsplit=1)[1].strip())

    return strip_matching_quotes(stripped)


def infer_project_name(source_path: Path) -> str:
    """Infer a project name from the requirements file location."""
    return source_path.resolve().parent.name


def read_requirements_txt_metadata(source: str = "requirements.txt", name: str = "") -> dict[str, Any]:
    """
    Read dependency metadata from a requirements.txt file.

    Args:
        source: Path to the requirements file.
        name: Optional explicit project name override.

    Returns:
        Minimal metadata containing the project name and dependencies.
    """
    source_path = Path(source)
    requirements = []
    for line in source_path.read_text(encoding="utf-8").splitlines():
        parsed = parse_requirement_line(line)
        if parsed:
            requirements.append(parsed)

    project_name = name or infer_project_name(source_path)
    metadata: dict[str, Any] = {"name": project_name, "dependencies": requirements}
    return metadata


def generate_from_requirements_txt(
    name: str = "", source: str = "requirements.txt", output: str = "__about__.py", validate: bool = False
) -> str:
    """
    Generate the metadata file from requirements.txt.

    Args:
        name: Explicit project name override.
        source: Path to the requirements.txt file.
        output: Name of the file to write to.
        validate: Validate file after writing.

    Returns:
        Path to the file that was written.
    """
    metadata = read_requirements_txt_metadata(source=source, name=name)
    project_name = metadata.get("name", "")
    if not project_name:
        raise ValueError("Project name could not be determined from requirements.txt.")

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
