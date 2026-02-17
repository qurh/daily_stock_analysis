# Changelog

All notable changes for the refactor project are documented in this file.

## [0.3.51-m3-global-metrics-multi-window-alert-threshold-config] - 2026-02-17

### Added

- New runtime settings for multi-window alert level thresholds:
  - `BACKTEST_MULTI_WINDOW_ALERT_WARN_LOW_WINDOWS` (default `1`)
  - `BACKTEST_MULTI_WINDOW_ALERT_WARN_THRESHOLD_UNMET_WINDOWS` (default `1`)
  - `BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_LOW_WINDOWS` (default `2`)
  - `BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_THRESHOLD_UNMET_WINDOWS` (default `3`)
- New tests:
  - global metrics endpoint supports multi-window alert threshold overrides
  - settings loader reads multi-window alert threshold env vars

### Changed

- Multi-window alert level classification now reads threshold values from runtime env settings.
- Backend app version bumped to `0.3.51-m3-global-metrics-multi-window-alert-threshold-config`.

## [0.3.50-m3-global-metrics-multi-window-alert-level-score] - 2026-02-17

### Added

- New multi-window sample alert level score metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_level_score`
- New tests:
  - global metrics endpoint includes backtest return sample multi-window alert level score

### Changed

- Multi-window alert level now has numeric score mapping for alert threshold integration:
  - `none -> 0.0`
  - `warn -> 0.5`
  - `critical -> 1.0`
- Backend app version bumped to `0.3.50-m3-global-metrics-multi-window-alert-level-score`.

## [0.3.49-m3-global-metrics-multi-window-alert-level] - 2026-02-17

### Added

- New multi-window sample alert level metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_level{level=none|warn|critical}`
- New tests:
  - global metrics endpoint includes backtest return sample multi-window alert level

### Changed

- Backtest quality snapshot now classifies multi-window sample quality into alert levels:
  - `critical`: low adequacy windows >= 2, or threshold-unmet windows >= 3
  - `warn`: at least one low adequacy or threshold-unmet window
  - `none`: no alert condition matched
- Backend app version bumped to `0.3.49-m3-global-metrics-multi-window-alert-level`.

## [0.3.48-m3-global-metrics-multi-window-alert-counts] - 2026-02-17

### Added

- New multi-window sample alert count metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_threshold_unmet_windows_total`
  - `refactor_backtest_records_return_sample_low_adequacy_windows_total`
- New tests:
  - global metrics endpoint includes backtest return sample multi-window alert counts

### Changed

- Backtest quality snapshot now aggregates 24h/7d/30d window adequacy into alert-friendly counts.
- Backend app version bumped to `0.3.48-m3-global-metrics-multi-window-alert-counts`.

## [0.3.47-m3-global-metrics-30d-adequacy-level] - 2026-02-17

### Added

- New 30-day adequacy level metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_adequacy_level_30d{level=low|medium|high}`
- New tests:
  - global metrics endpoint includes backtest return sample 30d adequacy level

### Changed

- Backtest quality snapshot now exposes one-hot adequacy level for 30d window, aligned with all-time/24h/7d level semantics.
- Backend app version bumped to `0.3.47-m3-global-metrics-30d-adequacy-level`.

## [0.3.46-m3-global-metrics-30d-sample-coverage-score] - 2026-02-17

### Added

- New 30-day sample quality metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_coverage_ratio_pct_30d`
  - `refactor_backtest_records_return_sample_adequacy_score_30d`
- New tests:
  - global metrics endpoint includes backtest return sample 30d coverage and adequacy score

### Changed

- Backtest quality snapshot now computes 30d coverage ratio and adequacy score, aligned with all-time/24h/7d windows.
- Backend app version bumped to `0.3.46-m3-global-metrics-30d-sample-coverage-score`.

## [0.3.45-m3-global-metrics-30d-sample-threshold] - 2026-02-17

### Added

- New 30-day sample threshold metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_size_30d`
  - `refactor_backtest_records_return_sample_size_threshold_met_30d`
- New tests:
  - global metrics endpoint includes backtest return sample 30d threshold metrics

### Changed

- Backtest quality snapshot now computes last-30d sample size and threshold readiness, extending multi-window quality observability.
- Backend app version bumped to `0.3.45-m3-global-metrics-30d-sample-threshold`.

## [0.3.44-m3-global-metrics-7d-adequacy-level] - 2026-02-17

### Added

- New 7-day adequacy level metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_adequacy_level_7d{level=low|medium|high}`
- New tests:
  - global metrics endpoint includes backtest return sample 7d adequacy level

### Changed

- Backtest quality snapshot now includes one-hot adequacy level for 7d window, aligned with existing all-time/24h/7d score logic.
- Backend app version bumped to `0.3.44-m3-global-metrics-7d-adequacy-level`.

## [0.3.43-m3-global-metrics-7d-sample-coverage-score] - 2026-02-17

### Added

- New 7-day sample quality metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_coverage_ratio_pct_7d`
  - `refactor_backtest_records_return_sample_adequacy_score_7d`
- New tests:
  - global metrics endpoint includes backtest return sample 7d coverage and adequacy score

### Changed

- Backtest quality snapshot now computes 7d coverage ratio and adequacy score using the same threshold and medium-boundary logic as all-time/24h windows.
- Backend app version bumped to `0.3.43-m3-global-metrics-7d-sample-coverage-score`.

## [0.3.42-m3-global-metrics-7d-sample-threshold] - 2026-02-17

### Added

