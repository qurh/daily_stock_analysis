# Changelog

All notable changes for the refactor project are documented in this file.

## [0.3.108-m3-threshold-sync-module-summary] - 2026-02-19

### Added

- JSON summary output now includes module-level change stats:
  - `modules.strict.changed_alerts_count`
  - `modules.governance.changed_alerts_count`
  - `modules.soft_audit.changed_alerts_count`
- Per-file JSON summary entries now also expose module-level counts.
- New tests:
  - verifies JSON summary includes module fields
  - verifies governance-only config change is attributed to governance module

### Changed

- Text summary output now prints a module aggregate line.
- README now documents module counters in JSON summary mode.
- Backend app version bumped to `0.3.108-m3-threshold-sync-module-summary`.

## [0.3.107-m3-threshold-sync-summary-json] - 2026-02-19

### Added

- `sync-strict-gate-alert-thresholds.py` now supports summary format selection:
  - `--summary-format text|json`
  - `json` mode emits a machine-readable summary object for CI consumption
- New tests:
  - verifies `--summary-only --summary-format json` output structure
  - verifies `--summary-format` requires `--summary-only`

### Changed

- README now includes JSON summary mode example.
- Backend app version bumped to `0.3.107-m3-threshold-sync-summary-json`.

## [0.3.106-m3-threshold-sync-summary-only] - 2026-02-19

### Added

- `sync-strict-gate-alert-thresholds.py` now supports compact summary mode:
  - `--summary-only` (requires `--dry-run`)
  - prints per-file and total `+/-` line summary without full patch body
- New tests:
  - verifies summary-only outputs compact summary and hides full unified diff
  - verifies summary-only requires dry-run

### Changed

- README now includes summary-only usage example.
- Backend app version bumped to `0.3.106-m3-threshold-sync-summary-only`.

## [0.3.105-m3-threshold-sync-dry-run-diff] - 2026-02-19

### Added

- `sync-strict-gate-alert-thresholds.py` now supports dry-run mode:
  - `--dry-run` prints unified diffs without writing files
  - `--check --dry-run` prints diffs and still fails when out of sync
- New tests:
  - verifies dry-run outputs unified diff and does not mutate rule files
  - verifies check + dry-run fails when config and rules are out of sync

### Changed

- README now documents `--dry-run` usage examples.
- Backend app version bumped to `0.3.105-m3-threshold-sync-dry-run-diff`.

## [0.3.104-m3-governance-threshold-param-sync] - 2026-02-19

### Added

- Threshold config now also includes threshold-governance alert profile fields:
  - `governance_warn_for`
  - `governance_warn_severity`
  - `governance_critical_for`
  - `governance_critical_severity`
  - `governance_normalization_for`
  - `governance_normalization_severity`

### Changed

- `sync-strict-gate-alert-thresholds.py` now syncs threshold-governance alert `for` and `severity` values from config.
- Backend app version bumped to `0.3.104-m3-governance-threshold-param-sync`.

## [0.3.103-m3-threshold-config-schema-validation] - 2026-02-19

### Added

- `sync-strict-gate-alert-thresholds.py` now supports custom config input:
  - `--config <path>`
- New config schema validation rules:
  - duration fields must match `^[1-9][0-9]*(ms|s|m|h|d|w|y)$`
  - severity fields must be one of `info|warning|critical`
  - ratio fields must be in `[0, 1]`
  - `critical_ratio` must be greater than or equal to `warn_ratio`
  - `min_hits` must be greater than `0`
- New tests for invalid config rejection:
  - invalid duration format
  - invalid severity enum
  - out-of-range ratio
  - invalid ratio relation (`critical_ratio < warn_ratio`)

### Changed

- README now documents threshold config schema constraints and `--config` usage.
- Backend app version bumped to `0.3.103-m3-threshold-config-schema-validation`.

## [0.3.102-m3-soft-audit-threshold-param-sync] - 2026-02-19

### Added

- Strict gate threshold config now also includes soft-audit alert profile fields:
  - `soft_audit_max_lines_for`
  - `soft_audit_max_lines_severity`
  - `soft_audit_max_bytes_for`
  - `soft_audit_max_bytes_severity`
  - `soft_audit_rotation_unbounded_for`
  - `soft_audit_rotation_unbounded_severity`

### Changed

- `sync-strict-gate-alert-thresholds.py` now syncs soft-audit alert `for` and `severity` values from config.
- Backend app version bumped to `0.3.102-m3-soft-audit-threshold-param-sync`.

## [0.3.101-m3-strict-gate-threshold-profile-sync] - 2026-02-19

### Added

- Strict gate threshold sync script now supports profile-only execution:
  - `--profile default|dev|staging|prod`
  - repeatable for multi-profile execution
