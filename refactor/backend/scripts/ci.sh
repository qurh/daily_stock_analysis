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

# Validator error code metadata lint config check
$PYTHON_BIN ./scripts/validate-validator-error-code-metadata-lint.py

# Validator error code metadata overrides check
$PYTHON_BIN ./scripts/validate-validator-error-code-metadata-overrides.py

# Profile suggestion actions schema check
$PYTHON_BIN ./scripts/validate-profile-suggestion-actions-schema.py

# Strict gate summary schema check
$PYTHON_BIN ./scripts/validate-strict-gate-summary-schema.py

# Strict gate summary contract changelog check
$PYTHON_BIN ./scripts/validate-summary-contract-changelog.py

# High-frequency validator error context schema check
$PYTHON_BIN ./scripts/validate-validator-error-context-high-frequency-schema.py

# Notification retry alert threshold sync check
$PYTHON_BIN ./scripts/sync-notification-retry-alert-thresholds.py --check

# Notification retry alert runbook consistency check
$PYTHON_BIN ./scripts/validate-notification-retry-runbook.py

# Alertmanager route consistency check
$PYTHON_BIN ./scripts/validate-alertmanager-route-consistency.py

# Prometheus rule validation
if [[ -n "${CI:-}" ]]; then
  export PROMTOOL_REQUIRED="${PROMTOOL_REQUIRED:-1}"
fi
./scripts/check-prometheus-rules.sh

# Unit tests
PYTHONPATH=src $PYTHON_BIN -m pytest tests/unit -q

# Optional M4 positive integration rehearsal
if [[ "${CI_RUN_M4_POSITIVE_REHEARSAL:-0}" == "1" ]]; then
  ./scripts/rehearse-m4-positive-flow.sh
fi