- New 7-day sample threshold metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_size_7d`
  - `refactor_backtest_records_return_sample_size_threshold_met_7d`
- New tests:
  - global metrics endpoint includes backtest return sample 7d threshold metrics

### Changed

- Backtest quality snapshot now computes last-7d sample size and threshold readiness alongside all-time and 24h windows.
- Backend app version bumped to `0.3.42-m3-global-metrics-7d-sample-threshold`.

## [0.3.41-m3-global-metrics-recent-adequacy-level] - 2026-02-17

### Added

- New recent-window adequacy level metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_adequacy_level_24h{level=low|medium|high}`
- New tests:
  - global metrics endpoint includes backtest return sample 24h adequacy level

### Changed

- Backtest quality snapshot now exposes one-hot adequacy level for last-24h samples, aligned with existing all-time level/score logic.
- Backend app version bumped to `0.3.41-m3-global-metrics-recent-adequacy-level`.

## [0.3.40-m3-global-metrics-recent-sample-coverage-score] - 2026-02-17

### Added

- New recent-window sample quality metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_coverage_ratio_pct_24h`
  - `refactor_backtest_records_return_sample_adequacy_score_24h`
- New tests:
  - global metrics endpoint includes backtest return sample 24h coverage and adequacy score

### Changed

- Backtest quality snapshot now computes last-24h coverage ratio and adequacy score using the same threshold and medium boundary rules as all-time scope.
- Backend app version bumped to `0.3.40-m3-global-metrics-recent-sample-coverage-score`.

## [0.3.39-m3-global-metrics-recent-sample-threshold] - 2026-02-17

### Added

- New recent-window sample metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_size_24h`
  - `refactor_backtest_records_return_sample_size_threshold_met_24h`
- New tests:
  - global metrics endpoint includes backtest return sample 24h threshold metrics

### Changed

- Backtest quality snapshot now computes sample-size readiness for the last 24 hours in addition to all-time scope.
- Backend app version bumped to `0.3.39-m3-global-metrics-recent-sample-threshold`.

## [0.3.38-m3-global-metrics-adequacy-score] - 2026-02-17

### Added

- New backtest sample adequacy score metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_adequacy_score`
- New tests:
  - global metrics endpoint includes backtest return sample adequacy score

### Changed

- Adequacy level now has a numeric score mapping for easier alert threshold usage:
  - `low -> 0.0`
  - `medium -> 0.5`
  - `high -> 1.0`
- Backend app version bumped to `0.3.38-m3-global-metrics-adequacy-score`.

## [0.3.37-m3-global-metrics-adequacy-threshold-config] - 2026-02-17

### Added

- New runtime setting:
  - `BACKTEST_RETURN_SAMPLE_MEDIUM_COVERAGE_PCT` (default `50`)
- New global metrics series in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_medium_coverage_threshold_pct`
- New tests:
  - sample adequacy level supports medium coverage threshold override
  - settings loader reads medium coverage threshold env

### Changed

- Sample adequacy level boundary for `medium` is now configurable instead of hard-coded at `50%`.
- Backend app version bumped to `0.3.37-m3-global-metrics-adequacy-threshold-config`.

## [0.3.36-m3-global-metrics-sample-adequacy-level] - 2026-02-17

### Added

- New one-hot adequacy level metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_adequacy_level{level=low|medium|high}`
- New tests:
  - global metrics endpoint includes backtest return sample adequacy level

### Changed

- Backtest sample adequacy is now classified into `low/medium/high` using threshold and coverage ratio:
  - `high`: sample size meets minimum threshold
  - `medium`: threshold unmet but coverage >= 50%
  - `low`: threshold unmet and coverage < 50%
- Backend app version bumped to `0.3.36-m3-global-metrics-sample-adequacy-level`.

## [0.3.35-m3-global-metrics-sample-coverage] - 2026-02-17

### Added

- New backtest sample adequacy metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_size_gap`
  - `refactor_backtest_records_return_sample_coverage_ratio_pct`
- New tests:
  - global metrics endpoint includes backtest return sample gap and coverage

### Changed

- Backtest quality snapshot now provides sample gap and coverage percentage to support threshold-tuning and alert interpretation.
- Backend app version bumped to `0.3.35-m3-global-metrics-sample-coverage`.

## [0.3.34-m3-global-metrics-sample-threshold] - 2026-02-17

### Added

- New backtest sample threshold metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_min_size_required`
  - `refactor_backtest_records_return_sample_size_threshold_met`
- New runtime setting:
  - `BACKTEST_RETURN_SAMPLE_MIN_SIZE` (default `20`)
- New tests:
  - global metrics endpoint includes configurable backtest return sample threshold metrics

### Changed

- Backtest quality snapshot now exposes threshold gate state for return sample size, supporting alert rules that combine quantiles and sample adequacy.
- Backend app version bumped to `0.3.34-m3-global-metrics-sample-threshold`.

## [0.3.33-m3-global-metrics-return-robust-mean] - 2026-02-17

### Added

- New robust backtest return metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_pct_trimmed_mean_10pct`
  - `refactor_backtest_records_return_pct_winsorized_mean_10pct`
- New tests:
  - global metrics endpoint includes backtest robust return means

### Changed

- Backtest return quality snapshot now includes 10pct trimmed mean and 10pct winsorized mean.
- Backend app version bumped to `0.3.33-m3-global-metrics-return-robust-mean`.

## [0.3.32-m3-global-metrics-return-tail-quantiles] - 2026-02-17

### Added

