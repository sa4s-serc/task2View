#!/bin/sh
# Creates app/.venv and installs the tool with the task2view package from ../code.
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e ../code -e .
echo "Installed. Start the tool with ./run.sh"
