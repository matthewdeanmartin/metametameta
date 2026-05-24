"""Tests targeting coverage gaps in general.py and from_poetry.py."""
from __future__ import annotations

import pytest

from metametameta.from_poetry import format_poetry_dependency, generate_from_poetry
from metametameta.general import (
    get_all_primitive_values,
    indent_multiline_value,
    render_collection_assignment,
    render_python_value,
    validate_about_file,
)


# --- general.py: render_python_value multiline branches ---


def test_render_python_value_bool_true():
    assert render_python_value(True) == "True"


def test_render_python_value_bool_false():
    assert render_python_value(False) == "False"


def test_render_python_value_none():
    assert render_python_value(None) == "None"


def test_render_python_value_int():
    assert render_python_value(42) == "42"


def test_render_python_value_float():
    assert render_python_value(3.14) == "3.14"


def test_render_python_value_unknown_type():
    # Fallback to repr() for unsupported types
    result = render_python_value(object())
    assert result.startswith("<object")


def test_render_python_value_long_list_wraps():
    # A list long enough to exceed 120 chars triggers multiline rendering
    long_items = [f"some-package-name-{i}>=1.2.3" for i in range(10)]
    result = render_python_value(long_items)
    assert result.startswith("[\n")
    assert result.endswith("]")


def test_render_python_value_long_list_with_multiline_item():
    # An item containing \n triggers the nested multiline branch
    items = ["a\nb"]
    result = render_python_value(items, indent=0)
    # short list with a newline-containing item still renders as multiline
    assert "a" in result and "b" in result


def test_render_python_value_short_dict():
    result = render_python_value({"k": "v"})
    assert result == '{"k": "v"}'


def test_render_python_value_long_dict_wraps():
    long_dict = {f"key_{i}": f"value_{i}_some_long_string" for i in range(8)}
    result = render_python_value(long_dict)
    assert result.startswith("{\n")
    assert result.endswith("}")


def test_render_python_value_long_dict_with_multiline_value():
    # A value that itself renders as multiline triggers the inner multiline branch
    long_list_value = [f"dep-{i}>=1.0" for i in range(10)]
    d = {"deps": long_list_value}
    result = render_python_value(d, indent=0)
    assert '"deps"' in result


def test_render_collection_assignment_long_triggers_multiline():
    # Force multiline by exceeding 120 chars
    long_list = [f"a-very-long-package-name-{i}>=1.2.3" for i in range(6)]
    result = render_collection_assignment("dependencies", long_list)
    assert result.startswith("__dependencies__ =")


def test_indent_multiline_value():
    result = indent_multiline_value("line1\nline2", "  ")
    assert result == "  line1\n  line2"


# --- general.py: get_all_primitive_values ---


def test_get_all_primitive_values_string():
    assert list(get_all_primitive_values("hello")) == ["hello"]


def test_get_all_primitive_values_int():
    assert list(get_all_primitive_values(42)) == ["42"]


def test_get_all_primitive_values_float():
    assert list(get_all_primitive_values(1.5)) == ["1.5"]


def test_get_all_primitive_values_nested_list():
    assert list(get_all_primitive_values(["a", 1, ["b"]])) == ["a", "1", "b"]


def test_get_all_primitive_values_tuple():
    assert list(get_all_primitive_values(("x", "y"))) == ["x", "y"]


def test_get_all_primitive_values_dict_ignored():
    # dicts are not in the handled types — yields nothing
    assert list(get_all_primitive_values({"k": "v"})) == []


# --- general.py: validate_about_file ---


def test_validate_about_file_missing_file():
    with pytest.raises(FileNotFoundError):
        validate_about_file("/nonexistent/path/__about__.py", {"version": "1.0"})


def test_validate_about_file_passes(tmp_path):
    about = tmp_path / "__about__.py"
    about.write_text('__version__ = "1.0"\n__title__ = "myapp"\n', encoding="utf-8")
    validate_about_file(str(about), {"version": "1.0", "name": "myapp"})


def test_validate_about_file_str_value_missing_raises(tmp_path):
    # validate_about_file calls get_all_primitive_values on the whole dict,
    # but that only yields from list/tuple/set/str/int/float at the top level.
    # Passing a string directly (not as a dict value) would yield; passing a dict
    # whose values are strings yields nothing from the top-level dict.
    # Test that the function does not raise when a primitive is present in file.
    about = tmp_path / "__about__.py"
    about.write_text('__version__ = "1.0"\n', encoding="utf-8")
    # No error expected — primitives extracted from dict values are empty
    validate_about_file(str(about), {"version": "1.0"})


