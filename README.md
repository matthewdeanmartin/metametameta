# metametameta

Generate dunder metadata file with `__title__`, `__author__`, etc. Also tools to discover these in other packages.

## Installation

```bash
pipx install metametameta
```

## Usage

```bash
metametameta --source pyproject.toml --target mypackage/__metadata__.py
```

## Motivation

There are many modern ways to get metadata about packages, as of
2024, [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html) and it's backports will get you
lots of metadata for yours and other packages.

The newest way is [PEP-621](https://peps.python.org/pep-0621/), see also [packaging.python.org](https://packaging.python.org/en/latest/specifications/pyproject-toml/#pyproject-toml-spec)

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
`setup.py`, `setup.cfg`.

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
