#!/bin/bash
set -euo pipefail
export PIP_DISABLE_PIP_VERSION_CHECK="1"
export UV_LINK_MODE="copy"
export UV_PROJECT_ENVIRONMENT=".venv"
export UV_CACHE_DIR=".uv"
export PACKAGE_DIR="bitrab"
