# metametameta/autodetect.py

"""
Autodetects the primary source of project metadata.
"""
from __future__ import annotations

import logging
from pathlib import Path

import toml

logger = logging.getLogger(__name__)


def detect_source(project_root: Path | None = None) -> str:
    """
    Autodetects the single viable metadata source in a project.

    It checks for the presence and content of standard Python packaging files
    in a specific order of preference.

    Args:
        project_root: The path to the project's root directory. Defaults to CWD.

    Returns:
        The name of the single viable source (e.g., 'pep621', 'poetry', 'setup_cfg').

    Raises:
        FileNotFoundError: If no viable metadata source can be found.
        ValueError: If multiple viable metadata sources are found, causing ambiguity.
    """
    if project_root is None:
        project_root = Path.cwd()

    logger.debug(f"Autodetecting metadata source in {project_root}")
    viable_sources = []

    # Check pyproject.toml for PEP 621 or Poetry (highest priority)
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            data = toml.load(pyproject_path)
            if "project" in data:
                logger.debug("Found [project] section in pyproject.toml (PEP 621)")
                viable_sources.append("pep621")
            if data.get("tool", {}).get("poetry"):
                logger.debug("Found [tool.poetry] section in pyproject.toml")
                viable_sources.append("poetry")
        except toml.TomlDecodeError:
            logger.warning("Could not parse pyproject.toml, skipping.")

    # Check for setup.cfg
    if (project_root / "setup.cfg").is_file():
        logger.debug("Found setup.cfg")
        viable_sources.append("setup_cfg")

    # Check for setup.py (lowest priority)
    if (project_root / "setup.py").is_file():
        logger.debug("Found setup.py")
        viable_sources.append("setup_py")

    if not viable_sources:
        raise FileNotFoundError("Could not find a viable metadata source (pyproject.toml, setup.cfg, or setup.py).")

    if len(viable_sources) > 1:
        raise ValueError(
            f"Multiple viable metadata sources found: {', '.join(viable_sources)}. "
            "Cannot determine which to use for sync check. Please specify one."
        )

    source = viable_sources[0]
    logger.info(f"Autodetected '{source}' as the metadata source.")
    return source
