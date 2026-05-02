# filesystem.py

"""
This module contains robust functions for writing to the filesystem, intelligently
locating the correct Python package directory within a given project root.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# --- Private Helper Functions ---


def find_existing_package_dir(base_path: Path, package_name: str) -> Path | None:
    """
    Search for an existing package directory using common layouts.

    Checks for directories matching the package name with hyphens replaced
    by underscores, the original name, and src-layout variants.

    Args:
        base_path: The root directory to search in.
        package_name: The name of the package to find.

    Returns:
        The Path to the first existing package directory found, or None.
    """
    package_name_underscore = package_name.replace("-", "_")

    # Define a clear, prioritized list of candidate directories to check.
    # Python-standard underscored names are checked first.
    candidate_dirs = [
        base_path / package_name_underscore,
        base_path / package_name,
        base_path / "src" / package_name_underscore,
        base_path / "src" / package_name,
    ]

    for candidate in candidate_dirs:
        if candidate.is_dir():
            logger.debug(f"Found existing package directory at: {candidate}")
            return candidate

    logger.debug(f"No existing package directory found for '{package_name}'.")
    return None


class PackageDirectoryNotFoundError(FileNotFoundError):
    """Raised when the package directory cannot be located by the project name."""


def _format_missing_package_message(base_path: Path, package_name: str) -> str:
    """Build a helpful error message describing how to point at the right module."""
    # Normalize names like "./demo-app" or ".\demo-app" to a bare package name
    # for the suggestion, so the hint reads cleanly.
    bare_name = package_name.lstrip("./").lstrip(".\\")
    bare_name_underscore = bare_name.replace("-", "_")
    searched = [
        base_path / bare_name_underscore,
        base_path / bare_name,
        base_path / "src" / bare_name_underscore,
        base_path / "src" / bare_name,
    ]
    searched_lines = "\n".join(f"  - {p}" for p in searched)
    suggested_output = f"{bare_name_underscore}/__about__.py"
    return (
        f"Could not locate a package directory for '{bare_name}' under {base_path}.\n"
        f"Searched:\n{searched_lines}\n\n"
        "metametameta will not create a new top-level package directory because "
        "guessing the module name from the project name is unreliable.\n\n"
        "To fix this, either:\n"
        f"  1. Create the package directory yourself (e.g. `{bare_name_underscore}/`) "
        "and re-run the command, or\n"
        f"  2. Pass an explicit path via --output, e.g. `--output {suggested_output}` "
        "(or `--output src/your_module/__about__.py` for a src-layout project)."
    )


def determine_target_dir(base_path: Path, package_name: str) -> Path:
    """
    Determines the target directory for a package.

    Locates an existing directory matching the package name. Raises
    :class:`PackageDirectoryNotFoundError` if no such directory exists, rather
    than guessing a location and creating an empty package.
    """
    existing_dir = find_existing_package_dir(base_path, package_name)
    if existing_dir:
        return existing_dir

    raise PackageDirectoryNotFoundError(_format_missing_package_message(base_path, package_name))


# --- New, Preferred Public Function ---


def write_to_package_dir(
    project_root: Path,
    package_dir_name: str,
    about_content: str,
    output_filename: str = "__about__.py",
) -> str:
    """
    Deterministically writes content to a file within the correct package directory.

    This is the preferred function for new code as it is not dependent on the
    current working directory.

    Args:
        project_root: The absolute path to the project's root directory.
        package_dir_name: The target package directory name (e.g., "my-project").
        about_content: The string content to write to the file.
        output_filename: The name of the file to write (e.g., "__about__.py").

    Returns:
        The full path to the file that was written as a string.
    """
    target_dir = determine_target_dir(project_root, package_dir_name)
    output_path = target_dir / output_filename

    try:
        # target_dir is guaranteed to exist (determine_target_dir would have raised
        # otherwise). Only create parents needed for a nested output_filename.
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(about_content, encoding="utf-8")
        logger.info(f"Successfully wrote metadata to {output_path}")
        return str(output_path)
    except OSError as e:
        logger.error(f"Failed to write to file {output_path}: {e}")
        raise


# --- Legacy Backward-Compatible Wrapper ---


def write_to_file(directory: str, about_content: str, output: str = "__about__.py") -> str:
    """
    Writes content to a file within a target directory.

    Note: This function is for backward compatibility. Its behavior depends on the
    current working directory. For deterministic and testable behavior, please use
    `write_to_package_dir()` instead.
    """
    # Preserve original non-deterministic behavior by using cwd()
    project_root = Path.cwd()

    return write_to_package_dir(
        project_root=project_root,
        package_dir_name=directory,
        about_content=about_content,
        output_filename=output,
    )
