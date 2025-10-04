# metametameta/validate.py

"""
Validation logic to check if __about__.py is in sync with source metadata.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Mapping from source metadata keys to the expected dunder names in __about__.py
KEY_MAP = {
    "name": "__title__",
    "version": "__version__",
    "description": "__description__",
    "license": "__license__",
    "homepage": "__homepage__",
    "summary": "__description__",  # importlib.metadata uses 'summary'
}


def read_about_file_ast(file_path: Path) -> dict[str, str]:
    """
    Safely reads an __about__.py file using AST to extract metadata.

    This avoids executing the file and is resilient to formatting changes.

    Args:
        file_path: The path to the __about__.py file.

    Returns:
        A dictionary of metadata found in the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Metadata file not found at: {file_path}")

    logger.debug(f"Parsing metadata from {file_path} using AST.")
    content = file_path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    metadata = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("__"):
                    try:
                        value = ast.literal_eval(node.value)
                        # We only care about simple string values for sync checking
                        if isinstance(value, str):
                            metadata[target.id] = value
                    except ValueError:
                        # Ignore values that aren't simple literals (e.g., function calls)
                        logger.debug(f"Skipping non-literal assignment for {target.id}")
    return metadata


def check_sync(source_metadata: dict[str, Any], about_path: Path) -> list[str]:
    """
    Compares source metadata with an __about__.py file to check for sync.

    Args:
        source_metadata: The dictionary of metadata from the source (e.g., pyproject.toml).
        about_path: The path to the __about__.py file to check.

    Returns:
        A list of keys that are out of sync. An empty list means everything is synced.
    """
    logger.info(f"Checking sync between source metadata and {about_path}")
    try:
        about_metadata = read_about_file_ast(about_path)
    except FileNotFoundError as e:
        return [f"File is missing: {e}"]

    mismatches = []

    # Normalize source keys for comparison
    normalized_source = {k.lower().replace("-", "_"): v for k, v in source_metadata.items()}

    for source_key, about_key in KEY_MAP.items():
        if source_key in normalized_source:
            source_value = normalized_source.get(source_key)
            about_value = about_metadata.get(about_key)

            # We only compare simple string values
            if not isinstance(source_value, str):
                logger.debug(f"Skipping sync check for non-string source key '{source_key}'")
                continue

            if about_value is None:
                mismatches.append(f"'{about_key}' is missing from {about_path.name}")
            elif source_value.strip() != about_value.strip():
                mismatch_msg = (
                    f"'{about_key}' is out of sync. Source: '{source_value}', {about_path.name}: '{about_value}'"
                )
                mismatches.append(mismatch_msg)
                logger.warning(mismatch_msg)

    return mismatches
