#!/bin/bash
set -euo pipefail

echo
echo "Formatting markdown files with mdformat"
echo
uv run mdformat .

echo
echo "Are the links okay?"
echo
uv run linkcheckMarkdown .
