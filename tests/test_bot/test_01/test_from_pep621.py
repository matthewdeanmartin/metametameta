from __future__ import annotations

from unittest.mock import patch

import pytest
import toml

from metametameta.from_pep621 import generate_from_pep621


@pytest.mark.parametrize(
    "project_data, expected_output, expected_content",
    [
        # Test case 3: Missing project section
        ({}, "No [project] section found in pyproject.toml.", None),
    ],
)
def test_generate_from_pep621(tmp_path, project_data, expected_output, expected_content):
    # Set up the mock for external dependencies
    mock_any_metadict = patch("metametameta.general.any_metadict").start()
    mock_merge_sections = patch("metametameta.general.merge_sections").start()

    # Configure the mocks
    if project_data:
        mock_any_metadict.return_value = (expected_content, ["version"])
        mock_merge_sections.return_value = expected_content

    # Create the temporary pyproject.toml file with the desired data.
    pyproject_content = {"project": project_data}
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(toml.dumps(pyproject_content), encoding="utf-8")

    # Call the function under test
    output_path = generate_from_pep621(source=str(pyproject_file), output=expected_output)

    # Check the results as expected
    if expected_content:
        # Verify that the returned output path is as expected
        assert output_path == str(tmp_path / expected_output)

        # Check if the __about__.py file has the expected content
        about_file_path = tmp_path / expected_output
        assert about_file_path.exists()
        with open(about_file_path, encoding="utf-8") as f:
            assert f.read() == expected_content
    else:
        # Ensure the function returns the expected error string
        assert output_path == expected_output

    # Stop the patchers
    mock_any_metadict.stop()
    mock_merge_sections.stop()


def test_generate_from_pep621_file_not_found():
    # Test case for FileNotFoundError
    with pytest.raises(FileNotFoundError):
        generate_from_pep621(source="non_existent_file.toml")


def test_generate_from_pep621_with_no_dependencies_writes_typed_empty_list(tmp_path, monkeypatch):
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        toml.dumps(
            {
                "project": {
                    "name": "demo-app",
                    "version": "0.1.0",
                    "description": "Demo package",
                    "dependencies": [],
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "demo_app").mkdir()
    monkeypatch.chdir(tmp_path)

    generated_path = generate_from_pep621(source=str(pyproject_file), validate=True)
    generated_content = (tmp_path / "demo_app" / "__about__.py").read_text(encoding="utf-8")

    assert generated_path.endswith("__about__.py")
    assert "__dependencies__: list[str] = []" in generated_content
