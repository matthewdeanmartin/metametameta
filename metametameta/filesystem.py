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


def _find_existing_package_dir(base_path: Path, package_name: str) -> Path | None:
    """Searches for an existing package directory using common layouts."""
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


def _determine_target_dir(base_path: Path, package_name: str) -> Path:
    """
    Determines the ideal target directory for a package.

    It first tries to find an existing directory. If none is found, it decides
    the best location to create one (e.g., inside 'src/' if it exists).
    """
    # 1. Try to find an existing directory first.
    existing_dir = _find_existing_package_dir(base_path, package_name)
    if existing_dir:
        return existing_dir

    # 2. If not found, decide where to create it.
    package_name_underscore = package_name.replace("-", "_")
    if (base_path / "src").is_dir():
        # Prefer 'src' layout if a 'src' directory exists.
        target_dir = base_path / "src" / package_name_underscore
    else:
        # Default to a flat layout.
        target_dir = base_path / package_name_underscore

    logger.debug(f"No existing directory found. Determined target for creation: {target_dir}")
    return target_dir


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
    target_dir = _determine_target_dir(project_root, package_dir_name)
    output_path = target_dir / output_filename

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
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
