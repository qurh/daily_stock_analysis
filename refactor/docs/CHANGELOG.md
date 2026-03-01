# Changelog

All notable changes for the refactor project are documented in this file.

## [0.4.43-m4-overrides-quality-policy-alertmanager] - 2026-03-01

### Added

- Added `alertmanager_route_consistency` metadata override quality-policy test:
  - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
  - test: `test_alertmanager_route_consistency_metadata_overrides_quality_policy`
  - validates fixed severity mapping for all 13 codes (`warning/error/critical`)
  - requires each remediation to include rerun guidance

### Changed

- Updated `alertmanager_route_consistency` remediations to satisfy rerun-guidance policy for:
  - `alertmanager_route_consistency_file_not_found`
  - `alertmanager_route_consistency_no_rule_files`
  - `alertmanager_route_consistency_no_alerts`
  - `alertmanager_route_consistency_shadowed_route`
  - `alertmanager_route_consistency_unmatched_alert`
  - `alertmanager_route_consistency_ambiguous_alert`
- Synced generated catalog after metadata override text update:
  - `refactor/backend/config/validator-error-codes.json`
- README metadata override section now documents `alertmanager_route_consistency` quality policy.
- Backend app version bumped to `0.4.43-m4-overrides-quality-policy-alertmanager`.
- Summary schema version: `1`

## [0.4.42-m4-overrides-quality-policy-reuse] - 2026-03-01

### Added

- Added reusable metadata overrides quality-policy assertion helper:
  - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
  - helper: `_assert_metadata_overrides_group_quality_policy(...)`
- Added `notification_retry_runbook` group quality-policy test:
  - `test_notification_retry_runbook_metadata_overrides_quality_policy`
  - validates fixed severity mapping and rerun-guidance remediation across all 5 codes

### Changed

- Updated `notification_retry_runbook_file_not_found` remediation to include rerun guidance:
  - `refactor/backend/config/validator-error-code-metadata-overrides.json`
- Synced generated catalog after metadata override text update:
  - `refactor/backend/config/validator-error-codes.json`
- README metadata override section now documents `notification_retry_runbook` quality policy.
- Backend app version bumped to `0.4.42-m4-overrides-quality-policy-reuse`.
- Summary schema version: `1`

## [0.4.41-m4-error-context-overrides-quality-policy] - 2026-02-20

### Added

- Added `error_context_high_frequency` metadata override quality-policy guard:
  - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
  - validates fixed severity mapping for all 8 codes
  - requires each remediation to include rerun guidance

### Changed

- Updated `error_context_high_frequency` remediations to satisfy rerun-guidance policy for:
  - `error_context_high_frequency_schema_file_not_found`
  - `error_context_high_frequency_samples_file_not_found`
  - `error_context_high_frequency_schema_invalid`
  - `error_context_high_frequency_sample_schema_validation_failed`
- README metadata override section now documents this quality policy.
- Backend app version bumped to `0.4.41-m4-error-context-overrides-quality-policy`.
- Summary schema version: `1`

## [0.4.40-m4-error-context-overrides-full-coverage] - 2026-02-20

### Added

- Full metadata overrides default policy coverage for `error_context_high_frequency` group:
  - `refactor/backend/config/validator-error-code-metadata-overrides.json`
  - newly added codes:
    - `error_context_high_frequency_schema_file_not_found`
    - `error_context_high_frequency_samples_file_not_found`
    - `error_context_high_frequency_json_parse_error`
    - `error_context_high_frequency_schema_invalid`
    - `error_context_high_frequency_samples_payload_invalid`
    - `error_context_high_frequency_sample_schema_validation_failed`
  - combined with existing:
    - `error_context_high_frequency_cli_args_invalid`
    - `error_context_high_frequency_unexpected_error`
- Expanded metadata overrides coverage assertion:
  - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
  - `error_context_high_frequency` now requires full 8-code subset coverage

### Changed

- README metadata overrides section now states full default policy coverage for all `error_context_high_frequency_*` codes.
- Backend app version bumped to `0.4.40-m4-error-context-overrides-full-coverage`.
- Summary schema version: `1`

## [0.4.39-m4-error-context-overrides-default-policy] - 2026-02-20

### Added

- Metadata overrides default policies for high-frequency context validator:
  - `refactor/backend/config/validator-error-code-metadata-overrides.json`
  - added:
    - `error_context_high_frequency_cli_args_invalid`
    - `error_context_high_frequency_unexpected_error`
- Expanded metadata overrides coverage assertion:
  - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
  - now requires `error_context_high_frequency` group in overrides config
  - validates the two default policy codes above are present

### Changed

- README metadata overrides section now documents default policy coverage for the two `error_context_high_frequency_*` codes.
- Backend app version bumped to `0.4.39-m4-error-context-overrides-default-policy`.
- Summary schema version: `1`

## [0.4.38-m4-error-context-catalog-sync] - 2026-02-20

### Added

- Error-code catalog group integration for high-frequency context validator:
  - `error_context_high_frequency` group added to:
    - `refactor/backend/config/validator-error-codes.json`
    - `refactor/backend/config/schemas/validator-error-codes.schema.json`
- `sync-validator-error-codes.py` now includes:
  - `validate-validator-error-context-high-frequency-schema.py`
  - in `VALIDATOR_SCRIPT_FILES` group mapping for catalog sync generation
- Expanded sync/catalog coverage tests:
  - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
  - validates:
    - catalog contains `error_context_high_frequency`
    - schema required groups include `error_context_high_frequency`
    - catalog json-output groups include `error_context_high_frequency`
    - all new script error codes are covered by catalog entries

### Changed

- README catalog groups list now includes `error_context_high_frequency`.
- Backend app version bumped to `0.4.38-m4-error-context-catalog-sync`.
- Summary schema version: `1`

## [0.4.37-m4-validator-error-context-schema-validator] - 2026-02-20

### Added

- New validator script for high-frequency error context contract:
  - `refactor/backend/scripts/validate-validator-error-context-high-frequency-schema.py`
  - validates:
    - `validator-error-context-high-frequency.schema.json` schema validity
    - sample payloads against the schema
  - supports:
    - `--json-errors`
    - `--json-output`
- New default sample payload file:
  - `refactor/backend/config/validator-error-context-high-frequency-samples.json`
- New unit test file:
  - `refactor/backend/tests/unit/test_validator_error_context_high_frequency_validator.py`
  - covers success/json-output/json-errors/validation-failure branches
- Expanded common validator contract coverage to include the new script:
  - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
  - added into shared success/CLI-failure/business-failure matrices

### Changed

- CI script now runs the new validator:
  - `refactor/backend/scripts/ci.sh`
- CI script contract test now asserts this invocation:
  - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
- README now documents new validator command and contracts.
- Backend app version bumped to `0.4.37-m4-validator-error-context-schema-validator`.
- Summary schema version: `1`

## [0.4.36-m4-validator-error-context-high-frequency-schema] - 2026-02-20

### Added

- New high-frequency validator error context sub-schema:
  - `refactor/backend/config/schemas/validator-error-context-high-frequency.schema.json`
  - defines code-specific `context` shape contracts for selected high-frequency business-failure errors
- Expanded shared validator contract tests:
  - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
  - new tests:
    - `test_validator_error_context_high_frequency_schema_exists_and_is_valid`
    - `test_validator_json_errors_high_frequency_context_contract`
  - validates 18 high-frequency business-failure payload samples against the new context sub-schema

### Changed

- README now documents high-frequency error context sub-schema path and scope.
- Backend app version bumped to `0.4.36-m4-validator-error-context-high-frequency-schema`.
- Summary schema version: `1`

## [0.4.35-m4-all-validator-business-failure-matrix] - 2026-02-20

### Added

- Expanded remaining validator business-failure matrix coverage:
  - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
  - new test:
    - `test_remaining_validator_scripts_json_errors_multi_business_failure_matrix`
  - covers remaining 5 validators with 10 business failure scenarios:
    - `validate-alertmanager-route-consistency.py`
    - `validate-notification-retry-runbook.py`
    - `validate-profile-suggestion-actions-schema.py`
    - `validate-validator-placeholder-markers.py`
    - `validate-validator-error-code-catalog.py`
  - each scenario validates:
    - payload matches validator error output base schema
    - exact `validator` and `code`
    - required `context` keys exist

### Changed

- README now documents that business-failure matrix tests cover all 9 validator scripts.
- Backend app version bumped to `0.4.35-m4-all-validator-business-failure-matrix`.
- Summary schema version: `1`

## [0.4.34-m4-key-validator-business-failure-matrix] - 2026-02-20

### Added

- Expanded key validator business-failure contract coverage:
  - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
  - new test:
    - `test_key_validator_scripts_json_errors_multi_business_failure_matrix`
  - covers 4 key validators with 8 business failure scenarios:
    - `validate-summary-contract-changelog.py`
    - `validate-strict-gate-summary-schema.py`
    - `validate-validator-error-code-metadata-lint.py`
    - `validate-validator-error-code-metadata-overrides.py`
  - each scenario validates:
    - error payload matches base schema
    - `validator` and `code` are exact-match
    - required `context` keys are present

### Changed

- `validate-strict-gate-summary-schema.py` now includes `context.validation_path`
  when raising `summary_schema_example_payload_schema_validation_failed`.
- README summary schema validator section now documents `context.validation_path`.
- Backend app version bumped to `0.4.34-m4-key-validator-business-failure-matrix`.
- Summary schema version: `1`

## [0.4.33-m4-validator-error-output-schema] - 2026-02-20

### Added

- New validator error output base schema:
  - `refactor/backend/config/schemas/validator-error-output.schema.json`
  - base contract:
    - `validator` must be non-empty string
    - `code` must be non-empty string
    - `message` must be non-empty string
    - `context` must be object
- Expanded shared validator contract tests:
  - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
  - new coverage:
    - `test_validator_error_output_schema_exists_and_is_valid`
    - `test_validator_scripts_json_errors_conform_base_contract_cli_failures`
    - `test_validator_scripts_json_errors_conform_base_contract_business_failures`
  - validates `--json-errors` payload base contract for all validator scripts in both:
    - CLI failure mode
    - representative business failure mode

### Changed

- README now documents validator error output base contract and schema path.
- Backend app version bumped to `0.4.33-m4-validator-error-output-schema`.
- Summary schema version: `1`

## [0.4.32-m4-validator-json-mode-business-failure-contract] - 2026-02-20

### Added

- Expanded combined JSON mode contract tests:
  - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
  - new business-failure matrix test with both flags enabled:
    - `test_validator_scripts_both_json_flags_business_failure_emit_structured_error`
  - for all validator scripts, verifies:
    - non-zero exit code on business failure
    - stdout remains empty
    - stderr contains structured JSON error
    - error code is not `*_cli_args_invalid` for business failures

### Changed

- README now clarifies combined JSON mode routing contract covers both CLI failures and business validation failures.
- Backend app version bumped to `0.4.32-m4-validator-json-mode-business-failure-contract`.
- Summary schema version: `1`

## [0.4.31-m4-validator-json-mode-contract] - 2026-02-20

### Added

- New combined JSON mode contract tests:
  - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
  - validates all validator scripts when both `--json-output` and `--json-errors` are provided
  - success branch contract:
    - exit code `0`
    - JSON success payload on stdout
    - stderr empty
  - failure branch contract (unknown args):
    - non-zero exit code
    - stdout empty
    - structured JSON error payload on stderr
    - `code` equals each validator's `*_cli_args_invalid`

### Changed

- README now documents combined JSON mode behavior contract.
- Backend app version bumped to `0.4.31-m4-validator-json-mode-contract`.
- Summary schema version: `1`

## [0.4.30-m4-validator-success-output-schema] - 2026-02-20

### Added

- New validator success output base schema:
  - `refactor/backend/config/schemas/validator-success-output.schema.json`
  - base contract:
    - `validator` must be non-empty string
    - `status` must be `ok`
- New shared contract test:
  - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
  - validates all validator `--json-output` payloads against the base schema
  - validates `validator` naming consistency for each validator script

### Changed

- README now documents the validator success output base contract schema and required fields.
- Backend app version bumped to `0.4.30-m4-validator-success-output-schema`.
- Summary schema version: `1`

## [0.4.29-m4-validator-json-output-phase2] - 2026-02-20

### Added

- `validate-alertmanager-route-consistency.py` now supports structured success output:
  - `--json-output`
  - payload fields:
    - `validator`, `status`, `rules_dir`, `alertmanager_file`
    - `alert_count`, `explicit_route_count`
