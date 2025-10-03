"""
This module contains an experimental function to generate the __about__.py file
by statically parsing a setup.py file using Python's AST module.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections

logger = logging.getLogger(__name__)


class SetupKwargsVisitor(ast.NodeVisitor):
    """An AST visitor to find keyword arguments in a setup() call."""

    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}
        self._found = False

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a Call node in the AST."""
        # Only capture the first valid setup() call we find.
        if self._found:
            return

        func_is_setup = False
        if isinstance(node.func, ast.Name) and node.func.id == "setup":
            func_is_setup = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "setup":
            # This covers `setuptools.setup()`
            func_is_setup = True

        if func_is_setup:
            for keyword in node.keywords:
                if keyword.arg:  # Ensure there is an argument name
                    try:
                        # Safely evaluate the value of the keyword argument
                        self.kwargs[keyword.arg] = ast.literal_eval(keyword.value)
                    except ValueError:
                        # This happens if the value is not a literal (e.g., a variable)
                        logger.warning(
                            f"Could not statically parse value for '{keyword.arg}' in setup.py. "
                            "Only literals (strings, numbers, lists, etc.) are supported."
                        )
            self._found = True

        # Continue traversing to find the call if it's nested
        self.generic_visit(node)


def read_setup_py_metadata(source: str = "setup.py") -> dict[str, Any]:
    """
    Reads a setup.py file and extracts metadata from the setup() call using AST.
    This method does not execute the file.
    """
    source_path = Path(source)
    if not source_path.exists():
        logger.error(f"Source file not found: {source}")
        return {}

    try:
        source_code = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source_code)
        visitor = SetupKwargsVisitor()
        visitor.visit(tree)
        return visitor.kwargs
    except (SyntaxError, UnicodeDecodeError) as e:
        logger.error(f"Failed to parse {source}: {e}")
        return {}


def generate_from_setup_py(name: str = "", source: str = "setup.py", output: str = "__about__.py") -> str:
    """
    Generate the __about__.py file from a setup.py file.
    """
    metadata = read_setup_py_metadata(source)
    if not metadata:
        message = "No setup() call with static metadata found in setup.py."
        logger.debug(message)
        return message

    # Use the name from the metadata, but allow CLI to override it if provided
    project_name = name or metadata.get("name", "")
    if not project_name:
        raise ValueError("Project 'name' not found in setup.py and not provided via arguments.")

    about_content, names = any_metadict(metadata)
    about_content = merge_sections(names, project_name, about_content)

    return write_to_file(project_name, about_content, output)