- New backtest return tail quantile metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_pct_p95`
  - `refactor_backtest_records_return_pct_p99`
- New tests:
  - global metrics endpoint includes backtest return p95 and p99 quantiles

### Changed

- Backtest return distribution snapshot now includes p95/p99 metrics in addition to p50/p90/stddev.
- Backend app version bumped to `0.3.32-m3-global-metrics-return-tail-quantiles`.

## [0.3.31-m3-global-metrics-return-distribution] - 2026-02-17

### Added

- New backtest return distribution metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_pct_p50`
  - `refactor_backtest_records_return_pct_p90`
  - `refactor_backtest_records_return_pct_stddev`
- New tests:
  - global metrics endpoint includes backtest return quantiles and stddev

### Changed

- Backtest quality snapshot now includes percentile and volatility statistics based on linear interpolation percentile and population stddev.
- Backend app version bumped to `0.3.31-m3-global-metrics-return-distribution`.

## [0.3.30-m3-global-metrics-quality-snapshots] - 2026-02-17

### Added

- New global metrics series in `/api/v2/metrics`:
  - `refactor_backtest_records_total{outcome=...}`
  - `refactor_backtest_records_return_sample_size`
  - `refactor_backtest_records_return_pct_avg`
  - `refactor_backtest_records_direction_sample_size`
  - `refactor_backtest_records_direction_accuracy_pct`
  - `refactor_optimization_quality_score_sample_size`
  - `refactor_optimization_quality_score_avg`
  - `refactor_optimization_recommendations_total{recommendation=...}`
- New tests:
  - global metrics endpoint includes backtest and optimization quality metrics

### Changed

- Global metrics endpoint now aggregates quality snapshots from:
  - `backtest_records`
  - completed `optimization_jobs.result_json`
- Backend app version bumped to `0.3.30-m3-global-metrics-quality-snapshots`.

## [0.3.29-m3-acceptance-rehearsal-loop] - 2026-02-17

### Added

- New M3 acceptance integration test:
  - `tests/integration/test_m3_acceptance_loop.py`
  - covers: cognition distill -> review approve -> strategy extract -> backtest -> proposal approve -> publish -> bind -> rollback -> post-rollback verification
- New rehearsal script:
  - `refactor/backend/scripts/rehearse-m3-loop.sh`
  - default test target: `test_m3_strategy_backtest_publish_rollback_rehearsal_loop`
- New script guard tests:
  - rehearsal script defaults to `refactor/backend/.env`
  - rehearsal script uses env key whitelist loader

### Changed

- `StrategyService.rollback_strategy(...)` now deactivates active bindings for the rolled-back strategy to avoid stale active bindings.
- Backend app version bumped to `0.3.29-m3-acceptance-rehearsal-loop`.

## [0.3.28-m3-global-metrics-message-chunk] - 2026-02-16

### Added

- New global metrics series in `/api/v2/metrics`:
  - `refactor_conversation_messages_total`
  - `refactor_conversation_messages_by_role_total{role=...}`
  - `refactor_knowledge_chunks_total`
  - `refactor_knowledge_chunks_token_count_total`
- New tests:
  - global metrics endpoint includes message and chunk metrics

### Changed

- Global metrics endpoint now aggregates additional metrics from:
  - `conversation_messages`
  - `knowledge_chunks`
- Backend app version bumped to `0.3.28-m3-global-metrics-message-chunk`.

## [0.3.27-m3-global-metrics-knowledge-chat-memory] - 2026-02-16

### Added

- New global metrics series in `/api/v2/metrics`:
  - `refactor_knowledge_documents_total{status=...}`
  - `refactor_conversation_sessions_total{status=...}`
  - `refactor_memory_summaries_total`
  - `refactor_long_term_memory_entries_total`
- New tests:
  - global metrics endpoint includes knowledge/chat/memory metrics

### Changed

- Global metrics endpoint now aggregates additional metrics from:
  - `knowledge_documents`
  - `conversation_sessions`
  - `memory_summaries`
  - `long_term_memory_entries`
- Backend app version bumped to `0.3.27-m3-global-metrics-knowledge-chat-memory`.

## [0.3.26-m3-global-metrics-analysis-workflow] - 2026-02-16

### Added

- New global metrics series in `/api/v2/metrics`:
  - `refactor_analysis_jobs_total{status=...}`
  - `refactor_workflow_executions_total{status=...}`
- New tests:
  - global metrics endpoint includes analysis and workflow status counts

### Changed

- Global metrics endpoint now aggregates additional status gauges from:
  - `analysis_jobs`
  - `workflow_executions`
- Backend app version bumped to `0.3.26-m3-global-metrics-analysis-workflow`.

## [0.3.25-m3-global-metrics-backtest-optimization] - 2026-02-16

### Added

- New global metrics series in `/api/v2/metrics`:
  - `refactor_backtest_jobs_total{status=...}`
  - `refactor_optimization_jobs_total{status=...}`
- New tests:
  - global metrics endpoint includes backtest and optimization status counts

### Changed

- Global metrics endpoint now aggregates additional status gauges from:
  - `backtest_jobs`
  - `optimization_jobs`
- Backend app version bumped to `0.3.25-m3-global-metrics-backtest-optimization`.

## [0.3.24-m3-global-metrics-endpoint] - 2026-02-16

### Added

- New global metrics API:
  - `GET /api/v2/metrics`
- New tests:
  - global metrics endpoint includes prompt lock metrics and build info

### Changed

- Global metrics API now returns Prometheus text format with:
  - backend build info metric
  - prompt lock overview metrics export payload
