"""Fail if the local project version is not newer than the last PyPI release."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from packaging.version import Version

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]


def load_project_metadata(pyproject_path: Path) -> tuple[str, Version]:
    """Load project name and version from pyproject.toml."""
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data["project"]
    return project["name"], Version(project["version"])


def fetch_pypi_version(project_name: str) -> Version | None:
    """Return the latest published PyPI version for a project."""
    request = Request(
        f"https://pypi.org/pypi/{project_name}/json",
        headers={"User-Agent": "metametameta prerelease version check"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except URLError as exc:
        raise SystemExit(f"Unable to reach PyPI for version check: {exc}") from exc
    return Version(payload["info"]["version"])


def main() -> int:
    """Check that the local version is ahead of the published PyPI version."""
    project_name, local_version = load_project_metadata(Path("pyproject.toml"))
    published_version = fetch_pypi_version(project_name)
    if published_version is None:
        print(f"Version OK: {project_name} has no published PyPI release yet; local is {local_version}.")
        return 0
    if local_version <= published_version:
        raise SystemExit(
            f"Local version {local_version} must be greater than published PyPI version {published_version}."
        )
    print(f"Version OK: local {local_version} is newer than PyPI {published_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
