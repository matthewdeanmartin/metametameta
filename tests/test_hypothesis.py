from __future__ import annotations

import os
import shutil
from pathlib import Path

import hypothesis.strategies as st
import toml
from hypothesis import HealthCheck, given, settings

from metametameta import (
    generate_from_pep621,
    generate_from_poetry,
    generate_from_setup_cfg,
    generate_from_setup_py,
    generate_from_conda_meta,
    generate_from_requirements_txt,
)

# --- Strategies ---

# Project names: alphanumeric, underscores, hyphens
project_names = st.from_regex(r"^[a-zA-Z0-9][a-zA-Z0-9_\-]*$", fullmatch=True)

# Versions: simple semver-ish
versions = st.from_regex(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", fullmatch=True)

# Descriptions: keep these TOML-safe so Hypothesis exercises our parser rather than
# third-party serializer bugs in the `toml` package.
toml_safe_ascii = st.characters(min_codepoint=32, max_codepoint=126, exclude_characters='"\\')

descriptions = st.text(
    alphabet=toml_safe_ascii,
    min_size=1,
    max_size=100
)

# Authors: list of dicts for PEP 621
authors_pep621 = st.lists(
    st.fixed_dictionaries({
        "name": st.text(
            alphabet=toml_safe_ascii,
            min_size=1,
            max_size=50
        ),
        "email": st.from_regex(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", fullmatch=True)
    }),
    min_size=0,
    max_size=3
)

# Dependencies: list of strings
dependencies = st.lists(
    st.from_regex(r"^[a-zA-Z0-9_\-]+([><=]+\d+\.\d+\.\d+)?$", fullmatch=True),
    min_size=0,
    max_size=5
)

@st.composite
def pep621_metadata(draw):
    name = draw(project_names)
    version = draw(versions)
    description = draw(descriptions)
    # We'll stick to a subset of fields for now
    data = {
        "name": name,
        "version": version,
        "description": description,
    }
    if draw(st.booleans()):
        data["dependencies"] = draw(dependencies)
    return data

@st.composite
def poetry_metadata(draw):
    name = draw(project_names)
    version = draw(versions)
    description = draw(descriptions)
    data = {
        "name": name,
        "version": version,
        "description": description,
    }
    return data

# --- Helper ---

def setup_test_dir(tmp_path, project_name):
    # Some generators expect the project directory to exist
    (tmp_path / project_name).mkdir(parents=True, exist_ok=True)
    # Normalize project name as the code might replace - with _
    (tmp_path / project_name.replace("-", "_")).mkdir(parents=True, exist_ok=True)

# --- Tests ---

@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(metadata=pep621_metadata())
def test_hypothesis_pep621(tmp_path, metadata):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        project_name = metadata["name"]
        setup_test_dir(tmp_path, project_name)

        pyproject_path = tmp_path / "pyproject.toml"
        with open(pyproject_path, "w", encoding="utf-8") as f:
            toml.dump({"project": metadata}, f)

        # Execution
        result_path = generate_from_pep621(source=str(pyproject_path), validate=True)

        assert Path(result_path).exists()
        assert "__about__.py" in result_path
    finally:
        os.chdir(original_cwd)
        # Clean up tmp_path because hypothesis runs many times
        shutil.rmtree(tmp_path, ignore_errors=True)
        os.makedirs(tmp_path, exist_ok=True)

@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(metadata=poetry_metadata())
def test_hypothesis_poetry(tmp_path, metadata):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        project_name = metadata["name"]
        setup_test_dir(tmp_path, project_name)

        pyproject_path = tmp_path / "pyproject.toml"
        with open(pyproject_path, "w", encoding="utf-8") as f:
            toml.dump({"tool": {"poetry": metadata}}, f)

        # Execution
        result_path = generate_from_poetry(source=str(pyproject_path), validate=True)

        # Poetry might generate multiple files if there are multiple packages,
        # but our strategy generates one.
        for path in result_path.split(", "):
            assert Path(path).exists()
            assert "__about__.py" in path
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(tmp_path, ignore_errors=True)
        os.makedirs(tmp_path, exist_ok=True)

@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(name=project_names, version=versions, description=descriptions)
def test_hypothesis_setup_cfg(tmp_path, name, version, description):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        setup_test_dir(tmp_path, name)

        cfg_path = tmp_path / "setup.cfg"
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write("[metadata]\n")
            f.write(f"name = {name}\n")
            f.write(f"version = {version}\n")
            f.write(f"description = {description}\n")

        # Execution
        result_path = generate_from_setup_cfg(source=str(cfg_path), validate=True)

        assert Path(result_path).exists()
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(tmp_path, ignore_errors=True)
        os.makedirs(tmp_path, exist_ok=True)

@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(name=project_names, version=versions, description=descriptions)
def test_hypothesis_setup_py(tmp_path, name, version, description):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        setup_test_dir(tmp_path, name)

        py_path = tmp_path / "setup.py"
        with open(py_path, "w", encoding="utf-8") as f:
            f.write("from setuptools import setup\n")
            f.write("setup(\n")
            f.write(f"    name={repr(name)},\n")
            f.write(f"    version={repr(version)},\n")
            f.write(f"    description={repr(description)},\n")
            f.write(")\n")

        # Execution
        result_path = generate_from_setup_py(source=str(py_path), validate=True)

        assert Path(result_path).exists()
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(tmp_path, ignore_errors=True)
        os.makedirs(tmp_path, exist_ok=True)

@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(name=project_names, version=versions, description=descriptions)
def test_hypothesis_conda_meta(tmp_path, name, version, description):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        setup_test_dir(tmp_path, name)

        meta_path = tmp_path / "meta.yaml"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("package:\n")
            f.write(f"  name: {name}\n")
            f.write(f"  version: {version}\n")
            f.write("about:\n")
            f.write(f"  summary: {description}\n")

        # Execution
        result_path = generate_from_conda_meta(source=str(meta_path), validate=True)

        assert Path(result_path).exists()
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(tmp_path, ignore_errors=True)
        os.makedirs(tmp_path, exist_ok=True)

@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(name=project_names, deps=dependencies)
def test_hypothesis_requirements_txt(tmp_path, name, deps):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        setup_test_dir(tmp_path, name)

        req_path = tmp_path / "requirements.txt"
        with open(req_path, "w", encoding="utf-8") as f:
            for dep in deps:
                f.write(f"{dep}\n")

        # Execution
        result_path = generate_from_requirements_txt(name=name, source=str(req_path), validate=True)

        assert Path(result_path).exists()
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(tmp_path, ignore_errors=True)
        os.makedirs(tmp_path, exist_ok=True)