- Backend app version bumped to `0.3.24-m3-global-metrics-endpoint`.

## [0.3.23-m3-prompt-lock-overview-prometheus-export] - 2026-02-16

### Added

- New Prometheus export API:
  - `GET /api/v2/prompt-lock/overview/metrics/prometheus`
- New tests:
  - service-level Prometheus metrics text generation
  - Prometheus metrics endpoint text response

### Changed

- `PromptLockAuditService` now supports Prometheus text export for overview metrics counters/gauges.
- Prometheus series includes:
  - overview request/degraded/cache-hit counters
  - overview degraded/cache-hit rate gauges
  - per-module (`summary/grouped/trends`) counters and rate gauges
- Backend app version bumped to `0.3.23-m3-prompt-lock-overview-prometheus-export`.

## [0.3.22-m3-prompt-lock-overview-metrics] - 2026-02-16

### Added

- New overview metrics API:
  - `GET /api/v2/prompt-lock/overview/metrics`
- New tests:
  - overview metrics track timeout/degrade/cache-hit counters
  - overview metrics endpoint returns current counters

### Changed

- `PromptLockAuditService` now records in-memory overview runtime metrics:
  - request total
  - degraded total
  - cache-hit total
  - per-module counters (`summary/grouped/trends`) including timeout/exception/degraded stats
- Overview metrics API returns computed rates:
  - `degraded_rate`
  - `cache_hit_rate`
  - module `timeout_rate` / `error_rate` / `degraded_rate`
- Backend app version bumped to `0.3.22-m3-prompt-lock-overview-metrics`.

## [0.3.21-m3-prompt-lock-overview-module-timeouts] - 2026-02-16

### Added

- New tests:
  - overview parallel timeout supports module override
  - settings env read for per-module timeout overrides
- New runtime settings:
  - `PROMPT_LOCK_OVERVIEW_TIMEOUT_SUMMARY_SEC`
  - `PROMPT_LOCK_OVERVIEW_TIMEOUT_GROUPED_SEC`
  - `PROMPT_LOCK_OVERVIEW_TIMEOUT_TRENDS_SEC`

### Changed

- `PromptLockAuditService.build_overview(...)` now supports module-specific timeout override in parallel aggregation.
- Timeout resolution order:
  - module-specific timeout (`summary/grouped/trends`)
  - fallback to global timeout (`PROMPT_LOCK_OVERVIEW_MODULE_TIMEOUT_SEC`)
- App startup now injects module-specific timeout overrides from settings.
- Backend app version bumped to `0.3.21-m3-prompt-lock-overview-module-timeouts`.

## [0.3.20-m3-prompt-lock-overview-timeout-degrade] - 2026-02-16

### Added

- New tests:
  - overview parallel timeout degrades module and skips cache
  - settings env read for overview module timeout
- New runtime setting:
  - `PROMPT_LOCK_OVERVIEW_MODULE_TIMEOUT_SEC`

### Changed

- `PromptLockAuditService.build_overview(...)` now supports per-module timeout degrade in parallel aggregation.
- Timeout/exception module now returns empty module payload with metadata:
  - `degraded`
  - `module_errors[]`
- Degraded overview responses are not cached.
- App startup now injects overview module timeout config from settings.
- Backend app version bumped to `0.3.20-m3-prompt-lock-overview-timeout-degrade`.

## [0.3.19-m3-prompt-lock-overview-cache-config] - 2026-02-16

### Added

- New tests:
  - overview cache TTL expiration
  - overview cache max-size eviction
  - settings env read for overview cache config
- New runtime settings:
  - `PROMPT_LOCK_OVERVIEW_CACHE_TTL_SEC`
  - `PROMPT_LOCK_OVERVIEW_CACHE_MAX_SIZE`

### Changed

- `PromptLockAuditService` overview cache now supports TTL-based expiration and configurable max size.
- App startup now injects prompt lock overview cache config from settings.
- Backend app version bumped to `0.3.19-m3-prompt-lock-overview-cache-config`.

## [0.3.18-m3-prompt-lock-overview-parallel] - 2026-02-16

### Added

- New tests:
  - overview runs selected modules in parallel

### Changed

- `PromptLockAuditService.build_overview(...)` now parallelizes multi-module aggregation (`summary/grouped/trends`) using thread pool.
- Single-module overview requests still use sequential execution path.
- Backend app version bumped to `0.3.18-m3-prompt-lock-overview-parallel`.

## [0.3.17-m3-prompt-lock-overview-cache] - 2026-02-16

### Added

- Prompt lock overview in-memory cache:
  - repeated requests with same params reuse cached overview aggregation result
- New tests:
  - overview cache hit and invalidation after new prompt lock event

### Changed

- `PromptLockAuditService.build_overview(...)` now uses param-keyed in-memory cache.
- `PromptLockAuditService.record_event(...)` now invalidates overview cache after write.
- Backend app version bumped to `0.3.17-m3-prompt-lock-overview-cache`.

## [0.3.16-m3-prompt-lock-overview-include-switch] - 2026-02-16

### Added

- Prompt lock overview include switch:
  - `GET /api/v2/prompt-lock/overview` supports `include` modules
  - allowed modules: `summary`, `grouped`, `trends`
- New tests:
  - overview include modules returns only requested sections
  - invalid include module validation

### Changed

- `PromptLockAuditService.build_overview(...)` now supports selective module aggregation.
- Backend app version bumped to `0.3.16-m3-prompt-lock-overview-include-switch`.

