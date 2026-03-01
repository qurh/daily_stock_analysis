# Refactor Backend (M4 Notification Hub Phase 2)

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
- Threshold governance warn ratio: `BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_WARN_RATIO` (default `0.25`)
- Threshold governance critical ratio: `BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_CRITICAL_RATIO` (default `0.5`, auto-raised to warn ratio when configured lower)
- Threshold normalization rule: `critical` thresholds are auto-adjusted to be no smaller than corresponding `warn` thresholds.
- Notification HTTP timeout seconds: `NOTIFICATION_HTTP_TIMEOUT_SEC` (default `10`)
- Notification send max retries per channel: `NOTIFICATION_SEND_MAX_RETRIES` (default `0`)
- Notification retry backoff ms (linear): `NOTIFICATION_RETRY_BACKOFF_MS` (default `0`)
- Analysis auto notify switch: `ANALYSIS_AUTO_NOTIFY_ENABLED` (default `false`)
- Analysis auto notify channels CSV: `ANALYSIS_AUTO_NOTIFY_CHANNELS` (default empty -> all enabled channels)
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
- `GET /api/v2/notifications/channels`
- `GET /api/v2/notifications/deliveries`
- `POST /api/v2/notifications/deliveries/{delivery_id}/retry`
- `POST /api/v2/notifications/preview`
- `POST /api/v2/notifications/send`
- `POST /api/v2/notifications/channels/test`
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

## Notification Hub

- Notification hub provides channel list, preview, send, and per-channel connectivity test.
- Delivery records are persisted and queryable via `GET /api/v2/notifications/deliveries`.
- Failed delivery can be retried via `POST /api/v2/notifications/deliveries/{delivery_id}/retry`.
- Per-channel send supports configurable retries (`NOTIFICATION_SEND_MAX_RETRIES`) with optional backoff.
- Global metrics (`GET /api/v2/metrics`) include notification retry observability:
  - `refactor_notification_retry_success_ratio`
  - `refactor_notification_auto_retry_final_failure_ratio`
  - plus status/channel/retry volume series for delivery tracking
- Prometheus alert rules for retry governance:
  - default: `monitoring/prometheus/rules/refactor-notification-retry-alerts.yml`
  - profiles: `*.dev.yml`, `*.staging.yml`, `*.prod.yml`
  - source config: `config/notification-retry-alert-thresholds.json`
  - sync/update: `python3 scripts/sync-notification-retry-alert-thresholds.py`
  - sync/check: `python3 scripts/sync-notification-retry-alert-thresholds.py --check`
- Alertmanager routing consistency:
  - route config: `monitoring/alertmanager/refactor-alertmanager-routing.yml`
  - validate: `python3 scripts/validate-alertmanager-route-consistency.py`
  - structured errors: `python3 scripts/validate-alertmanager-route-consistency.py --json-errors`
  - structured success output: `python3 scripts/validate-alertmanager-route-consistency.py --json-output`
    - success payload fields: `validator`, `status`, `rules_dir`, `alertmanager_file`, `alert_count`, `explicit_route_count`
  - json error code namespace: `alertmanager_route_consistency_*` (includes `cli_args_invalid`)
  - matcher operators supported in route check: `=`, `!=`, `=~`, `!~`
  - guardrails:
    - each alert must match at least one explicit route
    - each alert must not match multiple explicit routes (avoid ambiguous routing)
    - a later sibling route must not be shadowed by an earlier non-`continue` route
- Runbook:
  - `refactor/docs/runbooks/2026-02-20-notification-retry-alert-runbook.md`
  - threshold section between `<!-- notification-retry-thresholds:start -->` and
    `<!-- notification-retry-thresholds:end -->` is auto-rendered from threshold config
- Runbook/rule consistency guard:
  - `python3 scripts/validate-notification-retry-runbook.py`
  - validates `default/dev/staging/prod` rule files and checks `default == prod`
  - structured errors: `python3 scripts/validate-notification-retry-runbook.py --json-errors`
  - structured success output: `python3 scripts/validate-notification-retry-runbook.py --json-output`
    - success payload fields:
      - `validator`, `status`, `default_rule_file`, `dev_rule_file`, `staging_rule_file`
      - `prod_rule_file`, `runbook_file`, `profile_count`
  - json error code namespace: `notification_retry_runbook_*` (includes `cli_args_invalid`)
  - included in `scripts/ci.sh`