- `validate-notification-retry-runbook.py` now supports structured success output:
  - `--json-output`
  - payload fields:
    - `validator`, `status`
    - `default_rule_file`, `dev_rule_file`, `staging_rule_file`, `prod_rule_file`
    - `runbook_file`, `profile_count`
- `validate-profile-suggestion-actions-schema.py` now supports structured success output:
  - `--json-output`
  - payload fields:
    - `validator`, `status`, `schema_file`, `example_file`, `helper_file`, `example_action_count`
- New validator success JSON output tests:
  - alertmanager route consistency success branch with `--json-output`
  - notification retry runbook success branch with `--json-output`
  - profile suggestion actions success branch with `--json-output`

### Changed

- README now documents these three validators' `--json-output` contracts.
- Backend app version bumped to `0.4.29-m4-validator-json-output-phase2`.
- Summary schema version: `1`

## [0.4.28-m4-summary-json-output] - 2026-02-20

### Added

- `validate-strict-gate-summary-schema.py` now supports structured success output:
  - `--json-output`
  - payload fields: `validator`, `status`, `schema_file`, `sync_script_file`, `example_file`, `schema_version`
- `validate-summary-contract-changelog.py` now supports structured success output:
  - `--json-output`
  - payload fields:
    - `validator`, `status`, `schema_file`, `changelog_file`, `app_file`
    - `app_version`, `schema_version`, `changelog_version`
- New summary validator success JSON output tests:
  - summary schema success branch with `--json-output`
  - summary contract success branch with `--json-output`

### Changed

- README now documents summary schema / summary contract validator `--json-output` success payload contracts.
- Backend app version bumped to `0.4.28-m4-summary-json-output`.
- Summary schema version: `1`

## [0.4.27-m4-placeholder-json-output] - 2026-02-20

### Added

- `validate-validator-placeholder-markers.py` now supports structured success output:
  - `--json-output`
  - payload fields: `validator`, `status`, `markers_file`, `schema_file`, `markers_count`
- New placeholder markers validator success JSON output test:
  - success branch with `--json-output`

### Changed

- README now documents placeholder markers validator `--json-output` success payload contract.
- Backend app version bumped to `0.4.27-m4-placeholder-json-output`.
- Summary schema version: `1`

## [0.4.26-m4-metadata-json-output] - 2026-02-20

### Added

- `validate-validator-error-code-metadata-lint.py` now supports structured success output:
  - `--json-output`
  - payload fields:
    - `validator`, `status`, `lint_config_file`, `schema_file`, `selected_profile`
    - `min_remediation_length`, `action_verbs_count`
- `validate-validator-error-code-metadata-overrides.py` now supports structured success output:
  - `--json-output`
  - payload fields:
    - `validator`, `status`, `overrides_file`, `schema_file`, `catalog_file`
    - `lint_config_file`, `placeholder_markers_file`
    - `requested_overrides_profile`, `requested_lint_profile`
    - `total_override_groups`, `total_override_codes`
- New success JSON output tests:
  - metadata lint success branch with `--json-output`
  - metadata overrides success branch with `--json-output`

### Changed

- README now documents metadata lint / metadata overrides `--json-output` success payload contracts.
- Backend app version bumped to `0.4.26-m4-metadata-json-output`.
- Summary schema version: `1`

## [0.4.25-m4-error-code-catalog-json-output] - 2026-02-20

### Added

- `validate-validator-error-code-catalog.py` now supports structured success output:
  - `--json-output`
  - payload fields: `validator`, `status`, `catalog_file`, `schema_file`, `groups`, `total_codes`
- New catalog validator success JSON output test:
  - success branch with `--json-output`

### Changed

- README now documents catalog validator `--json-output` success payload contract.
- Backend app version bumped to `0.4.25-m4-error-code-catalog-json-output`.
- Summary schema version: `1`

## [0.4.24-m4-metadata-overrides-cli-json-errors] - 2026-02-20

### Added

- `validate-validator-error-code-metadata-overrides.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `error_code_metadata_overrides_cli_args_invalid`
- New metadata overrides validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`

### Changed

- Metadata overrides validator argument parsing now uses custom parser error handling
  to normalize CLI failures into validator error-code contract.
- README now documents metadata overrides validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.24-m4-metadata-overrides-cli-json-errors`.
- Summary schema version: `1`

## [0.4.23-m4-metadata-lint-cli-json-errors] - 2026-02-20

### Added

- `validate-validator-error-code-metadata-lint.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `error_code_metadata_lint_cli_args_invalid`
- New metadata lint validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`

### Changed

- Metadata lint validator argument parsing now uses custom parser error handling
  to normalize CLI failures into validator error-code contract.
- README now documents metadata lint validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.23-m4-metadata-lint-cli-json-errors`.
- Summary schema version: `1`

## [0.4.22-m4-error-code-catalog-cli-json-errors] - 2026-02-20

### Added

- `validate-validator-error-code-catalog.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `error_code_catalog_cli_args_invalid`
- New catalog validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`

### Changed

- Catalog validator argument parsing now uses custom parser error handling
  to normalize CLI failures into validator error-code contract.
- README now documents catalog validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.22-m4-error-code-catalog-cli-json-errors`.
- Summary schema version: `1`

## [0.4.21-m4-placeholder-markers-cli-json-errors] - 2026-02-20

### Added

- `validate-validator-placeholder-markers.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `placeholder_markers_cli_args_invalid`
- New placeholder markers validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`
- Validator metadata/catalog now include `placeholder_markers_cli_args_invalid`.

### Changed

- Placeholder markers validator argument parsing now uses custom parser error handling
  to normalize CLI failures into validator error-code contract.
- README now documents placeholder markers validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.21-m4-placeholder-markers-cli-json-errors`.
- Summary schema version: `1`

## [0.4.20-m4-summary-schema-cli-json-errors] - 2026-02-20

### Added

- `validate-strict-gate-summary-schema.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `summary_schema_cli_args_invalid`
- New summary schema validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`
- Validator metadata/catalog now include `summary_schema_cli_args_invalid`.

### Changed

- Summary schema validator argument parsing now uses custom parser error handling
  to normalize CLI failures into validator error-code contract.
- README now documents summary schema validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.20-m4-summary-schema-cli-json-errors`.
- Summary schema version: `1`

## [0.4.19-m4-summary-contract-cli-json-errors] - 2026-02-20

### Added

- `validate-summary-contract-changelog.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `summary_contract_cli_args_invalid`
- New summary contract validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`
- Validator metadata/catalog now include `summary_contract_cli_args_invalid`.

### Changed

- Summary contract validator argument parsing now uses custom parser error handling
  to normalize CLI failures into validator error-code contract.
- README now documents summary contract validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.19-m4-summary-contract-cli-json-errors`.
- Summary schema version: `1`

## [0.4.18-m4-profile-suggestion-cli-json-errors] - 2026-02-20

### Added

- `validate-profile-suggestion-actions-schema.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `profile_suggestion_actions_cli_args_invalid`
- New profile suggestion schema validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`
- Validator metadata/catalog now include `profile_suggestion_actions_cli_args_invalid`.

### Changed

- Profile suggestion schema validator argument parsing now uses custom parser error handling
  to normalize CLI failures into validator error-code contract.
- README now documents profile suggestion validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.18-m4-profile-suggestion-cli-json-errors`.
- Summary schema version: `1`

## [0.4.17-m4-alertmanager-cli-json-errors] - 2026-02-20

### Added

- `validate-alertmanager-route-consistency.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `alertmanager_route_consistency_cli_args_invalid`
- New alertmanager validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`
- Validator metadata/catalog now include `alertmanager_route_consistency_cli_args_invalid`.

### Changed

- Alertmanager route consistency argument parsing now uses custom parser error handling
  to normalize CLI failures into validator error-code contract.
- README now documents alertmanager validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.17-m4-alertmanager-cli-json-errors`.
- Summary schema version: `1`

## [0.4.16-m4-notification-runbook-cli-json-errors] - 2026-02-20

### Added

- `validate-notification-retry-runbook.py` now returns structured JSON errors for CLI argument failures:
  - unknown arguments (`parse_known_args` unknown list)
  - argparse parse errors (such as missing option values)
  - code: `notification_retry_runbook_cli_args_invalid`
- New runbook validator JSON error tests:
  - unknown args with `--json-errors`
  - missing option value with `--json-errors`
- Validator metadata/catalog now include `notification_retry_runbook_cli_args_invalid`.

### Changed

- Runbook validator argument parsing now uses custom parser error handling to normalize CLI failures
  into validator error-code contract.
- README now documents runbook validator JSON error namespace and `cli_args_invalid`.
- Backend app version bumped to `0.4.16-m4-notification-runbook-cli-json-errors`.
- Summary schema version: `1`

## [0.4.15-m4-notification-runbook-json-error-catalog-sync] - 2026-02-20

### Added

- `validate-notification-retry-runbook.py` now exposes validator registry and structured JSON errors:
  - `VALIDATOR_ERROR_CODES` with `notification_retry_runbook_*` namespace
  - `--json-errors` payload contract: `{validator, code, message, context}`
  - typed validation errors for:
    - file not found
    - baseline parse failed
    - baseline mismatch
- New runbook validator JSON error test coverage:
  - mismatch branch with `--json-errors`
  - missing file branch with `--json-errors`
- Validator error-code governance now includes `notification_retry_runbook` group end-to-end:
  - `sync-validator-error-codes.py` registry adds `validate-notification-retry-runbook.py`
  - `validator-error-codes.json` includes all `notification_retry_runbook_*` entries
  - `validator-error-code-metadata-overrides.json` includes full default metadata for
    `notification_retry_runbook_*`

### Changed

- Validator error-code catalog schema now requires `notification_retry_runbook`.
- README now documents `validate-notification-retry-runbook.py --json-errors` and
  catalog/override inclusion for `notification_retry_runbook`.
- Backend app version bumped to `0.4.15-m4-notification-runbook-json-error-catalog-sync`.
- Summary schema version: `1`

## [0.4.14-m4-alertmanager-error-code-catalog-sync] - 2026-02-20

### Added

- Validator error-code governance now includes `alertmanager_route_consistency` group end-to-end:
  - `sync-validator-error-codes.py` registry adds `validate-alertmanager-route-consistency.py`
  - `validator-error-codes.json` now contains all `alertmanager_route_consistency_*` entries
  - `validator-error-code-metadata-overrides.json` now includes full default metadata for all
    `alertmanager_route_consistency_*` entries
