from pathlib import Path

import pytest


def assert_paths_point_to_same_real_file(x: str, y: str) -> None:
    """Asserts that two paths could point to the same file based on their endings.

    Args:
        x (str): The first path, expected to be absolute.
        y (str): The second path, expected to be relative.

    Raises:
        AssertionError: If the paths do not end with the same folder and file name.
    """
    absolute_path = Path(x).resolve()
    relative_path = Path(y).resolve()

    if not absolute_path.name == relative_path.name:
        raise AssertionError(f"File names do not match: {absolute_path.name} != {relative_path.name}")

    relative_parts = list(Path(y).parts)
    absolute_tail_parts = list(absolute_path.parts)[-len(relative_parts) :]

    if relative_parts != absolute_tail_parts:
        raise AssertionError(f"Paths do not match: {absolute_tail_parts} != {relative_parts}")


def assert_paths_point_to_same_file(x: str, y: str) -> None:
    """Asserts that two paths could point to the same file based on their endings.

    Args:
        x (str): The first path, expected to be absolute.
        y (str): The second path, expected to be relative.

    Raises:
        AssertionError: If the paths do not end with the same folder and file name.
    """
    absolute_path = Path(x)
    relative_path = Path(y)

    # Convert the relative path to an absolute path by appending it to the root of the absolute path
    relative_path_as_absolute = Path(*absolute_path.parts[: -len(relative_path.parts)]) / relative_path

    # Check if the last parts of the paths are the same
    if list(absolute_path.parts[-len(relative_path.parts) :]) != list(
        relative_path_as_absolute.parts[-len(relative_path.parts) :]
    ):
        raise AssertionError(
            f"Paths do not match: {absolute_path.parts[-len(relative_path.parts):]} != {relative_path_as_absolute.parts[-len(relative_path.parts):]}"
        )


def test_assert_paths_point_to_same_file():
    x = "C:\\Users\\matth\\AppData\\Local\\Temp\\pytest-of-matth\\pytest-708\\test_generate_from_pep621_edge1\\my_project\\__about__.py"
    y = "./my_project\\__about__.py"

    assert_paths_point_to_same_file(x, y)


if __name__ == "__main__":
    pytest.main()
