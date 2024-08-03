import pytest

from metametameta.find_it import find_metadata_in_file, find_metadata_in_module, main


@pytest.mark.parametrize(
    "file_content, expected_output",
    [
        ("__version__ = '1.0.0'\n__author__ = 'John Doe'\n", {"version": "1.0.0", "author": "John Doe"}),
        (
            "__name__ = 'test_module'\n__description__ = 'Test module description'\n__version__ = '0.1.0'\n",
            {"name": "test_module", "description": "Test module description", "version": "0.1.0"},
        ),
        ("__author__ = 'Jane Doe'\n# Just a comment\n__license__ = 'MIT'\n", {"author": "Jane Doe", "license": "MIT"}),
        ("__version__ = '2.0.0'\ndef function(): pass\n", {"version": "2.0.0"}),
        ("", {}),  # No content
    ],
)
def test_find_metadata_in_file(tmp_path, file_content, expected_output):
    # Create a temporary file with the provided content
    temp_file = tmp_path / "test_about.py"
    temp_file.write_text(file_content, encoding="utf-8")

    # Call the function on the temp file and check the output
    result = find_metadata_in_file(temp_file)

    assert result == expected_output


def test_main_import_error(mocker):
    # Mocking importlib.import_module to raise an ImportError
    mocker.patch("importlib.import_module", side_effect=ImportError("Module not found"))

    with pytest.raises(SystemExit):  # main() would exit on error
        main(["script_name", "non_existent_module"])


def test_find_metadata_in_file_happy_path(tmp_path):
    # Create a sample metadata file
    metadata_file = tmp_path / "example_about.py"
    content = "__version__ = '1.0.0'\n__author__ = 'Test Author'\n"
    metadata_file.write_text(content, encoding="utf-8")

    expected_metadata = {"version": "1.0.0", "author": "Test Author"}

    # Testing the happy path
    metadata = find_metadata_in_file(metadata_file)
    assert metadata == expected_metadata


def test_find_metadata_in_file_empty_file(tmp_path):
    # Create an empty python file
    empty_file = tmp_path / "empty.py"
    empty_file.write_text("", encoding="utf-8")

    # Expecting an empty metadata dict
    metadata = find_metadata_in_file(empty_file)
    assert metadata == {}


def test_find_metadata_in_file_no_metadata(tmp_path):
    # Create a python file with no metadata
    non_metadata_file = tmp_path / "no_metadata.py"
    non_metadata_file.write_text("some_other_var = 'not metadata'\n", encoding="utf-8")

    # Expecting an empty metadata dict
    metadata = find_metadata_in_file(non_metadata_file)
    assert metadata == {}


def test_find_metadata_in_module_happy_path(tmp_path):
    # Create a sample directory with about files
    about_file_1 = tmp_path / "module1/about.py"
    about_file_1.parent.mkdir(parents=True, exist_ok=True)
    about_file_1.write_text("__version__ = '1.0.0'\n", encoding="utf-8")

    about_file_2 = tmp_path / "module2/about.py"
    about_file_2.parent.mkdir(parents=True, exist_ok=True)
    about_file_2.write_text("__version__ = '2.0.0'\n__author__ = 'Author Two'\n", encoding="utf-8")

    expected_results = {
        "module1.about": {"version": "1.0.0"},
        "module2.about": {"version": "2.0.0", "author": "Author Two"},
    }

    # Testing the happy path for module
    results = find_metadata_in_module(tmp_path)
    assert results == expected_results


def test_find_metadata_in_module_no_python_files(tmp_path):
    # Create a directory with an empty text file
    text_file = tmp_path / "not_a_python_file.txt"
    text_file.write_text("This is not a python file.", encoding="utf-8")

    # Expecting an empty metadata dict because there are no Python files
    results = find_metadata_in_module(tmp_path)
    assert results == {}


def test_find_metadata_in_file_read_error(mocker, tmp_path):
    # Create a legitimate path but will simulate a reading error later
    mock_file = tmp_path / "mock_file.py"
    mock_file.write_text("__version__ = '1.0.0'", encoding="utf-8")

    # Mocking the open function to raise an IOError
    mocker.patch("builtins.open", side_effect=OSError("File not readable"))

    with pytest.raises(IOError):
        find_metadata_in_file(mock_file)


def test_find_metadata_in_file_bad_format(tmp_path):
    # Create a file with improperly formatted metadata
    bad_format_file = tmp_path / "bad_format.py"
    bad_format_file.write_text("__version__ = 1.0.0\n", encoding="utf-8")

    # Expecting to capture the exception, since not a valid string
    metadata = find_metadata_in_file(bad_format_file)
    assert metadata == {}  # This test assumes the function should return an empty dict rather than raise an error
