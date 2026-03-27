# Contributing

Contributions are welcome.

## Setup

Install the project and development tools with `uv`:

```bash
uv sync --all-extras
```

## Common commands

- Run the full test suite:

  ```bash
  just test
  # or
  make test
  ```

- Run the quieter LLM-oriented test target:

  ```bash
  just test-llm
  # or
  make test-llm
  ```

- Run the tailored pre-release checks:

  ```bash
  just prerelease
  # or
  make prerelease
  ```

## Docs

Docs are built with MkDocs and published through Read the Docs.

```bash
uv run mkdocs build --strict --clean
uv run mkdocs serve
```

## Metadata and release-related changes

If you touch packaging metadata, keep `pyproject.toml`, `metametameta/__about__.py`, README examples, and docs in sync.

```bash
uv run metametameta sync-check
uv run python scripts/prerelease_version_check.py
```

For release work, also follow [`PRERELEASE.md`](PRERELEASE.md).
