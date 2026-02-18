# Refactor Backend (M2 Phase 2)

## Quick Start

```bash
cd refactor/backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --app-dir src --reload --port 18000
```

## Runtime Persistence

- Database: SQLite file (`DATABASE_URL`, default `sqlite:///refactor/backend/var/refactor.sqlite3`)
- Queue: persistent DB queue table (`task_queue`)
- Auto process queue: `QUEUE_AUTO_PROCESS=true` (default)
- Vector DB: Chroma local path (`CHROMA_PATH`, default `refactor/backend/var/chroma`)
- Chroma collection: `CHROMA_COLLECTION` (default `knowledge_chunks`)
- Memory collection: `MEMORY_COLLECTION` (default `memory_entries`)
- LLM provider: `LLM_PROVIDER` (default `mock-llm`)
- LLM model: `LLM_MODEL` (default `mock-v1`)
- LLM API key: `LLM_API_KEY` (required when provider is `openai-compatible` or `openai`)
- LLM base URL: `LLM_BASE_URL` (default `https://api.openai.com/v1`)
- LLM timeout seconds: `LLM_TIMEOUT_SEC` (default `30`)
- LLM max retries: `LLM_MAX_RETRIES` (default `0`, retries only when provider marks error as retryable)
- LLM retry backoff ms: `LLM_RETRY_BACKOFF_MS` (default `100`, exponential backoff with jitter)
- LLM circuit failure threshold: `LLM_CIRCUIT_FAILURE_THRESHOLD` (default `0`, disabled when `0`)
- LLM circuit reset timeout ms: `LLM_CIRCUIT_RESET_TIMEOUT_MS` (default `30000`)
- DashScope API key: `DASHSCOPE_API_KEY` (used when provider is `dashscope`)
- DashScope base HTTP API URL: `DASHSCOPE_BASE_HTTP_API_URL` (default `https://dashscope.aliyuncs.com/api/v1`)
- DashScope thinking mode: `DASHSCOPE_ENABLE_THINKING` (default `false`)
- Prompt ref lock mode: `PROMPT_REF_LOCK_MODE` (`lenient` by default, `strict` optional)
- Prompt lock overview cache TTL seconds: `PROMPT_LOCK_OVERVIEW_CACHE_TTL_SEC` (default `30`, disabled when `<=0`)
- Prompt lock overview cache max entries: `PROMPT_LOCK_OVERVIEW_CACHE_MAX_SIZE` (default `128`, disabled when `<=0`)
- Prompt lock overview module timeout seconds: `PROMPT_LOCK_OVERVIEW_MODULE_TIMEOUT_SEC` (default `0`, disabled when `<=0`)
- Prompt lock overview summary timeout override seconds: `PROMPT_LOCK_OVERVIEW_TIMEOUT_SUMMARY_SEC` (default `0`, module override)
- Prompt lock overview grouped timeout override seconds: `PROMPT_LOCK_OVERVIEW_TIMEOUT_GROUPED_SEC` (default `0`, module override)
- Prompt lock overview trends timeout override seconds: `PROMPT_LOCK_OVERVIEW_TIMEOUT_TRENDS_SEC` (default `0`, module override)
- Return sample min size: `BACKTEST_RETURN_SAMPLE_MIN_SIZE` (default `20`)
- Return sample medium coverage pct: `BACKTEST_RETURN_SAMPLE_MEDIUM_COVERAGE_PCT` (default `50`)
- Multi-window alert warn low windows threshold: `BACKTEST_MULTI_WINDOW_ALERT_WARN_LOW_WINDOWS` (default `1`)
- Multi-window alert warn threshold-unmet windows threshold: `BACKTEST_MULTI_WINDOW_ALERT_WARN_THRESHOLD_UNMET_WINDOWS` (default `1`)
- Multi-window alert critical low windows threshold: `BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_LOW_WINDOWS` (default `2`)
- Multi-window alert critical threshold-unmet windows threshold: `BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_THRESHOLD_UNMET_WINDOWS` (default `3`)
- Threshold normalization rule: `critical` thresholds are auto-adjusted to be no smaller than corresponding `warn` thresholds.
- Real smoke switch: `ENABLE_REAL_LLM_SMOKE` (`1` to run integration smoke)

Example:

