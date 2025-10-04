"""
Console interface for metametameta.
"""

from __future__ import annotations

import argparse
import logging
import logging.config
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import totalhelp
from rich_argparse import RichHelpFormatter

from metametameta import __about__, logging_config
from metametameta.autodetect import detect_source
from metametameta.filesystem import _find_existing_package_dir
from metametameta.from_importlib import generate_from_importlib
from metametameta.from_pep621 import generate_from_pep621, read_pep621_metadata
from metametameta.from_poetry import generate_from_poetry, read_poetry_metadata
from metametameta.from_setup_cfg import generate_from_setup_cfg, read_setup_cfg_metadata
from metametameta.from_setup_py import generate_from_setup_py, read_setup_py_metadata
from metametameta.utils.cli_suggestions import SmartParser
from metametameta.validate_sync import check_sync


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


# In metametameta/__main__.py


def handle_auto(args: argparse.Namespace) -> None:
    """Handle the auto subcommand for automatic source detection and generation."""
    print("🤖 Automatically detecting metadata source...")
    project_root = Path.cwd()
    try:
        source_type = detect_source(project_root)
        print(f"✅ Found single source: '{source_type}'")

        generators = {
            "pep621": generate_from_pep621,
            "poetry": generate_from_poetry,
            "setup_cfg": generate_from_setup_cfg,
            "setup_py": generate_from_setup_py,
        }

        generator_func = generators[source_type]

        # The file-based generators all share a compatible function signature
        generator_func(
            name=args.name,
            output=args.output,
            validate=args.validate,
        )
        print(f"Successfully generated {args.output} from {source_type}.")

    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Auto-generation failed: {e}", file=sys.stderr)
        sys.exit(1)


def handle_sync_check(args: argparse.Namespace) -> None:
    """Handle the sync-check subcommand."""
    print("Performing sync check...")
    project_root = Path.cwd()
    try:
        source_type = detect_source(project_root)

        # mypy doesn't understand this, maybe use a Protocol?
        metadata_readers = {
            "pep621": read_pep621_metadata,
            "poetry": read_poetry_metadata,
            "setup_cfg": read_setup_cfg_metadata,
            "setup_py": read_setup_py_metadata,
        }

        # Read the source metadata
        source_metadata = metadata_readers[source_type]()  # type: ignore[operator]
        project_name = source_metadata.get("name")
        if not project_name:
            print("❌ Error: Could not determine project name from metadata source.", file=sys.stderr)
            sys.exit(1)

        # Find the __about__.py file
        package_dir = _find_existing_package_dir(project_root, project_name)
        if not package_dir:
            print(f"❌ Error: Could not find package directory for '{project_name}'.", file=sys.stderr)
            sys.exit(1)

        about_path = package_dir / args.output

        # Perform the sync check
        mismatches = check_sync(source_metadata, about_path)

        if mismatches:
            print("❌ Sync check failed. The following items are out of sync:")
            for mismatch in mismatches:
                print(f"  - {mismatch}")
            sys.exit(1)
        else:
            print("✅ Sync check passed. Metadata is in sync.")

    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error during sync check: {e}", file=sys.stderr)
        sys.exit(1)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the CLI tool.
    Args:
        argv: The arguments to parse.

    Returns:
        int: The exit code.
    """
    formatter_class: Any = RichHelpFormatter

    parser = SmartParser(
        prog=__about__.__title__,
        description="metametameta: Generate __about__.py from various sources.",
        formatter_class=formatter_class,
    )
    totalhelp.add_totalhelp_flag(parser)

    parser.add_argument("--version", action="version", version=f"%(prog)s {__about__.__version__}")

    parser.add_argument("--verbose", action="store_true", help="verbose output")
    parser.add_argument("--quiet", action="store_true", help="minimal output")

    subparsers = parser.add_subparsers(help="sub-command help", dest="source")

    # Parent parser for common arguments shared by generation commands
    gen_parser = SmartParser(add_help=False)
    gen_parser.add_argument(
        "--validate", action="store_true", help="Validate that source values exist in the generated file."
    )

    # Subparser: setup_cfg
    parser_setup_cfg = subparsers.add_parser("setup_cfg", help="Generate from setup.cfg", parents=[gen_parser])
    parser_setup_cfg.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_setup_cfg.add_argument("--source", type=str, default="setup.cfg", help="Path to setup.cfg")
    parser_setup_cfg.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_setup_cfg.set_defaults(func=handle_cfg)

    # Subparser: pep621
    parser_pep621 = subparsers.add_parser("pep621", help="Generate from PEP 621 pyproject.toml", parents=[gen_parser])
    parser_pep621.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_pep621.add_argument("--source", type=str, default="pyproject.toml", help="Path to pyproject.toml")
    parser_pep621.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_pep621.set_defaults(func=handle_pep621)

    # Subparser: poetry
    parser_poetry = subparsers.add_parser("poetry", help="Generate from poetry pyproject.toml", parents=[gen_parser])
    parser_poetry.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_poetry.add_argument("--source", type=str, default="pyproject.toml", help="Path to pyproject.toml")
    parser_poetry.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_poetry.set_defaults(func=handle_poetry)

    # Subparser: importlib
    parser_importlib = subparsers.add_parser(
        "importlib", help="Generate from installed package metadata", parents=[gen_parser]
    )
    parser_importlib.add_argument("--name", type=str, help="Name of the package", required=True)
    parser_importlib.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_importlib.set_defaults(func=handle_importlib)

    # Subparser: setup_py
    parser_setup_py = subparsers.add_parser(
        "setup_py", help="Generate from setup.py using AST (experimental)", parents=[gen_parser]
    )
    parser_setup_py.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_setup_py.add_argument("--source", type=str, default="setup.py", help="Path to setup.py")
    parser_setup_py.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_setup_py.set_defaults(func=handle_setup_py)

    # In metametameta/__main__.py, inside the main() function

    # Subparser: auto (New command)
    parser_auto = subparsers.add_parser(
        "auto",
        help="Automatically detect the source and generate the metadata file.",
        parents=[gen_parser],  # Reuses the parent parser for the --validate flag
    )
    parser_auto.add_argument(
        "--name", type=str, default="", help="Name of the project (overrides name found in source file)"
    )
    parser_auto.add_argument("--output", type=str, default="__about__.py", help="Output file name")
    parser_auto.set_defaults(func=handle_auto)

    # Subparser: sync-check (New command)
    parser_sync_check = subparsers.add_parser(
        "sync-check", help="Check if __about__.py is in sync with the metadata source"
    )
    parser_sync_check.add_argument("--output", type=str, default="__about__.py", help="The metadata file to check")
    parser_sync_check.set_defaults(func=handle_sync_check)

    args = parser.parse_args(argv)

    if totalhelp and getattr(args, "totalhelp", False):
        doc = totalhelp.full_help_from_parser(parser, fmt=getattr(args, "format", "text"))
        totalhelp.print_output(doc, fmt=getattr(args, "format", "text"), open_browser=getattr(args, "open", False))
        sys.exit(0)

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