- New tests:
  - verifies profile check mode passes (`--check --profile dev`)
  - verifies unknown profile is rejected by CLI validation

### Changed

- README now documents profile-only sync/check examples.
- Backend app version bumped to `0.3.101-m3-strict-gate-threshold-profile-sync`.

## [0.3.100-m3-strict-gate-threshold-param-sync] - 2026-02-19

### Added

- New strict gate alert threshold config:
  - `refactor/backend/config/strict-gate-alert-thresholds.json`
- New threshold sync script:
  - `refactor/backend/scripts/sync-strict-gate-alert-thresholds.py`
  - supports `--check` mode for drift detection
- New tests:
  - verifies strict gate threshold config has required profile keys
  - verifies sync script check mode passes in current repository state

### Changed

- Backend CI script now runs strict gate threshold sync drift check before Prometheus rule checks.
- README now documents strict gate threshold config and sync command.
- Backend app version bumped to `0.3.100-m3-strict-gate-threshold-param-sync`.

## [0.3.99-m3-strict-gate-alert-runbook] - 2026-02-19

### Added

- New strict gate alert runbook:
  - `refactor/docs/runbooks/2026-02-19-strict-gate-alert-runbook.md`
- Runbook now covers:
  - trigger semantics and severity interpretation
  - PromQL and SQLite diagnostics
  - fast mitigation, permanent fix, rollback, and postmortem checklist

### Changed

- Backend README now links strict gate alert runbook under Prometheus alert rule section.
- Backend app version bumped to `0.3.99-m3-strict-gate-alert-runbook`.

## [0.3.98-m3-strict-publish-gate-alert-rules] - 2026-02-19

### Added

- New Prometheus alert rules for strict publish gate block ratio:
  - `RefactorStrategyPublishStrictGateBlockRatioWarn`
  - `RefactorStrategyPublishStrictGateBlockRatioCritical`
- Added rules to all profile templates:
  - `monitoring/prometheus/rules/refactor-threshold-governance-alerts.yml`
  - `monitoring/prometheus/rules/refactor-threshold-governance-alerts.dev.yml`
  - `monitoring/prometheus/rules/refactor-threshold-governance-alerts.staging.yml`
  - `monitoring/prometheus/rules/refactor-threshold-governance-alerts.prod.yml`
- New tests:
  - verifies base alert rule template includes strict gate alerts and expressions
  - verifies profile templates include strict gate alerts and profile thresholds

### Changed

- Prometheus rule template baseline count increased from six to eight.
- Backend app version bumped to `0.3.98-m3-strict-publish-gate-alert-rules`.

## [0.3.97-m3-strict-publish-gate-metrics] - 2026-02-19

### Added

- New strict publish gate audit table:
  - `strategy_publish_gate_events`
- New global metrics for strict publish gate `STR-GATE-009`:
  - `refactor_strategy_publish_strict_gate_hits_total`
  - `refactor_strategy_publish_strict_gate_blocked_total`
  - `refactor_strategy_publish_strict_gate_block_ratio`
- New tests:
  - verifies strict mode publish attempts persist gate audit events (`blocked` + `passed`)
  - verifies `/api/v2/metrics` exports strict gate hit/block/ratio series

### Changed

- `StrategyService.publish_strategy` now records strict gate evaluation events when strict mode is enabled.
- Backend app version bumped to `0.3.97-m3-strict-publish-gate-metrics`.

## [0.3.96-m3-publish-strict-proposal-mode] - 2026-02-19

### Added

- New strict publish mode switch:
  - `STRATEGY_PUBLISH_REQUIRE_PROPOSAL_ID=true`
  - when enabled, strategy publish requires explicit `proposal_id`
  - missing `proposal_id` is blocked with `STR-GATE-009`
- New tests:
  - verifies strict mode blocks publish without `proposal_id`
  - verifies strict mode allows publish after linked proposal approval

### Changed

- `StrategyPublishRequest` now carries `proposal_id` and publish route applies runtime strict-mode setting.
- `StrategyService.publish_strategy` now supports strict proposal-id requirement flag.
- Backend settings add `strategy_publish_require_proposal_id`.
- Backend app version bumped to `0.3.96-m3-publish-strict-proposal-mode`.

## [0.3.95-m3-explicit-proposal-publish-bind] - 2026-02-19

### Added

- Strategy publish API now supports explicit proposal binding:
  - `POST /api/v2/strategy/{strategy_id}/publish` accepts optional `proposal_id`
  - when provided, proposal must:
    - exist
    - be linked to current strategy (`diff.strategy_id == strategy_id`)
    - be in `approved` status
  - otherwise publish is blocked with:
    - `STR-GATE-007` (proposal not approved)
    - `STR-GATE-008` (proposal not linked to strategy)