- New catalog coverage test for alertmanager route consistency codes:
  - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`

### Changed

- Validator error-code catalog schema now requires:
  - `profile_suggestion_actions`
  - `alertmanager_route_consistency`
- README now documents alertmanager group inclusion in validator error-code catalog/overrides.
- Backend app version bumped to `0.4.14-m4-alertmanager-error-code-catalog-sync`.
- Summary schema version: `1`

## [0.4.13-m4-alertmanager-json-error-contract] - 2026-02-20

### Added

- `validate-alertmanager-route-consistency.py` now supports structured JSON error output:
  - `--json-errors`
  - payload contract: `{validator, code, message, context}`
- New JSON error coverage in route consistency tests:
  - unmatched alert with `--json-errors`
  - invalid regex matcher with `--json-errors`

### Changed

- Alertmanager route consistency validator now uses typed error codes for:
  - matcher format invalid
  - invalid regex matcher
  - no explicit routes / unmatched alerts / ambiguous alerts / shadowed routes
  - file or yaml loading failures
- README now documents `--json-errors` usage for alertmanager route consistency validation.
- Backend app version bumped to `0.4.13-m4-alertmanager-json-error-contract`.
- Summary schema version: `1`

## [0.4.12-m4-alertmanager-regex-matcher-support] - 2026-02-20

### Added

- Alertmanager route consistency tests now cover matcher operator expansion:
  - regex/non-regex matcher pass case (`=~`, `!~`)
  - invalid regex matcher failure case (`invalid regex`)

### Changed

- `validate-alertmanager-route-consistency.py` matcher parser now supports operators:
  - `=`
  - `!=`
  - `=~`
  - `!~`
- route matching and ambiguity/shadow checks now evaluate matcher operator semantics.
- README now documents matcher operator support in alertmanager route consistency validation.
- Backend app version bumped to `0.4.12-m4-alertmanager-regex-matcher-support`.
- Summary schema version: `1`

## [0.4.11-m4-alertmanager-route-shadow-guard] - 2026-02-20

### Added

- Alertmanager route consistency tests now cover static shadow route detection:
  - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
  - fails when a later sibling route is shadowed by an earlier non-`continue` route,
    even if no current alert hits that route

### Changed

- `validate-alertmanager-route-consistency.py` now enforces static sibling shadow guard:
  - if `route_i` matcher set is a subset of later `route_j` matcher set
  - and `route_i` has `continue=false`
  - then `route_j` is treated as shadowed and validation fails
- README now documents shadow route guard in alertmanager route guardrails.
- Backend app version bumped to `0.4.11-m4-alertmanager-route-shadow-guard`.
- Summary schema version: `1`

## [0.4.10-m4-alertmanager-route-ambiguity-guard] - 2026-02-20

### Added

- Alertmanager route consistency tests now cover ambiguous routing case:
  - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
  - fails when one alert matches multiple explicit routes

### Changed

- `validate-alertmanager-route-consistency.py` now enforces:
  - unmatched alerts fail validation
  - alerts matching multiple explicit routes fail validation (`multiple explicit routes matched alert`)
- README now documents route ambiguity guardrails for alertmanager validation.
- Backend app version bumped to `0.4.10-m4-alertmanager-route-ambiguity-guard`.
- Summary schema version: `1`

## [0.4.9-m4-alertmanager-route-consistency-guard] - 2026-02-20

### Added

- New alertmanager routing config for refactor alerts:
  - `refactor/backend/monitoring/alertmanager/refactor-alertmanager-routing.yml`
- New validator script:
  - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
  - validates that every alert from prometheus rule files is covered by at least one explicit route
  - validates route receiver references exist in alertmanager `receivers`
- New unit tests:
  - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
  - covers default pass, missing notification route failure, and CI invocation wiring

### Changed

- Backend CI script now runs alertmanager route consistency validation before promtool checks.
- Notification runbook references now include alertmanager routing config and validator script.
- Backend app version bumped to `0.4.9-m4-alertmanager-route-consistency-guard`.
- Summary schema version: `1`

## [0.4.8-m4-notification-runbook-thresholds-autogen] - 2026-02-20

### Added

- Notification retry runbook threshold block now supports marker-based auto rendering:
  - `<!-- notification-retry-thresholds:start -->`
  - `<!-- notification-retry-thresholds:end -->`
- Notification retry threshold sync test coverage now includes runbook drift detection:
  - `refactor/backend/tests/unit/test_notification_retry_alert_threshold_sync.py`

### Changed

- `sync-notification-retry-alert-thresholds.py` now syncs both:
  - notification retry Prometheus rule files (`default/dev/staging/prod`)
  - runbook threshold section in `2026-02-20-notification-retry-alert-runbook.md`
- `sync-notification-retry-alert-thresholds.py --check` now fails when runbook threshold section drifts.
- Backend app version bumped to `0.4.8-m4-notification-runbook-thresholds-autogen`.
- Summary schema version: `1`

## [0.4.7-m4-notification-alert-threshold-config-sync] - 2026-02-20

### Added

- New single-source threshold config for notification retry alerts:
  - `refactor/backend/config/notification-retry-alert-thresholds.json`
- New sync/check script:
  - `refactor/backend/scripts/sync-notification-retry-alert-thresholds.py`
  - generates `default/dev/staging/prod` notification retry alert rule files from config
  - supports `--check` drift gate mode
- New unit tests:
  - `refactor/backend/tests/unit/test_notification_retry_alert_threshold_sync.py`
  - covers default `--check` pass, profile drift fail, and CI invocation wiring

### Changed

- Backend CI script now runs:
  - `python3 scripts/sync-notification-retry-alert-thresholds.py --check`
- Notification retry runbook references now include threshold config and sync script paths.
- Backend app version bumped to `0.4.7-m4-notification-alert-threshold-config-sync`.
- Summary schema version: `1`

## [0.4.6-m4-notification-runbook-multi-profile-consistency] - 2026-02-20

### Added

- Notification retry runbook now includes profile baseline matrix for:
  - `dev`
  - `staging`
  - `prod`
- Validator coverage extended in unit tests:
  - runbook profile matrix drift detection
  - default rule drift from prod rule detection

### Changed

- `validate-notification-retry-runbook.py` now validates:
  - `refactor-notification-retry-alerts.dev.yml`
  - `refactor-notification-retry-alerts.staging.yml`
  - `refactor-notification-retry-alerts.prod.yml`
  - `refactor-notification-retry-alerts.yml == .prod.yml` baseline
  - runbook prod baseline bullets and profile matrix consistency
- Backend app version bumped to `0.4.6-m4-notification-runbook-multi-profile-consistency`.
- Summary schema version: `1`

## [0.4.5-m4-notification-runbook-consistency-guard] - 2026-02-20

### Added

- New validator script:
  - `refactor/backend/scripts/validate-notification-retry-runbook.py`
  - validates that notification retry runbook prod baseline thresholds are consistent with
    `refactor-notification-retry-alerts.yml`.
- Unit tests for validator:
  - default files pass
  - threshold drift in runbook fails validation
  - CI script includes validator invocation

### Changed

- Backend CI script now runs notification retry runbook consistency validation before promtool checks.
- Backend app version bumped to `0.4.5-m4-notification-runbook-consistency-guard`.
- Summary schema version: `1`

## [0.4.4-m4-notification-retry-alert-rules] - 2026-02-20

### Added

- Notification retry governance alert rules (Prometheus) added under:
  - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.yml`
  - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.dev.yml`
  - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.staging.yml`
  - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.prod.yml`
- Alert coverage includes:
  - low manual retry success ratio (`RefactorNotificationRetrySuccessRatioWarn/Critical`)
  - high auto-retry final failure ratio (`RefactorNotificationAutoRetryFinalFailureRatioWarn/Critical`)
- Unit tests for notification retry alert templates and profile files.

### Changed

- Backend app version bumped to `0.4.4-m4-notification-retry-alert-rules`.
- Summary schema version: `1`

## [0.4.3-m4-notification-retry-metrics] - 2026-02-20

### Added

- Global metrics now include notification delivery and retry quality series:
  - `refactor_notification_deliveries_total{status=...}`
  - `refactor_notification_deliveries_by_channel_total{channel=...}`
  - `refactor_notification_retry_attempts_total`
  - `refactor_notification_retry_success_total`
  - `refactor_notification_retry_failed_total`
  - `refactor_notification_retry_success_ratio`
  - `refactor_notification_auto_retry_deliveries_total`
  - `refactor_notification_auto_retry_final_failed_total`
  - `refactor_notification_auto_retry_final_failure_ratio`
- Unit test coverage for notification retry metrics in `/api/v2/metrics`.

### Changed

- Backend app version bumped to `0.4.3-m4-notification-retry-metrics`.
- Summary schema version: `1`

## [0.4.2-m4-notification-retry-loop] - 2026-02-20

### Added

- Notification delivery retry loop:
  - `NotificationHub` supports per-channel retry attempts via `NOTIFICATION_SEND_MAX_RETRIES`.
  - Optional linear backoff between retries via `NOTIFICATION_RETRY_BACKOFF_MS`.
  - Delivery result now tracks `attempt_count` and `retry_count`.
- Manual retry API:
  - `POST /api/v2/notifications/deliveries/{delivery_id}/retry`.
  - Retry records are persisted with `source_type=delivery_retry` and `retry_of_delivery_id`.
- Notification delivery persistence schema upgrades:
  - `notification_deliveries.attempt_count`
  - `notification_deliveries.retry_of_delivery_id`
  - Startup schema bootstrap adds backward-compatible column ensure for existing SQLite files.
- Unit tests:
  - auto retry success path with persisted attempt metadata
  - retry failed delivery through API and verify retry-linked persistence

### Changed

- `GET /api/v2/notifications/deliveries` now returns:
  - `display_name`
  - `attempt_count`
  - `retry_count`
  - `retry_of_delivery_id`
- `NotificationHub.send()` summary now includes `retried`.
- Refactor backend app version bumped to `0.4.2-m4-notification-retry-loop`.
- Summary schema version: `1`

## [0.4.1-m4-notification-delivery-persistence-auto-trigger] - 2026-02-19

### Added

- Notification delivery persistence:
  - New SQLite table `notification_deliveries` with source/channel/status/error/message tracking.
  - New API `GET /api/v2/notifications/deliveries` for querying persisted delivery records.
- Analysis auto notification trigger:
  - `ANALYSIS_AUTO_NOTIFY_ENABLED` to enable auto-send after successful analysis jobs.
  - `ANALYSIS_AUTO_NOTIFY_CHANNELS` to restrict channels by CSV list.
  - Delivery records tagged with `source_type=analysis_job` and `source_id=<job_id>`.
- Unit tests for:
  - Delivery persistence and query API behavior
  - Analysis auto-notify source binding persistence

### Changed

- `NotificationHub.send()` now returns `message_id` and `created_at`.
- Delivery result payload now includes `source_type`, `source_id`, `message_id`, and timestamp fields.
- OpenAPI draft extended for notification delivery query and updated notification response schemas.
- Summary schema version: `1`
- Backend app version bumped to `0.4.1-m4-notification-delivery-persistence-auto-trigger`.

## [0.4.0-m4-notification-hub-min-loop] - 2026-02-19

### Added

- Notification hub pluginized backend minimum loop:
  - `GET /api/v2/notifications/channels`
  - `POST /api/v2/notifications/preview`
  - `POST /api/v2/notifications/send`
  - `POST /api/v2/notifications/channels/test`
- New notification service module:
  - `ChannelPlugin` interface
  - `NotificationHub` orchestration
  - channel-aware formatter and delivery aggregation
- Built-in channels (config-driven):
  - `wechat`, `feishu`, `telegram`, `email`, `pushover`, `pushplus`, `serverchan3`, `custom`, `discord`, `astrbot`
- Unit tests for notification hub behavior and API contract:
  - channel listing, preview, send aggregation, per-channel test send
  - partial failure isolation (single channel failure does not block others)

### Changed

- Global error code contract extended with notification domain:
  - `NTF-CHANNEL-001`
  - `NTF-FORMAT-002`
  - `NTF-SEND-003`
  - `NTF-RETRY-004`
- Backend app version bumped to `0.4.0-m4-notification-hub-min-loop`.
- OpenAPI draft updated with notification APIs and schemas.
- README updated to M4 status and notification hub usage.
- `.env.example` updated with notification timeout and AstrBot optional keys.

## [0.3.200-m3-sync-json-errors-catalog-file-read-failure-mode-context] - 2026-02-19

### Added

- New assertions:
  - catalog file read-failed JSON errors now assert `context.failure_mode`

### Changed

- `sync-validator-error-codes.py` now includes `failure_mode` for catalog read failures:
  - `catalog_file_read_failed` for `error_code_sync_validator_error_codes_catalog_file_read_failed`
- README documents failure-mode mapping for catalog read failures.
- Summary schema version: `1`
- Backend app version bumped to `0.3.200-m3-sync-json-errors-catalog-file-read-failure-mode-context`.

## [0.3.199-m3-sync-json-errors-placeholder-markers-file-failure-mode-context] - 2026-02-19

### Added

- New assertions:
  - placeholder markers file missing/read-failed JSON errors now assert `context.failure_mode`

### Changed

- `sync-validator-error-codes.py` now includes `failure_mode` for placeholder markers file access errors:
  - `placeholder_markers_file_not_found` for `error_code_sync_validator_error_codes_placeholder_markers_file_not_found`
  - `placeholder_markers_file_read_failed` for `error_code_sync_validator_error_codes_placeholder_markers_read_failed`
- README documents failure-mode mapping for placeholder markers file access errors.
- Summary schema version: `1`
- Backend app version bumped to `0.3.199-m3-sync-json-errors-placeholder-markers-file-failure-mode-context`.

## [0.3.198-m3-sync-json-errors-metadata-overrides-file-failure-mode-context] - 2026-02-19

### Added

- New assertions:
  - metadata overrides file missing/read-failed JSON errors now assert `context.failure_mode`

### Changed

- `sync-validator-error-codes.py` now includes `failure_mode` for metadata overrides file access errors:
  - `metadata_overrides_file_not_found` for `error_code_sync_validator_error_codes_metadata_overrides_file_not_found`
  - `metadata_overrides_file_read_failed` for `error_code_sync_validator_error_codes_metadata_overrides_file_read_failed`
- README documents failure-mode mapping for metadata overrides file access errors.
- Summary schema version: `1`
- Backend app version bumped to `0.3.198-m3-sync-json-errors-metadata-overrides-file-failure-mode-context`.

## [0.3.197-m3-sync-json-errors-validator-registry-validation-failure-mode-context] - 2026-02-19

### Added

- New assertions:
  - validator registry missing/invalid JSON errors now assert `context.failure_mode`

### Changed

- `sync-validator-error-codes.py` now includes `failure_mode` in registry validation errors:
  - `missing_registry` for `error_code_sync_validator_error_codes_validator_registry_missing`
  - `invalid_registry_item` for `error_code_sync_validator_error_codes_validator_registry_invalid`
- README documents failure-mode mapping for registry validation errors.
- Summary schema version: `1`
- Backend app version bumped to `0.3.197-m3-sync-json-errors-validator-registry-validation-failure-mode-context`.

## [0.3.196-m3-sync-json-errors-validator-registry-validation-stage-context] - 2026-02-19

### Added

- New assertions:
  - validator registry missing/invalid JSON errors now assert `context.stage=validator_registry_validation`

### Changed

- `sync-validator-error-codes.py` now includes `stage=validator_registry_validation` in:
  - `error_code_sync_validator_error_codes_validator_registry_missing`
  - `error_code_sync_validator_error_codes_validator_registry_invalid`
- README documents stage context for registry validation errors.
- Summary schema version: `1`
- Backend app version bumped to `0.3.196-m3-sync-json-errors-validator-registry-validation-stage-context`.

## [0.3.195-m3-sync-json-errors-validator-registry-failure-mode-context] - 2026-02-19

### Added

- New assertions:
  - validator registry load failed (SyntaxError/SystemExit) now assert `context.failure_mode`

### Changed

- `sync-validator-error-codes.py` now includes `failure_mode` in `validator_registry_load_failed` context:
  - `exception` for generic loader exceptions
  - `system_exit` for `SystemExit` loader failures
- README documents `failure_mode` context mapping for registry load failures.
- Summary schema version: `1`
- Backend app version bumped to `0.3.195-m3-sync-json-errors-validator-registry-failure-mode-context`.

## [0.3.194-m3-sync-json-errors-validator-registry-stage-context] - 2026-02-19

### Added

- New assertions:
  - validator registry load failed (SyntaxError/SystemExit) now assert `context.stage=validator_registry_loading`

### Changed

- `sync-validator-error-codes.py` now includes `stage=validator_registry_loading` in `validator_registry_load_failed` context for:
  - generic loader exceptions
  - `SystemExit` loader failures
- README documents registry load failure stage context.
- Summary schema version: `1`
- Backend app version bumped to `0.3.194-m3-sync-json-errors-validator-registry-stage-context`.

## [0.3.193-m3-sync-json-errors-validator-registry-system-exit-code] - 2026-02-19

### Added

- New assertion:
  - validator registry load failed (`SystemExit`) now asserts `context.exit_code`

### Changed

- `sync-validator-error-codes.py` now includes `exit_code` in `validator_registry_load_failed` context when loader fails with `SystemExit`.
- README clarifies `exit_code` availability for registry loader `SystemExit` failures.
- Summary schema version: `1`
- Backend app version bumped to `0.3.193-m3-sync-json-errors-validator-registry-system-exit-code`.

## [0.3.192-m3-sync-json-errors-unexpected-runtime-exit-code] - 2026-02-19

### Added

- New assertion:
  - runtime unexpected-error JSON context now asserts `exit_code=1`

### Changed

- `sync-validator-error-codes.py` runtime unexpected-error context now includes:
  - `exit_code=1`
- README clarifies runtime unexpected-error exit code context.
- Summary schema version: `1`
- Backend app version bumped to `0.3.192-m3-sync-json-errors-unexpected-runtime-exit-code`.

## [0.3.191-m3-sync-json-errors-unexpected-runtime-unknown-args] - 2026-02-19

### Added

- New assertion:
  - runtime unexpected-error JSON context now asserts `unknown_args=[]`

### Changed

- `sync-validator-error-codes.py` runtime unexpected-error context now includes:
  - `unknown_args` (empty list)
- README clarifies runtime unexpected-error context field parity (`argv` + `unknown_args`).
- Summary schema version: `1`
- Backend app version bumped to `0.3.191-m3-sync-json-errors-unexpected-runtime-unknown-args`.

## [0.3.190-m3-sync-json-errors-unexpected-runtime-argv-context] - 2026-02-19

### Added

- New assertion:
  - unexpected runtime fallback JSON errors now assert `context.argv`

### Changed

- `sync-validator-error-codes.py` runtime unexpected-error context now includes:
  - `argv`
- README documents `argv` for runtime unexpected-error context.
- Summary schema version: `1`
- Backend app version bumped to `0.3.190-m3-sync-json-errors-unexpected-runtime-argv-context`.

## [0.3.189-m3-sync-json-errors-unexpected-runtime-context] - 2026-02-19

### Added

- New test:
  - injected runtime exception now asserts unexpected-error JSON context includes runtime stage and exception type

### Changed

- `sync-validator-error-codes.py` unexpected runtime fallback JSON now includes:
  - `context.stage=runtime`
  - `context.exception_type`
- README documents unexpected runtime failure context fields for `--json-errors`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.189-m3-sync-json-errors-unexpected-runtime-context`.

