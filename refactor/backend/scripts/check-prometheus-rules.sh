#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RULES_DIR="$ROOT_DIR/monitoring/prometheus/rules"
PROMTOOL_BIN="${PROMTOOL_BIN:-promtool}"

if [[ ! -d "$RULES_DIR" ]]; then
  echo "[check-prometheus-rules] rules directory not found: $RULES_DIR" >&2
  exit 0
fi

if ! command -v "$PROMTOOL_BIN" >/dev/null 2>&1; then
  echo "[check-prometheus-rules] promtool not found, skipping rule validation." >&2
  exit 0
fi

mapfile -t rule_files < <(find "$RULES_DIR" -maxdepth 1 -type f \( -name "*.yml" -o -name "*.yaml" \) | sort)

if [[ ${#rule_files[@]} -eq 0 ]]; then
  echo "[check-prometheus-rules] no rule files found under $RULES_DIR" >&2
  exit 0
fi

for rule_file in "${rule_files[@]}"; do
  # Equivalent command form: promtool check rules <rule-file>
  "$PROMTOOL_BIN" check rules "$rule_file"
done
