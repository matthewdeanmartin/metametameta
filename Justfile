# Get the project name from the parent directory
project := `basename $(pwd)`
test_folder := "tests"

# Set up virtual environment handling
venv := if env_var_or_default("VIRTUAL_ENV", "") == "" { "uv run" } else { "" }

# Default recipe
default:
    @just --list

# Install dependencies
poetry-install:
    @echo "Installing dependencies"
    uv sync --all-extras

metadata-sync-check:
    @echo "Checking generated metadata is in sync"
    {{venv}} metametameta sync-check

version-check:
    @echo "Checking version sources and PyPI ordering"
    {{venv}} metametameta sync-check
    {{venv}} python scripts/prerelease_version_check.py

bump-patch:
    @echo "Bumping patch version and refreshing generated metadata"
    {{venv}} python scripts/bump_patch_version.py
    {{venv}} metametameta pep621 --source pyproject.toml --output metametameta/__about__.py
    {{venv}} metametameta sync-check
    {{venv}} python scripts/prerelease_version_check.py

publish-gha:
    @echo "Dispatching GitHub Actions publish workflow"
    gh workflow run publish_to_pypi.yml --ref main

dev-status-check:
    @echo "Verifying Development Status classifier"
    uvx --from troml-dev-status troml-dev-status verify .

docstrings-check:
    @echo "Checking documented signatures for drift"
    uvx --from pydoclint pydoclint --quiet --config=pyproject.toml {{project}}

docs-build:
    @echo "Building MkDocs site"
    {{venv}} mkdocs build --strict --clean

docs-serve:
    @echo "Serving MkDocs site"
    {{venv}} mkdocs serve

update-deps:
    @echo "Updating dependencies"
    uv sync --all-extras
    pre-commit autoupdate
    pre-commit install || true
    @echo "Consider running  pipx upgrade-all"

gha-pin:
    @echo "Pinning GitHub Actions to current SHAs"
    {{venv}} python -c "import os, subprocess, sys; token=os.environ.get('GITHUB_TOKEN') or subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout.strip(); assert token, 'Set GITHUB_TOKEN or log in with gh auth login'; env=dict(os.environ, GITHUB_TOKEN=token); raise SystemExit(subprocess.run(['gha-update'], env=env).returncode)"

gha-validate:
    @echo "Validating GitHub Actions workflows"
    {{venv}} python -c "import pathlib, yaml; [yaml.safe_load(p.read_text(encoding='utf-8')) for p in pathlib.Path('.github/workflows').glob('*.yml')]; print('YAML parse OK')"
    {{venv}} python -c "from pathlib import Path; import yaml; data=yaml.safe_load(Path('.github/workflows/publish_to_pypi.yml').read_text(encoding='utf-8')); build_steps=data['jobs']['build']['steps']; publish_steps=data['jobs']['pypi-publish']['steps']; up=next(s for s in build_steps if s.get('uses','').startswith('actions/upload-artifact@')); down=next(s for s in publish_steps if s.get('uses','').startswith('actions/download-artifact@')); assert up['with']['name']==down['with']['name']=='packages'; assert up['with']['path']==down['with']['path']=='dist/'; print('Artifact handoff OK:', up['uses'], '->', down['uses'])"
    uvx zizmor --no-progress --no-exit-codes .

gha-upgrade: gha-pin gha-validate
    @echo "GitHub Actions upgrade complete"

clean:
    @echo "Removing compiled files"
    pyclean .

# Run tests
test: clean poetry-install
    #!/usr/bin/env python
    import toml
    import os
    import subprocess

    # Load the minimum test coverage from pyproject.toml
    config = toml.load('pyproject.toml')
    minimum_coverage = config['tool']['strict-build-script']['minimum_test_coverage']

    # Set the environment variable for minimum coverage
    os.environ['minimum_coverage'] = str(minimum_coverage)

    # Define the command to run the tests
    command = f"{{venv}} py.test {{test_folder}} -vv --cov={{project}} --cov-report=html --cov-fail-under {minimum_coverage}"

    # Run the command
    subprocess.run(command, shell=True, check=True)

test-llm: clean poetry-install
    {{venv}} pytest {{test_folder}} -q -x --maxfail=1 --disable-warnings --timeout=5 --session-timeout=600