- New tests:
  - verifies mismatched explicit `proposal_id` is rejected
  - verifies explicit proposal requires approval before publish
  - M3 acceptance rehearsal loop now publishes with explicit `proposal_id`

### Changed

- `StrategyService.publish_strategy` now accepts `proposal_id` and validates explicit proposal linkage.
- Backend app version bumped to `0.3.95-m3-explicit-proposal-publish-bind`.

## [0.3.94-m3-proposal-target-enum-api] - 2026-02-19

### Added

- API-level proposal target enum contract for `POST /api/v2/optimization/proposals`:
  - `prompt.chat.reply`
  - `workflow.stock.analysis`
  - `strategy.analysis.lifecycle`
- New OpenAPI contract test:
  - verifies proposal target enum is exposed in OpenAPI schema
- New API validation expectation test:
  - verifies unsupported target is rejected at request-validation layer (`422`)

### Changed

- `OptimizationProposalCreateRequest.target` now uses enum type in API model.
- `OptimizationService` target classifier now uses explicit whitelist mapping aligned with API enum.
- Backend app version bumped to `0.3.94-m3-proposal-target-enum-api`.

## [0.3.93-m3-proposal-target-schema] - 2026-02-19

### Added

- New proposal target namespace gate:
  - proposal target must be under `prompt.*`, `workflow.*`, or `strategy.*`
  - unsupported namespace is rejected with `400` (`FDB-INPUT-003`)
- New per-target diff schema gate:
  - `prompt.*` requires `diff.prompt_patch` (`FDB-INPUT-005`)
  - `workflow.*` requires `diff.flow_patch` (`FDB-INPUT-004`)
  - `strategy.*` requires `diff.strategy_id` (`FDB-INPUT-002`)
- New tests:
  - verifies unsupported target namespace is rejected
  - verifies workflow proposal without `flow_patch` is rejected
  - verifies prompt proposal without `prompt_patch` is rejected

### Changed

- `OptimizationService.create_proposal` now classifies proposal target and applies target-specific diff validation.
- Backend app version bumped to `0.3.93-m3-proposal-target-schema`.

## [0.3.92-m3-chatbot-proposal-schema-gate] - 2026-02-19

### Added

- New proposal schema gate for chatbot strategy lifecycle proposals:
  - when `source=chatbot` and `target` starts with `strategy.`,
    proposal `diff` must include `strategy_id`
  - missing linkage now returns `400` with `FDB-INPUT-002`
- New tests:
  - verifies chatbot strategy proposal is rejected when `diff.strategy_id` is missing
  - verifies same proposal passes when `strategy_id` is present

### Changed

- `OptimizationService.create_proposal` now normalizes linked `strategy_id` before persistence.
- Backend app version bumped to `0.3.92-m3-chatbot-proposal-schema-gate`.

## [0.3.91-m3-chatbot-proposal-publish-gate] - 2026-02-19

### Added

- New strategy publish gate for linked chatbot proposals:
  - when a linked chatbot proposal exists (`diff.strategy_id == strategy_id`),
    `POST /api/v2/strategy/{strategy_id}/publish` requires latest proposal status `approved`
  - otherwise publish is blocked with `STR-GATE-006`
- New tests:
  - verifies strategy publish is blocked when linked chatbot proposal is still `review_pending`
  - verifies publish succeeds after linked chatbot proposal approval
  - verifies M3 acceptance rehearsal loop remains passing with approved proposal flow

### Changed

- `StrategyService.publish_strategy` now includes chatbot proposal gate metadata in `gate_result`:
  - `proposal_id`
  - `proposal_source`
  - `proposal_status`
- Backend app version bumped to `0.3.91-m3-chatbot-proposal-publish-gate`.

## [0.3.90-m3-feedback-event-auto-trigger] - 2026-02-19

### Added

- Event-driven optimization auto-trigger path on feedback record API:
  - `POST /api/v2/feedback/records` now returns `optimization_trigger`.
  - when enabled, feedback writes can automatically create `event` optimization jobs.
- New optimization trigger controls in backend settings:
  - `FEEDBACK_EVENT_OPTIMIZATION_ENABLED`
  - `FEEDBACK_EVENT_OPTIMIZATION_MIN_RECORDS`
  - `FEEDBACK_EVENT_OPTIMIZATION_COOLDOWN_SECONDS`
- New tests:
  - verifies feedback API auto-triggers event optimization after threshold is met
  - verifies settings loader reads feedback event trigger env vars

### Changed

- `OptimizationService` adds cooldown/threshold aware feedback-event trigger method.
- Backend app version bumped to `0.3.90-m3-feedback-event-auto-trigger`.