## [0.3.188-m3-sync-json-errors-cli-unknown-args-empty-parity] - 2026-02-19

### Added

- New assertion:
  - missing-value argument parsing errors under `--json-errors` now assert `context.unknown_args=[]`

### Changed

- `sync-validator-error-codes.py` parse-time argument error JSON context now always includes:
  - `unknown_args` (empty list when not applicable)
- This aligns parse-time and unknown-argument parsing error context schema.
- Summary schema version: `1`
- Backend app version bumped to `0.3.188-m3-sync-json-errors-cli-unknown-args-empty-parity`.

## [0.3.187-m3-sync-json-errors-cli-argv-parity] - 2026-02-19

### Added

- New test:
  - unknown CLI arguments under `--json-errors` now assert `context.argv` for parsing-context parity

### Changed

- `sync-validator-error-codes.py` unknown-argument JSON error branch now includes:
  - `context.argv`
- README clarifies that unknown-argument parsing errors include both `unknown_args` and `argv`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.187-m3-sync-json-errors-cli-argv-parity`.

## [0.3.186-m3-sync-json-errors-cli-missing-arg-value] - 2026-02-19

### Added

- New test:
  - missing value for known CLI argument under `--json-errors` now asserts structured JSON payload

### Changed

- `sync-validator-error-codes.py` now captures argparse parse-time `SystemExit` failures in `--json-errors` mode and emits structured JSON:
  - `error_code_sync_validator_error_codes_unexpected_error`
  - with `context.stage=argument_parsing`
  - with `context.argv` and `context.exit_code`
- Existing unknown-argument JSON behavior is preserved.
- README clarifies argument parsing failure coverage in structured JSON mode.
- Summary schema version: `1`
- Backend app version bumped to `0.3.186-m3-sync-json-errors-cli-missing-arg-value`.

## [0.3.185-m3-sync-json-errors-cli-unknown-arguments] - 2026-02-19

### Added

- New tests:
  - unknown CLI arguments under `--json-errors` now assert structured JSON error payload
  - check mode unreadable catalog path JSON error coverage is now explicitly asserted

### Changed

- `sync-validator-error-codes.py` now parses arguments via `parse_known_args` and maps unknown arguments to:
  - `error_code_sync_validator_error_codes_unexpected_error`
  - with `context.stage=argument_parsing`
  - with `context.unknown_args` and `context.exit_code=2`
- README documents unknown-argument structured error behavior.
- Summary schema version: `1`
- Backend app version bumped to `0.3.185-m3-sync-json-errors-cli-unknown-arguments`.

## [0.3.184-m3-sync-json-errors-validator-registry-system-exit] - 2026-02-19

### Added

- New test:
  - validator registry loader now asserts structured JSON error when validator script exits with `SystemExit`

### Changed

- `sync-validator-error-codes.py` now maps `SystemExit` during validator registry loading to:
  - `error_code_sync_validator_error_codes_validator_registry_load_failed`
  - with `context.exception_type=SystemExit`
- README clarifies that registry load failures include syntax/runtime/SystemExit cases with `exception_type`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.184-m3-sync-json-errors-validator-registry-system-exit`.

## [0.3.183-m3-sync-json-errors-jsondecode-context-exception-type] - 2026-02-19

### Added

- New tests:
  - malformed existing catalog JSON parse errors now assert `context.exception_type=JSONDecodeError`
  - malformed metadata overrides JSON parse errors now assert `context.exception_type=JSONDecodeError`
  - malformed placeholder marker JSON parse errors now assert `context.exception_type=JSONDecodeError`

### Changed

- `sync-validator-error-codes.py` now attaches `exception_type` to JSON decode parse error contexts for:
  - existing catalog (`json_parse_error`)
  - metadata overrides (`json_parse_error`)
  - placeholder markers (`placeholder_markers_invalid`)
- README clarifies `exception_type` coverage for both decode and parse failures.
- Summary schema version: `1`
- Backend app version bumped to `0.3.183-m3-sync-json-errors-jsondecode-context-exception-type`.

## [0.3.182-m3-sync-json-errors-parse-context-exception-type] - 2026-02-19

### Added

- New tests:
  - invalid UTF-8 existing catalog parse errors now assert `context.exception_type`
  - invalid UTF-8 metadata overrides parse errors now assert `context.exception_type`
  - invalid UTF-8 placeholder marker parse errors now assert `context.exception_type`

### Changed

- `sync-validator-error-codes.py` now attaches `exception_type` to UTF-8 decode error contexts for:
  - existing catalog parse errors
  - metadata overrides parse errors
  - placeholder marker invalid payload errors
- README documents the new parse-context field behavior.
- Summary schema version: `1`
- Backend app version bumped to `0.3.182-m3-sync-json-errors-parse-context-exception-type`.

## [0.3.181-m3-sync-json-errors-output-write-failed] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated code for output write failures:
  - `error_code_sync_validator_error_codes_output_write_failed`
- New test:
  - when output file is read-only, sync now emits `output_write_failed` with `exception_type=PermissionError`

### Changed

- `sync-validator-error-codes.py` now captures output file write failures and emits structured sync errors instead of `unexpected_error`.
- README documents the new output-write-failed code.
- Summary schema version: `1`
- Backend app version bumped to `0.3.181-m3-sync-json-errors-output-write-failed`.

## [0.3.180-m3-sync-json-errors-placeholder-markers-utf8-parse] - 2026-02-19

### Added

- New test:
  - placeholder markers file with invalid UTF-8 bytes now asserts `error_code_sync_validator_error_codes_placeholder_markers_invalid`

### Changed

- `sync-validator-error-codes.py` placeholder marker loader now maps UTF-8 decode failures to marker-invalid errors instead of `unexpected_error`.
- README clarifies that invalid UTF-8 marker payloads are covered by `placeholder_markers_invalid`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.180-m3-sync-json-errors-placeholder-markers-utf8-parse`.

## [0.3.179-m3-sync-json-errors-metadata-overrides-utf8-parse] - 2026-02-19

### Added

- New test:
  - metadata overrides file with invalid UTF-8 bytes now asserts `error_code_sync_validator_error_codes_json_parse_error`

### Changed

- `sync-validator-error-codes.py` metadata overrides loader now maps UTF-8 decode failures to structured parse errors instead of `unexpected_error`.
- README clarifies that invalid UTF-8/invalid JSON metadata overrides payloads return `json_parse_error`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.179-m3-sync-json-errors-metadata-overrides-utf8-parse`.

## [0.3.178-m3-sync-json-errors-existing-catalog-utf8-parse] - 2026-02-19

### Added

- New test:
  - existing catalog file with invalid UTF-8 bytes now asserts `error_code_sync_validator_error_codes_json_parse_error`

### Changed