```bash
export DATABASE_URL="sqlite:////tmp/refactor-m1.sqlite3"
export QUEUE_AUTO_PROCESS=true
export CHROMA_PATH="/tmp/refactor-chroma"
export CHROMA_COLLECTION="knowledge_chunks"
export MEMORY_COLLECTION="memory_entries"
export LLM_PROVIDER="mock-llm"
export LLM_MODEL="mock-v1"
uvicorn app.main:app --app-dir src --reload --port 18000
```

Use OpenAI-compatible endpoint:

```bash
export LLM_PROVIDER="openai-compatible"
export LLM_MODEL="gpt-4o-mini"
export LLM_API_KEY="sk-xxx"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_TIMEOUT_SEC="30"
uvicorn app.main:app --app-dir src --reload --port 18000
```

Use DashScope SDK endpoint:

```bash
export LLM_PROVIDER="dashscope"
export LLM_MODEL="qwen-plus"
export DASHSCOPE_API_KEY="sk-xxx"
export DASHSCOPE_BASE_HTTP_API_URL="https://dashscope.aliyuncs.com/api/v1"
export DASHSCOPE_ENABLE_THINKING="true"
uvicorn app.main:app --app-dir src --reload --port 18000
```

## Available APIs

- `GET /api/v2/health`
- `POST /api/v2/analysis/jobs`
- `GET /api/v2/jobs/{job_id}`
- `POST /api/v2/backtest/jobs`
- `GET /api/v2/backtest/jobs/{job_id}`
- `GET /api/v2/backtest/results`
- `GET /api/v2/backtest/performance`
- `GET /api/v2/backtest/performance/{symbol}`
- `POST /api/v2/workflows/executions`
- `GET /api/v2/workflows/executions/{execution_id}`
- `POST /api/v2/workflows/executions/{execution_id}/cancel`
- `POST /api/v2/prompts/templates`
- `POST /api/v2/prompts/templates/{prompt_id}/versions`
- `POST /api/v2/prompts/templates/{prompt_id}/versions/{version}/publish`
- `POST /api/v2/prompts/templates/{prompt_id}/rollback`
- `GET /api/v2/prompts/templates/{prompt_id}`
- `POST /api/v2/knowledge/documents/upload`
- `POST /api/v2/knowledge/documents/{doc_id}/optimize`
- `POST /api/v2/knowledge/documents/{doc_id}/ingest`
- `GET /api/v2/knowledge/documents/{doc_id}`
- `GET /api/v2/knowledge/chunks/search`
- `DELETE /api/v2/knowledge/documents/{doc_id}`
- `POST /api/v2/chat/sessions`
- `POST /api/v2/chat/sessions/{session_id}/messages`
- `GET /api/v2/chat/sessions/{session_id}/messages`
- `GET /api/v2/memory/sessions/{session_id}`
- `POST /api/v2/memory/sessions/{session_id}/summarize`
- `POST /api/v2/memory/search`
- `DELETE /api/v2/memory/sessions/{session_id}`
- `POST /api/v2/feedback/records`
- `GET /api/v2/feedback/records`
- `POST /api/v2/optimization/jobs/trigger`
- `POST /api/v2/optimization/proposals`
- `POST /api/v2/optimization/proposals/{proposal_id}/approve`
- `POST /api/v2/optimization/proposals/{proposal_id}/reject`
- `POST /api/v2/strategy/cognition/distill`
- `POST /api/v2/strategy/cognition/{memo_id}/review`
- `POST /api/v2/strategy/extract`
- `GET /api/v2/strategy/versions`
- `POST /api/v2/strategy/{strategy_id}/publish`
- `POST /api/v2/strategy/{strategy_id}/rollback`
- `POST /api/v2/strategy/{strategy_id}/bind`
- `GET /api/v2/strategy/bindings`
- `GET /api/v2/prompt-lock/events`
- `GET /api/v2/prompt-lock/failures/summary`
- `GET /api/v2/prompt-lock/failures/grouped`
- `GET /api/v2/prompt-lock/failures/trends`
- `GET /api/v2/prompt-lock/overview`
- `GET /api/v2/prompt-lock/overview/metrics`
- `GET /api/v2/prompt-lock/overview/metrics/prometheus`
- `GET /api/v2/metrics`

## Prompt Binding