## [0.3.89-m3-soft-audit-alert-rules] - 2026-02-19

### Added

- New Prometheus alert rules for promtool soft audit rotation governance:
  - `RefactorPromtoolSoftAuditMaxLinesExceeded`
  - `RefactorPromtoolSoftAuditMaxBytesExceeded`
  - `RefactorPromtoolSoftAuditRotationUnbounded`
- Added the three alert rules to profile templates:
  - `refactor-threshold-governance-alerts.dev.yml`
  - `refactor-threshold-governance-alerts.staging.yml`
  - `refactor-threshold-governance-alerts.prod.yml`
- New tests:
  - verifies base alert template includes soft audit rotation governance rules and expressions
  - verifies dev/staging/prod profile templates include the new soft audit rules

### Changed

- `README` Prometheus rule template section now documents six baseline rules.
- Backend app version bumped to `0.3.89-m3-soft-audit-alert-rules`.

## [0.3.88-m3-promtool-audit-rotation-metrics] - 2026-02-19

### Added

- New global metrics for promtool soft audit rotation visibility:
  - `refactor_promtool_remote_soft_fallback_audit_file_line_count`
  - `refactor_promtool_remote_soft_fallback_audit_file_size_bytes`
  - `refactor_promtool_remote_soft_fallback_audit_config_max_lines`
  - `refactor_promtool_remote_soft_fallback_audit_config_max_bytes`
  - `refactor_promtool_remote_soft_fallback_audit_config_retention_days`
- New tests:
  - verifies `/api/v2/metrics` includes audit file footprint + rotation config gauges
  - verifies settings loader reads rotation config env vars

### Changed

- `AppSettings` now includes:
  - `promtool_remote_soft_audit_max_lines`
  - `promtool_remote_soft_audit_max_bytes`
  - `promtool_remote_soft_audit_retention_days`
- `/api/v2/metrics` soft audit loader now reports file line count/size and configured rotation thresholds.
- Backend app version bumped to `0.3.88-m3-promtool-audit-rotation-metrics`.

## [0.3.87-m3-promtool-retention-fallback] - 2026-02-19

### Added

- New fallback test for retention-days prune when python interpreters are unavailable:
  - verifies retention pruning still works via `date` fallback path

### Changed

- `validate-promtool-installer-config.sh` retention-days prune now:
  - tries python (`python3`/`python`) first
  - falls back to `date -d` (GNU) and `date -v` (BSD) when python is missing or execution fails
  - avoids hard failure when python binary exists but returns non-zero
- Backend app version bumped to `0.3.87-m3-promtool-retention-fallback`.

## [0.3.86-m3-promtool-soft-audit-rotation] - 2026-02-19

### Added

- New composite rotation controls for promtool soft-mode audit file:
  - `PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES` (`0` disables byte trimming)
  - `PROMTOOL_REMOTE_SOFT_AUDIT_RETENTION_DAYS` (`0` disables age-based prune)
- New tests:
  - verifies soft audit file trims to max bytes
  - verifies soft audit file prunes records by retention days
  - verifies invalid `PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES` fails validation

### Changed

- `validate-promtool-installer-config.sh` now applies composite soft audit rotation in order:
  - retention-days prune
  - max-lines trim
  - max-bytes trim
- Backend app version bumped to `0.3.86-m3-promtool-soft-audit-rotation`.

## [0.3.85-m3-promtool-soft-audit-retention] - 2026-02-19

### Added

- New retention control for promtool soft-mode audit file:
  - `PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES` (`0` disables trimming)
- New tests:
  - verifies audit file is trimmed to configured max retained lines
  - verifies invalid `PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES` value fails validation

### Changed

- `validate-promtool-installer-config.sh` now validates `PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES` and trims audit file after soft-mode append when configured.
- Backend app version bumped to `0.3.85-m3-promtool-soft-audit-retention`.

## [0.3.84-m3-promtool-soft-audit-metrics] - 2026-02-19

### Added

- New global metrics series for promtool soft fallback audit integration:
  - `refactor_promtool_remote_soft_fallback_audit_enabled`
  - `refactor_promtool_remote_soft_fallback_audit_events_total`
  - `refactor_promtool_remote_soft_fallback_audit_read_error`
  - `refactor_promtool_remote_soft_fallback_audit_last_seen_unixtime`
- New tests:
  - verifies `/api/v2/metrics` exports promtool soft fallback audit counters
  - verifies settings loader reads `PROMTOOL_REMOTE_SOFT_AUDIT_FILE`

### Changed

- `AppSettings` now includes `promtool_remote_soft_audit_file` sourced from `PROMTOOL_REMOTE_SOFT_AUDIT_FILE`.
- `/api/v2/metrics` now parses configured soft audit file and exports audit count/health gauge lines.
- Backend app version bumped to `0.3.84-m3-promtool-soft-audit-metrics`.

