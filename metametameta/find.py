"""
Find metadata in a module file.
"""

from __future__ import annotations

import inspect
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)


def get_module_file(module: Any) -> str:
    """
    Get the file path associated with a module.

    Args:
        module: The module object to get the file path for.

    Returns:
        The absolute path to the module's source file.
    """
    return inspect.getfile(module)


def is_package(module: Any) -> bool:
    """
    Check if a module is a package (i.e., an __init__.py file).

    Args:
        module: The module object to check.

    Returns:
        True if the module is a package, False otherwise.
    """
    module_file = get_module_file(module)
    return os.path.basename(module_file) == "__init__.py"


def get_meta(module_file: Any) -> dict[str, str]:
    """
    Extract metadata variables from a module file.

    Searches for variables matching the pattern __key__ = "value" and
    returns them as a dictionary.

    Args:
        module_file: Path to the module file or the module object.

    Returns:
        Dictionary of metadata key-value pairs found in the file.
    """
    metadata = {}
    if module_file and os.path.isfile(module_file):
        with open(module_file, encoding="utf-8") as file:
            content = file.read()

        # Define a regex pattern to match metadata variables
        pattern = r"__(\w+)__\s*=\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, content)

        for key, value in matches:
            metadata[key] = value
    return metadata


# # Usage example:
# try:
#     # ... some code that raises CustomError ...
#     raise CustomError("An error occurred")
# except CustomError as ce:
#     module = get_module(ce)
#     module_file = get_module_file(module)
#     metadata = get_meta(module_file)
#     print(metadata)
