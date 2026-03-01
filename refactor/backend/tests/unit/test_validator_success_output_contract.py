from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


VALIDATOR_SCRIPT_CASES: tuple[tuple[str, str], ...] = (
    (
        "validate-validator-error-context-high-frequency-schema.py",
        "validate-validator-error-context-high-frequency-schema",
    ),
    ("validate-alertmanager-route-consistency.py", "validate-alertmanager-route-consistency"),
    ("validate-notification-retry-runbook.py", "validate-notification-retry-runbook"),
    ("validate-profile-suggestion-actions-schema.py", "validate-profile-suggestion-actions-schema"),
    ("validate-validator-error-code-metadata-overrides.py", "validate-validator-error-code-metadata-overrides"),
    ("validate-validator-placeholder-markers.py", "validate-validator-placeholder-markers"),
    ("validate-summary-contract-changelog.py", "validate-summary-contract-changelog"),
    ("validate-validator-error-code-metadata-lint.py", "validate-validator-error-code-metadata-lint"),
    ("validate-strict-gate-summary-schema.py", "validate-strict-gate-summary-schema"),
    ("validate-validator-error-code-catalog.py", "validate-validator-error-code-catalog"),
)

VALIDATOR_SCRIPT_CLI_ERROR_CASES: tuple[tuple[str, str, str], ...] = (
    (
        "validate-validator-error-context-high-frequency-schema.py",
        "validate-validator-error-context-high-frequency-schema",
        "error_context_high_frequency_cli_args_invalid",
    ),
    (
        "validate-alertmanager-route-consistency.py",
        "validate-alertmanager-route-consistency",
        "alertmanager_route_consistency_cli_args_invalid",
    ),
    (
        "validate-notification-retry-runbook.py",
        "validate-notification-retry-runbook",
        "notification_retry_runbook_cli_args_invalid",
    ),
    (
        "validate-profile-suggestion-actions-schema.py",
        "validate-profile-suggestion-actions-schema",
        "profile_suggestion_actions_cli_args_invalid",
    ),
    (
        "validate-validator-error-code-metadata-overrides.py",
        "validate-validator-error-code-metadata-overrides",
        "error_code_metadata_overrides_cli_args_invalid",
    ),
    (
        "validate-validator-placeholder-markers.py",
        "validate-validator-placeholder-markers",
        "placeholder_markers_cli_args_invalid",
    ),
    (
        "validate-summary-contract-changelog.py",
        "validate-summary-contract-changelog",
        "summary_contract_cli_args_invalid",
    ),
    (
        "validate-validator-error-code-metadata-lint.py",
        "validate-validator-error-code-metadata-lint",
        "error_code_metadata_lint_cli_args_invalid",
    ),
    (
        "validate-strict-gate-summary-schema.py",
        "validate-strict-gate-summary-schema",
        "summary_schema_cli_args_invalid",
    ),
    (
        "validate-validator-error-code-catalog.py",
        "validate-validator-error-code-catalog",
        "error_code_catalog_cli_args_invalid",
    ),
)

VALIDATOR_SCRIPT_BUSINESS_FAILURE_CASES: tuple[tuple[str, str, str, str], ...] = (
    (
        "validate-validator-error-context-high-frequency-schema.py",
        "validate-validator-error-context-high-frequency-schema",
        "--schema-file",
        "missing-validator-error-context-high-frequency.schema.json",
    ),
    (
        "validate-alertmanager-route-consistency.py",
        "validate-alertmanager-route-consistency",
        "--rules-dir",
        "missing-rules-dir",
    ),
    (
        "validate-notification-retry-runbook.py",
        "validate-notification-retry-runbook",
        "--runbook-file",
        "missing-runbook.md",
    ),
    (
        "validate-profile-suggestion-actions-schema.py",
        "validate-profile-suggestion-actions-schema",
        "--schema-file",
        "missing-profile-suggestion-actions.schema.json",
    ),
    (
        "validate-validator-error-code-metadata-overrides.py",
        "validate-validator-error-code-metadata-overrides",
        "--overrides-file",
        "missing-metadata-overrides.json",
    ),
    (
        "validate-validator-placeholder-markers.py",
        "validate-validator-placeholder-markers",
        "--markers-file",
        "missing-placeholder-markers.json",
    ),
    (
        "validate-summary-contract-changelog.py",
        "validate-summary-contract-changelog",
        "--app-file",
        "missing-main.py",
    ),
    (
        "validate-validator-error-code-metadata-lint.py",
        "validate-validator-error-code-metadata-lint",
        "--lint-config-file",
        "missing-metadata-lint.json",
    ),
    (
        "validate-strict-gate-summary-schema.py",
        "validate-strict-gate-summary-schema",
        "--schema-file",
        "missing-summary-schema.json",
    ),
    (
        "validate-validator-error-code-catalog.py",
        "validate-validator-error-code-catalog",
        "--catalog-file",
        "missing-validator-error-codes.json",
    ),
)


