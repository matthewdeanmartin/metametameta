# Agent Notes

- Use `uv`/`uv run` for repo commands; prefer `uv run` for project tools.
- DO NOT use leading underscores for "private" members (functions, methods, classes, variables). Use public names instead.
- Leading underscores ARE allowed for unused variables (e.g., `_`, `_dirs`, `_event`) to satisfy linters.
- Dunder methods (e.g., `__init__`) are encouraged where appropriate.
