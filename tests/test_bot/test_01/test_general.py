from __future__ import annotations

import pytest

from metametameta.general import any_metadict, safe_quote


# Parameterized test cases for the any_metadict function
@pytest.mark.parametrize(
    "metadata, expected_content, expected_names",
    [
        ({"name": "my_package"}, '__title__ = "my_package"\n', ["__title__"]),
        (
            {"name": "my_package", "authors": ["John Doe <john@example.com>"]},
            '__title__ = "my_package"\n__author__ = "John Doe"\n__author_email__ = "john@example.com"\n',
            ["__title__", "__author__", "__author_email__"],
        ),
        (
            {
                "name": "my_package",
                "authors": ["Jane Doe", "John Smith"],
                "classifiers": ["Development Status :: 5 - Production/Stable"],
            },
            '__title__ = "my_package"\n__credits__ = ["Jane Doe", "John Smith"]\n__status__ = "5 - Production/Stable"\n',
            ["__title__", "__credits__", "__status__"],
        ),
        (
            {"name": "my_package", "keywords": ["keyword1", "keyword2"]},
            '__title__ = "my_package"\n__keywords__ = ["keyword1", "keyword2"]\n',
            ["__title__", "__keywords__"],
        ),
        (
            {"name": "my_package", "some-value": "example"},
            '__title__ = "my_package"\n__some_value__ = "example"\n',
            ["__title__", "__some_value__"],
        ),
    ],
)
def test_any_metadict(metadata, expected_content, expected_names):
    content, names = any_metadict(metadata)
    assert content.replace("'", '"').replace("\n", "") == expected_content.replace("'", '"').replace("\n", "")
    assert names == expected_names


def test_any_metadict_edge_case_empty_input():
    metadata = {}

    about_content, names = any_metadict(metadata)

    assert about_content == ""
    assert names == []


def test_safe_quote_happy_path():
    value = "Hello, world!"
    result = safe_quote(value)

    assert result == '"Hello, world!"'


def test_safe_quote_multiline_value():
    value = "Hello\nWorld"
    result = safe_quote(value)

    assert result == '"""Hello\nWorld"""'


def test_safe_quote_invalid_type():
    value = 42
    result = safe_quote(value)

    assert result == "42"