## [0.3.83-m3-promtool-soft-mode-audit] - 2026-02-19

### Added

- New soft-mode observability outputs for remote checksum validation:
  - metric-style stderr log: `remote_soft_fallback_total=1`
  - optional audit sink: `PROMTOOL_REMOTE_SOFT_AUDIT_FILE`
- New tests:
  - verifies soft fallback emits metric log
  - verifies soft fallback writes audit record when audit file is configured

### Changed

- `validate-promtool-installer-config.sh` now tracks remote validation failure reason and includes it in soft-mode logs/audit records.
- Backend app version bumped to `0.3.83-m3-promtool-soft-mode-audit`.

## [0.3.82-m3-promtool-workflow-explicit-strict-mode] - 2026-02-19

### Added

- New workflow-level gate-mode lock assertions in CI tests:
  - verifies active/example workflows explicitly set `PROMTOOL_VALIDATE_REMOTE_MODE: "strict"`

### Changed

- `.github/workflows/refactor-backend-ci.yml` now explicitly sets `PROMTOOL_VALIDATE_REMOTE_MODE: "strict"` in backend quality gate step.
- `refactor/backend/ci/github-actions/refactor-backend-ci.example.yml` now explicitly sets `PROMTOOL_VALIDATE_REMOTE_MODE: "strict"`.
- Backend app version bumped to `0.3.82-m3-promtool-workflow-explicit-strict-mode`.

## [0.3.81-m3-promtool-remote-gate-mode] - 2026-02-19

### Added

- New gate mode switch for remote checksum linkage validation:
  - `PROMTOOL_VALIDATE_REMOTE_MODE=strict|soft`
- New tests:
  - verifies `soft` mode does not block when remote checksum validation fails
  - verifies invalid mode value fails with explicit validation error

### Changed

- `validate-promtool-installer-config.sh` now applies remote validation mode:
  - `strict` keeps hard-fail behavior
  - `soft` logs remote validation failure and continues
- Backend app version bumped to `0.3.81-m3-promtool-remote-gate-mode`.

## [0.3.80-m3-promtool-remote-metadata-cache] - 2026-02-19

### Added

- New optional metadata cache controls for remote checksum linkage validation:
  - `PROMTOOL_REMOTE_FETCH_CACHE_FILE`
  - `PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS`
- New tests:
  - verifies fresh cache skips remote fetch
  - verifies stale cache refreshes from remote and updates cache metadata

### Changed

- `validate-promtool-installer-config.sh` now reuses fresh local `sha256sums` cache and refreshes stale cache after successful remote fetch.
- Backend app version bumped to `0.3.80-m3-promtool-remote-metadata-cache`.

## [0.3.79-m3-promtool-remote-fetch-hardening] - 2026-02-19

### Added

- New remote fetch hardening options for promtool checksum linkage validation:
  - `PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS`
  - `PROMTOOL_REMOTE_FETCH_CONNECT_TIMEOUT_SECONDS`
  - `PROMTOOL_REMOTE_FETCH_TIMEOUT_SECONDS`
  - `PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS`
- New tests:
  - verifies remote checksum fetch retries and succeeds after transient failure
  - verifies remote checksum fetch fails after max-attempt budget

### Changed

- `validate-promtool-installer-config.sh` now retries remote `sha256sums.txt` fetches with configurable timeout and delay.
- Backend app version bumped to `0.3.79-m3-promtool-remote-fetch-hardening`.

## [0.3.78-m3-promtool-config-remote-check] - 2026-02-19

### Added

- New optional remote linkage validation in promtool installer config checker:
  - validates configured checksums against release `sha256sums.txt`
  - supports custom source via `PROMTOOL_SHA256SUMS_URL`
- New tests:
  - verifies remote checksum validation passes on aligned data
  - verifies remote checksum validation fails on mismatch
  - verifies GitHub Actions workflows enable `PROMTOOL_VALIDATE_REMOTE=1`

### Changed

- `.github/workflows/refactor-backend-ci.yml` and example workflow now enable remote config linkage validation by default.
- Backend app version bumped to `0.3.78-m3-promtool-config-remote-check`.

## [0.3.77-m3-promtool-installer-config-validation] - 2026-02-19

### Added

- New config validation script for promtool installer defaults:
  - `refactor/backend/scripts/validate-promtool-installer-config.sh`
- New tests:
  - verifies `ci.sh` invokes promtool installer config validation
  - verifies config validation passes with default config
  - verifies config validation fails for invalid checksum format

### Changed

- `refactor/backend/scripts/ci.sh` now runs promtool installer config validation before Prometheus rule checks.
- Backend app version bumped to `0.3.77-m3-promtool-installer-config-validation`.

