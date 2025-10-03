"""
Tests for the filesystem module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Functions to test, including the private ones
from metametameta.filesystem import (
    _determine_target_dir,
    _find_existing_package_dir,
    write_to_file,
    write_to_package_dir,
)

# --- Tests for _find_existing_package_dir ---


def test_find_existing_flat_dir(tmp_path: Path):
    """Should find a simple directory in the root."""
    (tmp_path / "my_package").mkdir()
    result = _find_existing_package_dir(tmp_path, "my_package")
    assert result == tmp_path / "my_package"


def test_find_existing_src_layout_dir(tmp_path: Path):
    """Should find a directory within a 'src' layout."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "my_package").mkdir()
    result = _find_existing_package_dir(tmp_path, "my_package")
    assert result == tmp_path / "src" / "my_package"


def test_find_existing_dir_with_hyphen_preference(tmp_path: Path):
    """Should prefer the underscored name if both hyphenated and underscored exist."""
    (tmp_path / "my-package").mkdir()
    (tmp_path / "my_package").mkdir()  # This is the one it should find first
    result = _find_existing_package_dir(tmp_path, "my-package")
    assert result == tmp_path / "my_package"


def test_find_existing_dir_with_hyphen_fallback(tmp_path: Path):
    """Should find the hyphenated name if only that one exists."""
    (tmp_path / "my-package").mkdir()
    result = _find_existing_package_dir(tmp_path, "my-package")
    assert result == tmp_path / "my-package"


def test_find_existing_dir_not_found(tmp_path: Path):
    """Should return None if no matching directory is found."""
    result = _find_existing_package_dir(tmp_path, "non_existent_package")
    assert result is None


# --- Tests for _determine_target_dir ---


def test_determine_target_dir_returns_existing(tmp_path: Path):
    """Should return the existing directory if one is found."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "existing_package").mkdir()
    result = _determine_target_dir(tmp_path, "existing-package")
    assert result == tmp_path / "src" / "existing_package"


def test_determine_target_dir_creates_in_src(tmp_path: Path):
    """Should choose a path inside 'src' for creation if 'src' exists."""
    (tmp_path / "src").mkdir()
    result = _determine_target_dir(tmp_path, "new-package")
    assert result == tmp_path / "src" / "new_package"


def test_determine_target_dir_creates_in_root(tmp_path: Path):
    """Should choose a path in the root for creation if 'src' does not exist."""
    result = _determine_target_dir(tmp_path, "new-package")
    assert result == tmp_path / "new_package"


# --- Tests for write_to_package_dir (New Deterministic Function) ---


def test_write_to_package_dir_creates_flat_layout(tmp_path: Path):
    """Should create a directory and file in a flat layout."""
    project_root = tmp_path
    package_name = "my-new-app"
    file_content = "__version__ = '1.0.0'"

    result_path_str = write_to_package_dir(
        project_root=project_root, package_dir_name=package_name, about_content=file_content
    )

    expected_path = project_root / "my_new_app" / "__about__.py"
    assert Path(result_path_str) == expected_path
    assert expected_path.is_file()
    assert expected_path.read_text(encoding="utf-8") == file_content


def test_write_to_package_dir_creates_src_layout(tmp_path: Path):
    """Should create a directory and file correctly in a 'src' layout."""
    project_root = tmp_path
    (project_root / "src").mkdir()
    package_name = "my-src-app"
    file_content = "__version__ = '1.0.0'"

    result_path_str = write_to_package_dir(
        project_root=project_root, package_dir_name=package_name, about_content=file_content
    )

    expected_path = project_root / "src" / "my_src_app" / "__about__.py"
    assert Path(result_path_str) == expected_path
    assert expected_path.is_file()
    assert expected_path.read_text(encoding="utf-8") == file_content


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
    file_content = "__license__ = 'MIT'"

    # Call the old function signature
    result_path_str = write_to_file(directory=package_name, about_content=file_content)

    # It should behave just like the new function, but using CWD as the root
    expected_path = tmp_path / "legacy_app" / "__about__.py"
    assert Path(result_path_str) == expected_path
    assert expected_path.is_file()
    assert expected_path.read_text(encoding="utf-8") == file_content
