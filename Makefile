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

clean-pyc:
	@echo "Removing compiled files"


clean-test:
	@echo "Removing coverage data"
	@rm -f .coverage || true
	@rm -f .coverage.* || true

clean: clean-pyc clean-test

# tests can't be expected to pass if dependencies aren't installed.
# tests are often slow and linting is fast, so run tests on linted code.
test: clean uv.lock install_plugins
	@echo "Running unit tests"
	# $(VENV) pytest --doctest-modules metametameta
	# $(VENV) python -m unittest discover
	$(VENV) pytest tests -vv -n 2 --cov=metametameta --cov-report=html --cov-fail-under 65 --cov-branch --cov-report=xml --junitxml=junit.xml -o junit_family=legacy --timeout=5 --session-timeout=600
	$(VENV) bash ./scripts/basic_checks.sh
#	$(VENV) bash basic_test_with_logging.sh


.build_history:
	@mkdir -p .build_history

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

.PHONY: publish
publish: test
	rm -rf dist && hatch build

.PHONY: mypy
mypy:
	$(VENV) echo $$PYTHONPATH
	$(VENV) mypy metametameta --ignore-missing-imports --check-untyped-defs


check_docs:
	$(VENV) interrogate metametameta --verbose  --fail-under 70
	$(VENV) pydoctest --config .pydoctest.json | grep -v "__init__" | grep -v "__main__" | grep -v "Unable to parse"

make_docs:
	pdoc metametameta --html -o docs --force

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

check_self:
	# Can it verify itself?
	$(VENV) ./scripts/dog_food.sh

#audit:
#	# $(VENV) python -m metametameta audit
#	$(VENV) tool_audit single metametameta --version=">=2.0.0"
