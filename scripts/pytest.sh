#!/bin/bash
set -euo pipefail
if [[ "${CI:-}" == "" ]]; then
  . ./global_variables.sh
fi

uv run pytest tests -vv \
--cov="$PACKAGE_DIR" --cov-branch \
--cov-report=xml --cov-report=html \
--cov-fail-under=35 \
--junitxml=junit.xml -o junit_family=legacy \
--timeout=5 --session-timeout=600
