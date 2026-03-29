"""Find metadata in a Python module/package."""

from __future__ import annotations

import argparse
import importlib
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def find_metadata_in_file(file_path: Path) -> dict[str, Any]:
    """
    Find metadata variables in a given Python file.

    Searches for variables matching the pattern __key__ = "value".

    Args:
        file_path: Path to the Python file to search.

    Returns:
        Dictionary of metadata key-value pairs found in the file.
    """
    metadata = {}
    with open(file_path, encoding="utf-8") as file:
        content = file.read()
        # Match all possible metadata fields, assuming they follow the format __key__ = value
        matches = re.findall(r"__(\w+)__\s*=\s*['\"]([^'\"]+)['\"]", content)
        for key, value in matches:
            logger.debug(f"Found {key} : {value}")
            metadata[key] = value
    return metadata


def find_metadata_in_module(module_path: Path) -> dict[str, dict[str, Any]]:
    """
    Traverse a module/package directory and find metadata in all submodules.

    Looks for Python files containing "about" in their name that also
    contain version metadata.

    Args:
        module_path: Path to the module or package directory to search.

    Returns:
        Dictionary mapping module names to their metadata dictionaries.
    """
    metadata_results = {}
    for root, _dirs, files in os.walk(module_path):
        for file in files:
            if file.endswith(".py") and "about" in file:
                file_path = Path(root) / file
                metadata = find_metadata_in_file(file_path)
                if "version" in metadata:  # Check if this file has metadata
                    module_name = file_path.relative_to(module_path).with_suffix("")
                    metadata_results[str(module_name).replace(os.sep, ".")] = metadata
    return metadata_results


def main(argv: list[str] | None = None) -> None:
    """Find metadata in a Python module/package."""
    parser = argparse.ArgumentParser(description="Find metadata in a Python module/package.")
    parser.add_argument("module", type=str, help="The name of the module/package to inspect.")
    args = parser.parse_args(argv)

    module_name = args.module
    module = importlib.import_module(module_name)
    if not module.__file__:
        raise ValueError(f"Module {module_name} has no file attribute.")
    module_path = Path(module.__file__).parent

    metadata_results = find_metadata_in_module(module_path)
    for submodule, metadata in metadata_results.items():
        logger.debug(f"Metadata for {submodule}:")
        for key, value in metadata.items():
            logger.debug(f"  {key}: {value}")
        logger.debug("")


if __name__ == "__main__":
    main(["metametameta"])
