# jiggle-version bug report: fixture/example versions block real project bump

## Summary

`jiggle-version` fails to bump this repository because it treats example and test fixture version strings as authoritative project versions.

## Reproduction

From the repository root:

```bash
uvx --from jiggle-version jiggle_version bump --increment patch --scheme pep440 --autogit off
```

## Actual result

The command aborts with a version conflict similar to:

```text
Version conflict prevents bump. versions=['0.1', '0.1.6', '1.27.0']
❌ Version conflict detected! Cannot bump. Found: 0.1, 0.1.6, 1.27.0
```

## Expected result

The tool should either:

- prioritize actual project metadata sources such as `pyproject.toml` and the package `__about__.py`, or
- offer an easy way to ignore fixture/example/test directories without failing the default bump flow for common repository layouts.

## Repository context

This repository contains intentionally versioned fixtures and examples under paths such as:

- `tests/`
- `test_project/`
- `example/`
- `example.toml`
- `example2.toml`

Those are not release sources for the published package.

## Impact

This blocks automated patch version bumps for release preparation, even though the real package version sources agree.
