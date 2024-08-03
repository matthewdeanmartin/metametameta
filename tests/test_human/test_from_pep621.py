import os

from metametameta import generate_from_pep621


def test_generate_from_pep621(tmp_path):
    # Create a minimal pyproject.toml with [project] section in the tmp_path directory
    pyproject_toml_path = tmp_path / "pyproject.toml"
    with open(pyproject_toml_path, "w", encoding="utf-8") as file:
        file.write("[project]\n")
        file.write("name = 'MyPEP621Project'\n")
        file.write("version = '0.1.0'\n")
        file.write("description = 'A sample PEP 621 compliant project.'\n")
        # Add more [project] fields as needed

    # Store the original cwd and temporarily change cwd to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Execution: Call the function
        generate_from_pep621(source=str(pyproject_toml_path))

        # Expected output file path
        expected_file_path = tmp_path / "MyPEP621Project/__about__.py"

        # Assertion: Check if the file is created at the correct location
        assert os.path.isfile(expected_file_path), "File was not created at the expected location"

        # Assertion: Check the content of the file
        with open(expected_file_path, encoding="utf-8") as file:
            content = file.read()
        # Define the expected content based on the metadata in pyproject.toml
        expected_content = '''"""Metadata for MyPEP621Project."""

__all__ = [
    "__title__",
    "__version__",
    "__description__"
]

__title__ = "MyPEP621Project"
__version__ = "0.1.0"
__description__ = "A sample PEP 621 compliant project."'''
        assert content == expected_content, "Content of the file does not match the expected content"
    finally:
        # Revert the cwd back to the original
        os.chdir(original_cwd)