- Channel plugin architecture is extensible by implementing `ChannelPlugin` in
  `refactor/backend/src/app/services/notification_service.py`.
- Current built-in channels:
  - `wechat`, `feishu`, `telegram`, `email`, `pushover`, `pushplus`, `serverchan3`, `custom`, `discord`, `astrbot`
- Existing env keys are reused for channel enablement:
  - Webhook channels: `WECHAT_WEBHOOK_URL`, `FEISHU_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL`, `CUSTOM_WEBHOOK_URLS`
  - Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_MESSAGE_THREAD_ID`
  - Email: `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_RECEIVERS`
  - Other push channels: `PUSHOVER_USER_KEY`, `PUSHOVER_API_TOKEN`, `PUSHPLUS_TOKEN`, `SERVERCHAN3_SENDKEY`
  - AstrBot: `ASTRBOT_URL` (or `ASTRBOT_WEBHOOK_URL`), optional `ASTRBOT_TOKEN`
- Analysis auto notify:
  - set `ANALYSIS_AUTO_NOTIFY_ENABLED=true` to auto-send on analysis success
  - optional `ANALYSIS_AUTO_NOTIFY_CHANNELS=wechat,feishu` to limit channels
  - delivery source is tracked as `source_type=analysis_job` with `source_id=<job_id>`

## Feedback Event Trigger

- `POST /api/v2/feedback/records` includes `optimization_trigger` in response.
- When `FEEDBACK_EVENT_OPTIMIZATION_ENABLED=true`, feedback recording can auto-trigger
  `event` optimization jobs based on:
  - `FEEDBACK_EVENT_OPTIMIZATION_MIN_RECORDS`
  - `FEEDBACK_EVENT_OPTIMIZATION_COOLDOWN_SECONDS`
- Manual trigger and chatbot proposal entrypoints remain unchanged:
  - `POST /api/v2/optimization/jobs/trigger`
  - `POST /api/v2/optimization/proposals`

## Optimization Proposal Schema Gate

- API request model (`OptimizationProposalCreateRequest.target`) is restricted to enum values:
  - `prompt.chat.reply`
  - `workflow.stock.analysis`
  - `strategy.analysis.lifecycle`
- Unsupported target is rejected by request validation (`422`).
- `diff` required keys by target namespace:
  - `prompt.*` -> `diff.prompt_patch` (`FDB-INPUT-005`)
  - `workflow.*` -> `diff.flow_patch` (`FDB-INPUT-004`)
  - `strategy.*` -> `diff.strategy_id` (`FDB-INPUT-002`)
- Service layer still keeps target whitelist gate (`FDB-INPUT-003`) as defense-in-depth.
- `strategy.*` supports nested form `diff.strategy.strategy_id`; service normalizes it to `diff.strategy_id`.

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
- Strategy publish gate behavior:
  - publish request supports optional `proposal_id` for explicit proposal-strategy bind validation
  - strict mode switch `STRATEGY_PUBLISH_REQUIRE_PROPOSAL_ID=true` forces `proposal_id` to be provided
    for publish requests (missing proposal_id returns `409` with `STR-GATE-009`)
  - strict gate audit metrics are exported via `/api/v2/metrics`:
    - `refactor_strategy_publish_strict_gate_hits_total`
    - `refactor_strategy_publish_strict_gate_blocked_total`
    - `refactor_strategy_publish_strict_gate_block_ratio`
  - when `proposal_id` is provided:
    - proposal must exist
    - proposal must be linked to current strategy (`diff.strategy_id == strategy_id`)
    - proposal status must be `approved`
    - failures return `409` with `STR-GATE-007` / `STR-GATE-008`
  - if a linked `chatbot` change proposal exists for the strategy (`diff.strategy_id`),
    publish requires the latest linked proposal status to be `approved`
  - otherwise publish returns `409` with gate code `STR-GATE-006`
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
    - mismatch ratio denominator is aligned with threshold dimensions total via one backend constant.
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_warn_ratio`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_critical_ratio`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_warn_ratio_normalized`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_critical_ratio_normalized`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_ratio_normalization_applied`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_level{level=none|warn|critical}`
    - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_level_score`
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

