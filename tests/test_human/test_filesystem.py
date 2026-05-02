from __future__ import annotations

from pathlib import Path

import pytest

from metametameta.filesystem import PackageDirectoryNotFoundError, write_to_file


def test_write_to_file(tmp_path):
    # Test setup: Define directory, content, and expected output file
    directory = tmp_path / "test_package"
    directory.mkdir()
    about_content = "__version__ = '1.0.0'"
    output_file_name = "__about__.py"

    # Execution: Call the function
    the_result = write_to_file(str(directory), about_content, output_file_name)
    assert Path(the_result).exists()
    assert Path(the_result).is_file()

    with open(the_result, encoding="utf-8") as file:
        content = file.read()
    assert content == about_content, "Content of the file does not match the expected content"


def test_write_to_file_errors_when_package_dir_missing(tmp_path, monkeypatch):
    """The legacy wrapper must refuse to invent a package directory."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(PackageDirectoryNotFoundError) as exc_info:
        write_to_file("definitely-not-a-real-pkg", "__version__ = '0.0.0'")
    message = str(exc_info.value)
    assert "definitely-not-a-real-pkg" in message
    assert "--output" in message
    # The bogus directory must not have been created.
    assert not (tmp_path / "definitely-not-a-real-pkg").exists()
    assert not (tmp_path / "definitely_not_a_real_pkg").exists()

    # Is this some / vs \ thing?
    # # Expected output file path
    # expected_file_path = directory / output_file_name
    #
    # assert expected_file_path.exists()
    # assert expected_file_path.is_file()
    # # assert Path(result) == expected_file_path # varies by os!
    # # Assertion: Check if the file is created at the correct location
    # assert os.path.isfile(expected_file_path), "File was not created at the expected location"
    #
    # # Assertion: Check if the content of the file is as expected
    # with open(expected_file_path, encoding="utf-8") as file:
    #     content = file.read()
    # assert content == about_content, "Content of the file does not match the expected content"


# E       AssertionError: assert
#   WindowsPath('C:/Users/matth/AppData/Local/Temp/pytest_of_matth/pytest_2031/test_write_to_file0/test_package/__about__.py') ==
#   WindowsPath('C:/Users/matth/AppData/Local/Temp/pytest-of-matth/pytest-2031/test_write_to_file0/test_package/__about__.py')
# E WindowsPath('C:/Users/matth/AppData/Local/Temp/pytest_of_matth/pytest_2031/test_write_to_file0/test_package/__about__.py')
# =       Path('C:\\Users\\matth\\AppData\\Local\\Temp\\pytest_of_matth\\pytest_2031\\test_write_to_file0\\test_package\\__about__.py')