- `sync-validator-error-codes.py` existing catalog loader now maps UTF-8 decode failures to structured parse errors instead of `unexpected_error`.
- README clarifies that invalid UTF-8/invalid JSON existing catalog payloads return `json_parse_error`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.178-m3-sync-json-errors-existing-catalog-utf8-parse`.

## [0.3.177-m3-sync-json-errors-placeholder-markers-read-failed] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated code for unreadable placeholder marker path:
  - `error_code_sync_validator_error_codes_placeholder_markers_read_failed`
- New test:
  - when `--placeholder-markers-file` points to a directory, sync now emits `placeholder_markers_read_failed` with `exception_type=IsADirectoryError`

### Changed

- `sync-validator-error-codes.py` placeholder marker loader now distinguishes read failures from generic unexpected errors.
- README documents the new placeholder marker read-failure code.
- Summary schema version: `1`
- Backend app version bumped to `0.3.177-m3-sync-json-errors-placeholder-markers-read-failed`.

## [0.3.176-m3-sync-json-errors-output-parent-create-failed] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated code for output parent directory creation failures:
  - `error_code_sync_validator_error_codes_output_parent_create_failed`
- New test:
  - when output file parent path is a regular file, sync now emits `output_parent_create_failed` with `exception_type=FileExistsError`

### Changed

- `sync-validator-error-codes.py` now captures `mkdir` failures before writing output and emits structured sync errors.
- README documents the new output-parent-create-failed code.
- Summary schema version: `1`
- Backend app version bumped to `0.3.176-m3-sync-json-errors-output-parent-create-failed`.

## [0.3.175-m3-sync-json-errors-metadata-overrides-read-failed] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated code for unreadable metadata overrides path:
  - `error_code_sync_validator_error_codes_metadata_overrides_file_read_failed`
- New test:
  - when `--metadata-overrides-file` points to a directory, sync now emits `metadata_overrides_file_read_failed` with `exception_type=IsADirectoryError`

### Changed

- `sync-validator-error-codes.py` metadata overrides loader now distinguishes file read failures from generic unexpected errors.
- README documents the new metadata overrides read-failure code.
- Summary schema version: `1`
- Backend app version bumped to `0.3.175-m3-sync-json-errors-metadata-overrides-read-failed`.

## [0.3.174-m3-sync-json-errors-catalog-read-failed] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated code for unreadable catalog path:
  - `error_code_sync_validator_error_codes_catalog_file_read_failed`
- New test:
  - when `--output-file` points to a directory, sync now emits `catalog_file_read_failed` with `exception_type=IsADirectoryError`

### Changed

- `sync-validator-error-codes.py` existing catalog loader now distinguishes file read failure from generic unexpected errors.
- README documents the new catalog read-failure code.
- Summary schema version: `1`
- Backend app version bumped to `0.3.174-m3-sync-json-errors-catalog-read-failed`.

## [0.3.173-m3-sync-json-errors-placeholder-markers-non-object] - 2026-02-19

### Added

- New test:
  - sync `--json-errors` now covers non-object placeholder marker payload (array payload) and asserts invalid marker code

### Changed

- `sync-validator-error-codes.py` placeholder marker loader now validates that marker payload is a JSON object before reading `markers`.
- Non-object marker payload no longer falls back to `unexpected_error`; it returns:
  - `error_code_sync_validator_error_codes_placeholder_markers_invalid`
- README clarifies that `placeholder_markers_invalid` includes non-object payload cases.
- Summary schema version: `1`
- Backend app version bumped to `0.3.173-m3-sync-json-errors-placeholder-markers-non-object`.

## [0.3.172-m3-sync-json-errors-validator-registry-load-failed] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated code when validator registry script execution fails:
  - `error_code_sync_validator_error_codes_validator_registry_load_failed`
- New test:
  - isolated backend with syntax-error validator script now returns `validator_registry_load_failed` with `exception_type` context

### Changed

- `sync-validator-error-codes.py` now catches runtime load failures in `runpy.run_path` and emits structured sync errors.
- README documents the new registry load failure code.
- Summary schema version: `1`
- Backend app version bumped to `0.3.172-m3-sync-json-errors-validator-registry-load-failed`.

## [0.3.171-m3-sync-json-errors-validator-registry-codes] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated validator registry error codes:
  - `error_code_sync_validator_error_codes_validator_registry_missing`
  - `error_code_sync_validator_error_codes_validator_registry_invalid`
- New tests:
  - isolated backend with missing `VALIDATOR_ERROR_CODES` registry returns `validator_registry_missing`
  - isolated backend with invalid registry entry type returns `validator_registry_invalid`

### Changed

- `sync-validator-error-codes.py` now raises typed sync errors in registry loading path with `group/path` context.
- README documents new registry-related sync JSON error codes.
- Summary schema version: `1`
- Backend app version bumped to `0.3.171-m3-sync-json-errors-validator-registry-codes`.

## [0.3.170-m3-sync-json-errors-missing-validator-script-file] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated error code for missing validator script files:
  - `error_code_sync_validator_error_codes_validator_script_file_not_found`
- New test:
  - isolated backend copy with missing validator registry scripts now returns dedicated code with `group/path` context

### Changed

- `sync-validator-error-codes.py` now raises typed sync error in `_build_catalog` when a validator script file is missing.
- README documents the new sync JSON error code.
- Summary schema version: `1`
- Backend app version bumped to `0.3.170-m3-sync-json-errors-missing-validator-script-file`.

## [0.3.169-m3-sync-json-errors-missing-metadata-overrides-file] - 2026-02-19

### Added

- Sync `--json-errors` now includes dedicated error code for missing metadata overrides file:
  - `error_code_sync_validator_error_codes_metadata_overrides_file_not_found`
- New test:
  - sync missing metadata overrides file (`--json-errors`) now asserts dedicated code and path context

### Changed

- `sync-validator-error-codes.py` now raises typed sync error instead of generic exception when metadata overrides file does not exist.
- README documents the new sync JSON error code.
- Summary schema version: `1`
- Backend app version bumped to `0.3.169-m3-sync-json-errors-missing-metadata-overrides-file`.

## [0.3.168-m3-sync-json-errors-profile-actions-context] - 2026-02-19

### Added

- Sync `--json-errors` unknown metadata overrides profile context now includes `suggested_actions`:
  - close match: `copy_command` + `use_profile`
  - no close match: `show_profiles`
  - no profile mode config: `migrate_profile_mode`
- Sync `--json-errors` `fallback_reason=no_profiles_config` context now includes:
  - `suggested_config_snippet` for flat-to-profile migration
- New tests:
  - sync unknown metadata overrides profile (`--json-errors`) asserts `suggested_actions` payload
  - sync profile requested on flat overrides config (`--json-errors`) asserts `suggested_config_snippet` + migrate action

### Changed

- `sync-validator-error-codes.py` now reuses shared profile suggestion action helper for JSON context parity.
- README now documents sync profile suggestion `suggested_actions` and migration snippet fields.
- Summary schema version: `1`
- Backend app version bumped to `0.3.168-m3-sync-json-errors-profile-actions-context`.

## [0.3.167-m3-sync-json-errors-placeholder-marker-exceptions] - 2026-02-19

### Added

- Sync `--json-errors` now includes placeholder marker file exception coverage:
  - `error_code_sync_validator_error_codes_placeholder_markers_file_not_found`
  - `error_code_sync_validator_error_codes_placeholder_markers_invalid`
- New tests:
  - missing placeholder marker file (`--check --strict-descriptions --json-errors`) returns structured error code
  - invalid placeholder marker payload (`--check --strict-descriptions --json-errors`) returns structured error code

### Changed

- `sync-validator-error-codes.py` placeholder marker loader now raises typed sync errors instead of generic exceptions.
- README documents placeholder marker exception codes for sync JSON errors.
- Summary schema version: `1`
- Backend app version bumped to `0.3.167-m3-sync-json-errors-placeholder-marker-exceptions`.

## [0.3.166-m3-sync-json-errors-check-coverage] - 2026-02-19

### Added

- Sync `--json-errors` now covers additional `--check` failure branches:
  - `error_code_sync_validator_error_codes_catalog_not_in_sync`
  - `error_code_sync_validator_error_codes_placeholder_text_detected`
- New tests:
  - check drift (`--check --json-errors`) now asserts structured payload
  - strict placeholder failure (`--check --strict-descriptions --json-errors`) now asserts structured payload with violations

### Changed

- `sync-validator-error-codes.py` now emits structured JSON errors for:
  - catalog not found in check mode
  - catalog drift in check mode
  - strict placeholder violations (check/update mode)
- README updates sync JSON error code documentation for check/strict branches.
- Summary schema version: `1`
- Backend app version bumped to `0.3.166-m3-sync-json-errors-check-coverage`.

## [0.3.165-m3-sync-json-errors] - 2026-02-19

### Added

- Sync validator error-code script now supports structured JSON errors via:
  - `--json-errors`
- Structured sync JSON error codes added for key failure paths:
  - `error_code_sync_validator_error_codes_metadata_overrides_profile_not_found`
  - `error_code_sync_validator_error_codes_unknown_override_code`
  - plus payload/parse/unexpected categories in sync script runtime
- New tests:
  - sync unknown metadata overrides profile (`--json-errors`) now asserts structured payload fields
  - sync unknown override code (`--json-errors`) now asserts structured payload and context

### Changed

- `sync-validator-error-codes.py` now uses typed runtime error objects for structured error emission.
- README documents sync `--json-errors` usage and key error codes.
- Summary schema version: `1`
- Backend app version bumped to `0.3.165-m3-sync-json-errors`.

## [0.3.164-m3-sync-overrides-profile-suggestions] - 2026-02-19

### Added

- Sync script unknown metadata overrides profile errors now provide close-match suggestion hints:
  - `Did you mean: <profile>`
  - `Try: --metadata-overrides-profile <profile>`
- New tests:
  - close-match unknown profile on sync path now asserts suggestion hint text
  - no-close-match unknown profile on sync path now asserts available profile listing

### Changed

- `sync-validator-error-codes.py` now reuses shared profile suggestion helpers for metadata overrides profile selection.
- Unknown sync profile errors now keep default-profile-first ordering in available profile messages.
- README documents sync unknown profile suggestion behavior.
- Summary schema version: `1`
- Backend app version bumped to `0.3.164-m3-sync-overrides-profile-suggestions`.

## [0.3.163-m3-overrides-profile-suggestion-parity] - 2026-02-19

### Added

- Unknown `--overrides-profile` errors now provide the same suggestion payload quality as lint profile errors:
  - `fallback_reason` / `suggestion_level`
  - `suggested_profiles` / `suggested_cli_args`
  - `suggested_command`
  - `suggested_actions` (`copy_command`, `use_profile`, `show_profiles`)
- New tests:
  - unknown overrides profile (`no_close_match`) now asserts structured suggestion fields
  - nearby overrides profile (`close_match`) now asserts suggested command and actions

### Changed

- `validate-validator-error-code-metadata-overrides.py` now reuses shared helper payload generation for overrides profile
  suggestions.
- `profile_suggestion_helpers.py` now supports custom profile labels and CLI arg names
  (e.g. `--overrides-profile`).
- README adds unknown overrides profile suggestion contract notes.
- Summary schema version: `1`
- Backend app version bumped to `0.3.163-m3-overrides-profile-suggestion-parity`.

## [0.3.162-m3-metadata-overrides-profile-mode] - 2026-02-19

### Added

- Metadata overrides validator now supports overrides profile selection:
  - CLI: `--overrides-profile <profile>`
  - env fallback: `OVERRIDES_PROFILE`
  - structured JSON error code for unknown profile: `error_code_metadata_overrides_overrides_profile_not_found`
- Validator metadata overrides schema now supports both payload shapes:
  - flat: `group -> code -> fields`
  - profile mode: `default_profile + profiles.<name>.(group -> code -> fields)`
- Sync script now supports metadata overrides profile selection:
  - CLI: `--metadata-overrides-profile <profile>`
  - env fallback: `METADATA_OVERRIDES_PROFILE`

### Changed

- `validate-validator-error-code-metadata-overrides.py` now resolves overrides payload by profile before target/lint checks.
- `sync-validator-error-codes.py` now resolves metadata overrides profile before applying overrides.
- README documents overrides profile mode, CLI/env precedence, and sync profile usage.
- Summary schema version: `1`
- Backend app version bumped to `0.3.162-m3-metadata-overrides-profile-mode`.

## [0.3.161-m3-profile-suggestion-actions-full-metadata-overrides] - 2026-02-19

### Added

- Full default metadata override policy coverage for all `profile_suggestion_actions_*` codes:
  - `profile_suggestion_actions_file_not_found`
  - `profile_suggestion_actions_json_parse_error`
  - `profile_suggestion_actions_schema_invalid`
  - `profile_suggestion_actions_example_validation_failed`
  - `profile_suggestion_actions_helper_contract_failed`
  - `profile_suggestion_actions_unexpected_error`
- New tests:
  - metadata overrides config now requires full coverage for all profile suggestion actions codes
  - catalog key metadata checks include unexpected-error critical policy for profile suggestion actions

### Changed

- `validator-error-code-metadata-overrides.json` now includes full policy entries for profile suggestion actions group.
- `validator-error-codes.json` regenerated to apply full profile suggestion actions policy set.
- README now documents full policy coverage for `profile_suggestion_actions_*` codes.
- Summary schema version: `1`
- Backend app version bumped to `0.3.161-m3-profile-suggestion-actions-full-metadata-overrides`.

## [0.3.160-m3-profile-suggestion-actions-metadata-overrides-policy] - 2026-02-19

### Added

- Default metadata override policy for `profile_suggestion_actions` group:
  - `profile_suggestion_actions_example_validation_failed`
  - `profile_suggestion_actions_helper_contract_failed`
- Policy includes explicit description/severity/remediation and is enforced by existing metadata override validator.
- New tests:
  - metadata overrides config now must include `profile_suggestion_actions` policy block
  - catalog key metadata checks now assert `profile_suggestion_actions_helper_contract_failed` severity/remediation profile

### Changed

- `validator-error-code-metadata-overrides.json` now contains concrete default policy entries for `profile_suggestion_actions`.
- `validator-error-codes.json` regenerated via sync script to reflect new default overrides.
- README now documents profile suggestion actions default metadata override policy.
- Summary schema version: `1`
- Backend app version bumped to `0.3.160-m3-profile-suggestion-actions-metadata-overrides-policy`.

## [0.3.159-m3-error-code-catalog-profile-suggestion-actions-group] - 2026-02-19

### Added

- Validator error code catalog now includes dedicated group:
  - `profile_suggestion_actions`
- New catalog entries synced from `validate-profile-suggestion-actions-schema.py`:
  - `profile_suggestion_actions_file_not_found`
  - `profile_suggestion_actions_json_parse_error`
  - `profile_suggestion_actions_schema_invalid`
  - `profile_suggestion_actions_example_validation_failed`
  - `profile_suggestion_actions_helper_contract_failed`
  - `profile_suggestion_actions_unexpected_error`
- New tests:
  - catalog payload includes `profile_suggestion_actions` group
  - catalog schema required groups includes `profile_suggestion_actions`
  - script registry coverage includes `validate-profile-suggestion-actions-schema.py` codes

### Changed

- `sync-validator-error-codes.py` now syncs codes from `validate-profile-suggestion-actions-schema.py`.
- `validator-error-codes.schema.json` required groups now include `profile_suggestion_actions`.
- `validator-error-codes.json` profile suggestion actions entries now use concrete non-placeholder descriptions/remediations.
- README now documents updated catalog group list.
- Summary schema version: `1`
- Backend app version bumped to `0.3.159-m3-error-code-catalog-profile-suggestion-actions-group`.

## [0.3.158-m3-profile-suggestion-actions-schema-validator] - 2026-02-19

### Added

- New schema and example for unknown-profile UI actions:
  - `refactor/backend/config/schemas/profile-suggestion-actions.schema.json`
  - `refactor/backend/config/schemas/profile-suggestion-actions.example.json`
- New validator script:
  - `refactor/backend/scripts/validate-profile-suggestion-actions-schema.py`
  - validates schema structure, example payload, and helper-generated action payloads
  - supports structured JSON errors (`--json-errors`, `profile_suggestion_actions_*`)
- New tests:
  - CI wiring check includes profile suggestion actions schema validator script
  - validator passes default schema/example/helper files
  - validator returns structured JSON error for invalid example payload

### Changed

- CI now runs `validate-profile-suggestion-actions-schema.py` as part of default gate.
- README now documents schema/example file paths and validator usage.
- Summary schema version: `1`
- Backend app version bumped to `0.3.158-m3-profile-suggestion-actions-schema-validator`.

## [0.3.157-m3-error-code-suggested-actions-contract-validation] - 2026-02-19

### Added

- Strict suggested-actions contract validator in shared helper:
  - new helper function `validate_suggested_actions_contract(...)`
  - validates supported action enum:
    - `copy_command`
    - `use_profile`
    - `show_profiles`
    - `migrate_profile_mode`
  - validates required fields and basic value types per action
- New tests:
  - rejects unsupported action values (`unsupported action`)
  - rejects missing required action fields (`missing required field`)

### Changed

- `build_suggested_actions_for_profile_not_found(...)` now always enforces contract validation before returning actions.
- README now documents strict `suggested_actions` contract validation in shared helper module.
- Summary schema version: `1`
- Backend app version bumped to `0.3.157-m3-error-code-suggested-actions-contract-validation`.

## [0.3.156-m3-error-code-shared-suggestion-helpers] - 2026-02-19

### Added

- Shared helper module for unknown profile suggestions:
  - `refactor/backend/scripts/profile_suggestion_helpers.py`
  - includes reusable helpers for:
    - profile suggestion payload (`fallback_reason`, `suggestion_level`, `suggested_profiles`, command hints)
    - profile-mode migration snippet generation
    - structured UI actions (`suggested_actions`)
    - shell-safe path quoting and ordered available profiles
- New contract test:
  - validates shared helper module exists, is imported by both validators, and keeps action payload contract stable

### Changed

- `validate-validator-error-code-metadata-lint.py` now imports shared suggestion helpers instead of local duplicate logic.
- `validate-validator-error-code-metadata-overrides.py` now imports shared suggestion helpers instead of local duplicate logic.
- README now documents shared helper module location.
- Summary schema version: `1`
- Backend app version bumped to `0.3.156-m3-error-code-shared-suggestion-helpers`.

## [0.3.155-m3-error-code-suggested-actions] - 2026-02-19

### Added

- Structured UI action hints for unknown profile JSON context (`suggested_actions`):
  - close match:
    - `{"action":"copy_command","command":"..."}`
    - `{"action":"use_profile","profile":"..."}`
  - no close match:
    - `{"action":"show_profiles","profiles":[...]}`
  - profile mode not configured:
    - `{"action":"migrate_profile_mode","config_snippet":{...}}`
- Applies to both validators:
  - `validate-validator-error-code-metadata-lint.py`
  - `validate-validator-error-code-metadata-overrides.py`
- New tests:
  - validates `suggested_actions` for close-match/no-close-match/no-profiles-config in lint validator
  - validates `suggested_actions` for close-match/no-close-match/no-profiles-config in overrides validator

### Changed

- README now documents `suggested_actions` contract for unknown profile errors.
- Summary schema version: `1`
- Backend app version bumped to `0.3.155-m3-error-code-suggested-actions`.

## [0.3.154-m3-error-code-suggestion-level] - 2026-02-19

### Added

- Machine-readable suggestion severity for unknown profile JSON context:
  - `suggestion_level=hint` when `fallback_reason=close_match`
  - `suggestion_level=warning` when `fallback_reason=no_close_match`
  - `suggestion_level=error` when `fallback_reason=no_profiles_config`
- Applies to both validators:
  - `validate-validator-error-code-metadata-lint.py`
  - `validate-validator-error-code-metadata-overrides.py`
- New tests:
  - validates `suggestion_level` for close-match/no-close-match/no-profiles-config in lint validator
  - validates `suggestion_level` for close-match/no-close-match/no-profiles-config in overrides validator

### Changed

- README now documents `suggestion_level` semantics for unknown profile errors.
- Summary schema version: `1`
- Backend app version bumped to `0.3.154-m3-error-code-suggestion-level`.

## [0.3.153-m3-error-code-shell-safe-suggested-command] - 2026-02-19

### Added

- Shell-safe command template generation for unknown profile suggestions:
  - lint validator `context.suggested_command` now uses shell-safe quoting for `--lint-config-file`
  - overrides validator `context.suggested_command` now uses shell-safe quoting for `--lint-config-file`
- New tests:
  - validates lint validator nearby-profile suggestion command uses shell-safe lint-config path argument
  - validates overrides validator nearby-profile suggestion command uses shell-safe lint-config path argument

### Changed

- README now documents shell-safe quoting for `suggested_command` lint config path.
- Summary schema version: `1`
- Backend app version bumped to `0.3.153-m3-error-code-shell-safe-suggested-command`.

## [0.3.152-m3-error-code-no-profiles-config-snippet] - 2026-02-19

### Added

- Auto-fix snippet for `fallback_reason=no_profiles_config` in unknown-profile JSON errors:
  - lint validator now returns `context.suggested_config_snippet`
  - overrides validator now returns `context.suggested_config_snippet`
  - snippet shape:
    - `default_profile=<requested_profile>`
    - `profiles.<requested_profile>` seeded from flat lint config fields
- New tests:
  - validates lint validator no-profile-config path includes `suggested_config_snippet`
  - validates overrides validator no-profile-config path includes `suggested_config_snippet`

### Changed

- README now documents `suggested_config_snippet` for `fallback_reason=no_profiles_config`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.152-m3-error-code-no-profiles-config-snippet`.