- `ci.sh` now runs `./scripts/check-prometheus-rules.sh`.
- `ci.sh` now runs `./scripts/validate-promtool-installer-config.sh` before rule checks.
- `validate-promtool-installer-config.sh` validates required config keys, version format, and SHA256 checksum format.
- Set `PROMTOOL_VALIDATE_REMOTE=1` to verify configured checksums against release `sha256sums.txt`.
- `PROMTOOL_VALIDATE_REMOTE_MODE` controls gate behavior (`strict` default, `soft` optional).
  - `strict`: remote validation failure exits with non-zero status.
  - `soft`: remote validation failure is logged as warning and validation continues.
  - `soft` mode emits metric-style log: `remote_soft_fallback_total=1`.
  - optional audit log sink: `PROMTOOL_REMOTE_SOFT_AUDIT_FILE=<path>`.
  - optional audit retention: `PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES=<N>` (`0` disables trimming).
  - optional audit size cap: `PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES=<N>` (`0` disables byte trimming).
  - optional audit time window: `PROMTOOL_REMOTE_SOFT_AUDIT_RETENTION_DAYS=<N>` (`0` disables age prune).
  - retention-days prune uses python when available and falls back to `date` calculation when python is unavailable.
  - `/api/v2/metrics` can export audit counters from the same file when `PROMTOOL_REMOTE_SOFT_AUDIT_FILE` is set in backend env.
  - `/api/v2/metrics` also exports audit file footprint and configured rotation thresholds (max lines/bytes/retention days).
- Remote checksum validation supports fetch hardening knobs:
  - `PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS` (default: `3`)
  - `PROMTOOL_REMOTE_FETCH_CONNECT_TIMEOUT_SECONDS` (default: `10`)
  - `PROMTOOL_REMOTE_FETCH_TIMEOUT_SECONDS` (default: `30`)
  - `PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS` (default: `1`)
  - `PROMTOOL_REMOTE_FETCH_CACHE_FILE` (optional local cache path for `sha256sums.txt`)
  - `PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS` (default: `3600`)
  - when cache is fresh, remote fetch is skipped; stale cache triggers a refresh fetch
- If `promtool` is unavailable, rule validation is skipped with a warning.
- Override binary path with `PROMTOOL_BIN` when needed.
- Set `PROMTOOL_REQUIRED=1` to fail immediately when `promtool` is missing.
- In CI (`CI` env is set), `ci.sh` defaults `PROMTOOL_REQUIRED=1` unless explicitly overridden.
- On success, the checker prints a validated rule-file count summary.
- GitHub Actions workflow:
  - active workflow: `.github/workflows/refactor-backend-ci.yml`
  - example template: `refactor/backend/ci/github-actions/refactor-backend-ci.example.yml`
  - shared installer script: `refactor/backend/scripts/install-promtool.sh`
  - shared installer config: `refactor/backend/config/promtool-installer.defaults`
  - promtool version and per-platform SHA256 are managed in the shared config file.
  - workflow verifies archive SHA256 before extracting and installing `promtool`.
  - CI workflow enables `PROMTOOL_VALIDATE_REMOTE=1` to validate configured checksums against upstream release metadata.
  - CI workflow explicitly sets `PROMTOOL_VALIDATE_REMOTE_MODE=strict` for hard gate behavior.
  - installer script auto-detects `linux-amd64` / `linux-arm64` from machine architecture by default.
  - installer script supports smoke mode with `PROMTOOL_DRY_RUN=1` and arch override via `PROMTOOL_MACHINE_ARCH`.

## Prometheus Alert Rule Template

- Template file: `monitoring/prometheus/rules/refactor-threshold-governance-alerts.yml`
- Profile templates:
  - `monitoring/prometheus/rules/refactor-threshold-governance-alerts.dev.yml`
  - `monitoring/prometheus/rules/refactor-threshold-governance-alerts.staging.yml`
  - `monitoring/prometheus/rules/refactor-threshold-governance-alerts.prod.yml`
- Strict gate threshold config:
  - `config/strict-gate-alert-thresholds.json`
  - includes strict gate thresholds, threshold-governance alert profile values, and soft-audit alert profile values
- Strict gate threshold sync script:
  - `scripts/sync-strict-gate-alert-thresholds.py`
  - validates config schema before sync:
    - duration format: `^[1-9][0-9]*(ms|s|m|h|d|w|y)$`
    - severity enum: `info|warning|critical`
    - ratio range: `0.0 <= ratio <= 1.0`
    - ratio relation: `critical_ratio >= warn_ratio`
    - min hits: `min_hits > 0`
