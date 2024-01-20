import pytest

from metametameta.general import any_metadict, merge_sections


# Test cases for any_metadict function
@pytest.mark.parametrize(
    "metadata,expected_output",
    [
        ({"name": "MyProject"}, ('__title__ = "MyProject"\n', ["__title__"])),
        (
            {"authors": ["John Doe <john@example.com>"]},
            ('__author__ = "John Doe"\n__author_email__ = "john@example.com"\n', ["__author__", "__author_email__"]),
        ),
        ({"classifiers": ["Development Status :: 4 - Beta"]}, ('__status__ = "4 - Beta"\n', ["__status__"])),
        ({"keywords": ["python", "testing"]}, ('__keywords__ = ["python", "testing"]\n', ["__keywords__"])),
        # Add more test cases as needed
    ],
)
def test_any_metadict(metadata, expected_output):
    about_content, names = any_metadict(metadata)
    assert about_content.replace("'", '"') + "\n" == expected_output[0], "Incorrect about_content"
    assert names == expected_output[1], "Incorrect names"


# Test cases for merge_sections function
@pytest.mark.parametrize(
    "names,project_name,about_content,expected_output",
    [
        (
            ["__title__"],
            "MyProject",
            '__title__ = "MyProject"\n',
            '"""Metadata for MyProject."""\n\n__all__ = [\n    "__title__"\n]\n\n__title__ = "MyProject"\n',
        ),
        # Add more test cases as needed
    ],
)
def test_merge_sections(names, project_name, about_content, expected_output):
    merged_content = merge_sections(names, project_name, about_content)
    assert merged_content == expected_output, "Incorrect merged content"
