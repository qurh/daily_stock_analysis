#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TEST_NODE="${TEST_NODE:-tests/integration/test_m3_acceptance_loop.py::test_m3_strategy_backtest_publish_rollback_rehearsal_loop}"

cd "$ROOT_DIR"

ALLOWED_ENV_KEYS=(
  DATABASE_URL
  QUEUE_AUTO_PROCESS
  CHROMA_PATH
  CHROMA_COLLECTION
  MEMORY_COLLECTION
  LLM_PROVIDER
  LLM_MODEL
  LLM_API_KEY
  LLM_BASE_URL
  LLM_TIMEOUT_SEC
  LLM_MAX_RETRIES
  LLM_RETRY_BACKOFF_MS
  LLM_CIRCUIT_FAILURE_THRESHOLD
  LLM_CIRCUIT_RESET_TIMEOUT_MS
  DASHSCOPE_API_KEY
  DASHSCOPE_BASE_HTTP_API_URL
  DASHSCOPE_ENABLE_THINKING
  PROMPT_REF_LOCK_MODE
)

is_allowed_env_key() {
  local key="$1"
  local allowed
  for allowed in "${ALLOWED_ENV_KEYS[@]}"; do
    if [[ "$allowed" == "$key" ]]; then
      return 0
    fi
  done
  return 1
}

if [ -f "$ENV_FILE" ]; then
  while IFS= read -r raw_line || [ -n "$raw_line" ]; do
    line="${raw_line%$'\r'}"
    case "$line" in
      "" | "#"*)
        continue
        ;;
    esac
    if [[ "$line" != *=* ]]; then
      continue
    fi
    key="${line%%=*}"
    value="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    if is_allowed_env_key "$key"; then
      export "$key=$value"
    fi
  done <"$ENV_FILE"
fi

PYTHONPATH=src "$PYTHON_BIN" -m pytest "$TEST_NODE" -q
