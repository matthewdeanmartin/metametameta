"""Bump the patch version in pyproject.toml without external release tooling."""

from __future__ import annotations

import re
from pathlib import Path

from packaging.version import Version


PROJECT_VERSION_PATTERN = re.compile(r'(?ms)(^\[project\]\s.*?^version = ")([^"]+)(")')


def bump_patch(version_text: str) -> str:
    """Return the next patch version."""
    version = Version(version_text)
    return f"{version.major}.{version.minor}.{version.micro + 1}"


def update_project_version(pyproject_path: Path) -> str:
    """Update the project version in pyproject.toml and return the new version."""
    content = pyproject_path.read_text(encoding="utf-8")
    match = PROJECT_VERSION_PATTERN.search(content)
    if match is None:
        raise SystemExit("Could not find [project].version in pyproject.toml.")
    current_version = match.group(2)
    new_version = bump_patch(current_version)
    updated = PROJECT_VERSION_PATTERN.sub(
        lambda match_obj: f'{match_obj.group(1)}{new_version}{match_obj.group(3)}',
        content,
        count=1,
    )
    pyproject_path.write_text(updated, encoding="utf-8")
    print(f"Bumped version: {current_version} -> {new_version}")
    return new_version


def main() -> int:
    """Bump the patch version in pyproject.toml."""
    update_project_version(Path("pyproject.toml"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
