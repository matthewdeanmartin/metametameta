"""
Generate source code metadata for Python projects from existing metadata files.

.. include:: ../README.md

.. include:: ../CHANGELOG.md
"""

# All generate functions have the same signature:
# def _(name: str, source:str, output: str) -> None:

__all__ = ["generate_from_setup_cfg", "generate_from_pep621", "generate_from_poetry", "generate_from_importlib"]

from metametameta.from_importlib import generate_from_importlib
from metametameta.from_pep621 import generate_from_pep621
from metametameta.from_poetry import generate_from_poetry
from metametameta.from_setup_cfg import generate_from_setup_cfg
