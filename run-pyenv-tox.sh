#!/usr/bin/env bash
# Run tox for each pyenv interpreter on the system.
# This script runs environments individually so that
# code execution platforms with per-command time limits
# can execute each tox environment separately.
set -euo pipefail

# Determine the root of pyenv to locate python binaries
PYENV_ROOT="${PYENV_ROOT:-$(pyenv root)}"
GLOBAL_PYENV="$(pyenv global)"
# Locate tox binary once so pyenv shims do not interfere
# Use the pyenv shim for tox so we can select the binary via PYENV_VERSION
TOX_BIN="tox"
# Collect available tox environments to skip missing ones
AVAILABLE_ENVS="$("$TOX_BIN" -l | tr -d '\r')"

for pyv in $(pyenv versions --bare); do
  echo "=== Running tox for ${pyv} ==="
  # Derive tox environment name from the interpreter
  envname="$("$PYENV_ROOT/versions/$pyv/bin/python" - <<'PY'
import sys, platform
impl = platform.python_implementation().lower()
name = f"py{sys.version_info[0]}{sys.version_info[1]}" if impl == "cpython" else f"{impl}{sys.version_info[0]}{sys.version_info[1]}"
print(name)
PY
)"
  if echo "$AVAILABLE_ENVS" | grep -Fxq "$envname"; then
    # Run only that environment using the selected interpreter
    PYENV_VERSION="$pyv:$GLOBAL_PYENV" "$TOX_BIN" -e "$envname"
  else
    echo "Skipping $envname (not defined in tox.ini)"
  fi
done