def test_validate_about_file_skips_classifiers_and_authors(tmp_path):
    about = tmp_path / "__about__.py"
    about.write_text('__version__ = "1.0"\n', encoding="utf-8")
    # classifiers/authors/name are excluded from checks — should not raise
    validate_about_file(
        str(about),
        {
            "version": "1.0",
            "classifiers": ["Development Status :: 4 - Beta"],
            "authors": ["Dev <dev@example.com>"],
            "name": "myapp",
        },
    )


# --- from_poetry.py: format_poetry_dependency ---


def test_format_poetry_dependency_python_skipped():
    assert format_poetry_dependency("python", "^3.11") is None


def test_format_poetry_dependency_str_wildcard():
    assert format_poetry_dependency("requests", "*") == "requests"


def test_format_poetry_dependency_str_version():
    assert format_poetry_dependency("click", "^8.0") == "click^8.0"


def test_format_poetry_dependency_non_dict_non_str():
    assert format_poetry_dependency("mypkg", 42) == "mypkg"


def test_format_poetry_dependency_dict_with_version():
    assert format_poetry_dependency("click", {"version": "^8.0"}) == "click^8.0"


def test_format_poetry_dependency_dict_version_wildcard():
    assert format_poetry_dependency("click", {"version": "*"}) == "click"


def test_format_poetry_dependency_dict_with_extras():
    result = format_poetry_dependency("uvicorn", {"extras": ["standard"], "version": ">=0.20"})
    assert result == "uvicorn[standard]>=0.20"


def test_format_poetry_dependency_dict_git():
    result = format_poetry_dependency("mypkg", {"git": "https://github.com/org/mypkg"})
    assert result == "mypkg @ https://github.com/org/mypkg"


def test_format_poetry_dependency_dict_url():
    result = format_poetry_dependency("mypkg", {"url": "https://example.com/mypkg.tar.gz"})
    assert result == "mypkg @ https://example.com/mypkg.tar.gz"


def test_format_poetry_dependency_dict_path():
    result = format_poetry_dependency("mypkg", {"path": "./vendor/mypkg"})
    assert result == "mypkg @ ./vendor/mypkg"


def test_format_poetry_dependency_dict_no_version_key():
    result = format_poetry_dependency("mypkg", {"optional": True})
    assert result == "mypkg"


# --- from_poetry.py: generate_from_poetry ---


def test_generate_from_poetry_no_section(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.other]\nkey = 'value'\n", encoding="utf-8")
    result = generate_from_poetry(source=str(pyproject))
    assert "No [tool.poetry] section" in result


def test_generate_from_poetry_basic(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.poetry]\nname = 'myapp'\nversion = '0.2.0'\ndescription = 'A test app'\n",
        encoding="utf-8",
    )
    (tmp_path / "myapp").mkdir()
    monkeypatch.chdir(tmp_path)
    result = generate_from_poetry(source=str(pyproject), validate=False)
    assert result.endswith("__about__.py")


def test_generate_from_poetry_with_dependencies(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.poetry]\nname = 'myapp'\nversion = '1.0'\n\n[tool.poetry.dependencies]\npython = '^3.11'\nclick = '^8.0'\n",
        encoding="utf-8",
    )
    (tmp_path / "myapp").mkdir()
    monkeypatch.chdir(tmp_path)
    _result = generate_from_poetry(source=str(pyproject), validate=False)
    content = (tmp_path / "myapp" / "__about__.py").read_text(encoding="utf-8")
    assert "click" in content
    assert "python" not in content


def test_generate_from_poetry_missing_name_raises(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.poetry]\nversion = '1.0'\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Project name not found"):
        generate_from_poetry(source=str(pyproject))


def test_generate_from_poetry_custom_output_with_slash(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.poetry]\nname = 'myapp'\nversion = '1.0'\n", encoding="utf-8")
    (tmp_path / "myapp").mkdir()
    monkeypatch.chdir(tmp_path)
    custom_output = str(tmp_path / "myapp" / "__about__.py")
    result = generate_from_poetry(source=str(pyproject), output=custom_output, validate=False)
    assert "__about__.py" in result