## [0.3.76-m3-promtool-installer-centralized-config] - 2026-02-19

### Added

- New centralized config file for promtool installer:
  - `refactor/backend/config/promtool-installer.defaults`
  - contains pinned promtool version and per-platform checksum defaults
- New tests:
  - verifies config file exists with pinned defaults
  - verifies installer script reads centralized config
  - verifies CI workflows no longer hardcode `PROMTOOL_VERSION` / `PROMTOOL_SHA256`

### Changed

- `install-promtool.sh` now sources centralized config and resolves defaults from it.
- Backend app version bumped to `0.3.76-m3-promtool-installer-centralized-config`.

## [0.3.75-m3-promtool-installer-dryrun-smoke] - 2026-02-19

### Added

- New script-level smoke support in promtool installer:
  - `PROMTOOL_DRY_RUN=1` skips download/install after resolving platform
  - `PROMTOOL_MACHINE_ARCH` allows explicit arch override for testing
- New tests:
  - verifies dry-run auto-detects `x86_64` to `linux-amd64`
  - verifies dry-run auto-detects `arm64` to `linux-arm64`
  - verifies unsupported architecture fails with explicit error

### Changed

- `install-promtool.sh` now includes default checksum mapping for both `linux-amd64` and `linux-arm64`.
- Backend app version bumped to `0.3.75-m3-promtool-installer-dryrun-smoke`.

## [0.3.74-m3-promtool-installer-multi-arch] - 2026-02-19

### Added

- New multi-arch auto-detection in promtool installer script:
  - maps `x86_64/amd64` -> `linux-amd64`
  - maps `aarch64/arm64` -> `linux-arm64`
  - fails fast on unsupported machine architectures
- New tests:
  - verifies installer script includes multi-arch detection logic

### Changed

- `install-promtool.sh` now auto-detects architecture when `PROMTOOL_PLATFORM` is not explicitly set.
- Backend app version bumped to `0.3.74-m3-promtool-installer-multi-arch`.

## [0.3.73-m3-promtool-installer-script-reuse] - 2026-02-19

### Added

- New reusable promtool installer script:
  - `refactor/backend/scripts/install-promtool.sh`
- New tests:
  - verifies installer script exists and includes version pin + checksum verification flow

### Changed

- Backend CI workflows now call the shared installer script instead of duplicating inline installation commands.
- Backend app version bumped to `0.3.73-m3-promtool-installer-script-reuse`.

## [0.3.72-m3-promtool-checksum-verification] - 2026-02-19

### Added

- New checksum verification for promtool archive in backend CI workflows:
  - `.github/workflows/refactor-backend-ci.yml`
  - `refactor/backend/ci/github-actions/refactor-backend-ci.example.yml`
- New tests:
  - verifies workflows include pinned SHA256 and `sha256sum -c -` verification

### Changed

- Backend CI now validates archive integrity before extracting and installing promtool.
- Backend app version bumped to `0.3.72-m3-promtool-checksum-verification`.

## [0.3.71-m3-promtool-fixed-version-workflow] - 2026-02-19

### Added

- New fixed-version promtool install flow in backend CI workflows:
  - `.github/workflows/refactor-backend-ci.yml`
  - `refactor/backend/ci/github-actions/refactor-backend-ci.example.yml`
- New tests:
  - verifies workflows pin promtool version and use official release download flow instead of apt package install

### Changed

- Promtool installation in backend CI now downloads a pinned release tarball (`v2.52.0`) for better reproducibility.
- Backend app version bumped to `0.3.71-m3-promtool-fixed-version-workflow`.

## [0.3.70-m3-refactor-backend-github-actions-workflow] - 2026-02-19

### Added

- New active GitHub Actions workflow for refactor backend quality gate:
  - `.github/workflows/refactor-backend-ci.yml`
- New tests:
  - verifies root workflow exists and includes backend-path filters, promtool installation, and `scripts/ci.sh` execution

### Changed

- `README` now documents both active workflow and template paths.
- Backend app version bumped to `0.3.70-m3-refactor-backend-github-actions-workflow`.

## [0.3.69-m3-github-actions-promtool-ci-template] - 2026-02-19

### Added

- New GitHub Actions CI template for `refactor/backend`:
  - `refactor/backend/ci/github-actions/refactor-backend-ci.example.yml`
- New tests:
  - verifies CI template includes promtool installation and `scripts/ci.sh` execution

### Changed

- `README` now documents where to find and how to use the GitHub Actions CI template.
- Backend app version bumped to `0.3.69-m3-github-actions-promtool-ci-template`.

## [0.3.68-m3-promtool-rules-summary-and-bash3-compat] - 2026-02-19

