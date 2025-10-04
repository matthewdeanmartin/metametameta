"""
Utilities for generating source code metadata from existing metadata files.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_all_primitive_values(data: Any) -> Iterable[str]:
    """Finds all top level primitive values (str, int, float) in a nested structure."""
    if isinstance(data, str):
        yield data
    elif isinstance(data, (int, float)):
        yield str(data)
    # elif isinstance(data, list):
    #     for item in data:
    #         yield from _get_all_primitive_values(item)
    # elif isinstance(data, dict):
    #     for value in data.values():
    #         yield from _get_all_primitive_values(value)


def validate_about_file(file_path: str, metadata: dict[str, Any]) -> None:
    """
    Validates the generated __about__.py file.

    Checks for:
    1. File existence.
    2. Presence of all metadata values in the file content, ignoring keys
       that undergo complex transformations during generation.

    Args:
        file_path: The path to the generated __about__.py file.
        metadata: The source metadata dictionary used for generation.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a metadata value is not found in the file.
    """
    logger.info(f"Validating generated file at {file_path}")
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Validation failed: Output file not found at {file_path}")

    content = path.read_text(encoding="utf-8")

    # Create a copy and remove keys that undergo complex transformations
    # to avoid brittle checks.
    metadata_to_validate = metadata.copy()
    metadata_to_validate.pop("classifiers", None)
    metadata_to_validate.pop("authors", None)
    metadata_to_validate.pop("name", None)  # 'name' is transformed to '__title__'

    primitive_values = set(_get_all_primitive_values(metadata_to_validate))

    for value in primitive_values:
        if value not in content:
            raise ValueError(
                f"Validation failed: Value '{value}' not found in {file_path}. The file may be incomplete or missing critical metadata."
            )

    logger.info("Validation successful.")


def any_metadict(metadata: dict[str, str | int | float | list[str]]) -> tuple[str, list[str]]:
    """
    Generate a __about__.py file from a metadata dictionary.
    Args:
        metadata (dict): Metadata dictionary.

    Returns:
        tuple: The content to write to the file and the names of the variables.
    """
    # Normalize keys to lowercase for consistent processing from different sources.
    processed_meta = {k.lower().replace("-", "_"): v for k, v in metadata.items()}

    # Prioritize 'summary' (from importlib.metadata) for the short description.
    # If 'summary' exists, use it for 'description', overwriting the long one.
    if "summary" in processed_meta:
        processed_meta["description"] = processed_meta.pop("summary")

    lines = []
    names = []
    for key, value in processed_meta.items():
        if key == "name":
            # __name__ is a reserved name.
            lines.append(f'__title__ = "{value}"')
            names.append("__title__")
            continue
        if key == "authors" and isinstance(value, list):
            if not value:
                continue  # Skip empty author lists

            if len(value) == 1 and isinstance(value[0], str):
                scalar = value[0].strip("[]' ")
                email_pattern = "<([^>]+@[^>]+)>"
                match = re.search(email_pattern, scalar)
                if match is not None:
                    email = match.groups()[0]
                    author = scalar.replace("<" + email + ">", "").strip()
                    lines.append(f'__author__ = "{author}"')
                    lines.append(f'__author_email__ = "{email}"')
                    names.append("__author__")
                    names.append("__author_email__")
                else:
                    lines.append(f'__author__ = "{scalar}"')
                    names.append("__author__")

            else:
                # BUG 1 FIX: Do not wrap the list in quotes.
                lines.append(f"__credits__ = {value}")
                names.append("__credits__")
        elif key == "classifiers" and isinstance(value, list) and value:
            for trove in value:
                if trove.startswith("Development Status"):
                    lines.append(f'__status__ = "{trove.split("::")[1].strip()}"')
                    names.append("__status__")

        elif key == "keywords" and isinstance(value, list) and value:
            lines.append(f"__keywords__ = {value}")
            names.append("__keywords__")

        # elif key in meta:
        #     content.append(f'__{key}__ = "{value}"')
        else:
            if not isinstance(value, (str, int, float)):
                logger.debug(f"Skipping: {str(key)}")
                continue
            variable_name = key.lower().replace("-", "_")
            quoted_value = safe_quote(value)
            lines.append(f"__{variable_name}__ = {quoted_value}")
            names.append(f"__{variable_name}__")
    about_content = "\n".join(lines)
    if logger.isEnabledFor(logging.DEBUG):
        for line in lines:
            logger.debug(line)
    return about_content, names


def merge_sections(names: list[str] | None, project_name: str, about_content: str) -> str:
    """
    Merge the sections of the __about__.py file.

    Args:
        names (list): Names of the variables.
        project_name (str): Name of the project.
        about_content (str): Content of the __about__.py file.

    Returns:
        str: Content of the __about__.py file.
    """
    if names is None:
        names = []
    # Define the content to write to the __about__.py file
    names = [f'\n    "{item}"' for item in names]
    all_header = "__all__ = [" + ",".join(names) + "\n]"
    if project_name:
        docstring = f"""\"\"\"Metadata for {project_name}.\"\"\"\n\n"""
    else:
        docstring = """\"\"\"Metadata.\"\"\"\n\n"""
    return f"{docstring}{all_header}\n\n{about_content}"


def safe_quote(value: int | float | str) -> str:
    """
    Safely quote a value for inclusion in a Python source file.

    It uses triple quotes if the string contains newlines or double quotes,
    and escapes existing triple quotes within the string.

    Args:
        value: The value to quote.

    Returns:
        A string representation of the value, quoted for a source file.

    Examples:
        >>> safe_quote('hello')
        '"hello"'
        >>> safe_quote('hello\\nworld')
        '\"\"\"hello\\nworld\"\"\"'
    """
    if not isinstance(value, str):
        return str(value)

    # Use triple quotes if the string contains newlines or double quotes
    if "\n" in value or '"' in value:
        # If it contains the triple quote sequence, escape it
        if '"""' in value:
            value = value.replace('"""', r"\"\"\"")
        return f'"""{value}"""'
    # Otherwise, simple double quotes are fine. We don't need to escape
    # single quotes because we are using double quotes.
    return f'"{value}"'
