# Maintenance

This document outlines the periodic maintenance tasks required to keep the project healthy, secure, and up-to-date.

## Daily/Per-Commit Tasks

These tasks run automatically via pre-commit hooks and CI:

- **Pre-commit hooks**: Automatic code quality fixes via `pre-commit ci`
- **CI build**: Runs on every push via `.github/workflows/build.yml`

## Weekly Tasks

Run these tasks regularly to maintain code quality:

```bash
# Update dependencies
just update-deps

# Run full test suite
just test

# Run all quality checks
just check
```

## Monthly Tasks

Perform these tasks monthly to keep dependencies and tools current:

```bash
# Update pre-commit hooks to latest versions
pre-commit autoupdate

# Install/update global tools via pipx
pipx install black isort pylint pyupgrade vulture safety flake8 mypy bandit codespell

# Freeze tool versions for audit trail
cli_tool_audit freeze pipx black isort pylint pyupgrade vulture safety flake8 mypy bandit
```

## Pre-Release Tasks

Before publishing a new version:

1. Update version in `pyproject.toml`
1. Update `CHANGELOG.md` with recent changes
1. Run full test suite:
   ```bash
   just test
   ```
1. Run all checks:
   ```bash
   just check
   ```
1. Build and publish:
   ```bash
   just publish
   ```

## Quarterly Tasks

Review and update project configuration:

- Review `pyproject.toml` dependencies for outdated packages
- Check `.github/workflows/` for needed updates
- Verify Python version support in `pyproject.toml`
- Run `deptry` to check for unused dependencies:
  ```bash
  deptry metametameta -kf metametameta
  ```

## Security Maintenance

- Run security checks:
  ```bash
  just bandit
  ```
- Check for known vulnerabilities in dependencies (when `safety` is configured)
- Review and update `SECURITY.md` if needed

## Documentation Maintenance

- Check documentation:
  ```bash
  just check-docs
  just check-md
  just spell
  ```
- Generate documentation:
  ```bash
  just make-docs
  ```
- Verify all doc links work

## Troubleshooting

If checks fail:

- **Lint errors**: Run `ruff check --fix .` to auto-fix most issues
- **Type errors**: Review `mypy` output and add type annotations as needed
- **Test failures**: Check test output and fix failing tests before releasing
- **Pre-commit failures**: Run `pre-commit run --all-files` locally to see issues

## Available Just Commands

| Command | Description |
|---------|-------------|
| `just test` | Run test suite with coverage |
| `just check` | Run mypy, tests, pylint, bandit, pre-commit |
| `just pre-commit` | Run pre-commit hooks on all files |
| `just mypy` | Run type checking |
| `just bandit` | Run security checks |
| `just pylint` | Run linting with pylint and ruff |
| `just lock` | Sync uv lock file |
| `just update-deps` | Update dependencies and pre-commit |
| `just publish` | Build and publish to PyPI |
| `just check-docs` | Check docstring coverage |
| `just check-md` | Check Markdown formatting |
| `just spell` | Run spell checking |
| `just tool-audit` | Audit installed CLI tools |
| `just clean` | Remove compiled files |