## [0.3.15-m3-prompt-lock-overview-composite] - 2026-02-16

### Added

- Prompt lock governance overview API:
  - `GET /api/v2/prompt-lock/overview`
- Overview response combines:
  - `summary`
  - `grouped`
  - `trends`
- New tests:
  - overview endpoint aggregates summary/grouped/trends in one request

### Changed

- `PromptLockAuditService` now provides `build_overview(...)` composite aggregation.
- Backend app version bumped to `0.3.15-m3-prompt-lock-overview-composite`.

## [0.3.14-m3-prompt-lock-trends-reason-topn] - 2026-02-16

### Added

- Prompt lock trend reason top-N option:
  - `GET /api/v2/prompt-lock/failures/trends` supports `reason_top_n`
  - available when `split_by=reason`
- New tests:
  - trend reason top-N truncation

### Changed

- `PromptLockAuditService.failure_trends` now returns `reason_top_n` and applies per-bucket truncation for reason split.
- Backend app version bumped to `0.3.14-m3-prompt-lock-trends-reason-topn`.

## [0.3.13-m3-prompt-lock-trends-reason-split] - 2026-02-16

### Added

- Prompt lock trend split option:
  - `GET /api/v2/prompt-lock/failures/trends` supports `split_by=reason`
- Trend bucket reason breakdown output:
  - `reason_counts[]` in each bucket when `split_by=reason`
- New tests:
  - trend API reason split aggregation
  - invalid `split_by` validation

### Changed

- `PromptLockAuditService.failure_trends` now supports optional reason-level split stats.
- Backend app version bumped to `0.3.13-m3-prompt-lock-trends-reason-split`.

## [0.3.12-m3-prompt-lock-failure-trends] - 2026-02-16

### Added

- Prompt lock failure trend API:
  - `GET /api/v2/prompt-lock/failures/trends`
- Trend granularity:
  - `hour`
  - `day`
- Optional filters:
  - `last_hours`
  - `start_at`
  - `end_at`
- New tests:
  - hour-level trend bucket aggregation
  - day-level trend bucket aggregation with time range
  - invalid granularity validation

### Changed

- `PromptLockAuditService` now supports trend aggregation with event/failure counts per time bucket.
- Backend app version bumped to `0.3.12-m3-prompt-lock-failure-trends`.

## [0.3.11-m3-prompt-lock-grouped-aggregation] - 2026-02-16

### Added

- Prompt lock grouped failure aggregation API:
  - `GET /api/v2/prompt-lock/failures/grouped`
- Grouping dimensions:
  - `flow_id`
  - `source_type`
  - `reason`
- Optional filters:
  - `last_hours`
  - `start_at`
  - `end_at`
- New tests:
  - grouped aggregation by dimensions and counts
  - grouped aggregation with absolute time range
  - invalid `group_by` validation

### Changed

- `PromptLockAuditService` now supports grouped failure statistics output.
- Backend app version bumped to `0.3.11-m3-prompt-lock-grouped-aggregation`.

## [0.3.10-m3-prompt-lock-absolute-time-range] - 2026-02-16

### Added

- Prompt lock audit absolute time-range filters:
  - `GET /api/v2/prompt-lock/events` supports `start_at` and `end_at`
  - `GET /api/v2/prompt-lock/failures/summary` supports `start_at` and `end_at`
- Range validation:
  - when `start_at > end_at`, both APIs return `400`
- New tests:
  - events API absolute range filtering
  - summary API absolute range filtering
  - invalid range rejection for both APIs

### Changed

- `PromptLockAuditService` now supports merged lower-bound filtering from `last_hours` and `start_at`.
- Backend app version bumped to `0.3.10-m3-prompt-lock-absolute-time-range`.

## [0.3.9-m3-prompt-lock-time-window] - 2026-02-16

### Added

- Prompt lock audit time-window filters:
  - `GET /api/v2/prompt-lock/events` supports `last_hours`
  - `GET /api/v2/prompt-lock/failures/summary` supports `last_hours`
- New tests:
  - events API filters results by `last_hours`
  - summary API aggregates only events within `last_hours`

### Changed

- `PromptLockAuditService.list_events` and `summarize_failures` now support time-window filtering.
- Backend app version bumped to `0.3.9-m3-prompt-lock-time-window`.

## [0.3.8-m3-prompt-lock-audit] - 2026-02-16

### Added

- Prompt lock audit persistence and query APIs:
  - `GET /api/v2/prompt-lock/events`
  - `GET /api/v2/prompt-lock/failures/summary`
- New persistence table:
  - `prompt_lock_events`
- New audit service:
  - `PromptLockAuditService` for event recording, listing, and failure reason aggregation
- New tests:
  - chat strict lock failure is recorded and queryable
  - summary API aggregates strict lock failure reasons

### Changed

- chat strict lock failures now emit audit events with `source_type=chat`.
- analysis strict lock failures now emit audit events with `source_type=analysis`.
- Backend app version bumped to `0.3.8-m3-prompt-lock-audit`.

## [0.3.7-m3-prompt-lock-hardening] - 2026-02-16

### Added

- Shared prompt lock routing helper module:
  - `PromptLockError` with structured detail payload
  - reusable prompt ref parsing and lock-mode resolution functions
- Analysis flow prompt lock support:
  - analysis now resolves strategy `prompt_refs` with `strict/lenient` policy
  - analysis result meta includes resolved `prompt_ref`
  - strict lock failure persists structured error into analysis job result
