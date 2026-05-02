"""
Tests for the filesystem module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Functions to test, including the private ones
from metametameta.filesystem import (
    PackageDirectoryNotFoundError,
    determine_target_dir,
    find_existing_package_dir,
    write_to_file,
    write_to_package_dir,
)

# --- Tests for find_existing_package_dir ---


def test_find_existing_flat_dir(tmp_path: Path):
    """Should find a simple directory in the root."""
    (tmp_path / "my_package").mkdir()
    result = find_existing_package_dir(tmp_path, "my_package")
    assert result == tmp_path / "my_package"


def test_find_existing_src_layout_dir(tmp_path: Path):
    """Should find a directory within a 'src' layout."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "my_package").mkdir()
    result = find_existing_package_dir(tmp_path, "my_package")
    assert result == tmp_path / "src" / "my_package"


def test_find_existing_dir_with_hyphen_preference(tmp_path: Path):
    """Should prefer the underscored name if both hyphenated and underscored exist."""
    (tmp_path / "my-package").mkdir()
    (tmp_path / "my_package").mkdir()  # This is the one it should find first
    result = find_existing_package_dir(tmp_path, "my-package")
    assert result == tmp_path / "my_package"


def test_find_existing_dir_with_hyphen_fallback(tmp_path: Path):
    """Should find the hyphenated name if only that one exists."""
    (tmp_path / "my-package").mkdir()
    result = find_existing_package_dir(tmp_path, "my-package")
    assert result == tmp_path / "my-package"


def test_find_existing_dir_not_found(tmp_path: Path):
    """Should return None if no matching directory is found."""
    result = find_existing_package_dir(tmp_path, "non_existent_package")
    assert result is None


# --- Tests for determine_target_dir ---


def test_determine_target_dir_returns_existing(tmp_path: Path):
    """Should return the existing directory if one is found."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "existing_package").mkdir()
    result = determine_target_dir(tmp_path, "existing-package")
    assert result == tmp_path / "src" / "existing_package"


def test_determine_target_dir_raises_when_src_dir_missing(tmp_path: Path):
    """If only an empty 'src' directory exists (and no package dir), refuse to guess."""
    (tmp_path / "src").mkdir()
    with pytest.raises(PackageDirectoryNotFoundError):
        determine_target_dir(tmp_path, "new-package")


def test_determine_target_dir_raises_when_no_package_dir(tmp_path: Path):
    """If no candidate directory exists, refuse to guess and raise."""
    with pytest.raises(PackageDirectoryNotFoundError) as exc_info:
        determine_target_dir(tmp_path, "new-package")
    msg = str(exc_info.value)
    assert "new-package" in msg
    assert "--output" in msg


# --- Tests for write_to_package_dir (New Deterministic Function) ---


def test_write_to_package_dir_writes_into_existing_flat_layout(tmp_path: Path):
    """Should write a file into a pre-existing flat layout package."""
    project_root = tmp_path
    package_name = "my-new-app"
    (project_root / "my_new_app").mkdir()
    file_content = "__version__ = '1.0.0'"

    result_path_str = write_to_package_dir(
        project_root=project_root, package_dir_name=package_name, about_content=file_content
    )

    expected_path = project_root / "my_new_app" / "__about__.py"
    assert Path(result_path_str) == expected_path
    assert expected_path.is_file()
    assert expected_path.read_text(encoding="utf-8") == file_content


def test_write_to_package_dir_writes_into_existing_src_layout(tmp_path: Path):
    """Should write a file into a pre-existing src-layout package."""
    project_root = tmp_path
    (project_root / "src").mkdir()
    (project_root / "src" / "my_src_app").mkdir()
    package_name = "my-src-app"
    file_content = "__version__ = '1.0.0'"

    result_path_str = write_to_package_dir(
        project_root=project_root, package_dir_name=package_name, about_content=file_content
    )

    expected_path = project_root / "src" / "my_src_app" / "__about__.py"
    assert Path(result_path_str) == expected_path
    assert expected_path.is_file()
    assert expected_path.read_text(encoding="utf-8") == file_content


def test_write_to_package_dir_raises_when_dir_missing(tmp_path: Path):
    """If the target package directory does not exist, raise rather than create it."""
    with pytest.raises(PackageDirectoryNotFoundError):
        write_to_package_dir(
            project_root=tmp_path, package_dir_name="my-new-app", about_content="__version__ = '0.0.0'"
        )
    # Confirm no directory was silently created.
    assert not (tmp_path / "my_new_app").exists()
    assert not (tmp_path / "my-new-app").exists()


def test_write_to_package_dir_uses_existing_dir(tmp_path: Path):
    """Should write the file into an already existing package directory."""
    project_root = tmp_path
    package_dir = project_root / "existing_app"
    package_dir.mkdir()
    file_content = "__author__ = 'Test'"

    result_path_str = write_to_package_dir(
        project_root=project_root, package_dir_name="existing_app", about_content=file_content
    )

    expected_path = package_dir / "__about__.py"
    assert Path(result_path_str) == expected_path
    assert expected_path.read_text(encoding="utf-8") == file_content


# --- Tests for write_to_file (Legacy Wrapper) ---


def test_write_to_file_legacy_wrapper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Tests the legacy write_to_file function by controlling the CWD.
    """
    # We are "running" the script from tmp_path
    monkeypatch.chdir(tmp_path)

    package_name = "legacy-app"
    (tmp_path / "legacy_app").mkdir()
    file_content = "__license__ = 'MIT'"

    # Call the old function signature
    result_path_str = write_to_file(directory=package_name, about_content=file_content)

    # It should behave just like the new function, but using CWD as the root
    expected_path = tmp_path / "legacy_app" / "__about__.py"
    assert Path(result_path_str) == expected_path
    assert expected_path.is_file()
    assert expected_path.read_text(encoding="utf-8") == file_content


def test_write_to_file_legacy_wrapper_raises_when_dir_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The legacy wrapper must surface PackageDirectoryNotFoundError too."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(PackageDirectoryNotFoundError):
        write_to_file(directory="legacy-app", about_content="__license__ = 'MIT'")
    assert not (tmp_path / "legacy_app").exists()
