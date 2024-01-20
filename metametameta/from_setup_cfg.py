"""
This module contains the function to generate the __about__.py file from the setup.cfg file.
"""
import configparser

from metametameta import general
from metametameta.filesystem import write_to_file


def read_setup_cfg_metadata() -> dict:
    """
    Read the setup.cfg file and extract the [metadata] section.
    Returns:
        dict: The [metadata] section of the setup.cfg file.
    """
    # Path to the setup.cfg file
    setup_cfg_path = "setup.cfg"

    # Initialize the parser and read the file
    config = configparser.ConfigParser()
    config.read(setup_cfg_path)

    # Extract the [metadata] section
    metadata = dict(config.items("metadata")) if config.has_section("metadata") else {}
    return metadata


def generate_from_setup_cfg(name: str = "", source: str = "setup.cfg", output: str = "__about__.py") -> str:
    """
    Generate the __about__.py file from the setup.cfg file.

    Args:
        name (str): Name of the project.
        source (str): Path to the setup.cfg file.
        output (str): Name of the file to write to.

    Returns:
        str: Path to the file that was written.
    """
    metadata = read_setup_cfg_metadata()
    if metadata:
        # Directory name
        project_name = metadata.get("name")
        if output != "__about__.py" and "/" in output or "\\" in output:
            dir_path = "./"
        else:
            dir_path = f"./{project_name}"

        # Define the content to write to the __about__.py file
        about_content, names = general.any_metadict(metadata)
        about_content = general.merge_sections(names, project_name or "", about_content)
        return write_to_file(dir_path, about_content, output)
    return "No [metadata] section found in setup.cfg."


if __name__ == "__main__":
    generate_from_setup_cfg()