- New tests:
  - chat strict mode returns structured lock failure detail
  - analysis strict mode fails when bound prompt version is unavailable
  - analysis binding-level lenient mode overrides global strict mode

### Changed

- chat route now maps `PromptLockError` to structured HTTP `409` detail.
- Prompt lock behavior is now aligned between chat and analysis flows.
- Backend app version bumped to `0.3.7-m3-prompt-lock-hardening`.

## [0.3.6-m3-prompt-lock-mode] - 2026-02-16

### Added

- Prompt ref lock mode support (`strict` / `lenient`):
  - new runtime setting `PROMPT_REF_LOCK_MODE` (default `lenient`)
  - strategy bind API supports per-binding override `prompt_lock_mode`
- Prompt rendering by explicit version:
  - `PromptService.render_prompt_version(prompt_id, version, variables)`
- New tests:
  - strict mode rejects unresolved bound prompt version
  - binding-level lenient mode overrides global strict mode

### Changed

- `ChatService` now resolves strategy `prompt_refs` with lock mode policy:
  - `strict`: bound refs must resolve, otherwise request returns conflict
  - `lenient`: try bound version, then fallback to active/default/builtin
- chat route now maps prompt lock runtime conflict to HTTP `409`.
- `strategy_bindings` query payload now includes `prompt_lock_mode`.
- Backend app version bumped to `0.3.6-m3-prompt-lock-mode`.

## [0.3.5-m3-strategy-prompt-routing] - 2026-02-16

### Added

- Strategy-driven chat prompt routing:
  - chat flow now tries active strategy binding `prompt_refs` first
  - if strategy prompt is unavailable, falls back to `prompt.chat.reply`
  - if both are unavailable, falls back to builtin prompt
- New test:
  - active strategy binding prompt_ref overrides default chat prompt

### Changed

- `ChatService` prompt resolution now supports candidate prompt list from strategy binding context.
- Backend app version bumped to `0.3.5-m3-strategy-prompt-routing`.

## [0.3.4-m3-strategy-context-injection] - 2026-02-16

### Added

- Strategy context injection runtime behavior:
  - analysis execution writes active strategy binding context into `result.report.meta.strategy_context`
  - chat execution writes active strategy binding context into assistant `tool_trace`
- Strategy binding resolve method:
  - `StrategyService.resolve_active_binding(flow_id, symbol, report_type)`
  - supports MVP scope matching (`global`, `symbols`, `report_type`)
- New tests:
  - analysis result includes active strategy binding context
  - chat trace includes active strategy binding context

### Changed

- `AnalysisService` now resolves active strategy binding for `stock_analysis_v1`.
- `ChatService` now resolves active strategy binding for `chat_reply_v1`.
- Backend app version bumped to `0.3.4-m3-strategy-context-injection`.

## [0.3.3-m3-strategy-binding-loop] - 2026-02-16

### Added

- Strategy binding core APIs:
  - `POST /api/v2/strategy/{strategy_id}/bind`
  - `GET /api/v2/strategy/bindings`
- New SQLite persistence table:
  - `strategy_bindings`
- New strategy binding behavior:
  - only active strategy can be bound
  - single active binding per flow (rebind deactivates previous binding)
- New tests:
  - bind active strategy and query bindings
  - reject bind for non-active strategy
  - rebind same flow deactivates previous binding

### Changed

- `StrategyService` now includes binding management methods.

## [0.3.2-m3-cognition-strategy-loop] - 2026-02-16

### Added

- Strategy domain core APIs:
  - `POST /api/v2/strategy/cognition/distill`
  - `POST /api/v2/strategy/cognition/{memo_id}/review`
  - `POST /api/v2/strategy/extract`
  - `GET /api/v2/strategy/versions`
  - `POST /api/v2/strategy/{strategy_id}/publish`
  - `POST /api/v2/strategy/{strategy_id}/rollback`
- New domain service:
  - `StrategyService` for cognition memo distillation, review/indexing, strategy extraction, version lifecycle
- New SQLite persistence tables:
  - `cognition_memos`
  - `strategy_artifacts`
- New tests:
  - cognition distill and approve-to-knowledge flow
  - strategy extract and versions listing
  - publish gate + rollback workflow

### Changed

- Strategy service wired into app dependencies and router.
- Backend app version bumped to `0.3.2-m3-cognition-strategy-loop`.

## [0.3.1-m3-feedback-optimization-trigger] - 2026-02-16

### Added

- Feedback collection core APIs:
  - `POST /api/v2/feedback/records`
  - `GET /api/v2/feedback/records`
- Optimization trigger and proposal review APIs:
  - `POST /api/v2/optimization/jobs/trigger`
  - `POST /api/v2/optimization/proposals`
  - `POST /api/v2/optimization/proposals/{proposal_id}/approve`
  - `POST /api/v2/optimization/proposals/{proposal_id}/reject`
- New domain services:
  - `FeedbackService` for feedback persistence and snapshot features
  - `OptimizationService` for trigger job execution and proposal lifecycle
- New SQLite persistence tables:
  - `feedback_records`
  - `optimization_jobs`
  - `change_proposals`
- New tests:
  - feedback create/list flow
  - optimization trigger consuming feedback + backtest features
  - chatbot proposal approve/reject flow with conflict handling

### Changed

- API router, dependency wiring, and app state now include feedback/optimization services.
- Backend app version bumped to `0.3.1-m3-feedback-optimization-trigger`.

## [0.3.0-m3-backtest-core-loop] - 2026-02-16

### Added

