# metametameta

Generate dunder metadata file with `__title__`, `__author__`, etc. Also tools to discover these in other packages.

[![tests](https://github.com/matthewdeanmartin/metametameta/actions/workflows/build.yml/badge.svg)
](https://github.com/matthewdeanmartin/metametameta/actions/workflows/tests.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/matthewdeanmartin/metametameta/main.svg)
](https://results.pre-commit.ci/latest/github/matthewdeanmartin/metametameta/main)
[![Downloads](https://img.shields.io/pypi/dm/metametameta)](https://pypistats.org/packages/metametameta)
[![Python Version](https://img.shields.io/pypi/pyversions/metametameta)
![Release](https://img.shields.io/pypi/v/metametameta)
](https://pypi.org/project/metametameta/)

## Installation

```bash
pipx install metametameta
```

## Usage

Defaults to putting an `__about__.py` file in the module directory, assuming your package name is your main module name.

Make best guess what your metadata source is. Give up if there are two possibilities.
```bash
metametameta auto 
```

Run on CI server to see if your about file is out of sync
```bash
metametameta sync-check
```

```bash
metametameta poetry # or setup_cfg or pep621 or poetry or importlib or the experimental setup_py
```

Or set everything explicitly:

```bash
metametameta poetry --name "something" --source some.toml --output OUTPUT "mod/meta/__meta__.py"
```

Subcommand per source.

```text
Usage: metametameta [-h] [--version] [--verbose] [--quiet] {setup_cfg,pep621,poetry,importlib,setup_py,auto,sync-check} ...

metametameta: Generate __about__.py from various sources.

Positional Arguments:
  {setup_cfg,pep621,poetry,importlib,setup_py,auto,sync-check}
                        sub-command help
    setup_cfg           Generate from setup.cfg
    pep621              Generate from PEP 621 pyproject.toml
    poetry              Generate from poetry pyproject.toml
    importlib           Generate from installed package metadata
    setup_py            Generate from setup.py using AST (experimental)
    auto                Automatically detect the source and generate the metadata file.
    sync-check          Check if __about__.py is in sync with the metadata source

Options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --verbose             verbose output
  --quiet               minimal output
```

Subcommand help (they all have the same switches)

```text
usage: metametameta poetry [-h] [--name NAME] [--source SOURCE] [--output OUTPUT]

options:
  -h, --help       show this help message and exit
  --name NAME      Name of the project (from file if omitted)
  --source SOURCE  Path to pyproject.toml
  --output OUTPUT  Output file
```

## Programmatic interface.

```python
import metametameta as mmm

mmm.generate_from_pep621()
```

## Motivation

There are many modern ways to get metadata about packages, as of
2024, [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html) and it's backports will get you
lots of metadata for yours and other packages.

The newest way is [PEP-621](https://peps.python.org/pep-0621/), see
also [packaging.python.org](https://packaging.python.org/en/latest/specifications/pyproject-toml/#pyproject-toml-spec)

The oldest way to provide metadata was to use dunder variables in your package, e.g. `__author__`, `__version__`, etc.

The method was never strongly standardized, neither officially nor informally. [Here is one early proponent of this
sort of metadata](https://web.archive.org/web/20111010053227/http://jaynes.colorado.edu/PythonGuidelines.html#module_formatting).

- Metadata fields can appear in any or no python file in a project.
- Sometimes they are at the top of a single file python module, common locations for metadata:
    - `__init__.py`
    - `__meta__.py`
    - `__about__.py`
- Some metadata elements could reasonably be in every single file.
- There are no particular standards for the type of `__author__`. It could be a string, space delimited string, list
  or tuple. That is true for the other metadata elements as well.
- Sometimes the metadata values are code, e.g. `__version__` could be a string or some tuple or data class
  representing a version.

## Workflow

On each build, regenerate the `__about__.py`. Pick one source of your canonical metadata, e.g. `pyproject.toml`,
`setup.py` (experimental), `setup.cfg`.

## Using metadata

If you have a lot of packages and you are doing analytics or something with them, you could compile all the metadata
as declared in the source code. It could be different from the metadata that shows on the PyPI page. If you are
searching for contact info for a package maintainer, this might be useful.

Another marginal use case is in error logging. Error loggers gather up info from just about anywhere, anything can
be a clue including metadata of dependencies. So this is one more source of that. See `bug_trail` for a proof of
concept for this usage.

Another marginal use case is that is a folksonomy, a taxonomy created by the people. The official metadata is
governed by the Python Packaging Authority and the Python Software Foundation. If, say, you wanted to add a metadata
item for `__mailing_address__` you could easily do it with source code metadata.

## Project Health & Info

| Metric            | Health                                                                                                                                                                                                              | Metric          | Info                                                                                                                                                                                                              |
|:------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Tests             | [![Tests](https://github.com/matthewdeanmartin/metametameta/actions/workflows/build.yml/badge.svg)](https://github.com/matthewdeanmartin/metametameta/actions/workflows/build.yml)                                  | License         | [![License](https://img.shields.io/github/license/matthewdeanmartin/metametameta)](https://github.com/matthewdeanmartin/metametameta/blob/main/LICENSE.md)                                                        |
| Coverage          | [![Codecov](https://codecov.io/gh/matthewdeanmartin/metametameta/branch/main/graph/badge.svg)](https://codecov.io/gh/matthewdeanmartin/metametameta)                                                                | PyPI            | [![PyPI](https://img.shields.io/pypi/v/metametameta)](https://pypi.org/project/metametameta/)                                                                                                                     |
| Lint / Pre-commit | [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/matthewdeanmartin/metametameta/main.svg)](https://results.pre-commit.ci/latest/github/matthewdeanmartin/metametameta/main)                      | Python Versions | [![Python Version](https://img.shields.io/pypi/pyversions/metametameta)](https://pypi.org/project/metametameta/)                                                                                                  |
| Quality Gate      | [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=matthewdeanmartin_metametameta\&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=matthewdeanmartin_metametameta)    | Docs            | [![Docs](https://readthedocs.org/projects/metametameta/badge/?version=latest)](https://metametameta.readthedocs.io/en/latest/)                                                                                    |
| CI Build          | [![Build](https://github.com/matthewdeanmartin/metametameta/actions/workflows/build.yml/badge.svg)](https://github.com/matthewdeanmartin/metametameta/actions/workflows/build.yml)                                  | Downloads       | [![Downloads](https://static.pepy.tech/personalized-badge/metametameta?period=total\&units=international_system\&left_color=grey\&right_color=blue\&left_text=Downloads)](https://pepy.tech/project/metametameta) |
| Maintainability   | [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=matthewdeanmartin_metametameta\&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=matthewdeanmartin_metametameta) | Last Commit     | ![Last Commit](https://img.shields.io/github/last-commit/matthewdeanmartin/metametameta)                                                                                                                          |

| Category          | Health                                                                                                                                              
|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| **Open Issues**   | ![GitHub issues](https://img.shields.io/github/issues/matthewdeanmartin/metametameta)                                                               |
| **Stars**         | ![GitHub Repo stars](https://img.shields.io/github/stars/matthewdeanmartin/metametameta?style=social)                                               |
