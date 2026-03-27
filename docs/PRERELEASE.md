# Pre-release checklist

Use this before publishing `metametameta` to PyPI.

## 1. Sync code, metadata, README, and docs

- Treat `pyproject.toml` as the canonical package metadata source.

- Regenerate or verify `metametameta/__about__.py` before release work:

  ```bash
  uv run metametameta pep621 --source pyproject.toml --output metametameta/__about__.py
  uv run metametameta sync-check
  ```

- Review `README.md`, `docs/usage.md`, `docs/installation.md`, and `docs/CONTRIBUTING.md` together so examples, supported commands, and packaging guidance agree.

- Confirm the CLI help still matches the docs:

  ```bash
  uv run metametameta --help
  ```

## 2. Make sure the version is safe to publish

- Check that all local version sources agree:

  ```bash
  uv run metametameta sync-check
  ```

- Check that the local version is newer than the latest PyPI release:

  ```bash
  uv run python scripts/prerelease_version_check.py
  ```

- To perform the normal patch release bump and refresh generated metadata:

  ```bash
  make bump-patch
  # or
  just bump-patch
  ```

## 3. Verify the Development Status classifier

This project already ships a `Development Status` classifier, so verify it instead of guessing:

```bash
uvx --from troml-dev-status troml-dev-status validate .
```

## 4. Run doc checks that match this repo

This repo builds docs with MkDocs and Read the Docs, not `pdoc`.

```bash
uv run mkdocs build --strict --clean
uv run interrogate metametameta --verbose --fail-under 70
uv run pydoctest --config .pydoctest.json
uvx --from pydoclint pydoclint --quiet --config=pyproject.toml metametameta
```

`pydoclint` is here to catch wrong docstrings, such as stale parameter or return sections. Missing docstrings are acceptable; incorrect documented signatures are not.

## 5. Run the project checks

Full prerelease run:

```bash
just prerelease
# or
make prerelease
```

Low-noise LLM-friendly run:

```bash
just prerelease-llm
# or
make prerelease-llm
```

For a quieter test-only run:

```bash
just test-llm
# or
make test-llm
```

## 6. Final human review before publish

- `CHANGELOG.md` reflects the release.
- README badges and links still resolve.
- The docs nav includes the release-facing pages you expect.
- The release version is greater than the last PyPI release.
- `metametameta/__about__.py`, `pyproject.toml`, and the published docs all agree on the current state of the project.