- Backtest domain core loop:
  - `BacktestService` with job submission, execution, result query, and performance aggregation
  - deterministic evaluation core to keep M3-1 closed-loop reproducible in current refactor stage
- New SQLite persistence tables:
  - `backtest_jobs`
  - `backtest_records`
- New Backtest APIs:
  - `POST /api/v2/backtest/jobs`
  - `GET /api/v2/backtest/jobs/{job_id}`
  - `GET /api/v2/backtest/results`
  - `GET /api/v2/backtest/performance`
  - `GET /api/v2/backtest/performance/{symbol}`
- New unit tests:
  - backtest lifecycle and query endpoints
  - symbol-scope filtering
  - incompatible report fallback to `insufficient_data`

### Changed

- API router and dependency wiring now include `backtest_service`.
- Backend app version bumped to `0.3.0-m3-backtest-core-loop`.

## [0.2.9-m2-circuit-breaker] - 2026-02-15

### Added

- LLM circuit breaker wrapper `CircuitBreakerLLMProvider`:
  - opens when retryable provider failures reach threshold
  - returns structured provider error `category=circuit_open`, `error_code=CircuitOpen`
  - recovers automatically after reset timeout
- Runtime configs:
  - `LLM_CIRCUIT_FAILURE_THRESHOLD`
  - `LLM_CIRCUIT_RESET_TIMEOUT_MS`
- New tests:
  - circuit opens after consecutive retryable failures
  - circuit recovers after timeout
  - chat route maps `circuit_open` to HTTP `503`
  - env parsing for new circuit settings

### Changed

- `create_llm_provider(...)` now supports circuit breaker settings and composes wrappers as:
  - base provider -> retry wrapper (optional) -> circuit breaker wrapper (optional)
- Chat API now maps:
  - `rate_limit` -> `429`
  - `circuit_open` -> `503`
  - other provider errors -> `502`
- Smoke script env whitelist now includes circuit breaker keys.
- Backend app version bumped to `0.2.9-m2-circuit-breaker`.

## [0.2.8-m2-llm-reliability] - 2026-02-15

### Added

- LLM reliability wrapper `RetryingLLMProvider`:
  - retries only when `LLMProviderError.retryable == true`
  - exponential backoff with jitter
- Runtime configs:
  - `LLM_MAX_RETRIES`
  - `LLM_RETRY_BACKOFF_MS`
- New tests for retry behavior and settings env parsing:
  - retry succeeds after transient errors
  - non-retryable errors do not retry

### Changed

- `create_llm_provider(...)` now supports retry settings.
- App initialization now injects retry settings into provider construction.

## [0.2.7-m2-dashscope-error-layering] - 2026-02-15

### Added

- Structured provider exception type `LLMProviderError` with fields:
  - `provider`, `status_code`, `error_code`, `error_message`
  - `category`, `retryable`
- DashScope error classification mapping:
  - `rate_limit`, `upstream`, `auth`, `model_config`, `invalid_request`, `unknown`
- Chat API error mapping for provider failures:
  - returns structured detail with category/retryable/provider error code
  - maps rate-limit category to HTTP `429`, otherwise HTTP `502`
- New tests:
  - DashScope error layering in `test_llm_provider.py`
  - Chat error mapping in `test_chat_service.py`

### Changed

- Real smoke validation is now stable with whitelist env loader and passed against DashScope.

## [0.2.6-m2-env-key-normalization] - 2026-02-15

### Changed

- Refactor backend runtime env keys are now non-prefixed (no `REF_` namespace), including:
  - `DATABASE_URL`, `QUEUE_AUTO_PROCESS`
  - `CHROMA_PATH`, `CHROMA_COLLECTION`, `MEMORY_COLLECTION`
  - `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_TIMEOUT_SEC`
  - `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_HTTP_API_URL`, `DASHSCOPE_ENABLE_THINKING`
  - `ENABLE_REAL_LLM_SMOKE`
- `smoke-real-llm.sh` now uses `ENABLE_REAL_LLM_SMOKE`.
- `smoke-real-llm.sh` now loads only a whitelist of backend env keys instead of `source`-executing the whole `.env`.
- Backend README and `.env.example` were updated to use non-prefixed env keys only.
- Backend app version bumped to `0.2.6-m2-env-key-normalization`.

## [0.2.5-m2-dashscope-provider] - 2026-02-15

### Added

- DashScope SDK provider implementation:
  - `provider_name=dashscope` / `dashscope-sdk`
  - uses `dashscope.Generation.call(...)` with configurable `enable_thinking`
- New runtime config for DashScope:
  - `REF_DASHSCOPE_API_KEY`
  - `REF_DASHSCOPE_BASE_HTTP_API_URL`
  - `REF_DASHSCOPE_ENABLE_THINKING`
- Unit tests for DashScope provider creation and request payload behavior.
- Refactor backend `.env.example` section with `REF_*` variables to avoid mixing old project env keys.

### Changed

- `create_llm_provider(...)` now supports DashScope-specific arguments.
- App wiring now injects DashScope config from settings.
- Backend app version bumped to `0.2.5-m2-dashscope-provider`.

## [0.2.4-m2-real-smoke] - 2026-02-15

### Added

- Real LLM integration smoke test:
  - `tests/integration/test_real_llm_smoke.py`
- Smoke runner script:
  - `refactor/backend/scripts/smoke-real-llm.sh`
  - loads `refactor/backend/.env` by default and runs smoke with `REF_ENABLE_REAL_LLM_SMOKE=1`

### Changed

