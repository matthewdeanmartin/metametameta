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
    """
    Get package metadata using importlib.metadata.

    Args:
        package_name: The name of the package to get metadata for.

    Returns:
        Dictionary containing the package metadata.
    """
    try:
        pkg_metadata: md.PackageMetadata = md.metadata(package_name)
        # Core-metadata headers like "Classifier" and "Project-URL" legitimately
        # repeat. A plain dict comprehension over .items() keeps only the last
        # occurrence, silently dropping every classifier but one. Use get_all()
        # (available on the real message object) to preserve multi-valued fields
        # as lists, collapsing each header only once. Fall back gracefully when
        # the object is a plain mapping without get_all() (e.g. in tests).
        get_all = getattr(pkg_metadata, "get_all", None)
        result: dict[str, Any] = {}
        for key in cast(dict, pkg_metadata).keys():  # type: ignore[type-arg]
            if key in result:
                continue
            all_values = get_all(key) if get_all is not None else None
            if all_values is not None and len(all_values) > 1:
                result[key] = list(all_values)
            else:
                result[key] = pkg_metadata[key]
        return result
    except md.PackageNotFoundError:
        print(f"Package '{package_name}' not found.")
        return {}


# pylint: disable=unused-argument
def generate_from_importlib(name: str, source: str = "", output: str = "__about__.py", validate: bool = False) -> str:
    """
    Write package metadata to an __about__.py file.

    Args:
        name: Name of the package to get metadata from.
        source: Ignored (present for API compatibility).
        output: Name of the file to write to.
        validate: Validate file after writing.

    Returns:
        Path to the file that was written, or a message if no metadata was found.
    """
    pkg_metadata = get_package_metadata(name)
    if pkg_metadata:
        dir_path = "./"

        about_content, names = any_metadict(pkg_metadata)

        about_content = merge_sections(names, name, about_content)
        file_path = write_to_file(dir_path, about_content, output)
        if validate:
            validate_about_file(file_path, pkg_metadata)
        return file_path
    message = f"No metadata found for package '{name}' via importlib."
    logger.debug(message)
    return message


if __name__ == "__main__":
    generate_from_importlib("toml")
