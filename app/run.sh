#!/bin/sh
set -e
cd "$(dirname "$0")"
[ -x .venv/bin/t2v-app ] || ./setup.sh
exec .venv/bin/t2v-app "$@"
