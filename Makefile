.EXPORT_ALL_VARIABLES:
# Get changed files

FILES := $(wildcard **/*.py)

# if you wrap everything in uv run, it runs slower.
ifeq ($(origin VIRTUAL_ENV),undefined)
    VENV := uv run
else
    VENV :=
endif

uv.lock: pyproject.toml
	@echo "Installing dependencies"
	@uv sync --all-extras

.PHONY: metadata-sync-check
metadata-sync-check:
	@echo "Checking generated metadata is in sync"
	$(VENV) metametameta sync-check

.PHONY: version-check
version-check:
	@echo "Checking version sources and PyPI ordering"
	$(VENV) metametameta sync-check
	$(VENV) python scripts/prerelease_version_check.py

.PHONY: bump-patch
bump-patch:
	@echo "Bumping patch version and refreshing generated metadata"
	$(VENV) python scripts/bump_patch_version.py
	$(VENV) metametameta pep621 --source pyproject.toml --output metametameta/__about__.py
	$(VENV) metametameta sync-check
	$(VENV) python scripts/prerelease_version_check.py

.PHONY: publish-gha
publish-gha:
	@echo "Dispatching GitHub Actions publish workflow"
	gh workflow run publish_to_pypi.yml --ref main

.PHONY: dev-status-check
dev-status-check:
	@echo "Verifying Development Status classifier"
	uvx --from troml-dev-status troml-dev-status verify .

.PHONY: docstrings-check
docstrings-check:
	@echo "Checking documented signatures for drift"
	uvx --from pydoclint pydoclint --quiet --config=pyproject.toml metametameta

.PHONY: docs-build
docs-build:
	@echo "Building MkDocs site"
	$(VENV) mkdocs build --strict --clean

.PHONY: docs-serve
docs-serve:
	@echo "Serving MkDocs site"
	$(VENV) mkdocs serve

.PHONY: gha-pin
gha-pin:
	@echo "Pinning GitHub Actions to current SHAs"
	$(VENV) python -c "import os, subprocess, sys; token=os.environ.get('GITHUB_TOKEN') or subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout.strip(); assert token, 'Set GITHUB_TOKEN or log in with gh auth login'; env=dict(os.environ, GITHUB_TOKEN=token); raise SystemExit(subprocess.run(['gha-update'], env=env).returncode)"

.PHONY: gha-validate
gha-validate:
	@echo "Validating GitHub Actions workflows"
	$(VENV) python -c "import pathlib, yaml; [yaml.safe_load(p.read_text(encoding='utf-8')) for p in pathlib.Path('.github/workflows').glob('*.yml')]; print('YAML parse OK')"
	$(VENV) python -c "from pathlib import Path; import yaml; data=yaml.safe_load(Path('.github/workflows/publish_to_pypi.yml').read_text(encoding='utf-8')); build_steps=data['jobs']['build']['steps']; publish_steps=data['jobs']['pypi-publish']['steps']; up=next(s for s in build_steps if s.get('uses','').startswith('actions/upload-artifact@')); down=next(s for s in publish_steps if s.get('uses','').startswith('actions/download-artifact@')); assert up['with']['name']==down['with']['name']=='packages'; assert up['with']['path']==down['with']['path']=='dist/'; print('Artifact handoff OK:', up['uses'], '->', down['uses'])"
	uvx zizmor --no-progress --no-exit-codes .

.PHONY: gha-upgrade
gha-upgrade: gha-pin gha-validate
	@echo "GitHub Actions upgrade complete"

clean-pyc:
	@echo "Removing compiled files"


clean-test:
	@echo "Removing coverage data"
	@rm -f .coverage || true
	@rm -f .coverage.* || true

clean: clean-pyc clean-test

# tests can't be expected to pass if dependencies aren't installed.
# tests are often slow and linting is fast, so run tests on linted code.
test: clean uv.lock
	@echo "Running unit tests"
	# $(VENV) pytest --doctest-modules metametameta
	# $(VENV) python -m unittest discover
	$(VENV) pytest tests -vv -n 2 --cov=metametameta --cov-report=html --cov-fail-under 65 --cov-branch --cov-report=xml --junitxml=junit.xml -o junit_family=legacy --timeout=5 --session-timeout=600
	$(VENV) bash ./scripts/basic_checks.sh
#	$(VENV) bash basic_test_with_logging.sh

.PHONY: test-llm
test-llm: clean uv.lock
	@echo "Running quiet unit tests"
	$(VENV) pytest tests -q -x --maxfail=1 --disable-warnings --timeout=5 --session-timeout=600

.PHONY: tests-llm
tests-llm: test-llm


isort:
	@echo "Formatting imports"
	$(VENV) isort .

black: isort
	@echo "Formatting code"
	$(VENV) metametameta pep621
	$(VENV) black metametameta # --exclude .venv
	$(VENV) black tests # --exclude .venv
	$(VENV) bash ./scripts/make_source.sh


pre-commit: isort black
	@echo "Pre-commit checks"
	$(VENV) pre-commit run --all-files



bandit:
	@echo "Security checks"
	$(VENV)  bandit metametameta -r --quiet


pylint: isort black
	@echo "Linting with pylint"
	$(VENV) ruff check --fix
	$(VENV) pylint metametameta --fail-under 9.8


# for when using -j (jobs, run in parallel)
.NOTPARALLEL: isort black

check: mypy test pylint bandit pre-commit

#.PHONY: publish_test
#publish_test:
#	rm -rf dist && poetry version minor && poetry build && twine upload -r testpypi dist/*

.PHONY: build-dist
build-dist:
	rm -rf dist && hatch build

.PHONY: publish
publish: prerelease build-dist

.PHONY: mypy
mypy:
	$(VENV) echo $$PYTHONPATH
	$(VENV) mypy metametameta --ignore-missing-imports --check-untyped-defs


check_docs:
	uvx --from pydoclint pydoclint --quiet --config=pyproject.toml metametameta
	$(VENV) interrogate metametameta --verbose  --fail-under 70
	$(VENV) pydoctest --config .pydoctest.json | grep -v "__init__" | grep -v "__main__" | grep -v "Unable to parse"

make_docs:
	$(VENV) mkdocs build --strict --clean

check_md:
	$(VENV) linkcheckMarkdown README.md
	$(VENV) markdownlint README.md --config .markdownlintrc
	$(VENV) mdformat README.md docs/*.md


check_spelling:
	$(VENV) pylint metametameta --enable C0402 --rcfile=.pylintrc_spell
	$(VENV) pylint docs --enable C0402 --rcfile=.pylintrc_spell
	$(VENV) codespell README.md --ignore-words=private_dictionary.txt
	$(VENV) codespell metametameta --ignore-words=private_dictionary.txt
	$(VENV) codespell docs --ignore-words=private_dictionary.txt

check_changelog:
	# pipx install keepachangelog-manager
	$(VENV) changelogmanager validate

check_all_docs: check_docs check_md check_spelling check_changelog

.PHONY: prerelease
prerelease: metadata-sync-check version-check dev-status-check check_all_docs docs-build test
	@echo "Pre-release checks complete"

.PHONY: prerelease-llm
prerelease-llm: metadata-sync-check version-check dev-status-check docstrings-check docs-build test-llm
	@echo "Quiet pre-release checks complete"

check_self:
	# Can it verify itself?
	$(VENV) ./scripts/dog_food.sh

#audit:
#	# $(VENV) python -m metametameta audit
#	$(VENV) tool_audit single metametameta --version=">=2.0.0"