### Added

- New output summary for Prometheus rule checks:
  - `check-prometheus-rules.sh` now prints validated rule file count on success.
- New tests:
  - checker script emits validated rules summary when rule checks succeed

### Changed

- `check-prometheus-rules.sh` no longer relies on `mapfile`, improving compatibility with `bash 3.2` environments.
- Backend app version bumped to `0.3.68-m3-promtool-rules-summary-and-bash3-compat`.

## [0.3.67-m3-ci-default-promtool-strict] - 2026-02-18

### Added

- New CI default behavior:
  - `scripts/ci.sh` sets `PROMTOOL_REQUIRED=1` when `CI` env is present (unless already overridden).
- New tests:
  - ci script contains CI-aware strict mode setup for Prometheus rule checks

### Changed

- CI pipeline now enforces stricter Prometheus rule validation by default.
- Backend app version bumped to `0.3.67-m3-ci-default-promtool-strict`.

## [0.3.66-m3-promtool-strict-mode] - 2026-02-18

### Added

- New strict-mode behavior for Prometheus rule checker:
  - `PROMTOOL_REQUIRED=1` makes `check-prometheus-rules.sh` fail when `promtool` is missing.
- New tests:
  - strict mode fails when promtool binary is unavailable

### Changed

- `check-prometheus-rules.sh` now supports optional strict mode while preserving default skip behavior for local environments.
- Backend app version bumped to `0.3.66-m3-promtool-strict-mode`.

## [0.3.65-m3-promtool-rules-check-script] - 2026-02-18

### Added

- New script for Prometheus rule validation:
  - `refactor/backend/scripts/check-prometheus-rules.sh`
- New tests:
  - ci script invokes Prometheus rules check

### Changed

- `refactor/backend/scripts/ci.sh` now runs `./scripts/check-prometheus-rules.sh`.
- Rule validation supports `PROMTOOL_BIN` override and skips gracefully when `promtool` is not installed.
- Backend app version bumped to `0.3.65-m3-promtool-rules-check-script`.

## [0.3.64-m3-threshold-governance-alert-profiles] - 2026-02-18

### Added

- New environment-tiered Prometheus alert templates:
  - `refactor/backend/monitoring/prometheus/rules/refactor-threshold-governance-alerts.dev.yml`
  - `refactor/backend/monitoring/prometheus/rules/refactor-threshold-governance-alerts.staging.yml`
  - `refactor/backend/monitoring/prometheus/rules/refactor-threshold-governance-alerts.prod.yml`
- New tests:
  - threshold governance alert rule profile templates exist

### Changed

- Profile-specific durations and severities are now preconfigured for dev/staging/prod alert sensitivity.
- Backend app version bumped to `0.3.64-m3-threshold-governance-alert-profiles`.

## [0.3.63-m3-threshold-governance-alert-template] - 2026-02-18

### Added

- New Prometheus alert rule template file:
  - `refactor/backend/monitoring/prometheus/rules/refactor-threshold-governance-alerts.yml`
- New baseline alert rules:
  - `RefactorThresholdGovernanceWarn`
  - `RefactorThresholdGovernanceCritical`
  - `RefactorThresholdGovernanceNormalizationApplied`
- New tests:
  - threshold governance alert rule template exists with required alerts and expressions

### Changed

- README now documents alert template path and `promtool check rules` validation command.
- Backend app version bumped to `0.3.63-m3-threshold-governance-alert-template`.

## [0.3.62-m3-governance-ratio-normalization-flags] - 2026-02-18

### Added

