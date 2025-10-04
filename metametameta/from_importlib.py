"""
Generate an __about__.py file from package metadata using importlib.metadata.
"""

from __future__ import annotations

import importlib.metadata as md
import logging
from typing import Any, cast

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


def get_package_metadata(package_name: str) -> dict[str, Any]:
    """Get package metadata using importlib.metadata."""
    try:
        pkg_metadata: md.PackageMetadata = md.metadata(package_name)
        # dict for 3.8 support
        # pylint: disable=unnecessary-comprehension
        return {key: value for key, value in cast(dict, pkg_metadata).items()}  # type: ignore[type-arg]
    except md.PackageNotFoundError:
        print(f"Package '{package_name}' not found.")
        return {}


# pylint: disable=unused-argument
def generate_from_importlib(name: str, source: str = "", output: str = "__about__.py", validate: bool = False) -> str:
    """Write package metadata to an __about__.py file."""
    pkg_metadata = get_package_metadata(name)
    if pkg_metadata:
        dir_path = "./"

        about_content, names = any_metadict(pkg_metadata)

        about_content = merge_sections(names, name, about_content)
        file_path = write_to_file(dir_path, about_content, output)
        if validate:
            validate_about_file(file_path, pkg_metadata)
        return file_path
    message = "No [project] section found in pyproject.toml."
    logger.debug(message)
    return message


if __name__ == "__main__":
    generate_from_importlib("toml")