def _load_success_schema(backend_root: Path) -> dict:
    schema_file = backend_root / "config" / "schemas" / "validator-success-output.schema.json"
    assert schema_file.exists()

    schema_payload = json.loads(schema_file.read_text(encoding="utf-8"))
    assert isinstance(schema_payload, dict)
    Draft202012Validator.check_schema(schema_payload)
    return schema_payload


def _load_error_schema(backend_root: Path) -> dict:
    schema_file = backend_root / "config" / "schemas" / "validator-error-output.schema.json"
    assert schema_file.exists()

    schema_payload = json.loads(schema_file.read_text(encoding="utf-8"))
    assert isinstance(schema_payload, dict)
    Draft202012Validator.check_schema(schema_payload)
    return schema_payload


def _load_error_context_schema(backend_root: Path) -> dict:
    schema_file = backend_root / "config" / "schemas" / "validator-error-context-high-frequency.schema.json"
    assert schema_file.exists()

    schema_payload = json.loads(schema_file.read_text(encoding="utf-8"))
    assert isinstance(schema_payload, dict)
    Draft202012Validator.check_schema(schema_payload)
    return schema_payload


def _run_validator_with_json_errors(backend_root: Path, script_file_name: str, extra_args: list[str]) -> dict:
    script_file = backend_root / "scripts" / script_file_name
    assert script_file.exists()
    completed = subprocess.run(
        [
            sys.executable,
            str(script_file),
            "--json-errors",
            *extra_args,
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert completed.stdout == ""
    payload = json.loads(completed.stderr)
    assert isinstance(payload, dict)
    return payload


def test_validator_success_output_schema_exists_and_is_valid() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    _load_success_schema(backend_root=backend_root)


def test_validator_error_output_schema_exists_and_is_valid() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    _load_error_schema(backend_root=backend_root)


def test_validator_error_context_high_frequency_schema_exists_and_is_valid() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    _load_error_context_schema(backend_root=backend_root)


def test_validator_scripts_json_output_conforms_base_contract() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_payload = _load_success_schema(backend_root=backend_root)
    validator = Draft202012Validator(schema_payload)

    for script_file_name, expected_validator_name in VALIDATOR_SCRIPT_CASES:
        script_file = backend_root / "scripts" / script_file_name
        assert script_file.exists()

        completed = subprocess.run(
            [
                sys.executable,
                str(script_file),
                "--json-output",
            ],
            cwd=backend_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0
        payload = json.loads(completed.stdout)
        validator.validate(payload)
        assert payload["validator"] == expected_validator_name
        assert payload["status"] == "ok"


def test_validator_scripts_both_json_flags_success_mode_contract() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_payload = _load_success_schema(backend_root=backend_root)
    validator = Draft202012Validator(schema_payload)

    for script_file_name, expected_validator_name in VALIDATOR_SCRIPT_CASES:
        script_file = backend_root / "scripts" / script_file_name
        assert script_file.exists()

        completed = subprocess.run(
            [
                sys.executable,
                str(script_file),
                "--json-output",
                "--json-errors",
            ],
            cwd=backend_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0
        assert completed.stderr == ""
        payload = json.loads(completed.stdout)
        validator.validate(payload)
        assert payload["validator"] == expected_validator_name
        assert payload["status"] == "ok"


def test_validator_scripts_both_json_flags_unknown_args_emit_structured_error() -> None:
    backend_root = Path(__file__).resolve().parents[2]

    for script_file_name, expected_validator_name, expected_code in VALIDATOR_SCRIPT_CLI_ERROR_CASES:
        script_file = backend_root / "scripts" / script_file_name
        assert script_file.exists()

        completed = subprocess.run(
            [
                sys.executable,
                str(script_file),
                "--json-output",
                "--json-errors",
                "--unknown-flag",
            ],
            cwd=backend_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode != 0
        assert completed.stdout == ""
        payload = json.loads(completed.stderr)
        assert payload["validator"] == expected_validator_name
        assert payload["code"] == expected_code
        assert payload["context"]["failure_mode"] == "unknown_args"
        assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_validator_scripts_json_errors_conform_base_contract_cli_failures() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_payload = _load_error_schema(backend_root=backend_root)
    validator = Draft202012Validator(schema_payload)

    for script_file_name, expected_validator_name, expected_code in VALIDATOR_SCRIPT_CLI_ERROR_CASES:
        script_file = backend_root / "scripts" / script_file_name
        assert script_file.exists()

        completed = subprocess.run(
            [
                sys.executable,
                str(script_file),
                "--json-errors",
                "--unknown-flag",
            ],
            cwd=backend_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode != 0
        assert completed.stdout == ""
        payload = json.loads(completed.stderr)
        validator.validate(payload)
        assert payload["validator"] == expected_validator_name
        assert payload["code"] == expected_code


def test_validator_scripts_both_json_flags_business_failure_emit_structured_error(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    cli_invalid_code_by_validator = {
        validator_name: cli_invalid_code
        for _script_file_name, validator_name, cli_invalid_code in VALIDATOR_SCRIPT_CLI_ERROR_CASES
    }

    for script_file_name, expected_validator_name, failure_arg_name, missing_name in VALIDATOR_SCRIPT_BUSINESS_FAILURE_CASES:
        script_file = backend_root / "scripts" / script_file_name
        assert script_file.exists()
        missing_path = tmp_path / missing_name
        assert not missing_path.exists()

        completed = subprocess.run(
            [
                sys.executable,
                str(script_file),
                "--json-output",
                "--json-errors",
                failure_arg_name,
                str(missing_path),
            ],
            cwd=backend_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode != 0
        assert completed.stdout == ""
        payload = json.loads(completed.stderr)
        assert payload["validator"] == expected_validator_name
        assert payload["code"] != cli_invalid_code_by_validator[expected_validator_name]


def test_validator_scripts_json_errors_conform_base_contract_business_failures(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_payload = _load_error_schema(backend_root=backend_root)
    validator = Draft202012Validator(schema_payload)
    cli_invalid_code_by_validator = {
        validator_name: cli_invalid_code
        for _script_file_name, validator_name, cli_invalid_code in VALIDATOR_SCRIPT_CLI_ERROR_CASES
    }

    for script_file_name, expected_validator_name, failure_arg_name, missing_name in VALIDATOR_SCRIPT_BUSINESS_FAILURE_CASES:
        script_file = backend_root / "scripts" / script_file_name
        assert script_file.exists()
        missing_path = tmp_path / missing_name
        assert not missing_path.exists()

        completed = subprocess.run(
            [
                sys.executable,
                str(script_file),
                "--json-errors",
                failure_arg_name,
                str(missing_path),
            ],
            cwd=backend_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode != 0
        assert completed.stdout == ""
        payload = json.loads(completed.stderr)
        validator.validate(payload)
        assert payload["validator"] == expected_validator_name
        assert payload["code"] != cli_invalid_code_by_validator[expected_validator_name]
        assert isinstance(payload.get("context"), dict)


def test_key_validator_scripts_json_errors_multi_business_failure_matrix(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_payload = _load_error_schema(backend_root=backend_root)
    validator = Draft202012Validator(schema_payload)

    no_version_app_file = tmp_path / "no-version-main.py"
    no_version_app_file.write_text("print('no version')\n", encoding="utf-8")

    malformed_summary_schema_file = tmp_path / "malformed-summary-schema.json"
    malformed_summary_schema_file.write_text("{ bad json", encoding="utf-8")

    malformed_lint_config_file = tmp_path / "malformed-lint-config.json"
    malformed_lint_config_file.write_text("{ bad json", encoding="utf-8")

    summary_example_file = backend_root / "config" / "schemas" / "strict-gate-summary.example.json"
    summary_example_payload = json.loads(summary_example_file.read_text(encoding="utf-8"))
    summary_example_payload["schema_version"] = "broken-version"
    broken_summary_example_file = tmp_path / "broken-summary-example.json"
    broken_summary_example_file.write_text(json.dumps(summary_example_payload, ensure_ascii=False), encoding="utf-8")

    unknown_group_overrides_file = tmp_path / "unknown-group-overrides.json"
    unknown_group_overrides_file.write_text(
        json.dumps(
            {
                "unknown_group": {
                    "unknown_code": {
                        "description": "placeholder description",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    test_cases: tuple[tuple[str, str, str, list[str], tuple[str, ...]], ...] = (
        (
            "validate-summary-contract-changelog.py",
            "validate-summary-contract-changelog",
            "summary_contract_required_file_not_found",
            ["--app-file", str(tmp_path / "missing-main.py")],
            ("path",),
        ),
        (
            "validate-summary-contract-changelog.py",
            "validate-summary-contract-changelog",
            "summary_contract_app_version_not_found",
            ["--app-file", str(no_version_app_file)],
            ("path",),
        ),
        (
            "validate-strict-gate-summary-schema.py",
            "validate-strict-gate-summary-schema",
            "summary_schema_json_parse_error",
            ["--schema-file", str(malformed_summary_schema_file)],
            ("path",),
        ),
        (
            "validate-strict-gate-summary-schema.py",
            "validate-strict-gate-summary-schema",
            "summary_schema_example_payload_schema_validation_failed",
            ["--example-file", str(broken_summary_example_file)],
            ("validation_path",),
        ),
        (
            "validate-validator-error-code-metadata-lint.py",
            "validate-validator-error-code-metadata-lint",
            "error_code_metadata_lint_schema_file_not_found",
            ["--schema-file", str(tmp_path / "missing-lint-schema.json")],
            ("path",),
        ),
        (
            "validate-validator-error-code-metadata-lint.py",
            "validate-validator-error-code-metadata-lint",
            "error_code_metadata_lint_json_parse_error",
            ["--lint-config-file", str(malformed_lint_config_file)],
            ("path", "role"),
        ),
        (
            "validate-validator-error-code-metadata-overrides.py",
            "validate-validator-error-code-metadata-overrides",
            "error_code_metadata_overrides_placeholder_markers_file_not_found",
            ["--placeholder-markers-file", str(tmp_path / "missing-placeholder-markers.json")],
            ("path",),
        ),
        (
            "validate-validator-error-code-metadata-overrides.py",
            "validate-validator-error-code-metadata-overrides",
            "error_code_metadata_overrides_unknown_override_group",
            ["--overrides-file", str(unknown_group_overrides_file)],
            ("group",),
        ),
    )

    for script_file_name, expected_validator_name, expected_code, extra_args, context_keys in test_cases:
        payload = _run_validator_with_json_errors(
            backend_root=backend_root,
            script_file_name=script_file_name,
            extra_args=extra_args,
        )
        validator.validate(payload)
        assert payload["validator"] == expected_validator_name
        assert payload["code"] == expected_code
        assert isinstance(payload.get("context"), dict)
        for context_key in context_keys:
            assert context_key in payload["context"]


def test_remaining_validator_scripts_json_errors_multi_business_failure_matrix(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_payload = _load_error_schema(backend_root=backend_root)
    validator = Draft202012Validator(schema_payload)

    malformed_alertmanager_file = tmp_path / "malformed-alertmanager.yml"
    malformed_alertmanager_file.write_text("{ bad: [yaml\n", encoding="utf-8")

    malformed_dev_rule_file = tmp_path / "malformed-dev-rule.yml"
    malformed_dev_rule_file.write_text("alert: [broken\n", encoding="utf-8")

    malformed_profile_example_file = tmp_path / "malformed-profile-example.json"
    malformed_profile_example_file.write_text("{ bad json", encoding="utf-8")

    malformed_markers_file = tmp_path / "malformed-markers.json"
    malformed_markers_file.write_text("{ bad json", encoding="utf-8")

    malformed_catalog_file = tmp_path / "malformed-catalog.json"
    malformed_catalog_file.write_text("{ bad json", encoding="utf-8")

    test_cases: tuple[tuple[str, str, str, list[str], tuple[str, ...]], ...] = (
        (
            "validate-alertmanager-route-consistency.py",
            "validate-alertmanager-route-consistency",
            "alertmanager_route_consistency_rules_dir_invalid",
            ["--rules-dir", str(tmp_path / "missing-rules-dir")],
            ("path",),
        ),
        (
            "validate-alertmanager-route-consistency.py",
            "validate-alertmanager-route-consistency",
            "alertmanager_route_consistency_yaml_parse_error",
            ["--alertmanager-file", str(malformed_alertmanager_file)],
            ("path",),
        ),
        (
            "validate-notification-retry-runbook.py",
            "validate-notification-retry-runbook",
            "notification_retry_runbook_file_not_found",
            ["--runbook-file", str(tmp_path / "missing-runbook.md")],
            ("path",),
        ),
        (
            "validate-notification-retry-runbook.py",
            "validate-notification-retry-runbook",
            "notification_retry_runbook_baseline_parse_failed",
            ["--dev-rule-file", str(malformed_dev_rule_file)],
            ("source", "key"),
        ),
        (
            "validate-profile-suggestion-actions-schema.py",
            "validate-profile-suggestion-actions-schema",
            "profile_suggestion_actions_file_not_found",
            ["--schema-file", str(tmp_path / "missing-profile-schema.json")],
            ("path", "role"),
        ),
        (
            "validate-profile-suggestion-actions-schema.py",
            "validate-profile-suggestion-actions-schema",
            "profile_suggestion_actions_json_parse_error",
            ["--example-file", str(malformed_profile_example_file)],
            ("path", "role"),
        ),
        (
            "validate-validator-placeholder-markers.py",
            "validate-validator-placeholder-markers",
            "placeholder_markers_markers_file_not_found",
            ["--markers-file", str(tmp_path / "missing-markers.json")],
            ("path",),
        ),
        (
            "validate-validator-placeholder-markers.py",
            "validate-validator-placeholder-markers",
            "placeholder_markers_json_parse_error",
            ["--markers-file", str(malformed_markers_file)],
            ("path", "role"),
        ),
        (
            "validate-validator-error-code-catalog.py",
            "validate-validator-error-code-catalog",
            "error_code_catalog_catalog_file_not_found",
            ["--catalog-file", str(tmp_path / "missing-catalog.json")],
            ("path",),
        ),
        (
            "validate-validator-error-code-catalog.py",
            "validate-validator-error-code-catalog",
            "error_code_catalog_json_parse_error",
            ["--catalog-file", str(malformed_catalog_file)],
            ("path", "role"),
        ),
    )

    for script_file_name, expected_validator_name, expected_code, extra_args, context_keys in test_cases:
        payload = _run_validator_with_json_errors(
            backend_root=backend_root,
            script_file_name=script_file_name,
            extra_args=extra_args,
        )
        validator.validate(payload)
        assert payload["validator"] == expected_validator_name
        assert payload["code"] == expected_code
        assert isinstance(payload.get("context"), dict)
        for context_key in context_keys:
            assert context_key in payload["context"]


def test_validator_json_errors_high_frequency_context_contract(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_payload = _load_error_context_schema(backend_root=backend_root)
    validator = Draft202012Validator(schema_payload)

    no_version_app_file = tmp_path / "no-version-main.py"
    no_version_app_file.write_text("print('no version')\n", encoding="utf-8")

    malformed_summary_schema_file = tmp_path / "malformed-summary-schema.json"
    malformed_summary_schema_file.write_text("{ bad json", encoding="utf-8")

    malformed_lint_config_file = tmp_path / "malformed-lint-config.json"
    malformed_lint_config_file.write_text("{ bad json", encoding="utf-8")

    summary_example_file = backend_root / "config" / "schemas" / "strict-gate-summary.example.json"
    summary_example_payload = json.loads(summary_example_file.read_text(encoding="utf-8"))
    summary_example_payload["schema_version"] = "broken-version"
    broken_summary_example_file = tmp_path / "broken-summary-example.json"
    broken_summary_example_file.write_text(json.dumps(summary_example_payload, ensure_ascii=False), encoding="utf-8")

    unknown_group_overrides_file = tmp_path / "unknown-group-overrides.json"
    unknown_group_overrides_file.write_text(
        json.dumps(
            {
                "unknown_group": {
                    "unknown_code": {
                        "description": "placeholder description",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    malformed_alertmanager_file = tmp_path / "malformed-alertmanager.yml"
    malformed_alertmanager_file.write_text("{ bad: [yaml\n", encoding="utf-8")

    malformed_dev_rule_file = tmp_path / "malformed-dev-rule.yml"
    malformed_dev_rule_file.write_text("alert: [broken\n", encoding="utf-8")

    malformed_profile_example_file = tmp_path / "malformed-profile-example.json"
    malformed_profile_example_file.write_text("{ bad json", encoding="utf-8")

    malformed_markers_file = tmp_path / "malformed-markers.json"
    malformed_markers_file.write_text("{ bad json", encoding="utf-8")

    malformed_catalog_file = tmp_path / "malformed-catalog.json"
    malformed_catalog_file.write_text("{ bad json", encoding="utf-8")

    test_cases: tuple[tuple[str, list[str]], ...] = (
        (
            "validate-summary-contract-changelog.py",
            ["--app-file", str(tmp_path / "missing-main.py")],
        ),
        (
            "validate-summary-contract-changelog.py",
            ["--app-file", str(no_version_app_file)],
        ),
        (
            "validate-strict-gate-summary-schema.py",
            ["--schema-file", str(malformed_summary_schema_file)],
        ),
        (
            "validate-strict-gate-summary-schema.py",
            ["--example-file", str(broken_summary_example_file)],
        ),
        (
            "validate-validator-error-code-metadata-lint.py",
            ["--schema-file", str(tmp_path / "missing-lint-schema.json")],
        ),
        (
            "validate-validator-error-code-metadata-lint.py",
            ["--lint-config-file", str(malformed_lint_config_file)],
        ),
        (
            "validate-validator-error-code-metadata-overrides.py",
            ["--placeholder-markers-file", str(tmp_path / "missing-placeholder-markers.json")],
        ),
        (
            "validate-validator-error-code-metadata-overrides.py",
            ["--overrides-file", str(unknown_group_overrides_file)],
        ),
        (
            "validate-alertmanager-route-consistency.py",
            ["--rules-dir", str(tmp_path / "missing-rules-dir")],
        ),
        (
            "validate-alertmanager-route-consistency.py",
            ["--alertmanager-file", str(malformed_alertmanager_file)],
        ),
        (
            "validate-notification-retry-runbook.py",
            ["--runbook-file", str(tmp_path / "missing-runbook.md")],
        ),
        (
            "validate-notification-retry-runbook.py",
            ["--dev-rule-file", str(malformed_dev_rule_file)],
        ),
        (
            "validate-profile-suggestion-actions-schema.py",
            ["--schema-file", str(tmp_path / "missing-profile-schema.json")],
        ),
        (
            "validate-profile-suggestion-actions-schema.py",
            ["--example-file", str(malformed_profile_example_file)],
        ),
        (
            "validate-validator-placeholder-markers.py",
            ["--markers-file", str(tmp_path / "missing-markers.json")],
        ),
        (
            "validate-validator-placeholder-markers.py",
            ["--markers-file", str(malformed_markers_file)],
        ),
        (
            "validate-validator-error-code-catalog.py",
            ["--catalog-file", str(tmp_path / "missing-catalog.json")],
        ),
        (
            "validate-validator-error-code-catalog.py",
            ["--catalog-file", str(malformed_catalog_file)],
        ),
    )

    for script_file_name, extra_args in test_cases:
        payload = _run_validator_with_json_errors(
            backend_root=backend_root,
            script_file_name=script_file_name,
            extra_args=extra_args,
        )
        validator.validate(payload)