- Includes eight baseline rules:
  - `RefactorThresholdGovernanceWarn`
  - `RefactorThresholdGovernanceCritical`
  - `RefactorThresholdGovernanceNormalizationApplied`
  - `RefactorStrategyPublishStrictGateBlockRatioWarn`
  - `RefactorStrategyPublishStrictGateBlockRatioCritical`
  - `RefactorPromtoolSoftAuditMaxLinesExceeded`
  - `RefactorPromtoolSoftAuditMaxBytesExceeded`
  - `RefactorPromtoolSoftAuditRotationUnbounded`
- Strict gate alert runbook:
  - `refactor/docs/runbooks/2026-02-19-strict-gate-alert-runbook.md`
- Validate template with:

```bash
cd refactor/backend
python3 scripts/sync-strict-gate-alert-thresholds.py --check
promtool check rules monitoring/prometheus/rules/refactor-threshold-governance-alerts.yml
```

- Optional profile-only sync/check:

```bash
cd refactor/backend
python3 scripts/sync-strict-gate-alert-thresholds.py --check --profile dev
python3 scripts/sync-strict-gate-alert-thresholds.py --profile staging
python3 scripts/sync-strict-gate-alert-thresholds.py --check --config /tmp/strict-gate-alert-thresholds.json
python3 scripts/sync-strict-gate-alert-thresholds.py --dry-run --profile dev
python3 scripts/sync-strict-gate-alert-thresholds.py --check --dry-run --profile dev
python3 scripts/sync-strict-gate-alert-thresholds.py --dry-run --summary-only --profile dev
python3 scripts/sync-strict-gate-alert-thresholds.py --dry-run --summary-only --summary-format json --profile dev
python3 scripts/sync-strict-gate-alert-thresholds.py --dry-run --summary-only --summary-format json --summary-output /tmp/strict-gate-summary.json --profile dev
```

- In JSON summary mode, `modules` includes changed alert counts for:
  - `strict`
  - `governance`
  - `soft_audit`
- JSON summary payload includes `schema_version` for contract compatibility checks.
- Formal schema file:
  - `refactor/backend/config/schemas/strict-gate-summary.schema.json`
- Formal example payload:
  - `refactor/backend/config/schemas/strict-gate-summary.example.json`
- Validate schema contract:
  - `python3 scripts/validate-strict-gate-summary-schema.py`
  - validates `schema_version` consistency between schema file and sync script
  - validates example payload against schema
  - validates example payload internal consistency (file counts / line sums / module sums)
  - emits field-level mismatch details for consistency failures
  - supports `--json-errors` for structured stderr payloads (`code/message/context`)
    - `summary_schema_example_payload_schema_validation_failed` includes `context.validation_path`
  - supports `--json-output` for structured stdout payloads
    - success payload fields: `validator`, `status`, `schema_file`, `sync_script_file`, `example_file`, `schema_version`
  - json error `code` namespace: `summary_schema_*` (includes `cli_args_invalid`)
- Validate changelog linkage:
  - `python3 scripts/validate-summary-contract-changelog.py`
  - validates latest changelog version and summary schema version note
  - supports `--json-errors` for structured stderr payloads (`code/message/context`)
  - supports `--json-output` for structured stdout payloads
    - success payload fields: `validator`, `status`, `schema_file`, `changelog_file`, `app_file`, `app_version`, `schema_version`, `changelog_version`
  - json error `code` namespace: `summary_contract_*` (includes `cli_args_invalid`)
- Validator success output base contract:
  - schema file: `refactor/backend/config/schemas/validator-success-output.schema.json`
  - all validator `--json-output` payloads must include:
    - `validator` (non-empty string)
    - `status` (const: `ok`)
  - when `--json-output` and `--json-errors` are both provided:
    - success: structured JSON is printed to stdout
    - failure: structured JSON error is printed to stderr
    - this routing contract applies to both:
      - CLI argument failures
      - business validation failures (for example: missing required files)
- Validator error output base contract:
  - schema file: `refactor/backend/config/schemas/validator-error-output.schema.json`
  - all validator `--json-errors` payloads must include:
    - `validator` (non-empty string)
    - `code` (non-empty string)
    - `message` (non-empty string)
    - `context` (object)
  - contract tests cover both:
    - CLI argument failures
    - business validation failures
  - business-failure matrix tests cover all 9 validator scripts with exact `code` and required `context` keys
  - high-frequency context sub-schema:
    - `refactor/backend/config/schemas/validator-error-context-high-frequency.schema.json`
    - enforces `context` shape for selected high-frequency business-failure error codes
  - validate high-frequency context contract samples:
    - `python3 scripts/validate-validator-error-context-high-frequency-schema.py`
    - default samples file:
      - `refactor/backend/config/validator-error-context-high-frequency-samples.json`
    - supports `--json-errors` for structured stderr payloads (`code/message/context`)
    - supports `--json-output` for structured stdout payloads
      - success payload fields: `validator`, `status`, `schema_file`, `samples_file`, `sample_count`
    - json error `code` namespace: `error_context_high_frequency_*` (includes `cli_args_invalid`)
