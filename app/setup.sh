#!/bin/sh
# Creates app/.venv with Python 3.11 or newer and installs the tool with the task2view package from ../code.
set -e
cd "$(dirname "$0")"
PYTHON=""
for p in python3.13 python3.12 python3.11 python3; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
    PYTHON="$p"; break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "Python 3.11 or newer is needed (found: $(python3 --version 2>&1)). See README.md, Requirements."; exit 1
fi
"$PYTHON" -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e ../code -e . 2>&1 | grep -v -i "warn\|!!\|\*\*\*\|^ *$" || true
echo "Installed in app/.venv with $("$PYTHON" --version). Next: ./check.sh, then ./run.sh"
