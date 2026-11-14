#!/bin/bash
set -euo pipefail

echo
echo "Formatting markdown files with mdformat"
echo
uv run --no-build mdformat .

echo
echo "Checking documentation build and internal links"
echo
uv run --no-build mkdocs build --strict --clean