- Validator error code catalog:
  - `refactor/backend/config/validator-error-codes.json`
  - catalog schema: `refactor/backend/config/schemas/validator-error-codes.schema.json`
  - catalog entry shape: `{description, severity, remediation}`
  - catalog groups: `summary_schema`, `summary_contract`, `placeholder_markers`, `profile_suggestion_actions`, `alertmanager_route_consistency`, `notification_retry_runbook`, `error_context_high_frequency`
  - validate catalog schema and naming: `python3 scripts/validate-validator-error-code-catalog.py`
  - custom catalog/schema: `python3 scripts/validate-validator-error-code-catalog.py --catalog-file <path> --schema-file <path>`
  - structured error output: `python3 scripts/validate-validator-error-code-catalog.py --json-errors`
  - structured success output: `python3 scripts/validate-validator-error-code-catalog.py --json-output`
    - success payload fields: `validator`, `status`, `catalog_file`, `schema_file`, `groups`, `total_codes`
  - json error `code` namespace: `error_code_catalog_*` (includes `cli_args_invalid`)
  - placeholder marker config: `refactor/backend/config/validator-placeholder-markers.json`
  - placeholder marker schema: `refactor/backend/config/schemas/validator-placeholder-markers.schema.json`
  - validate marker config: `python3 scripts/validate-validator-placeholder-markers.py`
  - custom marker schema: `python3 scripts/validate-validator-placeholder-markers.py --schema-file <path>`
  - structured error output: `python3 scripts/validate-validator-placeholder-markers.py --json-errors`
  - structured success output: `python3 scripts/validate-validator-placeholder-markers.py --json-output`
    - success payload fields: `validator`, `status`, `markers_file`, `schema_file`, `markers_count`
  - placeholder markers validator supports `--json-errors`
    (`placeholder_markers_*`, includes `cli_args_invalid`)
  - validator scripts must expose `VALIDATOR_ERROR_CODES` registry for coverage checks
  - sync/check command: `python3 scripts/sync-validator-error-codes.py --check --strict-descriptions`
  - custom marker config: `python3 scripts/sync-validator-error-codes.py --check --strict-descriptions --placeholder-markers-file <path>`
  - metadata override config: `refactor/backend/config/validator-error-code-metadata-overrides.json`
    - includes default policy overrides for `profile_suggestion_actions` group
    - `profile_suggestion_actions_helper_contract_failed` defaults to `severity=critical`
    - includes full default policy coverage for all `profile_suggestion_actions_*` codes
    - includes `placeholder_markers_cli_args_invalid` for placeholder markers CLI JSON errors
    - includes full default policy coverage for all `alertmanager_route_consistency_*` codes
    - `alertmanager_route_consistency` override policy requires actionable remediation with rerun guidance for all 13 codes; severity levels keep `warning/error/critical` split by risk
    - includes full default policy coverage for all `notification_retry_runbook_*` codes
    - `notification_retry_runbook` override policy requires actionable remediation with rerun guidance for all 5 codes; `baseline_mismatch` and `unexpected_error` stay `severity=critical`
    - includes full default policy coverage for all `error_context_high_frequency_*` codes
    - `error_context_high_frequency` override policy requires actionable remediation with rerun guidance for all 8 codes; `unexpected_error` stays `severity=critical`
  - metadata override schema: `refactor/backend/config/schemas/validator-error-code-metadata-overrides.schema.json`
  - metadata lint config: `refactor/backend/config/validator-error-code-metadata-lint.json`
  - metadata lint schema: `refactor/backend/config/schemas/validator-error-code-metadata-lint.schema.json`
  - shared unknown-profile suggestion helpers: `refactor/backend/scripts/profile_suggestion_helpers.py`
    - includes strict `suggested_actions` contract validation (supported action enum + required fields)
  - profile suggestion actions schema: `refactor/backend/config/schemas/profile-suggestion-actions.schema.json`
  - profile suggestion actions example: `refactor/backend/config/schemas/profile-suggestion-actions.example.json`
  - validate profile suggestion actions schema/example/helper:
    - `python3 scripts/validate-profile-suggestion-actions-schema.py`
  - custom schema/example/helper:
    - `python3 scripts/validate-profile-suggestion-actions-schema.py --schema-file <path> --example-file <path> --helper-file <path>`
  - profile suggestion actions validator supports `--json-errors`
    (`profile_suggestion_actions_*`, includes `cli_args_invalid`)
  - profile suggestion actions validator supports `--json-output`
    - success payload fields: `validator`, `status`, `schema_file`, `example_file`, `helper_file`, `example_action_count`
  - metadata lint config supports profile mode:
    - `{"default_profile": "...", "profiles": {"dev": {...}, "prod": {...}}}`
  - validate metadata lint config: `python3 scripts/validate-validator-error-code-metadata-lint.py`
  - custom lint config/schema:
    - `python3 scripts/validate-validator-error-code-metadata-lint.py --lint-config-file <path> --schema-file <path>`
  - lint profile selection:
    - `python3 scripts/validate-validator-error-code-metadata-lint.py --lint-config-file <path> --lint-profile <profile>`
  - lint profile env default:
    - `LINT_PROFILE=<profile> python3 scripts/validate-validator-error-code-metadata-lint.py --lint-config-file <path>`
  - metadata lint validator supports `--json-errors`
    (`error_code_metadata_lint_*`, includes `cli_args_invalid`)
  - metadata lint validator supports `--json-output`
    - success payload fields:
      - `validator`, `status`, `lint_config_file`, `schema_file`, `selected_profile`
      - `min_remediation_length`, `action_verbs_count`
  - unknown lint profile errors include:
    - `available_profiles` and `suggested_profiles` in JSON `context`
      - `available_profiles` prioritizes `default_profile` first (then alphabetical)
    - `fallback_reason` in JSON `context`:
      - `close_match` / `no_close_match` / `no_profiles_config`
    - `suggestion_level` in JSON `context`:
      - `hint` when `fallback_reason=close_match`
      - `warning` when `fallback_reason=no_close_match`
      - `error` when `fallback_reason=no_profiles_config`
    - `suggested_cli_args` in JSON `context`
    - `suggested_command` in JSON `context`
      - now uses shell-safe quoting for current `--lint-config-file` path in template
    - `suggested_actions` in JSON `context`:
      - close match:
        - `{"action":"copy_command","command":"..."}`
        - `{"action":"use_profile","profile":"..."}`
      - no close match:
        - `{"action":"show_profiles","profiles":[...]}`
      - profile mode not configured:
        - `{"action":"migrate_profile_mode","config_snippet":{...}}`
    - plain stderr now includes "Did you mean: <profile>" when suggestion exists
    - plain stderr now includes quick fix args: `Try: --lint-profile <profile>`
    - if no close suggestion exists, error message includes `Available profiles: ...`
    - if `fallback_reason=no_profiles_config`, JSON `context` now includes:
      - `suggested_config_snippet` for migrating flat lint config to profile mode
    - if `fallback_reason=no_profiles_config`, message includes:
      - `profile mode is not configured for this lint config`
  - validate metadata overrides: `python3 scripts/validate-validator-error-code-metadata-overrides.py`
  - custom overrides/schema/catalog:
    - `python3 scripts/validate-validator-error-code-metadata-overrides.py --overrides-file <path> --schema-file <path> --catalog-file <path>`
  - overrides config supports profile mode:
    - `{"default_profile":"...", "profiles":{"dev": {...}, "prod": {...}}}`
  - overrides profile selection:
    - `python3 scripts/validate-validator-error-code-metadata-overrides.py --overrides-file <path> --overrides-profile <profile>`
  - overrides profile env default:
    - `OVERRIDES_PROFILE=<profile> python3 scripts/validate-validator-error-code-metadata-overrides.py --overrides-file <path>`
  - overrides profile precedence:
    - `--overrides-profile` > `OVERRIDES_PROFILE` > overrides config `default_profile`
  - unknown overrides profile errors include:
    - `fallback_reason` / `suggestion_level`
    - `suggested_profiles` / `suggested_cli_args`
    - `suggested_command` (includes shell-safe quoted `--overrides-file` path)
    - `suggested_actions` (`copy_command` / `use_profile` / `show_profiles`)
  - custom lint config:
    - `python3 scripts/validate-validator-error-code-metadata-overrides.py --lint-config-file <path>`
  - overrides lint profile selection:
    - `python3 scripts/validate-validator-error-code-metadata-overrides.py --lint-config-file <path> --lint-profile <profile>`
  - overrides lint profile env default:
    - `LINT_PROFILE=<profile> python3 scripts/validate-validator-error-code-metadata-overrides.py --lint-config-file <path>`
  - lint profile precedence:
    - `--lint-profile` > `LINT_PROFILE` > lint config `default_profile`
  - metadata override validator supports `--json-errors`
    (`error_code_metadata_overrides_*`, includes `cli_args_invalid`)
  - metadata override validator supports `--json-output`
    - success payload fields:
      - `validator`, `status`, `overrides_file`, `schema_file`, `catalog_file`
      - `lint_config_file`, `placeholder_markers_file`
      - `requested_overrides_profile`, `requested_lint_profile`
      - `total_override_groups`, `total_override_codes`
  - unknown overrides lint profile errors include:
    - `available_profiles` and `suggested_profiles` in JSON `context`
      - `available_profiles` prioritizes `default_profile` first (then alphabetical)
    - `fallback_reason` in JSON `context`:
      - `close_match` / `no_close_match` / `no_profiles_config`
    - `suggestion_level` in JSON `context`:
      - `hint` when `fallback_reason=close_match`
      - `warning` when `fallback_reason=no_close_match`
      - `error` when `fallback_reason=no_profiles_config`
    - `suggested_cli_args` in JSON `context`
    - `suggested_command` in JSON `context`
      - now uses shell-safe quoting for current `--lint-config-file` path in template
    - `suggested_actions` in JSON `context`:
      - close match:
        - `{"action":"copy_command","command":"..."}`
        - `{"action":"use_profile","profile":"..."}`
      - no close match:
        - `{"action":"show_profiles","profiles":[...]}`
      - profile mode not configured:
        - `{"action":"migrate_profile_mode","config_snippet":{...}}`
    - plain stderr now includes "Did you mean: <profile>" when suggestion exists
    - plain stderr now includes quick fix args: `Try: --lint-profile <profile>`
    - if no close suggestion exists, error message includes `Available profiles: ...`
    - if `fallback_reason=no_profiles_config`, JSON `context` now includes:
      - `suggested_config_snippet` for migrating flat lint config to profile mode
    - if `fallback_reason=no_profiles_config`, message includes:
      - `profile mode is not configured for this lint config`
  - metadata override semantic lint:
    - rejects placeholder text in `description/remediation` using marker config
    - requires remediation text to be actionable (contains action verbs and minimum text length)
  - custom metadata overrides: `python3 scripts/sync-validator-error-codes.py --metadata-overrides-file <path>`
  - sync metadata overrides profile selection:
    - `python3 scripts/sync-validator-error-codes.py --metadata-overrides-file <path> --metadata-overrides-profile <profile>`
  - sync metadata overrides profile env default:
    - `METADATA_OVERRIDES_PROFILE=<profile> python3 scripts/sync-validator-error-codes.py --metadata-overrides-file <path>`
  - sync metadata overrides profile precedence:
    - `--metadata-overrides-profile` > `METADATA_OVERRIDES_PROFILE` > overrides config `default_profile`
  - sync structured JSON errors:
    - `python3 scripts/sync-validator-error-codes.py --json-errors`
    - unexpected runtime failures return:
      - `error_code_sync_validator_error_codes_unexpected_error`
      - includes `context.stage=runtime`
      - includes `context.exception_type`
      - includes `context.exit_code=1`
      - includes `context.argv`
      - includes `context.unknown_args=[]`
    - argument parsing failures return:
      - `error_code_sync_validator_error_codes_unexpected_error`
      - includes `context.stage=argument_parsing`
      - includes `context.argv`
      - unknown argument cases include `context.unknown_args` and `context.argv`
    - catalog file read failed returns:
      - `error_code_sync_validator_error_codes_catalog_file_read_failed`
      - includes `failure_mode=catalog_file_read_failed` in JSON `context`
    - invalid UTF-8 (or invalid JSON text) in existing catalog returns:
      - `error_code_sync_validator_error_codes_json_parse_error`
      - includes `exception_type` in JSON `context` for decode/parse failures
    - output parent create failed returns:
      - `error_code_sync_validator_error_codes_output_parent_create_failed`
    - output write failed returns:
      - `error_code_sync_validator_error_codes_output_write_failed`
    - validator script file missing returns:
      - `error_code_sync_validator_error_codes_validator_script_file_not_found`
    - validator registry load failed returns:
      - `error_code_sync_validator_error_codes_validator_registry_load_failed`
      - includes syntax/runtime/SystemExit loader failures
      - includes `stage=validator_registry_loading` in JSON `context`
      - includes `exception_type` in JSON `context`
      - includes `failure_mode` in JSON `context`:
        - `exception` for generic loader exceptions
        - `system_exit` for `SystemExit` loader failures
      - SystemExit cases include `exit_code` in JSON `context`
    - validator registry missing returns:
      - `error_code_sync_validator_error_codes_validator_registry_missing`
      - includes `stage=validator_registry_validation` in JSON `context`
      - includes `failure_mode=missing_registry` in JSON `context`
    - validator registry invalid returns:
      - `error_code_sync_validator_error_codes_validator_registry_invalid`
      - includes `stage=validator_registry_validation` in JSON `context`
      - includes `failure_mode=invalid_registry_item` in JSON `context`
    - metadata overrides file missing returns:
      - `error_code_sync_validator_error_codes_metadata_overrides_file_not_found`
      - includes `failure_mode=metadata_overrides_file_not_found` in JSON `context`
    - metadata overrides file read failed returns:
      - `error_code_sync_validator_error_codes_metadata_overrides_file_read_failed`
      - includes `failure_mode=metadata_overrides_file_read_failed` in JSON `context`
    - invalid UTF-8 (or invalid JSON text) in metadata overrides returns:
      - `error_code_sync_validator_error_codes_json_parse_error`
      - includes `exception_type` in JSON `context` for decode/parse failures
    - placeholder marker file missing returns:
      - `error_code_sync_validator_error_codes_placeholder_markers_file_not_found`
      - includes `failure_mode=placeholder_markers_file_not_found` in JSON `context`
    - placeholder marker file read failed returns:
      - `error_code_sync_validator_error_codes_placeholder_markers_read_failed`
      - includes `failure_mode=placeholder_markers_file_read_failed` in JSON `context`
    - placeholder marker payload invalid returns:
      - `error_code_sync_validator_error_codes_placeholder_markers_invalid`
      - includes non-object JSON payload cases (for example: array payload)
      - includes invalid UTF-8 marker payload cases
      - includes `exception_type` in JSON `context` for UTF-8 decode and JSON parse failures
    - check drift returns:
      - `error_code_sync_validator_error_codes_catalog_not_in_sync`
    - strict placeholder text returns:
      - `error_code_sync_validator_error_codes_placeholder_text_detected`
    - unknown metadata overrides profile returns:
      - `error_code_sync_validator_error_codes_metadata_overrides_profile_not_found`
    - unknown override code returns:
      - `error_code_sync_validator_error_codes_unknown_override_code`
  - unknown sync metadata overrides profile errors:
    - close match includes `Did you mean: <profile>` and `Try: --metadata-overrides-profile <profile>`
    - no close match includes `Available profiles: ...` (default profile listed first)
    - JSON `context` now includes `suggested_actions`:
      - close match:
        - `{"action":"copy_command","command":"..."}`
        - `{"action":"use_profile","profile":"..."}`
      - no close match:
        - `{"action":"show_profiles","profiles":[...]}`
      - profile mode not configured:
        - `{"action":"migrate_profile_mode","config_snippet":{...}}`
    - when profile mode is not configured (`fallback_reason=no_profiles_config`), JSON `context` includes:
      - `suggested_config_snippet` for migrating flat overrides config to profile mode
  - override rules:
    - payload format: `group -> code -> {description|severity|remediation}`
    - profile payload format: `default_profile + profiles.<name>.(group -> code -> fields)`
    - unknown group/code is rejected to prevent silent typo drift
  - `--strict-descriptions` rejects placeholder text in `description/remediation` (`TODO:`, `TBD:`, `FIXME:`; case-insensitive)
  - strict error output includes marker list, `group.code.field` entries, and remediation hint
  - metadata policy defaults:
    - `*_unexpected_error` -> `severity=critical` and stack-trace remediation
    - `*_json_parse_error` -> JSON syntax remediation
    - `*_file_not_found` -> file path/existence remediation
    - `*_schema_invalid` / `*_schema_validation_failed` -> schema/payload remediation

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
