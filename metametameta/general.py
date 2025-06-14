"""
Utilities for generating source code metadata from existing metadata files.
"""

import logging
import re
from typing import Optional, Union

logger = logging.getLogger(__name__)


def any_metadict(metadata: dict[str, Union[str, int, float, list[str]]]) -> tuple[str, list[str]]:
    """
    Generate a __about__.py file from a metadata dictionary.
    Args:
        metadata (dict): Metadata dictionary.

    Returns:
        tuple: The content to write to the file and the names of the variables.
    """
    lines = []
    names = []
    for key, value in metadata.items():
        if key == "name":
            # __name__ is a reserved name.
            lines.append(f'__title__ = "{value}"')
            names.append("__title__")
            continue
        if key == "authors" and isinstance(value, list) and isinstance(value[0], str):
            if len(value) == 1:
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
                lines.append(f'__credits__ = "{value}"')
                names.append("__credits__")
        elif key == "classifiers" and isinstance(value, list):
            for trove in value:
                if trove.startswith("Development Status"):
                    lines.append(f'__status__ = "{trove.split("::")[1].strip()}"')
                    names.append("__status__")
        elif key == "keywords" and isinstance(value, list):
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


def merge_sections(names: Optional[list[str]], project_name: str, about_content: str) -> str:
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


def safe_quote(value: Union[int, float, str]) -> str:
    """
    Safely quote a value.
    Args:
        value (Union[int,float,str]): Value to quote.

    Returns:
        str: Quoted value.

    Examples:
        >>> safe_quote('hello')
        '"hello"'
        >>> safe_quote('hello\\nworld')
        '\"\"\"hello\\nworld\"\"\"'
    """
    if not isinstance(value, (str,)):
        return str(value)
    if "\n" in value:
        if '"""' in value:
            value = value.replace('"""', '\\"\\"\\"')
        quoted_value = f'"""{value}"""'
    else:
        quoted_value = f'"{value}"'
    return quoted_value