- Chat generation resolves active prompt template `prompt.chat.reply`.
- When active version exists, chat trace contains `prompt_ref` like `prompt.chat.reply@1`.
- If template is not published, fallback prompt `builtin.chat.reply@0` is used.

## Strategy Binding Context

- When an active binding matches `flow_id=stock_analysis_v1` and request scope, analysis result includes:
  - `result.report.meta.strategy_context`
- When an active binding matches `flow_id=chat_reply_v1`, assistant tool trace includes:
  - `strategy_id`
  - `strategy_binding_id`
  - `strategy_flow_id`
- Strategy rollback behavior:
  - rolling back an active strategy automatically deactivates its active bindings
- Chat prompt selection order:
  - strategy binding `prompt_refs` (first resolvable prompt)
  - fallback to `prompt.chat.reply`
  - fallback to builtin `builtin.chat.reply@0`
- Prompt lock mode:
  - `lenient`: bound version fails -> fallback to active/default/builtin
  - `strict`: bound prompt refs must resolve; otherwise request returns `409` (chat) or analysis job `failed`
  - per-binding override is supported via strategy bind field `prompt_lock_mode`
- Strict lock failure detail contains:
  - `error_code`, `code`, `flow_id`, `lock_mode`
  - `requested_prompt_refs`, `failures[]`
