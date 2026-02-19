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

# Strict gate alert threshold sync check
$PYTHON_BIN ./scripts/sync-strict-gate-alert-thresholds.py --check

# Placeholder marker config validation
$PYTHON_BIN ./scripts/validate-validator-placeholder-markers.py

# Validator error code catalog sync check
$PYTHON_BIN ./scripts/sync-validator-error-codes.py --check --strict-descriptions

# Validator error code catalog schema check
$PYTHON_BIN ./scripts/validate-validator-error-code-catalog.py

# Validator error code metadata overrides check
$PYTHON_BIN ./scripts/validate-validator-error-code-metadata-overrides.py

# Strict gate summary schema check
$PYTHON_BIN ./scripts/validate-strict-gate-summary-schema.py

# Strict gate summary contract changelog check
$PYTHON_BIN ./scripts/validate-summary-contract-changelog.py

# Prometheus rule validation
if [[ -n "${CI:-}" ]]; then
  export PROMTOOL_REQUIRED="${PROMTOOL_REQUIRED:-1}"
fi
./scripts/check-prometheus-rules.sh

# Unit tests
PYTHONPATH=src $PYTHON_BIN -m pytest tests/unit -q
