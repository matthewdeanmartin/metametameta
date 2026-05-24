"""
Utilities for generating source code metadata from existing metadata files.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
preferred_line_length = 120


def indent_multiline_value(value: str, indent: str) -> str:
    """Indent each line in a multiline rendered value."""
    return "\n".join(f"{indent}{line}" for line in value.splitlines())


def render_python_value(value: Any, indent: int = 0) -> str:
    """Render a Python literal using double quotes and stable trailing commas."""
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "None"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        inline = "[" + ", ".join(render_python_value(item) for item in value) + "]"
        if len(inline) <= preferred_line_length - indent:
            return inline
        inner_indent = " " * (indent + 4)
        rendered_items = []
        for item in value:
            rendered_item = render_python_value(item, indent + 4)
            if "\n" in rendered_item:
                rendered_items.append(f"{indent_multiline_value(rendered_item, inner_indent)},")
            else:
                rendered_items.append(f"{inner_indent}{rendered_item},")
        closing_indent = " " * indent
        return "[\n" + "\n".join(rendered_items) + f"\n{closing_indent}]"
    if isinstance(value, dict):
        inline_parts = [f"{json.dumps(str(key), ensure_ascii=True)}: {render_python_value(item)}" for key, item in value.items()]
        inline = "{" + ", ".join(inline_parts) + "}"
        if len(inline) <= preferred_line_length - indent:
            return inline
        inner_indent = " " * (indent + 4)
        rendered_items = []
        for key, item in value.items():
            rendered_item = render_python_value(item, indent + 4)
            if "\n" in rendered_item:
                first_line = f"{inner_indent}{json.dumps(str(key), ensure_ascii=True)}: {rendered_item.splitlines()[0]}"
                remaining_lines = [f"{inner_indent}{line}" for line in rendered_item.splitlines()[1:]]
                rendered_items.append("\n".join([first_line, *remaining_lines]) + ",")
            else:
                rendered_items.append(f"{inner_indent}{json.dumps(str(key), ensure_ascii=True)}: {rendered_item},")
        closing_indent = " " * indent
        return "{\n" + "\n".join(rendered_items) + f"\n{closing_indent}}}"
    return repr(value)


def render_collection_assignment(variable_name: str, value: list[Any] | dict[str, Any]) -> str:
    """Render a collection assignment in a formatter-stable layout."""
    inline_assignment = f"__{variable_name}__ = {render_python_value(value)}"
    if len(inline_assignment) <= preferred_line_length:
        return inline_assignment
    multiline_value = render_python_value(value)
    return f"__{variable_name}__ = {multiline_value}"


def render_string_list(variable_name: str, values: list[str]) -> str:
    """Render a string list assignment, annotating empty lists for static typing."""
    if values:
        return render_collection_assignment(variable_name, values)
    return f"__{variable_name}__: list[str] = []"


def get_all_primitive_values(data: Any) -> Iterable[str]:
    """Finds all top level primitive values (str, int, float) in a nested structure."""
    if isinstance(data, str):
        yield data
    elif isinstance(data, (int, float)):
        yield str(data)
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            yield from get_all_primitive_values(item)


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

    primitive_values = set(get_all_primitive_values(metadata_to_validate))

    for value in primitive_values:
        if value not in content:
            raise ValueError(f"Validation failed: Value '{value}' not found in {file_path}. The file may be incomplete or missing critical metadata.")

    logger.info("Validation successful.")


def any_metadict(metadata: dict[str, str | int | float | list[str]]) -> tuple[str, list[str]]:
    """
    Generate __about__.py content from a metadata dictionary.

    Args:
        metadata: Dictionary containing project metadata.

    Returns:
        A tuple containing the file content and list of variable names.
    """
    # Normalize keys to lowercase for consistent processing from different sources.
    processed_meta = {k.lower().replace("-", "_"): v for k, v in metadata.items()}
    if "install_requires" in processed_meta and "dependencies" not in processed_meta:
        processed_meta["dependencies"] = processed_meta.pop("install_requires")

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
                lines.append(render_collection_assignment("credits", value))
                names.append("__credits__")
        elif key == "classifiers" and isinstance(value, list) and value:
            for trove in value:
                if trove.startswith("Development Status"):
                    lines.append(f'__status__ = "{trove.split("::")[1].strip()}"')
                    names.append("__status__")

        elif key == "keywords" and isinstance(value, list) and value:
            lines.append(render_collection_assignment("keywords", value))
            names.append("__keywords__")
        elif key == "dependencies" and isinstance(value, list):
            lines.append(render_string_list("dependencies", value))
            names.append("__dependencies__")

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
        names: Names of the variables to include in __all__.
        project_name: Name of the project for the docstring.
        about_content: Content of the __about__.py file.

    Returns:
        The complete __about__.py file content.
    """
    if names is None:
        names = []
    names = sorted(dict.fromkeys(names))
    exported_names = render_python_value(names)
    all_header = f"__all__ = {exported_names}"
    if len(all_header) > preferred_line_length:
        all_header = f"__all__ = {render_python_value(names)}"
    if project_name:
        docstring = f"""\"\"\"Metadata for {project_name}.\"\"\"\n\n"""
    else:
        docstring = """\"\"\"Metadata.\"\"\"\n\n"""
    return f"{docstring}{all_header}\n\n{about_content}\n"


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
