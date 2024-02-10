import os

from metametameta import generate_from_poetry


def test_generate_from_poetry_alt(tmp_path):
    # Create a minimal pyproject.toml in the tmp_path directory
    pyproject_toml_path = tmp_path / "pyproject.toml"
    src_path = tmp_path / "my_package"
    src_path.mkdir()
    with open(pyproject_toml_path, "w", encoding="utf-8") as file:
        file.write("[tool.poetry]\n")
        file.write("name = 'MyPoetryProject'\n")
        file.write("version = '1.0.1'\n")
        file.write("description = 'A sample poetry project.'\n")
        file.write("packages = [\n")
        file.write("{ include = 'my_package' },")
        file.write("{ include = 'extra_package/**/*.py' },")
        file.write("]")
        # Add more [tool.poetry] fields as needed

    # Store the original cwd and temporarily change cwd to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Execution: Call the function
        generate_from_poetry()

        # Expected output file path
        expected_file_path = tmp_path / "my_package/__about__.py"

        # Assertion: Check if the file is created at the correct location
        assert os.path.isfile(expected_file_path), "File was not created at the expected location"

        # Assertion: Check the content of the file
        with open(expected_file_path, encoding="utf-8") as file:
            content = file.read()
        # Define the expected content based on the metadata in pyproject.toml
        expected_content = '''"""Metadata for my_package."""

__all__ = [
    "__title__",
    "__version__",
    "__description__"
]

__title__ = "MyPoetryProject"
__version__ = "1.0.1"
__description__ = "A sample poetry project."'''
        assert content == expected_content, "Content of the file does not match the expected content"
    finally:
        # Revert the cwd back to the original
        os.chdir(original_cwd)