tests-llm: test-llm


lock:
    uv sync --all-extras

# Format imports
isort:
    @echo "Formatting imports"
    {{venv}} isort .

# Format code
black: isort
    @echo "Formatting code"
    {{venv}} metametameta poetry
    {{venv}} black {{project}} --exclude .venv
    {{venv}} black {{test_folder}} --exclude .venv
    {{venv}} black scripts --exclude .venv

# Run pre-commit checks
pre-commit: isort black
    @echo "Running pre-commit checks"
    {{venv}} pre-commit run --all-files || { echo "First attempt failed, retrying..."; {{venv}} pre-commit run --all-files; }


# Run security checks
bandit:
    @echo "Security checks"
    {{venv}} bandit {{project}} -c pyproject.toml -r

# Run safety check
safety:
    @echo "Running safety on hold..."
#    # pipx inject poetry poetry-plugin-export
#    poetry export -f requirements.txt --output requirements.txt --without-hashes
#    {{venv}} safety check -r requirements.txt
#    rm requirements.txt

# Run pylint
pylint: isort black
    @echo "Linting with pylint"
    {{venv}} pylint {{project}} --rcfile=.pylintrc --fail-under 10 --ignore-paths=test_TODO
    # {{venv}} pylint scripts --rcfile=.pylintrc_scripts --fail-under 8.5 --ignore-paths=test_TODO
    {{venv}} pylint {{test_folder}} --rcfile=.pylintrc_tests --fail-under 10 --ignore-paths=test_TODO
    {{venv}} ruff check . --fix --exclude=test_legacy,dead_code

# Run all checks
check: mypy test pylint bandit pre-commit tool-audit

check-deps: lock safety
    echo "Checking dependencies"

# Run mypy
mypy:
    {{venv}} mypy {{project}} --ignore-missing-imports --check-untyped-defs --strict

# Build Docker image
docker:
    docker build -t {{project}} -f Dockerfile .

# Check documentation
check-docs:
    uvx --from pydoclint pydoclint --quiet --config=pyproject.toml {{project}}
    {{venv}} interrogate {{project}} --verbose
    {{venv}} pydoctest --config .pydoctest.json | grep -v "__init__" | grep -v "__main__" | grep -v "Unable to parse"

# Generate documentation
make-docs:
    {{venv}} mkdocs build --strict --clean

# Check Markdown files
check-md:
    {{venv}} mdformat README.md docs/*.md
    {{venv}} markdownlint README.md --config .markdownlintrc

# Check spelling
spell:
    {{venv}} pylint {{project}} --enable C0401,C0402,C0403 --rcfile=.pylintrc_spell
    {{venv}} codespell README.md --ignore-words=spelling_dictionary.dic
    {{venv}} codespell {{project}} --ignore-words=spelling_dictionary.dic

# Check changelog
check-changelog:
    {{venv}} changelogmanager validate

# Run all checks
check-all: check-docs check-md spell check-changelog

prerelease: metadata-sync-check version-check dev-status-check check-all docs-build test
    @echo "Pre-release checks complete"

prerelease-llm: metadata-sync-check version-check dev-status-check docstrings-check docs-build test-llm
    @echo "Quiet pre-release checks complete"


mr: lock safety spell
    @echo "Periodic burdensome checks"


upgrade-all: lock
    pre-commit autoupdate
    pre-commit install || true
    pre-commit run --all-files
    pipx upgrade-all

package-check:
    @echo "Check if pyproject.toml is as good as it can be"
    deptry {{project}} -kf {{project}}


pipx-installs:
    pipx install black
    pipx install isort
    pipx install pylint
    pipx inject pylint pyenchant
    pipx install pyupgrade
    pipx install vulture
    pipx install safety
    pipx install flake8
    pipx inject flake8 dlint mccabe pyflakes pep8-naming flake8-bugbear
    pipx install mypy
    pipx install bandit
    pipx install codespell

tool-audit-freeze:
    cli_tool_audit freeze pipx black isort pylint pyuprade vulture safety flake8 mypy bandit

tool-audit:
    cli_tool_audit audit

build-dist:
    rm -rf dist && hatch build

publish: prerelease build-dist
