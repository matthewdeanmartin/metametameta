"""
Console interface for metametameta.
"""

from __future__ import annotations

import argparse
import logging
import logging.config
import sys
from collections.abc import Sequence
from typing import Any

from metametameta import __about__, logging_config
from metametameta.from_importlib import generate_from_importlib
from metametameta.from_pep621 import generate_from_pep621
from metametameta.from_poetry import generate_from_poetry
from metametameta.from_setup_cfg import generate_from_setup_cfg
from metametameta.from_setup_py import generate_from_setup_py
from metametameta.utils.cli_suggestions import SmartParser


def process_args(args: argparse.Namespace) -> dict[str, Any]:
    """
    Process the arguments from argparse.Namespace to a dict.
    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        dict: The arguments as a dict.
    """
    kwargs = {}
    for key in ["name", "source", "output"]:
        if hasattr(args, key):
            kwargs[key] = getattr(args, key)
    return kwargs


def handle_importlib(args: argparse.Namespace) -> None:
    """
    Handle the importlib subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from importlib")
    # Call the generator with only the arguments it needs.
    generate_from_importlib(name=args.name, output=args.output)


def handle_poetry(args: argparse.Namespace) -> None:
    """
    Handle the poetry subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from poetry section of pyproject.toml")
    generate_from_poetry(name=args.name, source=args.source, output=args.output)


def handle_cfg(args: argparse.Namespace) -> None:
    """
    Handle the cfg subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from setup.cfg")
    generate_from_setup_cfg(name=args.name, source=args.source, output=args.output)


def handle_pep621(args: argparse.Namespace) -> None:
    """
    Handle the pep621 subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from project section of pyproject.toml")
    generate_from_pep621(name=args.name, source=args.source, output=args.output)


def handle_setup_py(args: argparse.Namespace) -> None:
    """
    Handle the setup_py subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from setup.py using AST")
    generate_from_setup_py(name=args.name, source=args.source, output=args.output)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the CLI tool.
    Args:
        argv: The arguments to parse.

    Returns:
        int: The exit code.
    """
    try:
        import argparse

        from rich_argparse import RichHelpFormatter

        formatter_class: Any = RichHelpFormatter
    except:
        formatter_class = argparse.RawTextHelpFormatter

    parser = SmartParser(
        prog=__about__.__title__,
        description="metametameta: Generate __about__.py from various sources.",
        formatter_class=formatter_class,
    )

    parser.add_argument("--verbose", action="store_true", help="verbose output")
    parser.add_argument("--quiet", action="store_true", help="minimal output")

    subparsers = parser.add_subparsers(help="sub-command help", dest="source")

    # Create a subparser for each generate function
    parser_setup_cfg = subparsers.add_parser("setup_cfg", help="Generate from setup.cfg")
    parser_pep621 = subparsers.add_parser("pep621", help="Generate from PEP 621 pyproject.toml")
    parser_poetry = subparsers.add_parser("poetry", help="Generate from poetry pyproject.toml")
    parser_importlib = subparsers.add_parser("importlib", help="Generate from installed package metadata")
    parser_setup_py = subparsers.add_parser("setup_py", help="Generate from setup.py using AST (experimental)")

    # Arguments for setup_cfg
    parser_setup_cfg.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_setup_cfg.add_argument("--source", type=str, default="setup.cfg", help="Path to setup.cfg")
    parser_setup_cfg.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_setup_cfg.set_defaults(func=handle_cfg)

    # Arguments for pep621
    parser_pep621.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_pep621.add_argument("--source", type=str, default="pyproject.toml", help="Path to pyproject.toml")
    parser_pep621.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_pep621.set_defaults(func=handle_pep621)

    # Arguments for poetry
    parser_poetry.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_poetry.add_argument("--source", type=str, default="pyproject.toml", help="Path to pyproject.toml")
    parser_poetry.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_poetry.set_defaults(func=handle_poetry)

    # Arguments for importlib
    parser_importlib.add_argument("--name", type=str, help="Name of the package", required=True)
    parser_importlib.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_importlib.set_defaults(func=handle_importlib)

    # Arguments for setup_py
    parser_setup_py.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_setup_py.add_argument("--source", type=str, default="setup.py", help="Path to setup.py")
    parser_setup_py.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_setup_py.set_defaults(func=handle_setup_py)

    args = parser.parse_args(argv)

    if args.verbose:
        level = "DEBUG"
    elif args.quiet:
        level = "FATAL"
    else:
        level = "WARNING"

    config = logging_config.generate_config(level)
    logging.config.dictConfig(config)

    if hasattr(args, "func") and args.func:
        args.func(args)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main([]))