- Smoke runner now strips CRLF when loading `.env` to avoid shell parsing errors.
- Backend README updated with real smoke execution instructions.

## [0.2.3-m2-llm-provider] - 2026-02-15

### Added

- OpenAI-compatible provider implementation in `app/llm/provider.py`.
- Runtime config for real provider connection:
  - `REF_LLM_API_KEY`
  - `REF_LLM_BASE_URL`
  - `REF_LLM_TIMEOUT_SEC`
- Unit tests for provider factory and HTTP payload behavior:
  - `test_llm_provider.py`

### Changed

- `create_llm_provider(...)` now supports provider-specific parameters while keeping mock default path.
- App initialization now injects `api_key/base_url/timeout` into provider construction.
- Backend app version bumped to `0.2.3-m2-llm-provider`.

## [0.2.2-m2-prompt-llm] - 2026-02-15

### Added

- LLM provider abstraction and mock provider implementation.
- Chat prompt-version binding to Prompt Center active template `prompt.chat.reply`.
- Trace fields in chat assistant message:
  - `prompt_ref`
  - `llm_provider`
  - `llm_model`
- Regression test for prompt binding:
  - `test_chat_prompt_binding.py`

### Changed

- `ChatService` now follows flow:
  - resolve active prompt -> render variables -> provider generate reply.
- Added runtime config:
  - `REF_LLM_PROVIDER`
  - `REF_LLM_MODEL`
- Fallback prompt path retained as `builtin.chat.reply@0` when no active prompt.

## [0.2.1-m2-phase2] - 2026-02-14

### Added

- Chat APIs for multi-turn interaction:
  - `POST /api/v2/chat/sessions`
  - `POST /api/v2/chat/sessions/{session_id}/messages`
  - `GET /api/v2/chat/sessions/{session_id}/messages`
- Memory APIs:
  - `GET /api/v2/memory/sessions/{session_id}`
  - `POST /api/v2/memory/sessions/{session_id}/summarize`
  - `POST /api/v2/memory/search`
  - `DELETE /api/v2/memory/sessions/{session_id}`
- `MemoryService` and `ChatService` with SQLite persistence.
- Chroma long-term memory collection adapter (`MemoryVectorStore`).
- Unit tests for chat RAG citation flow and memory summarize/search/delete flow.

### Changed

- SQLite schema extended with conversation and memory tables.
- Backend runtime config adds `REF_MEMORY_COLLECTION`.
- OpenAPI draft upgraded to M2 phase-2.

## [0.2.0-m2-phase1] - 2026-02-14

### Added

- Knowledge service minimum loop:
  - `POST /api/v2/knowledge/documents/upload`
  - `POST /api/v2/knowledge/documents/{doc_id}/optimize`
  - `POST /api/v2/knowledge/documents/{doc_id}/ingest`
  - `GET /api/v2/knowledge/documents/{doc_id}`
  - `GET /api/v2/knowledge/chunks/search`
  - `DELETE /api/v2/knowledge/documents/{doc_id}`
- Markdown processing pipeline (normalize, deterministic chunking, chunk summary).
- Chroma vector indexing adapter with deterministic local embeddings.
- SQLite metadata tables for knowledge documents/chunks.
- Unit tests for upload -> ingest -> search and delete cleanup paths.

### Changed

- Backend app version bumped to `0.2.0-m2-phase1`.
- OpenAPI draft updated with knowledge APIs and schemas.
- Backend runtime config now supports `REF_CHROMA_PATH` and `REF_CHROMA_COLLECTION`.

## [0.1.1-m1-persistence] - 2026-02-14

### Added

- SQLite persistence infrastructure:
  - `analysis_jobs`
  - `workflow_executions`
  - `workflow_trace_nodes`
  - `prompt_templates`
  - `prompt_versions`
  - `task_queue`
- Persistent task queue service (`analysis.run`, `workflow.run`) with status transitions.
- Unit tests for persistence across app restarts and queue table durability.

### Changed

- Replaced in-memory `AnalysisService` / `WorkflowService` / `PromptService` with SQLite-backed implementations.
- `create_app()` now bootstraps DB schema and injects persistent queue/service dependencies.
- Flake8 config aligned with black by ignoring `E203`.

## [0.1.0-m1] - 2026-02-14

### Added

- Workflow execution APIs with in-memory lifecycle and node trace:
  - `POST /api/v2/workflows/executions`
  - `GET /api/v2/workflows/executions/{execution_id}`
  - `POST /api/v2/workflows/executions/{execution_id}/cancel`
- Analysis job APIs connected to workflow trace:
  - `POST /api/v2/analysis/jobs`
  - `GET /api/v2/jobs/{job_id}`
- Prompt center baseline APIs:
  - `POST /api/v2/prompts/templates`
  - `POST /api/v2/prompts/templates/{prompt_id}/versions`
  - `POST /api/v2/prompts/templates/{prompt_id}/versions/{version}/publish`
  - `POST /api/v2/prompts/templates/{prompt_id}/rollback`
  - `GET /api/v2/prompts/templates/{prompt_id}`
- OpenAPI draft updated to M1 scope in `refactor/docs/07-OpenAPI-v2-接口草案.yaml`.

### Changed

- Backend app version bumped from `0.1.0-m0` to `0.1.0-m1`.
- Backend README updated with M1 API surface.

## [0.1.0-m0] - 2026-02-13

### Added

- Initial backend and frontend scaffold in `refactor/`.
- Health endpoint `GET /api/v2/health`.
- Basic error code and logging conventions.
- CI baseline script for format, lint, and tests.