- New governance ratio normalization flag metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_warn_ratio_normalized`
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_critical_ratio_normalized`
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_ratio_normalization_applied`
- New tests:
  - settings loader exposes governance ratio normalization flags
  - global metrics endpoint includes governance ratio normalization flags

### Changed

- Settings now track whether governance warn/critical ratio values were normalized.
- Governance ratio normalization states are exported for observability and alert governance debugging.
- Backend app version bumped to `0.3.62-m3-governance-ratio-normalization-flags`.

## [0.3.61-m3-governance-threshold-ratio-config] - 2026-02-18

### Added

- New configurable env vars for threshold-governance ratios:
  - `BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_WARN_RATIO`
  - `BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_CRITICAL_RATIO`
- New governance ratio metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_warn_ratio`
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_critical_ratio`
- New tests:
  - settings loader reads and normalizes governance ratio env vars
  - global metrics endpoint governance levels support env ratio overrides

### Changed

- Threshold-governance level computation now uses runtime-configured warn/critical ratios from settings.
- Governance critical ratio is normalized to be no smaller than warn ratio.
- Backend app version bumped to `0.3.61-m3-governance-threshold-ratio-config`.

## [0.3.60-m3-global-metrics-threshold-governance-level] - 2026-02-18

### Added

- New threshold governance metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_level{level=none|warn|critical}`
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_level_score`
- New tests:
  - global metrics endpoint includes threshold governance alert levels and score

### Changed

- Metrics snapshot now derives threshold-governance alert level from mismatch ratio:
  - `none` when ratio < 0.25
  - `warn` when ratio >= 0.25 and < 0.5
  - `critical` when ratio >= 0.5
- Backend app version bumped to `0.3.60-m3-global-metrics-threshold-governance-level`.

## [0.3.59-m3-global-metrics-threshold-dimensions-constant] - 2026-02-18

### Added

- New tests:
  - global metrics endpoint threshold dimensions total metric is validated against module constant

### Changed

- Replaced threshold mismatch ratio denominator magic number with unified module constant:
  - `app.api.routes.metrics.MULTI_WINDOW_ALERT_THRESHOLD_DIMENSIONS_TOTAL`
- Backend app version bumped to `0.3.59-m3-global-metrics-threshold-dimensions-constant`.

## [0.3.58-m3-global-metrics-threshold-dimensions-total] - 2026-02-18

### Added

- New threshold dimensions total metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_dimensions_total`
- New tests:
  - global metrics endpoint includes threshold dimensions total

### Changed

- Mismatch ratio denominator semantics are now explicitly observable through dedicated dimensions-total metric.
- Backend app version bumped to `0.3.58-m3-global-metrics-threshold-dimensions-total`.

## [0.3.57-m3-global-metrics-threshold-mismatch-ratio] - 2026-02-18

### Added

- New threshold mismatch ratio metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_raw_normalized_mismatch_ratio`
- New tests:
  - global metrics endpoint includes raw-normalized mismatch ratio

### Changed

- Metrics snapshot now exposes mismatch ratio (`mismatch_count / 4`) for raw-vs-normalized threshold governance.
- Backend app version bumped to `0.3.57-m3-global-metrics-threshold-mismatch-ratio`.

## [0.3.56-m3-global-metrics-threshold-mismatch-count] - 2026-02-18

### Added

- New threshold mismatch aggregate metric in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_raw_normalized_mismatch_count`
- New tests:
  - global metrics endpoint includes raw-normalized mismatch count

### Changed

- Metrics snapshot now aggregates raw-vs-normalized threshold mismatch count across all four threshold dimensions.
- Backend app version bumped to `0.3.56-m3-global-metrics-threshold-mismatch-count`.

## [0.3.55-m3-global-metrics-alert-threshold-raw-values] - 2026-02-17

### Added

- New raw threshold metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_warn_low_windows_threshold_raw`
  - `refactor_backtest_records_return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold_raw`
  - `refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold_raw`
  - `refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_raw`
- New tests:
  - global metrics endpoint includes raw multi-window alert thresholds
  - settings loader exposes raw threshold values

### Changed

- Settings now preserve configured raw threshold values alongside normalized effective thresholds.
- Backend app version bumped to `0.3.55-m3-global-metrics-alert-threshold-raw-values`.

## [0.3.54-m3-global-metrics-alert-threshold-normalization-flags] - 2026-02-17

### Added

- New normalization flag metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_threshold_normalization_applied`
  - `refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold_normalized`
  - `refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_normalized`
- New tests:
  - global metrics endpoint includes multi-window alert threshold normalization flags

### Changed

- Metrics layer now exposes whether threshold normalization was applied, improving configuration auditability.
- Backend app version bumped to `0.3.54-m3-global-metrics-alert-threshold-normalization-flags`.

## [0.3.53-m3-global-metrics-alert-threshold-observability] - 2026-02-17

### Added

- New normalized threshold metrics in `/api/v2/metrics`:
  - `refactor_backtest_records_return_sample_multi_window_alert_warn_low_windows_threshold`
  - `refactor_backtest_records_return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold`
  - `refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold`
  - `refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold`
- New tests:
  - global metrics endpoint includes normalized multi-window alert thresholds

### Changed

- Multi-window alert threshold observability now exposes effective (normalized) runtime values for governance and audit.
- Backend app version bumped to `0.3.53-m3-global-metrics-alert-threshold-observability`.

## [0.3.52-m3-global-metrics-alert-threshold-validation] - 2026-02-17

### Added

- New threshold validation behavior for multi-window alert settings:
  - `critical` thresholds are normalized to be no smaller than corresponding `warn` thresholds.
- New tests:
  - settings loader normalizes multi-window alert threshold relationship

### Changed

- Settings loader now applies non-negative and ordering constraints for multi-window alert thresholds.
- Backend app version bumped to `0.3.52-m3-global-metrics-alert-threshold-validation`.

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