- Prompt lock audit:
  - strict failures are recorded with source (`chat` / `analysis`) and source id
  - governance overview available via `/api/v2/prompt-lock/overview` (one request returns `summary + grouped + trends`)
  - overview supports `include` switch (`summary`, `grouped`, `trends`) for selective return
  - overview uses in-memory cache for repeated same-parameter queries and auto-invalidates on new prompt lock events
  - overview cache TTL and max entries are configurable via runtime env
  - overview multi-module aggregation is executed in parallel to reduce response latency
  - overview supports optional per-module timeout degrade in parallel mode (timeout module returns empty payload + module error metadata)
  - overview supports module-specific timeout override (`summary/grouped/trends`) with higher priority than global timeout
  - degraded overview responses are not cached
  - overview runtime counters are queryable via `/api/v2/prompt-lock/overview/metrics`
  - overview metrics can be exported in Prometheus text format via `/api/v2/prompt-lock/overview/metrics/prometheus`
  - global metrics endpoint `/api/v2/metrics` aggregates build info + prompt lock overview metrics + backtest/optimization/analysis/workflow/knowledge/chat/memory metrics
  - global metrics endpoint includes message/chunk metrics:
    - `refactor_conversation_messages_total`
    - `refactor_conversation_messages_by_role_total{role=...}`
    - `refactor_knowledge_chunks_total`
    - `refactor_knowledge_chunks_token_count_total`
  - global metrics endpoint includes backtest/optimization quality metrics:
    - `refactor_backtest_records_total{outcome=...}`
    - `refactor_backtest_records_return_sample_size`
    - `refactor_backtest_records_return_sample_size_24h`
    - `refactor_backtest_records_return_sample_size_7d`
    - `refactor_backtest_records_return_sample_size_30d`
    - `refactor_backtest_records_return_sample_min_size_required`
    - `refactor_backtest_records_return_sample_medium_coverage_threshold_pct`
    - `refactor_backtest_records_return_sample_size_threshold_met`
    - `refactor_backtest_records_return_sample_size_threshold_met_24h`
    - `refactor_backtest_records_return_sample_size_threshold_met_7d`
    - `refactor_backtest_records_return_sample_size_threshold_met_30d`
    - `refactor_backtest_records_return_sample_threshold_unmet_windows_total`
    - `refactor_backtest_records_return_sample_low_adequacy_windows_total`
    - `refactor_backtest_records_return_sample_multi_window_alert_warn_low_windows_threshold`
    - `refactor_backtest_records_return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold`
    - `refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold`
    - `refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold`
    - `refactor_backtest_records_return_sample_multi_window_alert_warn_low_windows_threshold_raw`
    - `refactor_backtest_records_return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold_raw`
    - `refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold_raw`
    - `refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_raw`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_raw_normalized_mismatch_count`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_raw_normalized_mismatch_ratio`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_dimensions_total`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_normalization_applied`
    - `refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold_normalized`
    - `refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_normalized`
    - `refactor_backtest_records_return_sample_multi_window_alert_level{level=none|warn|critical}`
    - `refactor_backtest_records_return_sample_multi_window_alert_level_score`
    - `refactor_backtest_records_return_sample_size_gap`
    - `refactor_backtest_records_return_sample_coverage_ratio_pct`
    - `refactor_backtest_records_return_sample_coverage_ratio_pct_24h`
    - `refactor_backtest_records_return_sample_coverage_ratio_pct_7d`
    - `refactor_backtest_records_return_sample_coverage_ratio_pct_30d`
    - `refactor_backtest_records_return_sample_adequacy_level{level=low|medium|high}`
    - `refactor_backtest_records_return_sample_adequacy_level_24h{level=low|medium|high}`
    - `refactor_backtest_records_return_sample_adequacy_level_7d{level=low|medium|high}`
    - `refactor_backtest_records_return_sample_adequacy_level_30d{level=low|medium|high}`
    - `refactor_backtest_records_return_sample_adequacy_score`
    - `refactor_backtest_records_return_sample_adequacy_score_24h`
    - `refactor_backtest_records_return_sample_adequacy_score_7d`
    - `refactor_backtest_records_return_sample_adequacy_score_30d`
    - `refactor_backtest_records_return_pct_avg`
    - `refactor_backtest_records_return_pct_trimmed_mean_10pct`
    - `refactor_backtest_records_return_pct_winsorized_mean_10pct`
    - `refactor_backtest_records_return_pct_p50`
    - `refactor_backtest_records_return_pct_p90`
    - `refactor_backtest_records_return_pct_p95`
    - `refactor_backtest_records_return_pct_p99`
    - `refactor_backtest_records_return_pct_stddev`
    - `refactor_backtest_records_direction_sample_size`
    - `refactor_backtest_records_direction_accuracy_pct`
    - `refactor_optimization_quality_score_sample_size`
    - `refactor_optimization_quality_score_avg`
    - `refactor_optimization_recommendations_total{recommendation=...}`
  - aggregated failure reasons available via `/api/v2/prompt-lock/failures/summary`
  - grouped failure stats available via `/api/v2/prompt-lock/failures/grouped`
  - time-bucket trend stats available via `/api/v2/prompt-lock/failures/trends` (`granularity=hour|day`)
  - trend buckets support optional reason split via `split_by=reason` and return `reason_counts`
  - reason split supports optional `reason_top_n` to limit per-bucket reason count rows
  - `/api/v2/prompt-lock/events`, `/api/v2/prompt-lock/failures/summary`, `/api/v2/prompt-lock/failures/grouped`, and `/api/v2/prompt-lock/failures/trends` support `last_hours`, `start_at`, and `end_at` filters
  - invalid absolute range (`start_at > end_at`) returns `400`
  - grouped API supports `group_by` dimensions: `flow_id`, `source_type`, `reason`
  - trends API supports `granularity` dimensions: `hour`, `day`
  - trends API supports `split_by` dimension: `reason`
  - trends API supports `reason_top_n` (effective when `split_by=reason`)
- MVP scope matching rules:
  - `{"scope":"global"}` matches all requests
  - `symbols` and `report_type` constraints must both match when configured

## Run Quality Checks

```bash
cd refactor/backend
./scripts/ci.sh
```

## Run Real LLM Smoke

```bash
cd refactor/backend
./scripts/smoke-real-llm.sh
```

## Run M3 Acceptance Rehearsal

```bash
cd refactor/backend
./scripts/rehearse-m3-loop.sh
```

Notes:

- The script loads environment variables from `refactor/backend/.env` by default.
- Required variables for a real call:
  - `LLM_PROVIDER=openai-compatible` (or `openai` / `dashscope`)
  - `LLM_MODEL=<your-model>`
  - `LLM_API_KEY=<your-key>` (or `DASHSCOPE_API_KEY` for `dashscope`)
  - `LLM_BASE_URL=<provider-base-url>` (for OpenAI-compatible providers)
  - `ENABLE_REAL_LLM_SMOKE=1`
- Optional reliability variables:
  - `LLM_MAX_RETRIES`, `LLM_RETRY_BACKOFF_MS`
  - `LLM_CIRCUIT_FAILURE_THRESHOLD`, `LLM_CIRCUIT_RESET_TIMEOUT_MS`
