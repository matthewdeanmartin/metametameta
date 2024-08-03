import pytest

from metametameta.from_poetry import generate_from_poetry


def test_generate_from_poetry_file_not_found(tmp_path):
    # A non-existent file path
    non_existent_file = tmp_path / "non_existent_pyproject.toml"

    with pytest.raises(FileNotFoundError):
        generate_from_poetry(source=str(non_existent_file))
