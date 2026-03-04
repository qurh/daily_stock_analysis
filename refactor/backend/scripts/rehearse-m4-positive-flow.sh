#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-18080}"
MAX_SYMBOL_ATTEMPTS="${MAX_SYMBOL_ATTEMPTS:-40}"
SAMPLES_PER_SYMBOL="${SAMPLES_PER_SYMBOL:-5}"
REPORT_TYPE="${REPORT_TYPE:-detailed}"
ISOLATE_RUNTIME="${ISOLATE_RUNTIME:-1}"
KEEP_RUNTIME_ARTIFACTS="${KEEP_RUNTIME_ARTIFACTS:-0}"

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
  STRATEGY_PUBLISH_REQUIRE_PROPOSAL_ID
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

RUNTIME_ID="$(date +%Y%m%d%H%M%S)-$$"
RUNTIME_ROOT="${TMPDIR:-/tmp}/refactor-m4-positive-flow-${RUNTIME_ID}"
mkdir -p "$RUNTIME_ROOT"
RUNTIME_DB_FILE="$RUNTIME_ROOT/refactor.sqlite3"
RUNTIME_CHROMA_PATH="$RUNTIME_ROOT/chroma"
BACKEND_LOG_FILE="$RUNTIME_ROOT/backend.log"
SMOKE_LOG_FILE="$RUNTIME_ROOT/smoke.log"
mkdir -p "$RUNTIME_CHROMA_PATH"

if [[ "$ISOLATE_RUNTIME" == "1" ]]; then
  export DATABASE_URL="sqlite:///$RUNTIME_DB_FILE"
  export CHROMA_PATH="$RUNTIME_CHROMA_PATH"
fi
export LLM_PROVIDER="${LLM_PROVIDER:-mock-llm}"
export QUEUE_AUTO_PROCESS="${QUEUE_AUTO_PROCESS:-true}"

API_BASE_URL="http://${API_HOST}:${API_PORT}/api/v2"
SERVER_PID=""

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  if [[ "$KEEP_RUNTIME_ARTIFACTS" == "1" ]]; then
    echo "Runtime artifacts: $RUNTIME_ROOT"
  else
    rm -rf "$RUNTIME_ROOT"
  fi
  exit "$exit_code"
}
trap cleanup EXIT INT TERM

echo "Starting backend at ${API_BASE_URL} ..."
PYTHONPATH=src "$PYTHON_BIN" -m uvicorn app.main:app --app-dir src --host "$API_HOST" --port "$API_PORT" \
  >"$BACKEND_LOG_FILE" 2>&1 &
SERVER_PID="$!"

HEALTH_OK="0"
for _ in $(seq 1 80); do
  if curl -sf "${API_BASE_URL}/health" >/dev/null; then
    HEALTH_OK="1"
    break
  fi
  sleep 0.25
done

if [[ "$HEALTH_OK" != "1" ]]; then
  echo "Backend health check failed: ${API_BASE_URL}/health" >&2
  echo "Backend log tail:" >&2
  tail -n 80 "$BACKEND_LOG_FILE" >&2 || true
  exit 1
fi

echo "Running positive strategy smoke ..."
if ! ./scripts/smoke-positive-strategy-flow.py \
  --base-url "$API_BASE_URL" \
  --max-symbol-attempts "$MAX_SYMBOL_ATTEMPTS" \
  --samples-per-symbol "$SAMPLES_PER_SYMBOL" \
  --report-type "$REPORT_TYPE" \
  >"$SMOKE_LOG_FILE" 2>&1; then
  echo "Positive smoke failed." >&2
  cat "$SMOKE_LOG_FILE" >&2 || true
  echo "Backend log tail:" >&2
  tail -n 120 "$BACKEND_LOG_FILE" >&2 || true
  exit 1
fi

cat "$SMOKE_LOG_FILE"
echo "One-click positive smoke rehearsal completed."
echo "Backend log: $BACKEND_LOG_FILE"
echo "Smoke log: $SMOKE_LOG_FILE"
