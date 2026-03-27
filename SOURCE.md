## Tree for metametameta
```
├── autodetect.py
├── filesystem.py
├── find.py
├── find_it.py
├── from_conda_meta.py
├── from_importlib.py
├── from_pep621.py
├── from_poetry.py
├── from_requirements_txt.py
├── from_setup_cfg.py
├── from_setup_py.py
├── general.py
├── known.py
├── logging_config.py
├── py.typed
├── utils/
│   └── cli_suggestions.py
├── validate_sync.py
├── __about__.py
└── __main__.py
```

## File: autodetect.py
```python
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
    primary_sources = []
    fallback_sources = []

    # Check pyproject.toml for PEP 621 or Poetry (highest priority)
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            data = toml.load(pyproject_path)
            if "project" in data:
                logger.debug("Found [project] section in pyproject.toml (PEP 621)")
                primary_sources.append("pep621")
            if data.get("tool", {}).get("poetry"):
                logger.debug("Found [tool.poetry] section in pyproject.toml")
                primary_sources.append("poetry")
        except toml.TomlDecodeError:
            logger.warning("Could not parse pyproject.toml, skipping.")

    # Check for setup.cfg
    if (project_root / "setup.cfg").is_file():
        logger.debug("Found setup.cfg")
        primary_sources.append("setup_cfg")

    # Check for setup.py (lowest priority)
    if (project_root / "setup.py").is_file():
        logger.debug("Found setup.py")
        primary_sources.append("setup_py")

    requirements_path = project_root / "requirements.txt"
    if requirements_path.is_file():
        requirements_lines = [
            line.strip()
            for line in requirements_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if requirements_lines:
            logger.debug("Found populated requirements.txt")
            fallback_sources.append("requirements_txt")

    conda_meta_path = project_root / "conda" / "meta.yaml"
    if conda_meta_path.is_file():
        conda_text = conda_meta_path.read_text(encoding="utf-8")
        if "package:" in conda_text or "about:" in conda_text:
            logger.debug("Found conda/meta.yaml")
            fallback_sources.append("conda_meta")

    viable_sources = primary_sources or fallback_sources

    if not viable_sources:
        raise FileNotFoundError(
            "Could not find a viable metadata source (pyproject.toml, setup.cfg, setup.py, requirements.txt, or conda/meta.yaml)."
        )

    if len(viable_sources) > 1:
        raise ValueError(
            f"Multiple viable metadata sources found: {', '.join(viable_sources)}. Cannot determine which to use for sync check. Please specify one."
        )

    source = viable_sources[0]
    logger.info(f"Autodetected '{source}' as the metadata source.")
    return source
```
## File: filesystem.py
```python
# filesystem.py

"""
This module contains robust functions for writing to the filesystem, intelligently
locating the correct Python package directory within a given project root.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# --- Private Helper Functions ---


def _find_existing_package_dir(base_path: Path, package_name: str) -> Path | None:
    """
    Search for an existing package directory using common layouts.

    Checks for directories matching the package name with hyphens replaced
    by underscores, the original name, and src-layout variants.

    Args:
        base_path: The root directory to search in.
        package_name: The name of the package to find.

    Returns:
        The Path to the first existing package directory found, or None.
    """
    package_name_underscore = package_name.replace("-", "_")

    # Define a clear, prioritized list of candidate directories to check.
    # Python-standard underscored names are checked first.
    candidate_dirs = [
        base_path / package_name_underscore,
        base_path / package_name,
        base_path / "src" / package_name_underscore,
        base_path / "src" / package_name,
    ]

    for candidate in candidate_dirs:
        if candidate.is_dir():
            logger.debug(f"Found existing package directory at: {candidate}")
            return candidate

    logger.debug(f"No existing package directory found for '{package_name}'.")
    return None


def _determine_target_dir(base_path: Path, package_name: str) -> Path:
    """
    Determines the ideal target directory for a package.

    It first tries to find an existing directory. If none is found, it decides
    the best location to create one (e.g., inside 'src/' if it exists).
    """
    # 1. Try to find an existing directory first.
    existing_dir = _find_existing_package_dir(base_path, package_name)
    if existing_dir:
        return existing_dir

    # 2. If not found, decide where to create it.
    package_name_underscore = package_name.replace("-", "_")
    if (base_path / "src").is_dir():
        # Prefer 'src' layout if a 'src' directory exists.
        target_dir = base_path / "src" / package_name_underscore
    else:
        # Default to a flat layout.
        target_dir = base_path / package_name_underscore

    logger.debug(f"No existing directory found. Determined target for creation: {target_dir}")
    return target_dir


# --- New, Preferred Public Function ---


def write_to_package_dir(
    project_root: Path,
    package_dir_name: str,
    about_content: str,
    output_filename: str = "__about__.py",
) -> str:
    """
    Deterministically writes content to a file within the correct package directory.

    This is the preferred function for new code as it is not dependent on the
    current working directory.

    Args:
        project_root: The absolute path to the project's root directory.
        package_dir_name: The target package directory name (e.g., "my-project").
        about_content: The string content to write to the file.
        output_filename: The name of the file to write (e.g., "__about__.py").

    Returns:
        The full path to the file that was written as a string.
    """
    target_dir = _determine_target_dir(project_root, package_dir_name)
    output_path = target_dir / output_filename

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(about_content, encoding="utf-8")
        logger.info(f"Successfully wrote metadata to {output_path}")
        return str(output_path)
    except OSError as e:
        logger.error(f"Failed to write to file {output_path}: {e}")
        raise


# --- Legacy Backward-Compatible Wrapper ---


def write_to_file(directory: str, about_content: str, output: str = "__about__.py") -> str:
    """
    Writes content to a file within a target directory.

    Note: This function is for backward compatibility. Its behavior depends on the
    current working directory. For deterministic and testable behavior, please use
    `write_to_package_dir()` instead.
    """
    # Preserve original non-deterministic behavior by using cwd()
    project_root = Path.cwd()

    return write_to_package_dir(
        project_root=project_root,
        package_dir_name=directory,
        about_content=about_content,
        output_filename=output,
    )
```
## File: find.py
```python
"""
Find metadata in a module file.
"""

from __future__ import annotations

import inspect
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)


def get_module_file(module: Any) -> str:
    """
    Get the file path associated with a module.

    Args:
        module: The module object to get the file path for.

    Returns:
        The absolute path to the module's source file.
    """
    return inspect.getfile(module)


def is_package(module: Any) -> bool:
    """
    Check if a module is a package (i.e., an __init__.py file).

    Args:
        module: The module object to check.

    Returns:
        True if the module is a package, False otherwise.
    """
    module_file = get_module_file(module)
    return os.path.basename(module_file) == "__init__.py"


def get_meta(module_file: Any) -> dict[str, str]:
    """
    Extract metadata variables from a module file.

    Searches for variables matching the pattern __key__ = "value" and
    returns them as a dictionary.

    Args:
        module_file: Path to the module file or the module object.

    Returns:
        Dictionary of metadata key-value pairs found in the file.
    """
    metadata = {}
    if module_file and os.path.isfile(module_file):
        with open(module_file, encoding="utf-8") as file:
            content = file.read()

        # Define a regex pattern to match metadata variables
        pattern = r"__(\w+)__\s*=\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, content)

        for key, value in matches:
            metadata[key] = value
    return metadata


# # Usage example:
# try:
#     # ... some code that raises CustomError ...
#     raise CustomError("An error occurred")
# except CustomError as ce:
#     module = get_module(ce)
#     module_file = get_module_file(module)
#     metadata = get_meta(module_file)
#     print(metadata)
```
## File: find_it.py
```python
from __future__ import annotations

import argparse
import importlib
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def find_metadata_in_file(file_path: Path) -> dict[str, Any]:
    """
    Find metadata variables in a given Python file.

    Searches for variables matching the pattern __key__ = "value".

    Args:
        file_path: Path to the Python file to search.

    Returns:
        Dictionary of metadata key-value pairs found in the file.
    """
    metadata = {}
    with open(file_path, encoding="utf-8") as file:
        content = file.read()
        # Match all possible metadata fields, assuming they follow the format __key__ = value
        matches = re.findall(r"__(\w+)__\s*=\s*['\"]([^'\"]+)['\"]", content)
        for key, value in matches:
            logger.debug(f"Found {key} : {value}")
            metadata[key] = value
    return metadata


def find_metadata_in_module(module_path: Path) -> dict[str, dict[str, Any]]:
    """
    Traverse a module/package directory and find metadata in all submodules.

    Looks for Python files containing "about" in their name that also
    contain version metadata.

    Args:
        module_path: Path to the module or package directory to search.

    Returns:
        Dictionary mapping module names to their metadata dictionaries.
    """
    metadata_results = {}
    for root, _dirs, files in os.walk(module_path):
        for file in files:
            if file.endswith(".py") and "about" in file:
                file_path = Path(root) / file
                metadata = find_metadata_in_file(file_path)
                if "version" in metadata:  # Check if this file has metadata
                    module_name = file_path.relative_to(module_path).with_suffix("")
                    metadata_results[str(module_name).replace(os.sep, ".")] = metadata
    return metadata_results


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Find metadata in a Python module/package.")
    parser.add_argument("module", type=str, help="The name of the module/package to inspect.")
    args = parser.parse_args(argv)

    module_name = args.module
    module = importlib.import_module(module_name)
    if not module.__file__:
        raise ValueError(f"Module {module_name} has no file attribute.")
    module_path = Path(module.__file__).parent

    metadata_results = find_metadata_in_module(module_path)
    for submodule, metadata in metadata_results.items():
        logger.debug(f"Metadata for {submodule}:")
        for key, value in metadata.items():
            logger.debug(f"  {key}: {value}")
        logger.debug("")


if __name__ == "__main__":
    main(["metametameta"])
```
## File: from_conda_meta.py
```python
"""
Generate metadata from a conda recipe meta.yaml file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


def _strip_matching_quotes(value: str) -> str:
    """Strip matching single or double quotes from a string."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _strip_comment(value: str) -> str:
    """Strip YAML-style comments from a line."""
    if " #" in value:
        return value.split(" #", maxsplit=1)[0].rstrip()
    return value.rstrip()


def _infer_project_name(source_path: Path) -> str:
    """Infer a project name from the recipe location."""
    parent = source_path.resolve().parent
    if parent.name == "conda" and parent.parent.name:
        return parent.parent.name
    return parent.name


def read_conda_meta_metadata(source: str = "conda/meta.yaml", name: str = "") -> dict[str, Any]:
    """
    Read metadata from a conda recipe.

    Args:
        source: Path to the conda meta.yaml file.
        name: Optional explicit project name override.

    Returns:
        A metadata dictionary with the supported fields extracted.
    """
    source_path = Path(source)
    parsed: dict[str, Any] = {"package": {}, "about": {}, "requirements": {"run": []}}
    current_section = ""
    current_subsection = ""

    for raw_line in source_path.read_text(encoding="utf-8").splitlines():
        without_comment = _strip_comment(raw_line)
        stripped = without_comment.strip()
        if not stripped or stripped.startswith("{%"):
            continue

        indent = len(without_comment) - len(without_comment.lstrip(" "))

        if stripped.endswith(":") and not stripped.startswith("- "):
            section_name = stripped[:-1].strip()
            if indent == 0:
                current_section = section_name
                current_subsection = ""
            else:
                current_subsection = section_name
            continue

        if stripped.startswith("- "):
            item = _strip_matching_quotes(stripped[2:].strip())
            if current_section == "requirements" and current_subsection:
                parsed["requirements"].setdefault(current_subsection, []).append(item)
            continue

        if ":" not in stripped:
            continue

        key, value = stripped.split(":", maxsplit=1)
        cleaned_value = _strip_matching_quotes(value.strip())
        if current_section in {"package", "about"}:
            parsed[current_section][key.strip()] = cleaned_value

    package_data = parsed.get("package", {})
    about_data = parsed.get("about", {})
    run_dependencies = parsed.get("requirements", {}).get("run", [])

    project_name = name or package_data.get("name") or _infer_project_name(source_path)

    metadata: dict[str, Any] = {"name": project_name}
    if package_data.get("version"):
        metadata["version"] = package_data["version"]
    if about_data.get("summary"):
        metadata["summary"] = about_data["summary"]
    elif about_data.get("description"):
        metadata["description"] = about_data["description"]
    if about_data.get("license"):
        metadata["license"] = about_data["license"]
    if about_data.get("home"):
        metadata["homepage"] = about_data["home"]
    if run_dependencies:
        metadata["dependencies"] = run_dependencies

    return metadata


def generate_from_conda_meta(
    name: str = "", source: str = "conda/meta.yaml", output: str = "__about__.py", validate: bool = False
) -> str:
    """
    Generate the metadata file from conda/meta.yaml.

    Args:
        name: Explicit project name override.
        source: Path to the conda recipe.
        output: Name of the file to write to.
        validate: Validate file after writing.

    Returns:
        Path to the file that was written.
    """
    metadata = read_conda_meta_metadata(source=source, name=name)
    project_name = metadata.get("name", "")
    if not project_name:
        raise ValueError("Project name could not be determined from conda/meta.yaml.")

    if output != "__about__.py" and ("/" in output or "\\" in output):
        dir_path = "./"
    else:
        dir_path = f"./{project_name}"

    about_content, names = any_metadict(metadata)
    about_content = merge_sections(names, project_name, about_content)
    file_path = write_to_file(dir_path, about_content, output)
    if validate:
        validate_about_file(file_path, metadata)
    return file_path
```
## File: from_importlib.py
```python
"""
Generate an __about__.py file from package metadata using importlib.metadata.
"""

from __future__ import annotations

import importlib.metadata as md
import logging
from typing import Any, cast

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


def get_package_metadata(package_name: str) -> dict[str, Any]:
    """
    Get package metadata using importlib.metadata.

    Args:
        package_name: The name of the package to get metadata for.

    Returns:
        Dictionary containing the package metadata.
    """
    try:
        pkg_metadata: md.PackageMetadata = md.metadata(package_name)
        # dict for 3.8 support
        # pylint: disable=unnecessary-comprehension
        return {key: value for key, value in cast(dict, pkg_metadata).items()}  # type: ignore[type-arg]
    except md.PackageNotFoundError:
        print(f"Package '{package_name}' not found.")
        return {}


# pylint: disable=unused-argument
def generate_from_importlib(name: str, source: str = "", output: str = "__about__.py", validate: bool = False) -> str:
    """
    Write package metadata to an __about__.py file.

    Args:
        name: Name of the package to get metadata from.
        source: Ignored (present for API compatibility).
        output: Name of the file to write to.
        validate: Validate file after writing.

    Returns:
        Path to the file that was written, or a message if no metadata was found.
    """
    pkg_metadata = get_package_metadata(name)
    if pkg_metadata:
        dir_path = "./"

        about_content, names = any_metadict(pkg_metadata)

        about_content = merge_sections(names, name, about_content)
        file_path = write_to_file(dir_path, about_content, output)
        if validate:
            validate_about_file(file_path, pkg_metadata)
        return file_path
    message = "No [project] section found in pyproject.toml."
    logger.debug(message)
    return message


if __name__ == "__main__":
    generate_from_importlib("toml")
```
## File: from_pep621.py
```python
"""
This module contains the function to generate the __about__.py file from the pyproject.toml file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

import toml

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


def read_pep621_metadata(source: str = "pyproject.toml") -> dict[str, Any]:
    """
    Read the pyproject.toml file and extract the [project] section.

    Args:
        source: Path to the pyproject.toml file.

    Returns:
        The [project] section of the pyproject.toml file.
    """
    # Read the pyproject.toml file
    with open(source, encoding="utf-8") as file:
        data = toml.load(file)

    # Extract the [project] section
    project_data = data.get("project", {})
    # must be dict for 3.8 support
    return cast(dict, project_data)  # type: ignore[type-arg]


# pylint: disable=unused-argument
def generate_from_pep621(
    name: str = "", source: str = "pyproject.toml", output: str = "__about__.py", validate: bool = False
) -> str:
    """
    Generate the __about__.py file from the pyproject.toml file.

    Args:
        name: Name of the project.
        source: Path to the pyproject.toml file.
        output: Name of the file to write to.
        validate: Validate file after writing.

    Returns:
        Path to the file that was written.
    """
    project_data = read_pep621_metadata(source)
    if project_data:
        # Extract the project name and create a directory
        project_name = project_data.get("name", "")
        if not project_name:
            raise TypeError("Project name not found in [project] section of pyproject.toml.")
        if output != "__about__.py" and "/" in output or "\\" in output:
            dir_path = "./"
        else:
            dir_path = f"./{project_name}"

        # if the dir_path does not exist check if project_name.replace("-", "_") exists
        if not Path(dir_path).exists():
            project_name = project_name.replace("-", "_")
            dir_path = f"./{project_name}"

        if not Path(dir_path).exists():
            project_name = project_name.replace("_", "-")
            dir_path = f"./{project_name}"

        result_tuple = None
        try:
            result_tuple = any_metadict(project_data)
            about_content, names = result_tuple
        except Exception:
            print(result_tuple)
            raise
        about_content = merge_sections(names, project_name or "", about_content)
        file_path = write_to_file(dir_path, about_content, output)

        if validate:
            validate_about_file(file_path, project_data)

        return file_path
    logger.debug("No [project] section found in pyproject.toml.")
    return "No [project] section found in pyproject.toml."


if __name__ == "__main__":
    print(generate_from_pep621(source="../pyproject.toml"))
```
## File: from_poetry.py
```python
"""
This module contains the functions to generate the __about__.py file from the [tool.poetry] section of the
pyproject.toml file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import toml

from metametameta import filesystem
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


def read_poetry_metadata(
    source: str = "pyproject.toml",
) -> Any:
    """
    Read the pyproject.toml file and extract the [tool.poetry] section.

    Args:
        source: Path to the pyproject.toml file.

    Returns:
        The [tool.poetry] section of the pyproject.toml file.
    """
    # Read the pyproject.toml file
    with open(source, encoding="utf-8") as file:
        data = toml.load(file)

    # Extract the [tool.poetry] section
    poetry_data = data.get("tool", {}).get("poetry", {})
    return poetry_data


# pylint: disable=unused-argument
def generate_from_poetry(
    name: str = "", source: str = "pyproject.toml", output: str = "__about__.py", validate: bool = True
) -> str:
    """
    Generate the __about__.py file from the pyproject.toml file.

    Args:
        name: Name of the project.
        source: Path to the pyproject.toml file.
        output: Name of the file to write to.
        validate: Check if top level values are in about file after written.

    Returns:
        Path to the file that was written.
    """
    poetry_data = read_poetry_metadata(source)
    if poetry_data:
        candidate_packages = []
        packages_data_list = poetry_data.get("packages")
        if packages_data_list:
            for package_data in packages_data_list:
                include_part = None
                from_part = None  # subfolder(s)
                _format_part = None  # can be dist, i.e not a folder
                for key, value in package_data.items():
                    if key == "include":
                        include_part = value
                    elif key == "from":
                        from_part = value
                    elif key == "format":
                        pass
                candidate_path = ""
                if include_part:
                    candidate_path = include_part
                if include_part and from_part:
                    candidate_from_path = Path(candidate_path) / from_part
                    if candidate_from_path.exists():
                        candidate_path = candidate_from_path
                if Path(candidate_path).exists():
                    candidate_packages.append(candidate_path)

        project_name = poetry_data.get("name")
        if not candidate_packages:
            candidate_packages.append(project_name)
        written = []
        for candidate in candidate_packages:
            if output != "__about__.py" and "/" in output or "\\" in output:
                dir_path = "./"
            else:
                dir_path = f"./{candidate}"
            result_tuple = any_metadict(poetry_data)
            about_content, names = result_tuple
            about_content = merge_sections(names, candidate or "", about_content)
            # Define the content to write to the __about__.py file
            file_path = filesystem.write_to_file(dir_path, about_content, output)

            if validate:
                validate_about_file(file_path, poetry_data)

            written.append(file_path)
    logger.debug("No [tool.poetry] section found in pyproject.toml.")
    return "No [tool.poetry] section found in pyproject.toml."


if __name__ == "__main__":
    generate_from_poetry()
```
## File: from_requirements_txt.py
```python
"""
Generate metadata from a requirements.txt file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)

_SKIPPED_PREFIXES = (
    "-r",
    "--requirement",
    "-c",
    "--constraint",
    "-i",
    "--index-url",
    "--extra-index-url",
    "-f",
    "--find-links",
    "--trusted-host",
)


def _strip_matching_quotes(value: str) -> str:
    """Strip matching single or double quotes from a string."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _strip_inline_comment(line: str) -> str:
    """Strip trailing comments while preserving URL fragments like #egg."""
    if " #" in line:
        return line.split(" #", maxsplit=1)[0].rstrip()
    return line.rstrip()


def _parse_requirement_line(line: str) -> str | None:
    """Parse a single requirements.txt line into a dependency string."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if stripped.startswith(_SKIPPED_PREFIXES):
        return None

    if stripped.startswith(("-e ", "--editable ")):
        parts = stripped.split(maxsplit=1)
        stripped = parts[1].strip() if len(parts) == 2 else ""

    stripped = _strip_inline_comment(stripped)
    if not stripped:
        return None

    if "#egg=" in stripped:
        return _strip_matching_quotes(stripped.split("#egg=", maxsplit=1)[1].strip())

    return _strip_matching_quotes(stripped)


def _infer_project_name(source_path: Path) -> str:
    """Infer a project name from the requirements file location."""
    return source_path.resolve().parent.name


def read_requirements_txt_metadata(source: str = "requirements.txt", name: str = "") -> dict[str, Any]:
    """
    Read dependency metadata from a requirements.txt file.

    Args:
        source: Path to the requirements file.
        name: Optional explicit project name override.

    Returns:
        Minimal metadata containing the project name and dependencies.
    """
    source_path = Path(source)
    requirements = []
    for line in source_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_requirement_line(line)
        if parsed:
            requirements.append(parsed)

    project_name = name or _infer_project_name(source_path)
    metadata: dict[str, Any] = {"name": project_name}
    if requirements:
        metadata["dependencies"] = requirements
    return metadata


def generate_from_requirements_txt(
    name: str = "", source: str = "requirements.txt", output: str = "__about__.py", validate: bool = False
) -> str:
    """
    Generate the metadata file from requirements.txt.

    Args:
        name: Explicit project name override.
        source: Path to the requirements.txt file.
        output: Name of the file to write to.
        validate: Validate file after writing.

    Returns:
        Path to the file that was written.
    """
    metadata = read_requirements_txt_metadata(source=source, name=name)
    project_name = metadata.get("name", "")
    if not project_name:
        raise ValueError("Project name could not be determined from requirements.txt.")

    if output != "__about__.py" and ("/" in output or "\\" in output):
        dir_path = "./"
    else:
        dir_path = f"./{project_name}"

    about_content, names = any_metadict(metadata)
    about_content = merge_sections(names, project_name, about_content)
    file_path = write_to_file(dir_path, about_content, output)
    if validate:
        validate_about_file(file_path, metadata)
    return file_path
```
## File: from_setup_cfg.py
```python
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

    # Initialize the parser and read the file
    config = configparser.ConfigParser()
    config.read(setup_cfg_path)

    # Extract the [metadata] section
    metadata = dict(config.items("metadata")) if config.has_section("metadata") else {}
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
```
## File: from_setup_py.py
```python
"""
This module contains an experimental function to generate the __about__.py file
by statically parsing a setup.py file using Python's AST module.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

from metametameta.filesystem import write_to_file
from metametameta.general import any_metadict, merge_sections, validate_about_file

logger = logging.getLogger(__name__)


class SetupKwargsVisitor(ast.NodeVisitor):
    """An AST visitor to find keyword arguments in a setup() call."""

    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}
        self._found = False

    def visit_Call(self, node: ast.Call) -> None:
        """
        Visit a Call node in the AST.

        Looks for setup() function calls and extracts keyword arguments.
        Only captures the first valid setup() call found.
        """
        # Only capture the first valid setup() call we find.
        if self._found:
            return

        func_is_setup = False
        if isinstance(node.func, ast.Name) and node.func.id == "setup":
            func_is_setup = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "setup":
            # This covers `setuptools.setup()`
            func_is_setup = True

        if func_is_setup:
            for keyword in node.keywords:
                if keyword.arg:  # Ensure there is an argument name
                    try:
                        # Safely evaluate the value of the keyword argument
                        self.kwargs[keyword.arg] = ast.literal_eval(keyword.value)
                    except ValueError:
                        # This happens if the value is not a literal (e.g., a variable)
                        logger.warning(
                            f"Could not statically parse value for '{keyword.arg}' in setup.py. Only literals (strings, numbers, lists, etc.) are supported."
                        )
            self._found = True

        # Continue traversing to find the call if it's nested
        self.generic_visit(node)


def read_setup_py_metadata(source: str = "setup.py") -> dict[str, Any]:
    """
    Read a setup.py file and extract metadata from the setup() call using AST.

    This method does not execute the file, it only parses it statically.

    Args:
        source: Path to the setup.py file.

    Returns:
        Dictionary containing the metadata found in the setup() call.
    """
    source_path = Path(source)
    if not source_path.exists():
        logger.error(f"Source file not found: {source}")
        return {}

    try:
        source_code = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source_code)
        visitor = SetupKwargsVisitor()
        visitor.visit(tree)
        return visitor.kwargs
    except (SyntaxError, UnicodeDecodeError) as e:
        logger.error(f"Failed to parse {source}: {e}")
        return {}


def generate_from_setup_py(
    name: str = "", source: str = "setup.py", output: str = "__about__.py", validate: bool = False
) -> str:
    """
    Generate the __about__.py file from a setup.py file.

    Args:
        name: Name of the project (optional, will be read from setup.py if not provided).
        source: Path to the setup.py file.
        output: Name of the file to write to.
        validate: Validate file after writing.

    Returns:
        Path to the file that was written, or a message if no metadata was found.
    """
    metadata = read_setup_py_metadata(source)
    if not metadata:
        message = "No setup() call with static metadata found in setup.py."
        logger.debug(message)
        return message

    # Use the name from the metadata, but allow CLI to override it if provided
    project_name = name or metadata.get("name", "")
    if not project_name:
        raise ValueError("Project 'name' not found in setup.py and not provided via arguments.")

    about_content, names = any_metadict(metadata)
    about_content = merge_sections(names, project_name, about_content)

    file_path = write_to_file(project_name, about_content, output)
    if validate:
        validate_about_file(file_path, metadata)
    return file_path
```
## File: general.py
```python
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
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            yield from _get_all_primitive_values(item)


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
    Generate __about__.py content from a metadata dictionary.

    Args:
        metadata: Dictionary containing project metadata.

    Returns:
        A tuple containing the file content and list of variable names.
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
        elif key == "dependencies" and isinstance(value, list) and value:
            lines.append(f"__dependencies__ = {value}")
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
```
## File: known.py
```python
"""
Known metadata fields, as opposed to ad hoc ones people make up.
"""

from __future__ import annotations

# https://web.archive.org/web/20111010053227/http://jaynes.colorado.edu/PythonGuidelines.html#module_formatting
meta = [
    "name",  # title
    "version",
    "description",
    "authors",  # credits/ author/ author_email
    "license",  # copyright
    "homepage",  # url
    "keywords",
]
```
## File: logging_config.py
```python
"""
Logging configuration.
"""

from __future__ import annotations

import os
from typing import Any


def generate_config(level: str = "DEBUG") -> dict[str, Any]:
    """
    Generate a logging configuration.

    Returns:
        dict: The logging configuration.
    """
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {"format": "[%(levelname)s] %(name)s: %(message)s"},
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(levelname)-8s%(reset)s %(green)s%(message)s",
            },
        },
        "handlers": {
            "default": {
                "level": level,
                "formatter": "colored",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",  # Default is stderr
            },
        },
        "loggers": {
            "metametameta": {
                "handlers": ["default"],
                "level": level,
                "propagate": False,
            }
        },
    }
    if os.environ.get("NO_COLOR") or os.environ.get("CI"):
        config["handlers"]["default"]["formatter"] = "standard"
    return config
```
## File: py.typed
```
# when type checking dependents, tell type checkers to use this package's types
```
## File: validate_sync.py
```python
# metametameta/validate.py

"""
Validation logic to check if __about__.py is in sync with source metadata.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Mapping from source metadata keys to the expected dunder names in __about__.py
KEY_MAP = {
    "name": "__title__",
    "version": "__version__",
    "description": "__description__",
    "license": "__license__",
    "homepage": "__homepage__",
    "dependencies": "__dependencies__",
    "summary": "__description__",  # importlib.metadata uses 'summary'
}


def _is_supported_sync_value(value: Any) -> bool:
    """Return True for metadata values that can be compared for sync."""
    if isinstance(value, str):
        return True
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _normalize_sync_value(value: Any) -> Any:
    """Normalize supported metadata values for comparison."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [item.strip() if isinstance(item, str) else item for item in value]
    return value


def read_about_file_ast(file_path: Path) -> dict[str, Any]:
    """
    Safely reads an __about__.py file using AST to extract metadata.

    This avoids executing the file and is resilient to formatting changes.

    Args:
        file_path: The path to the __about__.py file.

    Returns:
        A dictionary of metadata found in the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Metadata file not found at: {file_path}")

    logger.debug(f"Parsing metadata from {file_path} using AST.")
    content = file_path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    metadata = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("__"):
                    try:
                        value = ast.literal_eval(node.value)
                        if _is_supported_sync_value(value):
                            metadata[target.id] = value
                    except ValueError:
                        # Ignore values that aren't simple literals (e.g., function calls)
                        logger.debug(f"Skipping non-literal assignment for {target.id}")
    return metadata


def check_sync(source_metadata: dict[str, Any], about_path: Path) -> list[str]:
    """
    Compares source metadata with an __about__.py file to check for sync.

    Args:
        source_metadata: The dictionary of metadata from the source (e.g., pyproject.toml).
        about_path: The path to the __about__.py file to check.

    Returns:
        A list of keys that are out of sync. An empty list means everything is synced.
    """
    logger.info(f"Checking sync between source metadata and {about_path}")
    try:
        about_metadata = read_about_file_ast(about_path)
    except FileNotFoundError as e:
        return [f"File is missing: {e}"]

    mismatches = []

    # Normalize source keys for comparison
    normalized_source = {k.lower().replace("-", "_"): v for k, v in source_metadata.items()}

    for source_key, about_key in KEY_MAP.items():
        if source_key in normalized_source:
            source_value = normalized_source.get(source_key)
            about_value = about_metadata.get(about_key)

            if not _is_supported_sync_value(source_value):
                logger.debug(f"Skipping sync check for non-string source key '{source_key}'")
                continue

            if about_value is None:
                mismatches.append(f"'{about_key}' is missing from {about_path.name}")
            elif _normalize_sync_value(source_value) != _normalize_sync_value(about_value):
                mismatch_msg = (
                    f"'{about_key}' is out of sync. Source: '{source_value}', {about_path.name}: '{about_value}'"
                )
                mismatches.append(mismatch_msg)
                logger.warning(mismatch_msg)

    return mismatches
```
## File: __about__.py
```python
"""Metadata for metametameta."""

__all__ = [
    "__title__",
    "__version__",
    "__description__",
    "__credits__",
    "__readme__",
    "__requires_python__",
    "__keywords__",
    "__status__",
    "__dependencies__",
]

__title__ = "metametameta"
__version__ = "0.1.7"
__description__ = "Generate __about__.py with dunder meta."
__credits__ = [{"name": "Matthew Martin", "email": "matthewdeanmartin@gmail.com"}]
__readme__ = "README.md"
__requires_python__ = ">=3.8"
__keywords__ = ["packaging", "metadata"]
__status__ = "5 - Production/Stable"
__dependencies__ = ["rich_argparse>=1.7.1", "toml>=0.10.2", "colorlog>=6.9.0", "totalhelp"]
```
## File: __main__.py
```python
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
from metametameta.from_conda_meta import generate_from_conda_meta, read_conda_meta_metadata
from metametameta.from_importlib import generate_from_importlib
from metametameta.from_pep621 import generate_from_pep621, read_pep621_metadata
from metametameta.from_poetry import generate_from_poetry, read_poetry_metadata
from metametameta.from_requirements_txt import generate_from_requirements_txt, read_requirements_txt_metadata
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


def handle_requirements_txt(args: argparse.Namespace) -> None:
    """
    Handle the requirements_txt subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from requirements.txt")
    generate_from_requirements_txt(name=args.name, source=args.source, output=args.output, validate=args.validate)


def handle_conda_meta(args: argparse.Namespace) -> None:
    """
    Handle the conda_meta subcommand.
    Args:
        args (argparse.Namespace): The arguments.
    """
    print("Generating metadata source from conda/meta.yaml")
    generate_from_conda_meta(name=args.name, source=args.source, output=args.output, validate=args.validate)


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
            "requirements_txt": generate_from_requirements_txt,
            "conda_meta": generate_from_conda_meta,
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
            "requirements_txt": read_requirements_txt_metadata,
            "conda_meta": read_conda_meta_metadata,
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

    parser_requirements = subparsers.add_parser(
        "requirements_txt", help="Generate from requirements.txt", parents=[gen_parser]
    )
    parser_requirements.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_requirements.add_argument("--source", type=str, default="requirements.txt", help="Path to requirements.txt")
    parser_requirements.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_requirements.set_defaults(func=handle_requirements_txt)

    parser_conda_meta = subparsers.add_parser("conda_meta", help="Generate from conda/meta.yaml", parents=[gen_parser])
    parser_conda_meta.add_argument("--name", type=str, default="", help="Name of the project (from file if omitted)")
    parser_conda_meta.add_argument("--source", type=str, default="conda/meta.yaml", help="Path to conda/meta.yaml")
    parser_conda_meta.add_argument("--output", type=str, default="__about__.py", help="Output file")
    parser_conda_meta.set_defaults(func=handle_conda_meta)

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
```
## File: utils\cli_suggestions.py
```python
"""
Smart argument parser with typo suggestions.

This module provides a subclass of `argparse.ArgumentParser` that enhances
the error reporting behavior when users supply invalid choices. If a user
makes a typo in a choice, the parser will suggest the closest matches
based on string similarity.

Example:
    ```python
    import sys

    parser = SmartParser(prog="myapp")
    parser.add_argument("color", choices=["red", "green", "blue"])
    args = parser.parse_args()

    # If the user runs:
    #   myapp gren
    #
    # The output will include:
    #   error: invalid choice: 'gren' (choose from 'red', 'green', 'blue')
    #
    #   Did you mean: green?
    ```
"""

from __future__ import annotations

import argparse
import sys
from difflib import get_close_matches
from typing import Never


class SmartParser(argparse.ArgumentParser):
    """Argument parser that suggests similar choices on invalid input.

    This class extends `argparse.ArgumentParser` to provide more helpful
    error messages when the user provides an invalid choice for an argument.
    Instead of only showing the list of valid choices, it also suggests the
    closest matches using fuzzy string matching.

    Example:
        ```python
        parser = SmartParser()
        parser.add_argument("fruit", choices=["apple", "banana", "cherry"])
        args = parser.parse_args()
        ```

    If the user types:
        ```
        myprog bannna
        ```

    The error message will include:
        ```
        Did you mean: banana?
        ```
    """

    def error(self, message: str) -> Never:
        """Handle parsing errors with suggestions for invalid choices.

        Args:
            message (str): The error message generated by argparse,
                typically when parsing fails (e.g., due to invalid
                choices or syntax errors).

        Side Effects:
            - Prints usage information to `sys.stderr`.
            - Exits the program with status code 2.

        Behavior:
            - If the error message contains an "invalid choice" message,
              attempts to suggest the closest valid alternatives by
              computing string similarity.
            - Otherwise, preserves standard argparse behavior.
        """
        # Detect "invalid choice: 'foo' (choose from ...)"
        if "invalid choice" in message and "choose from" in message:
            bad = message.split("invalid choice:")[1].split("(")[0].strip().strip("'\"")
            choices_str = message.split("choose from")[1]
            choices = [c.strip().strip(",)'") for c in choices_str.split() if c.strip(",)")]

            tips = get_close_matches(bad, choices, n=3, cutoff=0.6)
            if tips:
                message += f"\n\nDid you mean: {', '.join(tips)}?"

        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")
```
