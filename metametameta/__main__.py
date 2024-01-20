"""
Console interface for metametameta.
"""
import argparse
import sys
from collections.abc import Sequence
from typing import Optional

from metametameta.from_importlib import generate_from_importlib
from metametameta.from_pep621 import generate_from_pep621
from metametameta.from_poetry import generate_from_poetry
from metametameta.from_setup_cfg import generate_from_setup_cfg


def process_args(args: argparse.Namespace) -> dict:
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
    generate_from_importlib(**process_args(args))


def handle_poetry(args: argparse.Namespace) -> None:
    """
    Handle the poetry subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from poetry section of pyproject.toml")
    generate_from_poetry(**process_args(args))


def handle_cfg(args: argparse.Namespace) -> None:
    """
    Handle the cfg subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from setup.cfg")
    generate_from_setup_cfg(**process_args(args))


def handle_pep621(args: argparse.Namespace) -> None:
    """
    Handle the pep621 subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from project section of pyproject.toml")
    generate_from_pep621(**process_args(args))


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse arguments and run the CLI tool.
    Args:
        argv: The arguments to parse.

    Returns:
        int: The exit code.
    """
    parser = argparse.ArgumentParser(description="metametameta: Generate __about__.py from various sources.")
    subparsers = parser.add_subparsers(help="sub-command help", dest="source")

    # Create a subparser for each generate function
    parser_setup_cfg = subparsers.add_parser("setup_cfg", help="Generate from setup.cfg")
    parser_pep621 = subparsers.add_parser("pep621", help="Generate from PEP 621 pyproject.toml")
    parser_poetry = subparsers.add_parser("poetry", help="Generate from poetry pyproject.toml")
    parser_importlib = subparsers.add_parser("importlib", help="Generate from installed package metadata")

    # Arguments for setup_cfg
    parser_setup_cfg.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_setup_cfg.add_argument("--source", type=str, default="setup.cfg", help="Path to setup.cfg")
    parser_setup_cfg.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_setup_cfg.set_defaults(func=handle_cfg)

    # Arguments for pep621
    parser_pep621.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_pep621.add_argument("--source", type=str, default="pyproject.toml", help="Path to pyproject.toml")
    parser_pep621.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_pep621.set_defaults(func=handle_poetry)

    # Arguments for poetry
    parser_poetry.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_poetry.add_argument("--source", type=str, default="pyproject.toml", help="Path to pyproject.toml")
    parser_poetry.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_poetry.set_defaults(func=handle_poetry)

    # Arguments for importlib
    parser_importlib.add_argument("--name", type=str, help="Name of the package", required=True)
    parser_importlib.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_importlib.set_defaults(func=handle_importlib)

    args = parser.parse_args(argv)

    if args.func:
        args.func(args)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main([]))