## [0.3.151-m3-error-code-profile-mode-not-configured-hint] - 2026-02-19

### Added

- Explicit no-profile-mode guidance when `--lint-profile` is used with flat lint config:
  - lint validator now returns message containing:
    - `profile mode is not configured for this lint config`
  - overrides validator now returns message containing:
    - `profile mode is not configured for this lint config`
- New tests:
  - validates lint validator no-profile-config path returns explicit profile-mode guidance
  - validates overrides validator no-profile-config path returns explicit profile-mode guidance

### Changed

- README now documents explicit message for `fallback_reason=no_profiles_config`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.151-m3-error-code-profile-mode-not-configured-hint`.

## [0.3.150-m3-error-code-profile-default-first-order] - 2026-02-19

### Added

- Available profile ordering strategy for unknown profile responses:
  - `available_profiles` now prioritizes `default_profile` first
  - remaining profiles keep alphabetical order
- New tests:
  - validates lint validator no-match case returns `available_profiles` with `default_profile` first
  - validates overrides validator no-match case returns `available_profiles` with `default_profile` first

### Changed

- README now documents `available_profiles` ordering semantics.
- Summary schema version: `1`
- Backend app version bumped to `0.3.150-m3-error-code-profile-default-first-order`.

## [0.3.149-m3-error-code-profile-fallback-reason] - 2026-02-19

### Added

- Unknown profile JSON context now includes structured fallback reason:
  - `fallback_reason=close_match` when fuzzy suggestions exist
  - `fallback_reason=no_close_match` when no fuzzy suggestion but profiles exist
  - `fallback_reason=no_profiles_config` when profile mode is not configured
- New tests:
  - validates fallback reason for close-match suggestion paths (lint/overrides)
  - validates fallback reason for no-close-match paths (lint/overrides)

### Changed

- README now documents `fallback_reason` enum semantics.
- Summary schema version: `1`
- Backend app version bumped to `0.3.149-m3-error-code-profile-fallback-reason`.

## [0.3.148-m3-error-code-profile-no-match-fallback] - 2026-02-19

### Added

- No-match fallback message for unknown profile:
  - when fuzzy match returns no candidate, validators now append:
    - `Available profiles: <profile-list>.`
- New tests:
  - validates lint validator no-match case returns empty suggestions and contains available profiles in message
  - validates overrides validator no-match case returns empty suggestions and contains available profiles in message

### Changed

- README now documents no-match fallback behavior for unknown profile errors.
- Summary schema version: `1`
- Backend app version bumped to `0.3.148-m3-error-code-profile-no-match-fallback`.

## [0.3.147-m3-error-code-profile-suggestion-helper] - 2026-02-19

### Added

- Shared profile suggestion helper in both validators:
  - `_build_profile_suggestion_payload(...)` added in lint validator
  - `_build_profile_suggestion_payload(...)` added in overrides validator
- New tests:
  - verifies lint validator script contains the shared helper entry point
  - verifies overrides validator script contains the shared helper entry point

### Changed

- Unknown profile suggestion building logic is centralized per script to reduce duplication.
- Summary schema version: `1`
- Backend app version bumped to `0.3.147-m3-error-code-profile-suggestion-helper`.

## [0.3.146-m3-error-code-lint-profile-config-aware-command] - 2026-02-19

### Added

- Path-aware command template for unknown profile JSON context:
  - lint validator `suggested_command` now includes current `--lint-config-file "<path>"`
  - overrides validator `suggested_command` now includes current `--lint-config-file "<path>"`
- New tests:
  - validates lint validator `suggested_command` includes lint-config-file path
  - validates overrides validator `suggested_command` includes lint-config-file path

### Changed

- README now documents that `suggested_command` includes lint config path.
- Summary schema version: `1`
- Backend app version bumped to `0.3.146-m3-error-code-lint-profile-config-aware-command`.

## [0.3.145-m3-error-code-lint-profile-command-context] - 2026-02-19

### Added

- Unknown profile JSON error context now includes full command template:
  - `suggested_command` for `validate-validator-error-code-metadata-lint.py`
  - `suggested_command` for `validate-validator-error-code-metadata-overrides.py`
- New tests:
  - validates lint validator JSON context contains `suggested_command`
  - validates overrides validator JSON context contains `suggested_command`

### Changed

- README now documents `suggested_command` in unknown profile JSON context.
- Summary schema version: `1`
- Backend app version bumped to `0.3.145-m3-error-code-lint-profile-command-context`.

## [0.3.144-m3-error-code-lint-profile-cli-args-context] - 2026-02-19

### Added

- Unknown profile JSON error context now includes quick-fix args field:
  - `suggested_cli_args` for `validate-validator-error-code-metadata-lint.py`
  - `suggested_cli_args` for `validate-validator-error-code-metadata-overrides.py`
- New tests:
  - validates lint validator JSON context contains `suggested_cli_args`
  - validates overrides validator JSON context contains `suggested_cli_args`

### Changed

- README now documents `suggested_cli_args` in unknown profile JSON context.
- Summary schema version: `1`
- Backend app version bumped to `0.3.144-m3-error-code-lint-profile-cli-args-context`.

## [0.3.143-m3-error-code-lint-profile-cli-hint] - 2026-02-19

### Added

- Unknown profile plain stderr hints now include quick-fix CLI args:
  - `validate-validator-error-code-metadata-lint.py`
    - `Try: --lint-profile <suggested_profile>`
  - `validate-validator-error-code-metadata-overrides.py`
    - `Try: --lint-profile <suggested_profile>`
- New tests:
  - validates lint validator plain stderr contains `--lint-profile <suggested>`
  - validates overrides validator plain stderr contains `--lint-profile <suggested>`

### Changed

- README now documents quick-fix CLI args in unknown profile stderr hints.
- Summary schema version: `1`
- Backend app version bumped to `0.3.143-m3-error-code-lint-profile-cli-hint`.

## [0.3.142-m3-error-code-lint-profile-message-hint] - 2026-02-19

### Added

- Human-readable profile hint in plain stderr output for unknown profile:
  - `validate-validator-error-code-metadata-lint.py` now appends
    - `Did you mean: <profile>?` when fuzzy suggestion exists
  - `validate-validator-error-code-metadata-overrides.py` now appends
    - `Did you mean: <profile>?` when fuzzy suggestion exists
- New tests:
  - validates lint validator plain stderr includes suggested profile hint
  - validates overrides validator plain stderr includes suggested profile hint

### Changed

- README now documents plain stderr suggestion behavior.
- Summary schema version: `1`
- Backend app version bumped to `0.3.142-m3-error-code-lint-profile-message-hint`.

## [0.3.141-m3-error-code-lint-profile-suggestion] - 2026-02-19

### Added

- Unknown lint profile errors now include nearby profile suggestions:
  - `validate-validator-error-code-metadata-lint.py` JSON error `context` includes:
    - `available_profiles`
    - `suggested_profiles` (from fuzzy matching)
  - `validate-validator-error-code-metadata-overrides.py` JSON error `context` includes:
    - `available_profiles`
    - `suggested_profiles`
- New tests:
  - validates lint validator returns suggested profile for typo input
  - validates overrides validator returns suggested profile for typo input

### Changed

- README now documents suggested profile fields in JSON error payloads.
- Summary schema version: `1`
- Backend app version bumped to `0.3.141-m3-error-code-lint-profile-suggestion`.

## [0.3.140-m3-error-code-lint-profile-env] - 2026-02-19

### Added

- `LINT_PROFILE` environment variable support for metadata lint profile selection:
  - `validate-validator-error-code-metadata-lint.py`
  - `validate-validator-error-code-metadata-overrides.py`
- New tests:
  - validates metadata lint validator can use `LINT_PROFILE` when `--lint-profile` is not provided
  - validates metadata overrides validator can use `LINT_PROFILE` when `--lint-profile` is not provided

### Changed

- Lint profile precedence is now explicit: `--lint-profile` > `LINT_PROFILE` > `default_profile`.
- README now documents env-based profile selection and precedence.
- Summary schema version: `1`
- Backend app version bumped to `0.3.140-m3-error-code-lint-profile-env`.

## [0.3.139-m3-error-code-lint-profile-support] - 2026-02-19

### Added

- Metadata lint profile mode support:
  - lint config schema now supports `default_profile + profiles` structure.
  - `validate-validator-error-code-metadata-lint.py` now supports:
    - `--lint-profile <profile>`
    - `error_code_metadata_lint_profile_not_found`
  - `validate-validator-error-code-metadata-overrides.py` now supports:
    - `--lint-profile <profile>`
    - `error_code_metadata_overrides_lint_profile_not_found`
- New tests:
  - validates metadata lint validator supports profiled lint config
  - validates metadata lint validator returns structured error for unknown profile
  - validates metadata overrides validator supports lint profile selection
  - validates metadata overrides validator returns structured error for unknown profile

### Changed

- README now documents lint profile config and `--lint-profile` usage.
- Summary schema version: `1`
- Backend app version bumped to `0.3.139-m3-error-code-lint-profile-support`.

## [0.3.138-m3-error-code-lint-validator] - 2026-02-19

### Added

- New metadata lint schema file:
  - `refactor/backend/config/schemas/validator-error-code-metadata-lint.schema.json`
- New metadata lint validator script:
  - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
  - validates lint config payload against schema and action-verb constraints
  - supports `--json-errors` with `error_code_metadata_lint_*` namespace
- New tests:
  - validates metadata lint schema file exists and matches JSON Schema contract
  - validates metadata lint validator passes default config
  - validates validator emits structured JSON error for schema violations

### Changed

- CI now enforces metadata lint config validation:
  - `python3 scripts/validate-validator-error-code-metadata-lint.py`
- README now documents metadata lint schema and validator usage.
- Summary schema version: `1`
- Backend app version bumped to `0.3.138-m3-error-code-lint-validator`.

## [0.3.137-m3-error-code-lint-configurable] - 2026-02-19

### Added

- New metadata lint config file:
  - `refactor/backend/config/validator-error-code-metadata-lint.json`
  - includes `min_remediation_length` and `action_verbs`
- Metadata overrides validator now supports:
  - `--lint-config-file <path>`
  - loading remediation quality rules from lint config instead of hardcoded values
- New tests:
  - validates lint config file exists and contains valid contract fields
  - validates custom lint config is honored by validator
  - validates invalid lint config returns structured JSON error

### Changed

- `validate-validator-error-code-metadata-overrides.py` now enforces lint rules from external config.
- README now documents metadata lint config path and custom lint-config flag.
- Summary schema version: `1`
- Backend app version bumped to `0.3.137-m3-error-code-lint-configurable`.

## [0.3.136-m3-error-code-overrides-semantic-lint] - 2026-02-19

### Added

- Metadata overrides validator now includes semantic lint rules:
  - rejects placeholder text in override `description/remediation` based on marker config
  - requires override remediation text to be actionable (verb + minimum length)
- New validator error codes:
  - `error_code_metadata_overrides_placeholder_text_detected`
  - `error_code_metadata_overrides_remediation_quality_invalid`
  - `error_code_metadata_overrides_placeholder_markers_file_not_found`
  - `error_code_metadata_overrides_placeholder_markers_invalid`
- New tests:
  - validates validator fails with structured error when override remediation contains placeholder text
  - validates validator fails with structured error when remediation is non-actionable

### Changed

- README now documents semantic lint behavior in metadata overrides validator.
- Summary schema version: `1`
- Backend app version bumped to `0.3.136-m3-error-code-overrides-semantic-lint`.

## [0.3.135-m3-error-code-metadata-overrides-validator] - 2026-02-19

### Added

- New metadata overrides schema:
  - `refactor/backend/config/schemas/validator-error-code-metadata-overrides.schema.json`
- New metadata overrides validator script:
  - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
  - validates override payload schema and override targets against catalog (`group.code`)
  - supports `--json-errors` (`error_code_metadata_overrides_*`)
- New tests:
  - validates metadata overrides schema file exists
  - validates overrides validator passes default config
  - validates overrides validator emits structured error for unknown override code

### Changed

- CI now enforces metadata overrides validation:
  - `python3 scripts/validate-validator-error-code-metadata-overrides.py`
- README now documents metadata overrides schema and validator usage.
- Summary schema version: `1`
- Backend app version bumped to `0.3.135-m3-error-code-metadata-overrides-validator`.

## [0.3.134-m3-error-code-metadata-overrides] - 2026-02-19

### Added

- New metadata override config file:
  - `refactor/backend/config/validator-error-code-metadata-overrides.json`
- `sync-validator-error-codes.py` now supports:
  - `--metadata-overrides-file <path>`
  - override payload format: `group -> code -> {description|severity|remediation}`
  - strict validation: unknown override group/code is rejected
- New tests:
  - validates metadata overrides config file exists
  - validates custom metadata overrides are applied
  - validates script fails on unknown override code

### Changed

- README now documents metadata override config and override rules.
- Summary schema version: `1`
- Backend app version bumped to `0.3.134-m3-error-code-metadata-overrides`.

## [0.3.133-m3-error-code-metadata-policy] - 2026-02-19

### Added

- Sync policy now auto-infers severity/remediation by error-code family:
  - `*_unexpected_error` -> `severity=critical` + stack-trace remediation
  - `*_json_parse_error` -> JSON syntax remediation
  - `*_file_not_found` -> file path/existence remediation
  - `*_schema_invalid` / `*_schema_validation_failed` -> schema/payload remediation
- Legacy metadata upgrade behavior in sync script:
  - when legacy default values are present, sync upgrades to inferred specific metadata
- New tests:
  - validates key codes use specific metadata policy
  - validates sync upgrades downgraded legacy metadata for unexpected errors

### Changed

- `refactor/backend/config/validator-error-codes.json` refreshed with policy-based metadata values.
- README now documents metadata policy defaults for validator error catalog.
- Summary schema version: `1`
- Backend app version bumped to `0.3.133-m3-error-code-metadata-policy`.

## [0.3.132-m3-error-code-catalog-structured-entries] - 2026-02-19

### Added

- Validator error code catalog entries are now structured objects:
  - `{description, severity, remediation}`
  - default severity is `error`
- `sync-validator-error-codes.py` now supports legacy string-entry migration:
  - legacy `code: "description"` input is auto-upgraded to structured entry output
- Strict placeholder gate now scans both fields:
  - `description`
  - `remediation`
- New tests:
  - validates catalog entries are structured objects with required fields
  - validates sync script migrates legacy string entries
  - validates strict gate blocks placeholder in remediation field

### Changed

- Catalog schema now enforces structured entry fields and severity enum.
- README now documents structured catalog entry contract and strict gate field scope.
- `refactor/backend/config/validator-error-codes.json` migrated to structured entry format.
- Summary schema version: `1`
- Backend app version bumped to `0.3.132-m3-error-code-catalog-structured-entries`.

## [0.3.131-m3-error-code-catalog-schema] - 2026-02-19

### Added

- New validator error code catalog schema:
  - `refactor/backend/config/schemas/validator-error-codes.schema.json`
  - enforces required groups and non-empty description strings
- New validator script for catalog contract:
  - `refactor/backend/scripts/validate-validator-error-code-catalog.py`
  - validates catalog against JSON Schema and group-prefix naming rule (`<group>_`)
  - supports structured error output via `--json-errors` (`error_code_catalog_*`)
- New tests:
  - validates catalog schema file exists and contains required groups
  - validates catalog validator script passes default catalog
  - validates catalog validator emits structured schema-validation errors

### Changed

- CI now enforces catalog schema validation:
  - `python3 scripts/validate-validator-error-code-catalog.py`
- README now documents catalog schema path and validator usage.
- Summary schema version: `1`
- Backend app version bumped to `0.3.131-m3-error-code-catalog-schema`.

## [0.3.130-m3-marker-error-code-catalog] - 2026-02-19

### Added

- Marker validator error codes are now included in unified validator error code governance:
  - marker validator exposes `VALIDATOR_ERROR_CODES`
  - catalog adds `placeholder_markers` group in `refactor/backend/config/validator-error-codes.json`
  - sync script now harvests marker validator error code registry
- New tests:
  - validates catalog includes `placeholder_markers` group
  - validates marker validator registry is exposed and namespaced
  - validates catalog coverage check includes marker validator script codes

### Changed

- README now documents catalog group set including `placeholder_markers`.
- Summary schema version: `1`
- Backend app version bumped to `0.3.130-m3-marker-error-code-catalog`.

## [0.3.129-m3-marker-validator-json-errors] - 2026-02-19

### Added

- `validate-validator-placeholder-markers.py` now supports structured error output:
  - `--json-errors`
  - emits JSON payload with `validator/code/message/context` on failures
  - error code namespace: `placeholder_markers_*`
- New tests:
  - validates json error payload for duplicate marker failures
  - validates json error payload for schema validation failures

### Changed

- README now documents `--json-errors` usage for marker config validator.
- Summary schema version: `1`
- Backend app version bumped to `0.3.129-m3-marker-validator-json-errors`.

## [0.3.128-m3-marker-schema-validation] - 2026-02-19

### Added

- New marker config schema file:
  - `refactor/backend/config/schemas/validator-placeholder-markers.schema.json`
  - defines required `markers` array and base type constraints
- `validate-validator-placeholder-markers.py` now supports schema validation:
  - `--schema-file <path>`
  - validates schema itself (`Draft2020-12`) and validates marker payload against schema
- New tests:
  - validates marker schema file exists and includes required contract fields
  - validates marker validator fails on schema violations
  - validates marker validator fails when given invalid schema file

### Changed

- README now documents marker schema path and custom schema flag.
- Summary schema version: `1`
- Backend app version bumped to `0.3.128-m3-marker-schema-validation`.

## [0.3.127-m3-placeholder-marker-validator] - 2026-02-19

### Added

- New marker config validator script:
  - `refactor/backend/scripts/validate-validator-placeholder-markers.py`
  - validates placeholder marker config shape, non-empty values, format, and duplicate markers
- New tests:
  - validates marker validator script passes default config
  - validates marker validator script fails when duplicate markers exist

### Changed

- CI now enforces marker config validation before strict catalog sync:
  - `python3 scripts/validate-validator-placeholder-markers.py`
- `sync-validator-error-codes.py` now fails on duplicate markers in loaded marker config.
- README now documents marker config validation command.
- Summary schema version: `1`
- Backend app version bumped to `0.3.127-m3-placeholder-marker-validator`.

## [0.3.126-m3-validator-placeholder-config] - 2026-02-19

### Added

- New placeholder marker config file:
  - `refactor/backend/config/validator-placeholder-markers.json`
  - default markers: `TODO`, `TBD`, `FIXME`
- `sync-validator-error-codes.py` now supports:
  - `--placeholder-markers-file <path>`
  - loading strict-description marker vocabulary from config file
- New tests:
  - validates placeholder marker config file exists and is non-empty
  - validates strict error output includes `group.code` entry and remediation hint
  - validates custom placeholder marker file is honored in strict mode

### Changed

- Strict placeholder failure output is now structured with:
  - marker list
  - per-violation `group.code` line
  - remediation guidance
- README now documents marker config path and custom marker file usage.
- Summary schema version: `1`
- Backend app version bumped to `0.3.126-m3-validator-placeholder-config`.

## [0.3.125-m3-validator-placeholder-vocabulary] - 2026-02-19

### Added

- Strict description placeholder detection now covers multiple markers:
  - `TODO:`
  - `TBD:`
  - `FIXME:`
  - case-insensitive match
- New test:
  - validates strict mode fails when catalog contains `TBD:` / `FIXME:` placeholders

### Changed

- README strict-description note now documents full placeholder marker set.
- Summary schema version: `1`
- Backend app version bumped to `0.3.125-m3-validator-placeholder-vocabulary`.

## [0.3.124-m3-validator-description-strict-check] - 2026-02-19

### Added

- `sync-validator-error-codes.py` now supports `--strict-descriptions`:
  - fails when any error-code description uses `TODO:` placeholder text
- New tests:
  - validates strict mode passes on current catalog
  - validates strict mode fails when catalog contains TODO placeholder description

### Changed

- CI now enforces strict description checks:
  - `python3 scripts/sync-validator-error-codes.py --check --strict-descriptions`
- README now documents strict description behavior.
- Summary schema version: `1`
- Backend app version bumped to `0.3.124-m3-validator-description-strict-check`.

## [0.3.123-m3-validator-error-code-sync] - 2026-02-19

### Added

- New sync script:
  - `refactor/backend/scripts/sync-validator-error-codes.py`
  - generates validator error code catalog from validator script registries
  - supports `--check` mode for CI drift detection
- New tests:
  - validates sync script passes on default catalog
  - validates sync script check fails on catalog drift

### Changed

- CI now includes validator error code catalog sync check:
  - `python3 scripts/sync-validator-error-codes.py --check`
- README now documents validator catalog sync/check command.
- Summary schema version: `1`
- Backend app version bumped to `0.3.123-m3-validator-error-code-sync`.

## [0.3.122-m3-validator-error-code-registry] - 2026-02-19

### Added

- Validator scripts now expose explicit error-code registries:
  - `validate-strict-gate-summary-schema.py` -> `VALIDATOR_ERROR_CODES`
  - `validate-summary-contract-changelog.py` -> `VALIDATOR_ERROR_CODES`
- New tests:
  - verifies both validator scripts expose non-empty error-code registries
  - verifies catalog coverage includes declared registry codes (not only literal codes)

### Changed

- Both validator scripts now emit JSON error `code` values via registry constants.
- README now documents validator registry expectation.
- Summary schema version: `1`
- Backend app version bumped to `0.3.122-m3-validator-error-code-registry`.

## [0.3.121-m3-validator-error-code-catalog] - 2026-02-19

### Added

- New validator error code catalog:
  - `refactor/backend/config/validator-error-codes.json`
  - includes grouped codes for `summary_schema` and `summary_contract`
- New tests:
  - verifies catalog file exists with required groups
  - verifies catalog covers all literal validator error codes

### Changed

- README now documents validator error code catalog path.
- Summary schema version: `1`
- Backend app version bumped to `0.3.121-m3-validator-error-code-catalog`.

## [0.3.120-m3-validator-error-code-prefix] - 2026-02-19

### Added

- Validator json error codes now use explicit namespaces:
  - summary schema validator: `summary_schema_*`
  - contract changelog validator: `summary_contract_*`
- New tests:
  - validates summary schema validator json error code prefix
  - validates contract changelog validator json error code prefix

### Changed

- Existing json-error tests now assert namespaced error codes.
- README now documents json error code namespace conventions.
- Summary schema version: `1`
- Backend app version bumped to `0.3.120-m3-validator-error-code-prefix`.

## [0.3.119-m3-contract-validator-json-errors] - 2026-02-19

### Added

- `validate-summary-contract-changelog.py` now supports structured error output:
  - `--json-errors`
  - emits JSON payload with `validator/code/message/context` on failures
- New tests:
  - verifies `--json-errors` payload for missing summary schema note
  - verifies `--json-errors` payload for changelog/app version mismatch

### Changed

- README now documents `--json-errors` usage for contract changelog validator.
- Summary schema version: `1`
- Backend app version bumped to `0.3.119-m3-contract-validator-json-errors`.

## [0.3.118-m3-summary-validator-json-errors] - 2026-02-19

### Added

- `validate-strict-gate-summary-schema.py` now supports structured error output:
  - `--json-errors`
  - emits JSON payload with `validator/code/message/context` on failures
- New test:
  - validates `--json-errors` outputs structured payload for consistency failures

### Changed

- README now documents `--json-errors` usage for schema validator.
- Summary schema version: `1`
- Backend app version bumped to `0.3.118-m3-summary-validator-json-errors`.

## [0.3.117-m3-summary-consistency-error-details] - 2026-02-19

### Added

- `validate-strict-gate-summary-schema.py` now emits field-level consistency mismatch details:
  - `changed_files_count` expected/actual values
  - `total_added_lines` expected/actual values
  - `total_removed_lines` expected/actual values
  - per-module total mismatch with module name and expected/actual values
- New test:
  - validator fails with explicit module mismatch message

### Changed

- Existing inconsistent totals test now asserts specific mismatch key in stderr.
- README now documents field-level mismatch diagnostics.
- Summary schema version: `1`
- Backend app version bumped to `0.3.117-m3-summary-consistency-error-details`.

## [0.3.116-m3-summary-example-consistency-guard] - 2026-02-19

### Added

- `validate-strict-gate-summary-schema.py` now validates example payload consistency:
  - `changed_files_count == len(files)`
  - `total_added_lines == sum(files[].added_lines)`
  - `total_removed_lines == sum(files[].removed_lines)`
  - module totals equal per-file module sums
- New test:
  - validator fails when example totals are inconsistent

### Changed

- README now documents consistency checks for summary example payload.
- Summary schema version: `1`
- Backend app version bumped to `0.3.116-m3-summary-example-consistency-guard`.

## [0.3.115-m3-summary-contract-changelog-link] - 2026-02-19

### Added

- New contract validator script:
  - `refactor/backend/scripts/validate-summary-contract-changelog.py`
  - validates latest changelog entry version equals backend app version
  - validates latest changelog entry includes summary schema version note
- New tests:
  - verifies CI script includes contract changelog validator
  - verifies contract changelog validator passes default files
  - verifies validator fails when schema version note is missing

### Changed

- Backend CI now runs contract changelog validator.
- README now documents changelog contract validation command.
- Summary schema version: `1`
- Backend app version bumped to `0.3.115-m3-summary-contract-changelog-link`.

## [0.3.114-m3-summary-schema-example-golden] - 2026-02-19

### Added

- New strict gate summary example payload:
  - `refactor/backend/config/schemas/strict-gate-summary.example.json`
- `validate-strict-gate-summary-schema.py` now validates example payload against schema.
- New tests:
  - validator passes with default example payload
  - validator fails when example payload violates schema

### Changed

- README now documents example payload and example validation behavior.
- Backend app version bumped to `0.3.114-m3-summary-schema-example-golden`.

## [0.3.113-m3-summary-schema-version-drift-guard] - 2026-02-19

### Added

- `validate-strict-gate-summary-schema.py` now checks schema version drift:
  - compares `properties.schema_version.const` in schema file
  - against `SUMMARY_SCHEMA_VERSION` in `sync-strict-gate-alert-thresholds.py`
- New test:
  - validator fails when schema version and sync script version mismatch

### Changed

- README now explicitly documents schema-version consistency check behavior.
- Backend app version bumped to `0.3.113-m3-summary-schema-version-drift-guard`.

## [0.3.112-m3-summary-schema-validator-ci] - 2026-02-19

### Added

- New schema validator script:
  - `refactor/backend/scripts/validate-strict-gate-summary-schema.py`
  - validates JSON parse, JSON Schema draft validity, and required contract fields
- New tests:
  - verifies CI script includes summary schema validator
  - verifies validator passes default schema
  - verifies validator fails on invalid JSON

### Changed

- Backend CI script now runs strict gate summary schema validation.
- README now documents validator usage.
- Backend app version bumped to `0.3.112-m3-summary-schema-validator-ci`.

## [0.3.111-m3-summary-json-schema-validation] - 2026-02-19

### Added

- New formal JSON Schema for strict gate summary payload:
  - `refactor/backend/config/schemas/strict-gate-summary.schema.json`
- New schema validation test:
  - validates `--summary-format json` output against schema

### Changed

- Added explicit dev dependency declaration: `jsonschema>=4.21.0`.
- README now documents the schema file path.
- Backend app version bumped to `0.3.111-m3-summary-json-schema-validation`.

## [0.3.110-m3-threshold-summary-schema-version] - 2026-02-19

### Added

- JSON summary payload now includes a schema contract field:
  - `schema_version: \"1\"`
- New test:
  - verifies summary JSON contains `schema_version`

### Changed

- README now documents `schema_version` in JSON summary payload.
- Backend app version bumped to `0.3.110-m3-threshold-summary-schema-version`.

## [0.3.109-m3-threshold-sync-summary-output-file] - 2026-02-19

### Added

- `sync-strict-gate-alert-thresholds.py` now supports:
  - `--summary-output <path>`
  - writes JSON summary payload to file when used with `--summary-only --summary-format json`
- New tests:
  - verifies summary JSON file is written and matches stdout payload
  - verifies `--summary-output` requires `--summary-format json`

### Changed

- README now includes `--summary-output` usage example.
- Backend app version bumped to `0.3.109-m3-threshold-sync-summary-output-file`.

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
