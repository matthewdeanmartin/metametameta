"""
This module contains the function to generate the __about__.py file from the setup.cfg file.
"""

from __future__ import annotations

import configparser
import logging
from pathlib import Path
from typing import Any

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


def parse_cfg_list(value: str) -> list[str]:
    """Parse a setup.cfg multiline list value."""
    return [line.strip() for line in value.splitlines() if line.strip()]


def read_setup_cfg_metadata(setup_cfg_path: Path | None = None) -> dict[str, Any]:
    """
    Read the setup.cfg file and extract the [metadata] section.

    Args:
        setup_cfg_path: Path to the setup.cfg file. Defaults to "setup.cfg".

    Returns:
        The [metadata] section of the setup.cfg file.
    """
    # Path to the setup.cfg file
    if setup_cfg_path is None:
        setup_cfg_path = Path("setup.cfg")
        use_default_encoding = True
    else:
        use_default_encoding = False

    # Initialize the parser and read the file
    config = configparser.ConfigParser(interpolation=None)
    if use_default_encoding:
        config.read(setup_cfg_path)
    else:
        config.read(setup_cfg_path, encoding="utf-8")

    # Extract the [metadata] section
    metadata: dict[str, Any] = dict(config.items("metadata")) if config.has_section("metadata") else {}
    if config.has_section("options") and config.has_option("options", "install_requires"):
        metadata["dependencies"] = parse_cfg_list(config.get("options", "install_requires"))
    return metadata


# pylint: disable=unused-argument
def generate_from_setup_cfg(
    name: str = "", source: str = "setup.cfg", output: str = "__about__.py", validate: bool = True
) -> str:
    """
    Generate the __about__.py file from the setup.cfg file.

    Args:
        name: Name of the project.
        source: Path to the setup.cfg file.
        output: Name of the file to write to.
        validate: Check if top level values are in about file after written.

    Returns:
        Path to the file that was written.
    """
    metadata = read_setup_cfg_metadata(Path(source))
    if metadata:
        # Directory name
        project_name = metadata.get("name")
        if output != "__about__.py" and "/" in output or "\\" in output:
            dir_path = "./"
        else:
            dir_path = f"./{project_name}"

        # Define the content to write to the __about__.py file
        result_tuple = None
        try:
            result_tuple = any_metadict(metadata)
            about_content, names = result_tuple
        except Exception:
            logger.warning("Can't parse metadata")
            logger.warning(result_tuple)
            raise
        about_content = merge_sections(names, project_name or "", about_content)
        file_path = write_to_file(dir_path, about_content, output)

        if validate:
            validate_about_file(file_path, metadata)

        return file_path
    logger.debug("No [metadata] section found in setup.cfg.")
    return "No [metadata] section found in setup.cfg."


if __name__ == "__main__":
    generate_from_setup_cfg()
