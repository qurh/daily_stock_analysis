#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

# Syntax check
$PYTHON_BIN -m py_compile $(find src tests -name "*.py")

# Style checks
$PYTHON_BIN -m black --check src tests
$PYTHON_BIN -m isort --check-only src tests
$PYTHON_BIN -m flake8 src tests --max-line-length=120

# Promtool installer config validation
./scripts/validate-promtool-installer-config.sh

# Prometheus rule validation
if [[ -n "${CI:-}" ]]; then
  export PROMTOOL_REQUIRED="${PROMTOOL_REQUIRED:-1}"
fi
./scripts/check-prometheus-rules.sh

# Unit tests
PYTHONPATH=src $PYTHON_BIN -m pytest tests/unit -q
