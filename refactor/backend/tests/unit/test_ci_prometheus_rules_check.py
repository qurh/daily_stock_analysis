import json
import os
import re
import runpy
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

PROMTOOL_DEFAULT_VERSION = "2.52.0"
PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64 = "7f31c5d6474bbff3e514e627e0b7a7fbbd4e5cea3f315fd0b76cad50be4c1ba3"
PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64 = "b503c0f552e381d7d3f84dfd275166bf07c74f99c428ffed69447d4ab3259901"
VALIDATOR_CODE_PATTERN = re.compile(r'code="([^"]+)"')


def _load_validator_error_codes(script_file: Path) -> dict[str, str]:
    namespace = runpy.run_path(str(script_file))
    payload = namespace.get("VALIDATOR_ERROR_CODES")
    assert isinstance(payload, dict)
    assert payload
    for error_name, error_code in payload.items():
        assert isinstance(error_name, str)
        assert isinstance(error_code, str)
    return payload


def test_profile_suggestion_helper_module_is_shared_and_contract_stable() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    helper_file = backend_root / "scripts" / "profile_suggestion_helpers.py"
    lint_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    overrides_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"

    assert helper_file.exists()
    assert lint_script_file.exists()
    assert overrides_script_file.exists()

    lint_script_content = lint_script_file.read_text(encoding="utf-8")
    overrides_script_content = overrides_script_file.read_text(encoding="utf-8")
    assert "from profile_suggestion_helpers import" in lint_script_content
    assert "from profile_suggestion_helpers import" in overrides_script_content

    namespace = runpy.run_path(str(helper_file))
    build_profile_suggestion_payload = namespace.get("build_profile_suggestion_payload")
    build_suggested_actions_for_profile_not_found = namespace.get("build_suggested_actions_for_profile_not_found")
    build_profile_mode_config_snippet = namespace.get("build_profile_mode_config_snippet")

    assert callable(build_profile_suggestion_payload)
    assert callable(build_suggested_actions_for_profile_not_found)
    assert callable(build_profile_mode_config_snippet)

    (
        _message,
        fallback_reason,
        suggestion_level,
        suggested_profiles,
        suggested_cli_args,
        suggested_command,
    ) = build_profile_suggestion_payload(
        selected_profile="prdo",
        available_profiles=["prod", "dev"],
        command_prefix="python3 scripts/validate-validator-error-code-metadata-lint.py --lint-config-file /tmp/a.json",
    )
    assert fallback_reason == "close_match"
    assert suggestion_level == "hint"
    assert suggested_profiles[0] == "prod"
    assert suggested_cli_args == "--lint-profile prod"
    assert suggested_command is not None

    close_actions = build_suggested_actions_for_profile_not_found(
        fallback_reason=fallback_reason,
        suggested_profiles=suggested_profiles,
        available_profiles=["prod", "dev"],
        suggested_command=suggested_command,
    )
    assert close_actions[0]["action"] == "copy_command"
    assert close_actions[1] == {"action": "use_profile", "profile": "prod"}

    no_close_actions = build_suggested_actions_for_profile_not_found(
        fallback_reason="no_close_match",
        suggested_profiles=[],
        available_profiles=["prod", "dev"],
        suggested_command=None,
    )
    assert no_close_actions == [{"action": "show_profiles", "profiles": ["prod", "dev"]}]

    snippet = build_profile_mode_config_snippet(
        flat_config={"min_remediation_length": 12, "action_verbs": ["verify"]},
        selected_profile="dev",
    )
    no_profile_actions = build_suggested_actions_for_profile_not_found(
        fallback_reason="no_profiles_config",
        suggested_profiles=[],
        available_profiles=[],
        suggested_command=None,
        suggested_config_snippet=snippet,
    )
    assert no_profile_actions == [{"action": "migrate_profile_mode", "config_snippet": snippet}]


def test_profile_suggestion_helper_rejects_unknown_action_contract() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    helper_file = backend_root / "scripts" / "profile_suggestion_helpers.py"
    assert helper_file.exists()

    namespace = runpy.run_path(str(helper_file))
    validate_suggested_actions_contract = namespace.get("validate_suggested_actions_contract")
    assert callable(validate_suggested_actions_contract)

    with pytest.raises(ValueError, match="unsupported action"):
        validate_suggested_actions_contract([{"action": "invalid_action"}])


def test_profile_suggestion_helper_rejects_missing_required_action_field() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    helper_file = backend_root / "scripts" / "profile_suggestion_helpers.py"
    assert helper_file.exists()

    namespace = runpy.run_path(str(helper_file))
    validate_suggested_actions_contract = namespace.get("validate_suggested_actions_contract")
    assert callable(validate_suggested_actions_contract)

    with pytest.raises(ValueError, match="missing required field"):
        validate_suggested_actions_contract([{"action": "copy_command"}])


def test_ci_script_invokes_prometheus_rules_check() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    ci_file = backend_root / "scripts" / "ci.sh"
    check_file = backend_root / "scripts" / "check-prometheus-rules.sh"

    assert ci_file.exists()
    assert check_file.exists()

    ci_content = ci_file.read_text(encoding="utf-8")
    check_content = check_file.read_text(encoding="utf-8")

    assert "./scripts/check-prometheus-rules.sh" in ci_content
    assert "./scripts/validate-promtool-installer-config.sh" in ci_content
    assert "./scripts/sync-strict-gate-alert-thresholds.py --check" in ci_content
    assert "./scripts/sync-validator-error-codes.py --check --strict-descriptions" in ci_content
    assert "./scripts/validate-validator-placeholder-markers.py" in ci_content
    assert "./scripts/validate-validator-error-code-catalog.py" in ci_content
    assert "./scripts/validate-validator-error-code-metadata-lint.py" in ci_content
    assert "./scripts/validate-validator-error-code-metadata-overrides.py" in ci_content
    assert "./scripts/validate-profile-suggestion-actions-schema.py" in ci_content
    assert "./scripts/validate-strict-gate-summary-schema.py" in ci_content
    assert "./scripts/validate-summary-contract-changelog.py" in ci_content
    assert "./scripts/validate-validator-error-context-high-frequency-schema.py" in ci_content
    assert "promtool check rules" in check_content
    assert "PROMTOOL_REQUIRED" in ci_content
    assert "CI" in ci_content


def test_validator_error_code_catalog_exists_and_has_prefix_groups() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert "summary_schema" in payload
    assert "summary_contract" in payload
    assert "placeholder_markers" in payload
    assert "profile_suggestion_actions" in payload
    assert "alertmanager_route_consistency" in payload
    assert "notification_retry_runbook" in payload
    assert "error_context_high_frequency" in payload
    assert isinstance(payload["summary_schema"], dict)
    assert isinstance(payload["summary_contract"], dict)
    assert isinstance(payload["placeholder_markers"], dict)
    assert isinstance(payload["profile_suggestion_actions"], dict)
    assert isinstance(payload["alertmanager_route_consistency"], dict)
    assert isinstance(payload["notification_retry_runbook"], dict)
    assert isinstance(payload["error_context_high_frequency"], dict)
    for group_payload in payload.values():
        for entry_payload in group_payload.values():
            assert isinstance(entry_payload, dict)
            assert isinstance(entry_payload.get("description"), str)
            assert isinstance(entry_payload.get("severity"), str)
            assert isinstance(entry_payload.get("remediation"), str)


def test_validator_error_code_catalog_schema_exists_and_has_required_fields() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_file = backend_root / "config" / "schemas" / "validator-error-codes.schema.json"
    assert schema_file.exists()

    payload = json.loads(schema_file.read_text(encoding="utf-8"))
    assert payload.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert payload.get("type") == "object"
    required_groups = payload.get("required", [])
    assert "summary_schema" in required_groups
    assert "summary_contract" in required_groups
    assert "placeholder_markers" in required_groups
    assert "profile_suggestion_actions" in required_groups
    assert "alertmanager_route_consistency" in required_groups
    assert "notification_retry_runbook" in required_groups
    assert "error_context_high_frequency" in required_groups


def test_validator_error_code_catalog_validator_script_passes_default_catalog() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-catalog.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "catalog is valid" in completed.stdout.lower()


def test_validator_error_code_catalog_validator_script_json_errors_for_schema_violation(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-catalog.py"
    assert validate_script_file.exists()

    invalid_catalog_file = tmp_path / "validator-error-codes.json"
    invalid_catalog_file.write_text(
        json.dumps({"summary_schema": []}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--catalog-file",
            str(invalid_catalog_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-catalog"
    assert payload["code"] == "error_code_catalog_schema_validation_failed"
    assert "schema validation failed" in payload["message"].lower()


def test_validator_error_code_catalog_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-catalog.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--unknown-flag",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-catalog"
    assert payload["code"] == "error_code_catalog_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_validator_error_code_catalog_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-catalog.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--catalog-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-catalog"
    assert payload["code"] == "error_code_catalog_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--catalog-file" in payload["context"]["argv"]


def test_validator_error_code_catalog_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-catalog.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-output",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["validator"] == "validate-validator-error-code-catalog"
    assert payload["status"] == "ok"
    assert payload["total_codes"] >= 1
    assert "summary_schema" in payload["groups"]
    assert "placeholder_markers" in payload["groups"]
    assert "error_context_high_frequency" in payload["groups"]


def test_validator_error_code_sync_script_migrates_legacy_string_catalog_entries(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_schema"]["summary_schema_json_parse_error"] = "Legacy plain string description."
    legacy_catalog_file = tmp_path / "validator-error-codes-legacy.json"
    legacy_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(legacy_catalog_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    migrated_payload = json.loads(legacy_catalog_file.read_text(encoding="utf-8"))
    migrated_entry = migrated_payload["summary_schema"]["summary_schema_json_parse_error"]
    assert isinstance(migrated_entry, dict)
    assert migrated_entry["description"] == "Legacy plain string description."
    assert migrated_entry["severity"] == "error"
    assert "json" in migrated_entry["remediation"].lower()
    assert "syntax" in migrated_entry["remediation"].lower()


def test_validator_error_code_catalog_has_specific_metadata_for_key_codes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    unexpected_error_cases = [
        ("summary_schema", "summary_schema_unexpected_error"),
        ("summary_contract", "summary_contract_unexpected_error"),
        ("placeholder_markers", "placeholder_markers_unexpected_error"),
    ]
    for group_name, code_name in unexpected_error_cases:
        entry = payload[group_name][code_name]
        assert entry["severity"] == "critical"
        assert "stack trace" in entry["remediation"].lower()

    parse_entry = payload["summary_schema"]["summary_schema_json_parse_error"]
    assert parse_entry["severity"] == "error"
    assert "json" in parse_entry["remediation"].lower()
    assert "syntax" in parse_entry["remediation"].lower()
    summary_schema_cli_entry = payload["summary_schema"]["summary_schema_cli_args_invalid"]
    assert summary_schema_cli_entry["severity"] == "error"
    assert "cli" in summary_schema_cli_entry["description"].lower()
    assert "arguments" in summary_schema_cli_entry["description"].lower()

    profile_actions_entry = payload["profile_suggestion_actions"]["profile_suggestion_actions_helper_contract_failed"]
    assert profile_actions_entry["severity"] == "critical"
    assert "schema" in profile_actions_entry["description"].lower()
    assert "rerun" in profile_actions_entry["remediation"].lower()

    profile_actions_unexpected_entry = payload["profile_suggestion_actions"][
        "profile_suggestion_actions_unexpected_error"
    ]
    assert profile_actions_unexpected_entry["severity"] == "critical"
    assert "stack trace" in profile_actions_unexpected_entry["remediation"].lower()

    summary_contract_cli_entry = payload["summary_contract"]["summary_contract_cli_args_invalid"]
    assert summary_contract_cli_entry["severity"] == "error"
    assert "cli" in summary_contract_cli_entry["description"].lower()
    assert "arguments" in summary_contract_cli_entry["description"].lower()


def test_validator_error_code_sync_script_upgrades_legacy_default_metadata(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_schema"]["summary_schema_unexpected_error"]["severity"] = "error"
    payload["summary_schema"]["summary_schema_unexpected_error"][
        "remediation"
    ] = "Review validator output and update configuration or input data for this error."
    downgraded_catalog_file = tmp_path / "validator-error-codes-downgraded.json"
    downgraded_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(downgraded_catalog_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    upgraded_payload = json.loads(downgraded_catalog_file.read_text(encoding="utf-8"))
    upgraded_entry = upgraded_payload["summary_schema"]["summary_schema_unexpected_error"]
    assert upgraded_entry["severity"] == "critical"
    assert "stack trace" in upgraded_entry["remediation"].lower()


def test_validator_error_code_metadata_overrides_config_exists() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    overrides_file = backend_root / "config" / "validator-error-code-metadata-overrides.json"
    assert overrides_file.exists()

    payload = json.loads(overrides_file.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert "profile_suggestion_actions" in payload
    profile_suggestion_actions_overrides = payload["profile_suggestion_actions"]
    expected_profile_suggestion_actions_codes = {
        "profile_suggestion_actions_file_not_found",
        "profile_suggestion_actions_json_parse_error",
        "profile_suggestion_actions_schema_invalid",
        "profile_suggestion_actions_example_validation_failed",
        "profile_suggestion_actions_helper_contract_failed",
        "profile_suggestion_actions_cli_args_invalid",
        "profile_suggestion_actions_unexpected_error",
    }
    assert expected_profile_suggestion_actions_codes.issubset(set(profile_suggestion_actions_overrides.keys()))
    helper_contract_override = profile_suggestion_actions_overrides["profile_suggestion_actions_helper_contract_failed"]
    assert helper_contract_override["severity"] == "critical"
    assert "schema" in helper_contract_override["description"].lower()

    assert "summary_contract" in payload
    summary_contract_overrides = payload["summary_contract"]
    expected_summary_contract_codes = {
        "summary_contract_cli_args_invalid",
    }
    assert expected_summary_contract_codes.issubset(set(summary_contract_overrides.keys()))
    assert "summary_schema" in payload
    summary_schema_overrides = payload["summary_schema"]
    expected_summary_schema_codes = {
        "summary_schema_cli_args_invalid",
    }
    assert expected_summary_schema_codes.issubset(set(summary_schema_overrides.keys()))
    assert "placeholder_markers" in payload
    placeholder_markers_overrides = payload["placeholder_markers"]
    expected_placeholder_markers_codes = {
        "placeholder_markers_cli_args_invalid",
    }
    assert expected_placeholder_markers_codes.issubset(set(placeholder_markers_overrides.keys()))
    assert "error_context_high_frequency" in payload
    error_context_high_frequency_overrides = payload["error_context_high_frequency"]
    expected_error_context_high_frequency_codes = {
        "error_context_high_frequency_cli_args_invalid",
        "error_context_high_frequency_schema_file_not_found",
        "error_context_high_frequency_samples_file_not_found",
        "error_context_high_frequency_json_parse_error",
        "error_context_high_frequency_schema_invalid",
        "error_context_high_frequency_samples_payload_invalid",
        "error_context_high_frequency_sample_schema_validation_failed",
        "error_context_high_frequency_unexpected_error",
    }
    assert expected_error_context_high_frequency_codes.issubset(set(error_context_high_frequency_overrides.keys()))


def test_error_context_high_frequency_metadata_overrides_quality_policy() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    overrides_file = backend_root / "config" / "validator-error-code-metadata-overrides.json"
    assert overrides_file.exists()

    payload = json.loads(overrides_file.read_text(encoding="utf-8"))
    assert "error_context_high_frequency" in payload
    group_payload = payload["error_context_high_frequency"]

    expected_severity_by_code = {
        "error_context_high_frequency_cli_args_invalid": "error",
        "error_context_high_frequency_schema_file_not_found": "error",
        "error_context_high_frequency_samples_file_not_found": "error",
        "error_context_high_frequency_json_parse_error": "error",
        "error_context_high_frequency_schema_invalid": "error",
        "error_context_high_frequency_samples_payload_invalid": "error",
        "error_context_high_frequency_sample_schema_validation_failed": "error",
        "error_context_high_frequency_unexpected_error": "critical",
    }

    for code, expected_severity in expected_severity_by_code.items():
        assert code in group_payload
        code_payload = group_payload[code]
        assert code_payload["severity"] == expected_severity
        remediation = code_payload["remediation"].strip()
        assert remediation.endswith(".")
        assert "rerun" in remediation.lower()


def test_validator_error_code_metadata_overrides_schema_exists() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_file = backend_root / "config" / "schemas" / "validator-error-code-metadata-overrides.schema.json"
    assert schema_file.exists()

    payload = json.loads(schema_file.read_text(encoding="utf-8"))
    assert payload.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert payload.get("type") == "object"


def test_validator_error_code_metadata_lint_config_exists_and_is_valid() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    lint_config_file = backend_root / "config" / "validator-error-code-metadata-lint.json"
    assert lint_config_file.exists()

    payload = json.loads(lint_config_file.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert isinstance(payload.get("min_remediation_length"), int)
    assert payload["min_remediation_length"] >= 1
    assert isinstance(payload.get("action_verbs"), list)
    assert payload["action_verbs"]
    assert all(isinstance(item, str) and item.strip() for item in payload["action_verbs"])


def test_validator_error_code_metadata_lint_schema_exists() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_file = backend_root / "config" / "schemas" / "validator-error-code-metadata-lint.schema.json"
    assert schema_file.exists()

    payload = json.loads(schema_file.read_text(encoding="utf-8"))
    assert payload.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert payload.get("type") == "object"


def test_validator_error_code_metadata_lint_validator_script_passes_default_config() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "lint config is valid" in completed.stdout.lower()


def test_validator_error_code_metadata_lint_validator_script_json_errors_for_schema_violation(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    invalid_lint_config_file = tmp_path / "metadata-lint-invalid.json"
    invalid_lint_config_file.write_text(
        json.dumps(
            {"min_remediation_length": 0, "action_verbs": []},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(invalid_lint_config_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-lint"
    assert payload["code"] == "error_code_metadata_lint_schema_validation_failed"
    assert "schema validation failed" in payload["message"].lower()


def test_validator_error_code_metadata_lint_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--unknown-flag",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-lint"
    assert payload["code"] == "error_code_metadata_lint_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_validator_error_code_metadata_lint_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--lint-config-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-lint"
    assert payload["code"] == "error_code_metadata_lint_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--lint-config-file" in payload["context"]["argv"]


def test_validator_error_code_metadata_lint_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-output",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["validator"] == "validate-validator-error-code-metadata-lint"
    assert payload["status"] == "ok"
    assert payload["action_verbs_count"] >= 1
    assert payload["min_remediation_length"] >= 1


def test_validator_error_code_metadata_lint_validator_script_supports_profiled_lint_config(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata lint profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "dev",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "lint config is valid" in completed.stdout.lower()


def test_validator_error_code_metadata_lint_validator_script_json_errors_for_unknown_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "staging",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-lint"
    assert payload["code"] == "error_code_metadata_lint_profile_not_found"
    assert "lint profile" in payload["message"].lower()


def test_validator_error_code_metadata_lint_validator_script_suggests_nearby_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()
    assert "_build_profile_suggestion_payload" in validate_script_file.read_text(encoding="utf-8")

    lint_config_file = tmp_path / "metadata-lint-profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "prdo",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-lint"
    assert payload["code"] == "error_code_metadata_lint_profile_not_found"
    assert payload["context"]["fallback_reason"] == "close_match"
    assert payload["context"]["suggestion_level"] == "hint"
    assert payload["context"]["suggested_profiles"][0] == "prod"
    assert payload["context"]["suggested_cli_args"] == "--lint-profile prod"
    expected_lint_config_arg = f"--lint-config-file {shlex.quote(str(lint_config_file))}"
    assert "validate-validator-error-code-metadata-lint.py" in payload["context"]["suggested_command"]
    assert expected_lint_config_arg in payload["context"]["suggested_command"]
    assert "--lint-profile prod" in payload["context"]["suggested_command"]
    assert str(lint_config_file) in payload["context"]["suggested_command"]
    suggested_actions = payload["context"]["suggested_actions"]
    assert suggested_actions[0]["action"] == "copy_command"
    assert suggested_actions[0]["command"] == payload["context"]["suggested_command"]
    assert suggested_actions[1] == {"action": "use_profile", "profile": "prod"}


def test_validator_error_code_metadata_lint_validator_script_handles_no_nearby_profile_suggestion(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "xyzxyz",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-lint"
    assert payload["code"] == "error_code_metadata_lint_profile_not_found"
    assert payload["context"]["fallback_reason"] == "no_close_match"
    assert payload["context"]["suggestion_level"] == "warning"
    assert payload["context"]["available_profiles"][0] == "prod"
    assert payload["context"]["suggested_profiles"] == []
    assert payload["context"]["suggested_cli_args"] is None
    assert payload["context"]["suggested_command"] is None
    assert payload["context"]["suggested_actions"] == [
        {"action": "show_profiles", "profiles": payload["context"]["available_profiles"]}
    ]
    assert "available profiles" in payload["message"].lower()


def test_validator_error_code_metadata_lint_validator_script_reports_non_profile_config_when_profile_requested(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-flat.json"
    lint_config_file.write_text(
        json.dumps(
            {"min_remediation_length": 12, "action_verbs": ["verify"]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "dev",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-lint"
    assert payload["code"] == "error_code_metadata_lint_profile_not_found"
    assert payload["context"]["fallback_reason"] == "no_profiles_config"
    assert payload["context"]["suggestion_level"] == "error"
    assert payload["context"]["suggested_profiles"] == []
    assert payload["context"]["suggested_cli_args"] is None
    assert payload["context"]["suggested_command"] is None
    suggested_config_snippet = payload["context"]["suggested_config_snippet"]
    assert suggested_config_snippet["default_profile"] == "dev"
    assert suggested_config_snippet["profiles"]["dev"]["min_remediation_length"] == 12
    assert suggested_config_snippet["profiles"]["dev"]["action_verbs"] == ["verify"]
    suggested_actions = payload["context"]["suggested_actions"]
    assert suggested_actions[0]["action"] == "migrate_profile_mode"
    assert suggested_actions[0]["config_snippet"] == suggested_config_snippet
    assert "profile mode is not configured" in payload["message"].lower()


def test_validator_error_code_metadata_lint_validator_script_plain_errors_include_profile_suggestion(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "prdo",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "did you mean" in completed.stderr.lower()
    assert "prod" in completed.stderr.lower()
    assert "--lint-profile prod" in completed.stderr.lower()


def test_validator_error_code_metadata_lint_validator_script_uses_env_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-lint.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-profiled-env.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["do!"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "LINT_PROFILE": "dev"},
    )

    assert completed.returncode == 0
    assert "lint config is valid" in completed.stdout.lower()


def test_validator_error_code_metadata_overrides_validator_script_passes_default_config() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "overrides config is valid" in completed.stdout.lower()


def test_validator_error_code_metadata_overrides_validator_script_json_errors_for_unknown_code(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-invalid.json"
    overrides_file.write_text(
        json.dumps(
            {
                "summary_schema": {
                    "summary_schema_not_exists": {
                        "severity": "warning",
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_unknown_override_code"
    assert "unknown override code" in payload["message"].lower()


def test_validator_error_code_metadata_overrides_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--unknown-flag",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_validator_error_code_metadata_overrides_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--overrides-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--overrides-file" in payload["context"]["argv"]


def test_validator_error_code_metadata_overrides_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-output",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["status"] == "ok"
    assert payload["total_override_groups"] >= 1
    assert payload["total_override_codes"] >= 1


def test_validator_error_code_metadata_overrides_validator_script_supports_custom_lint_config(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-custom-lint.json"
    overrides_file.write_text(
        json.dumps(
            {"summary_schema": {"summary_schema_json_parse_error": {"remediation": "Do now"}}},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    lint_config_file = tmp_path / "metadata-lint-config.json"
    lint_config_file.write_text(
        json.dumps(
            {"min_remediation_length": 2, "action_verbs": ["do"]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--lint-config-file",
            str(lint_config_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "overrides config is valid" in completed.stdout.lower()


def test_validator_error_code_metadata_overrides_validator_script_supports_lint_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-profiled-lint.json"
    overrides_file.write_text(
        json.dumps(
            {"summary_schema": {"summary_schema_json_parse_error": {"remediation": "Do now"}}},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    lint_config_file = tmp_path / "metadata lint config profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 30,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "dev",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "overrides config is valid" in completed.stdout.lower()


def test_validator_error_code_metadata_overrides_validator_script_supports_overrides_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-profiled.json"
    overrides_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "summary_schema": {"summary_schema_json_parse_error": {"remediation": "Do now"}},
                    },
                    "prod": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "remediation": "Verify JSON syntax and rerun validation with expected schema."
                            }
                        },
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    lint_config_file = tmp_path / "metadata-lint-config-profiled-overrides-profile.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 30,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--overrides-profile",
            "dev",
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "dev",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "overrides config is valid" in completed.stdout.lower()


def test_validator_error_code_metadata_overrides_validator_script_json_errors_for_unknown_overrides_profile(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-profiled-unknown.json"
    overrides_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "prod": {
                        "summary_schema": {"summary_schema_json_parse_error": {"remediation": "Verify and rerun."}},
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--overrides-profile",
            "staging",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_overrides_profile_not_found"
    assert payload["context"]["fallback_reason"] == "no_close_match"
    assert payload["context"]["suggestion_level"] == "warning"
    assert payload["context"]["available_profiles"][0] == "prod"
    assert payload["context"]["suggested_profiles"] == []
    assert payload["context"]["suggested_cli_args"] is None
    assert payload["context"]["suggested_command"] is None
    assert payload["context"]["suggested_actions"] == [
        {"action": "show_profiles", "profiles": payload["context"]["available_profiles"]}
    ]
    assert "overrides profile" in payload["message"].lower()
    assert "available profiles" in payload["message"].lower()


def test_validator_error_code_metadata_overrides_validator_script_suggests_nearby_overrides_profile(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-profiled-nearby.json"
    overrides_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "summary_schema": {"summary_schema_json_parse_error": {"remediation": "Do now"}},
                    },
                    "prod": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "remediation": "Verify JSON syntax and rerun validation with expected schema."
                            }
                        },
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--overrides-profile",
            "prdo",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_overrides_profile_not_found"
    assert payload["context"]["fallback_reason"] == "close_match"
    assert payload["context"]["suggestion_level"] == "hint"
    assert payload["context"]["suggested_profiles"][0] == "prod"
    assert payload["context"]["suggested_cli_args"] == "--overrides-profile prod"
    expected_overrides_file_arg = f"--overrides-file {shlex.quote(str(overrides_file))}"
    assert "validate-validator-error-code-metadata-overrides.py" in payload["context"]["suggested_command"]
    assert expected_overrides_file_arg in payload["context"]["suggested_command"]
    assert "--overrides-profile prod" in payload["context"]["suggested_command"]
    suggested_actions = payload["context"]["suggested_actions"]
    assert suggested_actions[0]["action"] == "copy_command"
    assert suggested_actions[0]["command"] == payload["context"]["suggested_command"]
    assert suggested_actions[1] == {"action": "use_profile", "profile": "prod"}


def test_validator_error_code_metadata_overrides_validator_script_json_errors_for_unknown_lint_profile(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-config-profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "staging",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_lint_profile_not_found"
    assert "lint profile" in payload["message"].lower()


def test_validator_error_code_metadata_overrides_validator_script_suggests_nearby_lint_profile(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()
    assert "_build_profile_suggestion_payload" in validate_script_file.read_text(encoding="utf-8")

    lint_config_file = tmp_path / "metadata-lint-config-profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "prdo",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_lint_profile_not_found"
    assert payload["context"]["fallback_reason"] == "close_match"
    assert payload["context"]["suggestion_level"] == "hint"
    assert payload["context"]["suggested_profiles"][0] == "prod"
    assert payload["context"]["suggested_cli_args"] == "--lint-profile prod"
    expected_lint_config_arg = f"--lint-config-file {shlex.quote(str(lint_config_file))}"
    assert "validate-validator-error-code-metadata-overrides.py" in payload["context"]["suggested_command"]
    assert expected_lint_config_arg in payload["context"]["suggested_command"]
    assert "--lint-profile prod" in payload["context"]["suggested_command"]
    assert str(lint_config_file) in payload["context"]["suggested_command"]
    suggested_actions = payload["context"]["suggested_actions"]
    assert suggested_actions[0]["action"] == "copy_command"
    assert suggested_actions[0]["command"] == payload["context"]["suggested_command"]
    assert suggested_actions[1] == {"action": "use_profile", "profile": "prod"}


def test_validator_error_code_metadata_overrides_validator_script_handles_no_nearby_lint_profile_suggestion(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-config-profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "xyzxyz",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_lint_profile_not_found"
    assert payload["context"]["fallback_reason"] == "no_close_match"
    assert payload["context"]["suggestion_level"] == "warning"
    assert payload["context"]["available_profiles"][0] == "prod"
    assert payload["context"]["suggested_profiles"] == []
    assert payload["context"]["suggested_cli_args"] is None
    assert payload["context"]["suggested_command"] is None
    assert payload["context"]["suggested_actions"] == [
        {"action": "show_profiles", "profiles": payload["context"]["available_profiles"]}
    ]
    assert "available profiles" in payload["message"].lower()


def test_validator_error_code_metadata_overrides_validator_script_reports_non_profile_config_when_profile_requested(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-flat.json"
    lint_config_file.write_text(
        json.dumps(
            {"min_remediation_length": 12, "action_verbs": ["verify"]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "dev",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_lint_profile_not_found"
    assert payload["context"]["fallback_reason"] == "no_profiles_config"
    assert payload["context"]["suggestion_level"] == "error"
    assert payload["context"]["suggested_profiles"] == []
    assert payload["context"]["suggested_cli_args"] is None
    assert payload["context"]["suggested_command"] is None
    suggested_config_snippet = payload["context"]["suggested_config_snippet"]
    assert suggested_config_snippet["default_profile"] == "dev"
    assert suggested_config_snippet["profiles"]["dev"]["min_remediation_length"] == 12
    assert suggested_config_snippet["profiles"]["dev"]["action_verbs"] == ["verify"]
    suggested_actions = payload["context"]["suggested_actions"]
    assert suggested_actions[0]["action"] == "migrate_profile_mode"
    assert suggested_actions[0]["config_snippet"] == suggested_config_snippet
    assert "profile mode is not configured" in payload["message"].lower()


def test_validator_error_code_metadata_overrides_validator_script_plain_errors_include_lint_profile_suggestion(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-config-profiled.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 12,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--lint-profile",
            "prdo",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "did you mean" in completed.stderr.lower()
    assert "prod" in completed.stderr.lower()
    assert "--lint-profile prod" in completed.stderr.lower()


def test_validator_error_code_metadata_overrides_validator_script_uses_env_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-profiled-lint-env.json"
    overrides_file.write_text(
        json.dumps(
            {"summary_schema": {"summary_schema_json_parse_error": {"remediation": "Do now"}}},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    lint_config_file = tmp_path / "metadata-lint-config-profiled-env.json"
    lint_config_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "min_remediation_length": 2,
                        "action_verbs": ["do"],
                    },
                    "prod": {
                        "min_remediation_length": 30,
                        "action_verbs": ["verify"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--lint-config-file",
            str(lint_config_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "LINT_PROFILE": "dev"},
    )

    assert completed.returncode == 0
    assert "overrides config is valid" in completed.stdout.lower()


def test_validator_error_code_metadata_overrides_validator_script_json_errors_for_invalid_lint_config(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    lint_config_file = tmp_path / "metadata-lint-config-invalid.json"
    lint_config_file.write_text(
        json.dumps(
            {"min_remediation_length": 0, "action_verbs": []},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--lint-config-file",
            str(lint_config_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_lint_config_invalid"
    assert "lint config" in payload["message"].lower()


def test_validator_error_code_metadata_overrides_validator_script_json_errors_for_placeholder_text(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-placeholder.json"
    overrides_file.write_text(
        json.dumps(
            {"summary_schema": {"summary_schema_json_parse_error": {"remediation": "TODO: fill remediation later."}}},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_placeholder_text_detected"
    assert "placeholder" in payload["message"].lower()


def test_validator_error_code_metadata_overrides_validator_script_json_errors_for_non_actionable_remediation(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-code-metadata-overrides.py"
    assert validate_script_file.exists()

    overrides_file = tmp_path / "metadata-overrides-non-actionable-remediation.json"
    overrides_file.write_text(
        json.dumps(
            {"summary_schema": {"summary_schema_json_parse_error": {"remediation": "N/A"}}},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--overrides-file",
            str(overrides_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-code-metadata-overrides"
    assert payload["code"] == "error_code_metadata_overrides_remediation_quality_invalid"
    assert "remediation" in payload["message"].lower()


def test_validator_error_code_sync_script_applies_custom_metadata_overrides(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overrides_file = tmp_path / "metadata-overrides.json"
    overrides_file.write_text(
        json.dumps(
            {
                "summary_schema": {
                    "summary_schema_json_parse_error": {
                        "severity": "warning",
                        "remediation": "Use jq/JSONLint to validate syntax before rerun.",
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(overrides_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    entry = payload["summary_schema"]["summary_schema_json_parse_error"]
    assert entry["severity"] == "warning"
    assert entry["remediation"] == "Use jq/JSONLint to validate syntax before rerun."


def test_validator_error_code_sync_script_supports_metadata_overrides_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-profiled-overrides.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overrides_file = tmp_path / "metadata-overrides-profiled.json"
    overrides_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "severity": "warning",
                            }
                        }
                    },
                    "prod": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "severity": "error",
                            }
                        }
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(overrides_file),
            "--metadata-overrides-profile",
            "dev",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    entry = payload["summary_schema"]["summary_schema_json_parse_error"]
    assert entry["severity"] == "warning"


def test_validator_error_code_sync_script_suggests_nearby_metadata_overrides_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-profiled-overrides-nearby.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overrides_file = tmp_path / "metadata-overrides-profiled-nearby.json"
    overrides_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "severity": "warning",
                            }
                        }
                    },
                    "prod": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "severity": "error",
                            }
                        }
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(overrides_file),
            "--metadata-overrides-profile",
            "prdo",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "metadata overrides profile not found: prdo" in completed.stderr.lower()
    assert "did you mean: prod" in completed.stderr.lower()
    assert "try: --metadata-overrides-profile prod" in completed.stderr.lower()


def test_validator_error_code_sync_script_reports_available_profiles_for_unknown_metadata_overrides_profile(
    tmp_path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-profiled-overrides-unknown.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overrides_file = tmp_path / "metadata-overrides-profiled-unknown-sync.json"
    overrides_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "severity": "warning",
                            }
                        }
                    },
                    "prod": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "severity": "error",
                            }
                        }
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(overrides_file),
            "--metadata-overrides-profile",
            "staging",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "metadata overrides profile not found: staging" in completed.stderr.lower()
    assert "available profiles: prod, dev" in completed.stderr.lower()


def test_validator_error_code_sync_script_json_errors_for_unknown_metadata_overrides_profile(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-profiled-overrides-json-errors.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overrides_file = tmp_path / "metadata-overrides-profiled-json-errors.json"
    overrides_file.write_text(
        json.dumps(
            {
                "default_profile": "prod",
                "profiles": {
                    "dev": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "severity": "warning",
                            }
                        }
                    },
                    "prod": {
                        "summary_schema": {
                            "summary_schema_json_parse_error": {
                                "severity": "error",
                            }
                        }
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(overrides_file),
            "--metadata-overrides-profile",
            "prdo",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_metadata_overrides_profile_not_found"
    assert payload["context"]["fallback_reason"] == "close_match"
    assert payload["context"]["suggestion_level"] == "hint"
    assert payload["context"]["suggested_profiles"][0] == "prod"
    assert payload["context"]["suggested_cli_args"] == "--metadata-overrides-profile prod"
    suggested_actions = payload["context"]["suggested_actions"]
    assert suggested_actions[0]["action"] == "copy_command"
    assert suggested_actions[0]["command"] == payload["context"]["suggested_command"]
    assert suggested_actions[1] == {"action": "use_profile", "profile": "prod"}


def test_validator_error_code_sync_script_json_errors_for_non_profile_overrides_config_when_profile_requested(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-non-profile-overrides-json-errors.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overrides_file = tmp_path / "metadata-overrides-flat-sync.json"
    overrides_file.write_text(
        json.dumps(
            {
                "summary_schema": {
                    "summary_schema_json_parse_error": {
                        "severity": "warning",
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(overrides_file),
            "--metadata-overrides-profile",
            "dev",
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_metadata_overrides_profile_not_found"
    assert payload["context"]["fallback_reason"] == "no_profiles_config"
    assert payload["context"]["suggestion_level"] == "error"
    assert payload["context"]["suggested_profiles"] == []
    assert payload["context"]["suggested_cli_args"] is None
    assert payload["context"]["suggested_command"] is None
    suggested_config_snippet = payload["context"]["suggested_config_snippet"]
    assert suggested_config_snippet["default_profile"] == "dev"
    assert "summary_schema" in suggested_config_snippet["profiles"]["dev"]
    assert payload["context"]["suggested_actions"] == [
        {"action": "migrate_profile_mode", "config_snippet": suggested_config_snippet}
    ]


def test_validator_error_code_sync_script_json_errors_for_missing_metadata_overrides_file(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-sync-missing-overrides.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    missing_overrides_file = tmp_path / "metadata-overrides-missing-sync.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(missing_overrides_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_metadata_overrides_file_not_found"
    assert payload["context"]["path"] == str(missing_overrides_file)
    assert payload["context"]["failure_mode"] == "metadata_overrides_file_not_found"


def test_validator_error_code_sync_script_json_errors_for_unknown_cli_arguments() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    assert sync_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--json-errors",
            "--unknown-flag",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_unexpected_error"
    assert "unrecognized arguments" in payload["message"]
    assert payload["context"]["stage"] == "argument_parsing"
    assert payload["context"]["exception_type"] == "SystemExit"
    assert payload["context"]["exit_code"] == 2
    assert payload["context"]["argv"] == ["--json-errors", "--unknown-flag"]
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_validator_error_code_sync_script_json_errors_for_missing_cli_argument_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    assert sync_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--json-errors",
            "--metadata-overrides-profile",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_unexpected_error"
    assert "expected one argument" in payload["message"]
    assert payload["context"]["stage"] == "argument_parsing"
    assert payload["context"]["exception_type"] == "SystemExit"
    assert payload["context"]["exit_code"] == 2
    assert payload["context"]["argv"] == ["--json-errors", "--metadata-overrides-profile"]
    assert payload["context"]["unknown_args"] == []


def test_validator_error_code_sync_script_json_errors_for_unexpected_runtime_exception_context(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_source = backend_root / "scripts" / "sync-validator-error-codes.py"
    helper_source = backend_root / "scripts" / "profile_suggestion_helpers.py"
    assert sync_script_source.exists()
    assert helper_source.exists()

    isolated_backend_root = tmp_path / "isolated-backend-unexpected-runtime"
    isolated_scripts_dir = isolated_backend_root / "scripts"
    isolated_scripts_dir.mkdir(parents=True, exist_ok=True)

    isolated_sync_script = isolated_scripts_dir / "sync-validator-error-codes.py"
    isolated_helper = isolated_scripts_dir / "profile_suggestion_helpers.py"

    source_content = sync_script_source.read_text(encoding="utf-8")
    injected_content = source_content.replace(
        "existing_catalog = _load_existing_catalog(path=args.output_file)",
        "raise RuntimeError('simulated runtime failure')\n        existing_catalog = _load_existing_catalog(path=args.output_file)",
        1,
    )
    assert injected_content != source_content

    isolated_sync_script.write_text(injected_content, encoding="utf-8")
    isolated_helper.write_text(helper_source.read_text(encoding="utf-8"), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(isolated_sync_script),
            "--json-errors",
        ],
        cwd=isolated_backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_unexpected_error"
    assert "simulated runtime failure" in payload["message"]
    assert payload["context"]["stage"] == "runtime"
    assert payload["context"]["exception_type"] == "RuntimeError"
    assert payload["context"]["exit_code"] == 1
    assert payload["context"]["argv"] == ["--json-errors"]
    assert payload["context"]["unknown_args"] == []


def test_validator_error_code_sync_script_json_errors_for_unreadable_metadata_overrides_path(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-sync-unreadable-overrides.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    unreadable_overrides_path = tmp_path / "metadata-overrides-dir"
    unreadable_overrides_path.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(unreadable_overrides_path),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_metadata_overrides_file_read_failed"
    assert payload["context"]["path"] == str(unreadable_overrides_path)
    assert payload["context"]["failure_mode"] == "metadata_overrides_file_read_failed"
    assert payload["context"]["exception_type"] == "IsADirectoryError"


def test_validator_error_code_sync_script_json_errors_for_invalid_utf8_metadata_overrides(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-sync-invalid-utf8-overrides.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    invalid_overrides_file = tmp_path / "metadata-overrides-invalid-utf8.json"
    invalid_overrides_file.write_bytes(b"\xff\xfe\xfd")

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(invalid_overrides_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_json_parse_error"
    assert payload["context"]["path"] == str(invalid_overrides_file)
    assert payload["context"]["role"] == "metadata_overrides"
    assert payload["context"]["exception_type"] == "UnicodeDecodeError"


def test_validator_error_code_sync_script_json_errors_for_malformed_metadata_overrides(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-sync-malformed-overrides.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    malformed_overrides_file = tmp_path / "metadata-overrides-malformed.json"
    malformed_overrides_file.write_text("{not-json", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(malformed_overrides_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_json_parse_error"
    assert payload["context"]["path"] == str(malformed_overrides_file)
    assert payload["context"]["role"] == "metadata_overrides"
    assert payload["context"]["exception_type"] == "JSONDecodeError"


def test_validator_error_code_sync_script_json_errors_for_missing_validator_script_file(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_source = backend_root / "scripts" / "sync-validator-error-codes.py"
    helper_source = backend_root / "scripts" / "profile_suggestion_helpers.py"
    assert sync_script_source.exists()
    assert helper_source.exists()

    isolated_backend_root = tmp_path / "isolated-backend"
    isolated_scripts_dir = isolated_backend_root / "scripts"
    isolated_scripts_dir.mkdir(parents=True, exist_ok=True)
    isolated_sync_script = isolated_scripts_dir / "sync-validator-error-codes.py"
    isolated_helper = isolated_scripts_dir / "profile_suggestion_helpers.py"
    isolated_sync_script.write_text(sync_script_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_helper.write_text(helper_source.read_text(encoding="utf-8"), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(isolated_sync_script),
            "--json-errors",
        ],
        cwd=isolated_backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_validator_script_file_not_found"
    assert payload["context"]["group"] == "summary_schema"
    assert payload["context"]["path"] == str(isolated_backend_root / "scripts" / "validate-strict-gate-summary-schema.py")


def test_validator_error_code_sync_script_json_errors_for_missing_validator_registry(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_source = backend_root / "scripts" / "sync-validator-error-codes.py"
    helper_source = backend_root / "scripts" / "profile_suggestion_helpers.py"
    assert sync_script_source.exists()
    assert helper_source.exists()

    isolated_backend_root = tmp_path / "isolated-backend-missing-registry"
    isolated_scripts_dir = isolated_backend_root / "scripts"
    isolated_scripts_dir.mkdir(parents=True, exist_ok=True)

    isolated_sync_script = isolated_scripts_dir / "sync-validator-error-codes.py"
    isolated_helper = isolated_scripts_dir / "profile_suggestion_helpers.py"
    isolated_summary_script = isolated_scripts_dir / "validate-strict-gate-summary-schema.py"

    isolated_sync_script.write_text(sync_script_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_helper.write_text(helper_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_summary_script.write_text("DUMMY = True\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(isolated_sync_script),
            "--json-errors",
        ],
        cwd=isolated_backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_validator_registry_missing"
    assert payload["context"]["group"] == "summary_schema"
    assert payload["context"]["path"] == str(isolated_summary_script)
    assert payload["context"]["stage"] == "validator_registry_validation"
    assert payload["context"]["failure_mode"] == "missing_registry"


def test_validator_error_code_sync_script_json_errors_for_invalid_validator_registry_item(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_source = backend_root / "scripts" / "sync-validator-error-codes.py"
    helper_source = backend_root / "scripts" / "profile_suggestion_helpers.py"
    assert sync_script_source.exists()
    assert helper_source.exists()

    isolated_backend_root = tmp_path / "isolated-backend-invalid-registry"
    isolated_scripts_dir = isolated_backend_root / "scripts"
    isolated_scripts_dir.mkdir(parents=True, exist_ok=True)

    isolated_sync_script = isolated_scripts_dir / "sync-validator-error-codes.py"
    isolated_helper = isolated_scripts_dir / "profile_suggestion_helpers.py"
    isolated_summary_script = isolated_scripts_dir / "validate-strict-gate-summary-schema.py"

    isolated_sync_script.write_text(sync_script_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_helper.write_text(helper_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_summary_script.write_text(
        "VALIDATOR_ERROR_CODES = {'summary_schema_invalid_registry_entry': 100}\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(isolated_sync_script),
            "--json-errors",
        ],
        cwd=isolated_backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_validator_registry_invalid"
    assert payload["context"]["group"] == "summary_schema"
    assert payload["context"]["path"] == str(isolated_summary_script)
    assert payload["context"]["stage"] == "validator_registry_validation"
    assert payload["context"]["failure_mode"] == "invalid_registry_item"
    assert payload["context"]["registry_key"] == "summary_schema_invalid_registry_entry"


def test_validator_error_code_sync_script_json_errors_for_validator_registry_load_failed(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_source = backend_root / "scripts" / "sync-validator-error-codes.py"
    helper_source = backend_root / "scripts" / "profile_suggestion_helpers.py"
    assert sync_script_source.exists()
    assert helper_source.exists()

    isolated_backend_root = tmp_path / "isolated-backend-registry-load-failed"
    isolated_scripts_dir = isolated_backend_root / "scripts"
    isolated_scripts_dir.mkdir(parents=True, exist_ok=True)

    isolated_sync_script = isolated_scripts_dir / "sync-validator-error-codes.py"
    isolated_helper = isolated_scripts_dir / "profile_suggestion_helpers.py"
    isolated_summary_script = isolated_scripts_dir / "validate-strict-gate-summary-schema.py"

    isolated_sync_script.write_text(sync_script_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_helper.write_text(helper_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_summary_script.write_text("def broken(:\n    pass\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(isolated_sync_script),
            "--json-errors",
        ],
        cwd=isolated_backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_validator_registry_load_failed"
    assert payload["context"]["group"] == "summary_schema"
    assert payload["context"]["path"] == str(isolated_summary_script)
    assert payload["context"]["stage"] == "validator_registry_loading"
    assert payload["context"]["exception_type"] == "SyntaxError"
    assert payload["context"]["failure_mode"] == "exception"


def test_validator_error_code_sync_script_json_errors_for_validator_registry_load_failed_system_exit(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_source = backend_root / "scripts" / "sync-validator-error-codes.py"
    helper_source = backend_root / "scripts" / "profile_suggestion_helpers.py"
    assert sync_script_source.exists()
    assert helper_source.exists()

    isolated_backend_root = tmp_path / "isolated-backend-registry-load-failed-system-exit"
    isolated_scripts_dir = isolated_backend_root / "scripts"
    isolated_scripts_dir.mkdir(parents=True, exist_ok=True)

    isolated_sync_script = isolated_scripts_dir / "sync-validator-error-codes.py"
    isolated_helper = isolated_scripts_dir / "profile_suggestion_helpers.py"
    isolated_summary_script = isolated_scripts_dir / "validate-strict-gate-summary-schema.py"

    isolated_sync_script.write_text(sync_script_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_helper.write_text(helper_source.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_summary_script.write_text("import sys\nsys.exit(7)\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(isolated_sync_script),
            "--json-errors",
        ],
        cwd=isolated_backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_validator_registry_load_failed"
    assert payload["context"]["group"] == "summary_schema"
    assert payload["context"]["path"] == str(isolated_summary_script)
    assert payload["context"]["stage"] == "validator_registry_loading"
    assert payload["context"]["exception_type"] == "SystemExit"
    assert payload["context"]["failure_mode"] == "system_exit"
    assert payload["context"]["exit_code"] == 7


def test_validator_error_code_sync_script_fails_on_unknown_override_code(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overrides_file = tmp_path / "metadata-overrides-invalid.json"
    overrides_file.write_text(
        json.dumps(
            {
                "summary_schema": {
                    "summary_schema_not_exists": {
                        "severity": "warning",
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(overrides_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "unknown override code" in completed.stderr.lower()


def test_validator_error_code_sync_script_json_errors_for_unknown_override_code(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-json-errors-unknown-code.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overrides_file = tmp_path / "metadata-overrides-invalid-json-errors.json"
    overrides_file.write_text(
        json.dumps(
            {
                "summary_schema": {
                    "summary_schema_not_exists": {
                        "severity": "warning",
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--metadata-overrides-file",
            str(overrides_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_unknown_override_code"
    assert payload["context"]["group"] == "summary_schema"
    assert payload["context"]["code"] == "summary_schema_not_exists"


def test_validator_placeholder_markers_config_exists_and_is_non_empty() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    markers_file = backend_root / "config" / "validator-placeholder-markers.json"
    assert markers_file.exists()

    payload = json.loads(markers_file.read_text(encoding="utf-8"))
    markers = payload.get("markers")
    assert isinstance(markers, list)
    assert markers
    assert all(isinstance(marker, str) and marker.strip() for marker in markers)


def test_validator_placeholder_markers_validator_script_passes_default_config() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "is valid" in completed.stdout.lower()


def test_validator_placeholder_markers_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-output",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["validator"] == "validate-validator-placeholder-markers"
    assert payload["status"] == "ok"
    assert payload["markers_count"] >= 1
    assert payload["markers_file"].endswith("validator-placeholder-markers.json")


def test_validator_placeholder_markers_validator_script_fails_on_duplicate_markers(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    invalid_markers_file = tmp_path / "validator-placeholder-markers.json"
    invalid_markers_file.write_text(
        json.dumps({"markers": ["TODO", "todo", "FIXME"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--markers-file",
            str(invalid_markers_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "duplicate marker" in completed.stderr.lower()


def test_validator_placeholder_markers_schema_exists_and_has_required_fields() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    schema_file = backend_root / "config" / "schemas" / "validator-placeholder-markers.schema.json"
    assert schema_file.exists()

    payload = json.loads(schema_file.read_text(encoding="utf-8"))
    assert payload.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert payload.get("type") == "object"
    assert "markers" in payload.get("required", [])


def test_validator_placeholder_markers_validator_script_fails_on_schema_violation(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    invalid_markers_file = tmp_path / "validator-placeholder-markers.json"
    invalid_markers_file.write_text(
        json.dumps({"markers": "TODO"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--markers-file",
            str(invalid_markers_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "schema validation failed" in completed.stderr.lower()


def test_validator_placeholder_markers_validator_script_fails_on_invalid_schema_file(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    invalid_schema_file = tmp_path / "validator-placeholder-markers.schema.json"
    invalid_schema_file.write_text(
        json.dumps({"type": "not-a-valid-schema-type"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--schema-file",
            str(invalid_schema_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "invalid json schema" in completed.stderr.lower()


def test_validator_placeholder_markers_validator_script_json_errors_for_duplicate_markers(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    invalid_markers_file = tmp_path / "validator-placeholder-markers.json"
    invalid_markers_file.write_text(
        json.dumps({"markers": ["TODO", "todo"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--markers-file",
            str(invalid_markers_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-placeholder-markers"
    assert payload["code"] == "placeholder_markers_duplicate_marker"
    assert payload["context"]["marker"] == "TODO"


def test_validator_placeholder_markers_validator_script_json_errors_for_schema_violation(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    invalid_markers_file = tmp_path / "validator-placeholder-markers.json"
    invalid_markers_file.write_text(
        json.dumps({"markers": "TODO"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--markers-file",
            str(invalid_markers_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-placeholder-markers"
    assert payload["code"] == "placeholder_markers_schema_validation_failed"
    assert "schema validation failed" in payload["message"].lower()


def test_validator_placeholder_markers_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--unknown-flag",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-placeholder-markers"
    assert payload["code"] == "placeholder_markers_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_validator_placeholder_markers_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--markers-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-placeholder-markers"
    assert payload["code"] == "placeholder_markers_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--markers-file" in payload["context"]["argv"]


def test_validator_error_code_sync_script_passes_default_catalog() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    assert sync_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(sync_script_file), "--check"],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "in sync" in completed.stdout.lower()


def test_validator_error_code_sync_script_strict_descriptions_pass_default_catalog() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    assert sync_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(sync_script_file), "--check", "--strict-descriptions"],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "in sync" in completed.stdout.lower()


def test_validator_error_code_sync_script_check_fails_on_drift(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_contract"].pop("summary_contract_unexpected_error", None)
    drifted_catalog_file = tmp_path / "validator-error-codes.json"
    drifted_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--output-file",
            str(drifted_catalog_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "not in sync" in completed.stderr.lower()


def test_validator_error_code_sync_script_json_errors_for_check_drift(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_contract"].pop("summary_contract_unexpected_error", None)
    drifted_catalog_file = tmp_path / "validator-error-codes-drifted-json-errors.json"
    drifted_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--output-file",
            str(drifted_catalog_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_catalog_not_in_sync"
    assert payload["context"]["path"] == str(drifted_catalog_file)


def test_validator_error_code_sync_script_json_errors_for_check_unreadable_catalog_path(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"

    assert sync_script_file.exists()

    unreadable_catalog_path = tmp_path / "catalog-dir-for-check"
    unreadable_catalog_path.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--output-file",
            str(unreadable_catalog_path),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_catalog_file_read_failed"
    assert payload["context"]["path"] == str(unreadable_catalog_path)
    assert payload["context"]["failure_mode"] == "catalog_file_read_failed"
    assert payload["context"]["exception_type"] == "IsADirectoryError"


def test_validator_error_code_sync_script_strict_descriptions_fail_on_todo(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_schema"]["summary_schema_json_parse_error"][
        "description"
    ] = "TODO: document summary_schema_json_parse_error."
    todo_catalog_file = tmp_path / "validator-error-codes.json"
    todo_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--output-file",
            str(todo_catalog_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "placeholder descriptions" in completed.stderr.lower()


def test_validator_error_code_sync_script_json_errors_for_strict_placeholder_descriptions(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_schema"]["summary_schema_json_parse_error"][
        "description"
    ] = "TODO: document summary_schema_json_parse_error."
    todo_catalog_file = tmp_path / "validator-error-codes-strict-json-errors.json"
    todo_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--output-file",
            str(todo_catalog_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_placeholder_text_detected"
    assert payload["context"]["markers"]
    assert payload["context"]["violations"]
    first_violation = payload["context"]["violations"][0]
    assert first_violation["group"] == "summary_schema"
    assert first_violation["code"] == "summary_schema_json_parse_error"
    assert first_violation["field"] == "description"
    assert first_violation["marker"] == "TODO"


def test_validator_error_code_sync_script_json_errors_for_missing_placeholder_markers_file(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    missing_markers_file = tmp_path / "missing-placeholder-markers.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--placeholder-markers-file",
            str(missing_markers_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_placeholder_markers_file_not_found"
    assert payload["context"]["path"] == str(missing_markers_file)
    assert payload["context"]["failure_mode"] == "placeholder_markers_file_not_found"


def test_validator_error_code_sync_script_json_errors_for_unreadable_placeholder_markers_path(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    unreadable_markers_path = tmp_path / "placeholder-markers-dir"
    unreadable_markers_path.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--placeholder-markers-file",
            str(unreadable_markers_path),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_placeholder_markers_read_failed"
    assert payload["context"]["path"] == str(unreadable_markers_path)
    assert payload["context"]["failure_mode"] == "placeholder_markers_file_read_failed"
    assert payload["context"]["exception_type"] == "IsADirectoryError"


def test_validator_error_code_sync_script_json_errors_for_invalid_placeholder_markers_payload(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    invalid_markers_file = tmp_path / "invalid-placeholder-markers.json"
    invalid_markers_file.write_text(
        json.dumps({"markers": "TODO"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--placeholder-markers-file",
            str(invalid_markers_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_placeholder_markers_invalid"
    assert payload["context"]["path"] == str(invalid_markers_file)


def test_validator_error_code_sync_script_json_errors_for_non_object_placeholder_markers_payload(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    invalid_markers_file = tmp_path / "invalid-placeholder-markers-non-object.json"
    invalid_markers_file.write_text(
        json.dumps(["TODO", "FIXME"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--placeholder-markers-file",
            str(invalid_markers_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_placeholder_markers_invalid"
    assert payload["context"]["path"] == str(invalid_markers_file)


def test_validator_error_code_sync_script_json_errors_for_invalid_utf8_placeholder_markers(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    invalid_markers_file = tmp_path / "invalid-placeholder-markers-utf8.json"
    invalid_markers_file.write_bytes(b"\xff\xfe\xfd")

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--placeholder-markers-file",
            str(invalid_markers_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_placeholder_markers_invalid"
    assert payload["context"]["path"] == str(invalid_markers_file)
    assert payload["context"]["exception_type"] == "UnicodeDecodeError"


def test_validator_error_code_sync_script_json_errors_for_malformed_placeholder_markers(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    malformed_markers_file = tmp_path / "invalid-placeholder-markers-malformed.json"
    malformed_markers_file.write_text("{not-json", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--placeholder-markers-file",
            str(malformed_markers_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_placeholder_markers_invalid"
    assert payload["context"]["path"] == str(malformed_markers_file)
    assert payload["context"]["exception_type"] == "JSONDecodeError"


def test_validator_error_code_sync_script_json_errors_for_unreadable_catalog_path(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_dir = tmp_path / "catalog-dir"
    catalog_dir.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(catalog_dir),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_catalog_file_read_failed"
    assert payload["context"]["path"] == str(catalog_dir)
    assert payload["context"]["failure_mode"] == "catalog_file_read_failed"
    assert payload["context"]["exception_type"] == "IsADirectoryError"


def test_validator_error_code_sync_script_json_errors_for_invalid_utf8_catalog(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    invalid_catalog_file = tmp_path / "validator-error-codes-invalid-utf8.json"
    invalid_catalog_file.write_bytes(b"\xff\xfe\xfd")

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(invalid_catalog_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_json_parse_error"
    assert payload["context"]["path"] == str(invalid_catalog_file)
    assert payload["context"]["role"] == "existing_catalog"
    assert payload["context"]["exception_type"] == "UnicodeDecodeError"


def test_validator_error_code_sync_script_json_errors_for_malformed_catalog(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    malformed_catalog_file = tmp_path / "validator-error-codes-malformed.json"
    malformed_catalog_file.write_text("{not-json", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(malformed_catalog_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_json_parse_error"
    assert payload["context"]["path"] == str(malformed_catalog_file)
    assert payload["context"]["role"] == "existing_catalog"
    assert payload["context"]["exception_type"] == "JSONDecodeError"


def test_validator_error_code_sync_script_json_errors_for_output_parent_create_failed(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"

    output_parent_file = tmp_path / "output-parent-file"
    output_parent_file.write_text("not-a-directory", encoding="utf-8")
    output_file = output_parent_file / "validator-error-codes.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--output-file",
            str(output_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_output_parent_create_failed"
    assert payload["context"]["path"] == str(output_file)
    assert payload["context"]["parent"] == str(output_parent_file)
    assert payload["context"]["exception_type"] == "FileExistsError"


def test_validator_error_code_sync_script_json_errors_for_output_write_failed(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    assert sync_script_file.exists()
    assert catalog_file.exists()

    source_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    output_file = tmp_path / "validator-error-codes-readonly.json"
    output_file.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(output_file, 0o400)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(sync_script_file),
                "--output-file",
                str(output_file),
                "--json-errors",
            ],
            cwd=backend_root,
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        os.chmod(output_file, 0o600)

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "sync-validator-error-codes"
    assert payload["code"] == "error_code_sync_validator_error_codes_output_write_failed"
    assert payload["context"]["path"] == str(output_file)
    assert payload["context"]["exception_type"] == "PermissionError"


def test_validator_error_code_sync_script_strict_error_includes_group_and_remediation(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_schema"]["summary_schema_json_parse_error"][
        "description"
    ] = "TODO: document summary_schema_json_parse_error."
    todo_catalog_file = tmp_path / "validator-error-codes-with-todo.json"
    todo_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--output-file",
            str(todo_catalog_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "summary_schema.summary_schema_json_parse_error" in completed.stderr.lower()
    assert "remediation" in completed.stderr.lower()


def test_validator_error_code_sync_script_strict_descriptions_fail_on_remediation_placeholder(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_schema"]["summary_schema_json_parse_error"]["remediation"] = "TODO: fill remediation later."
    todo_catalog_file = tmp_path / "validator-error-codes-remediation-todo.json"
    todo_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--output-file",
            str(todo_catalog_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "summary_schema.summary_schema_json_parse_error.remediation" in completed.stderr.lower()


def test_validator_error_code_sync_script_supports_custom_placeholder_marker_file(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    payload["summary_schema"]["summary_schema_json_parse_error"]["description"] = "DRAFTTODO: fill later."
    custom_catalog_file = tmp_path / "validator-error-codes-custom-marker.json"
    custom_catalog_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    custom_markers_file = tmp_path / "placeholder-markers.json"
    custom_markers_file.write_text(
        json.dumps({"markers": ["DRAFTTODO"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--strict-descriptions",
            "--placeholder-markers-file",
            str(custom_markers_file),
            "--output-file",
            str(custom_catalog_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "placeholder descriptions" in completed.stderr.lower()


def test_validator_error_code_sync_script_strict_descriptions_fail_on_tbd_fixme(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-validator-error-codes.py"
    catalog_file = backend_root / "config" / "validator-error-codes.json"

    assert sync_script_file.exists()
    assert catalog_file.exists()

    placeholder_cases = [
        ("summary_schema", "summary_schema_json_parse_error", "TBD: fill later."),
        ("summary_contract", "summary_contract_unexpected_error", "fixme: fill later."),
    ]

    for group_name, code_name, placeholder_description in placeholder_cases:
        payload = json.loads(catalog_file.read_text(encoding="utf-8"))
        payload[group_name][code_name]["description"] = placeholder_description
        placeholder_catalog_file = tmp_path / f"{group_name}-{code_name}.json"
        placeholder_catalog_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(sync_script_file),
                "--check",
                "--strict-descriptions",
                "--output-file",
                str(placeholder_catalog_file),
            ],
            cwd=backend_root,
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode != 0
        assert "placeholder descriptions" in completed.stderr.lower()


def test_validator_scripts_expose_error_code_registries() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    summary_script = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    contract_script = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    placeholder_markers_script = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    profile_suggestion_actions_script = backend_root / "scripts" / "validate-profile-suggestion-actions-schema.py"
    alertmanager_route_consistency_script = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    notification_retry_runbook_script = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    error_context_high_frequency_script = (
        backend_root / "scripts" / "validate-validator-error-context-high-frequency-schema.py"
    )

    assert summary_script.exists()
    assert contract_script.exists()
    assert placeholder_markers_script.exists()
    assert profile_suggestion_actions_script.exists()
    assert alertmanager_route_consistency_script.exists()
    assert notification_retry_runbook_script.exists()
    assert error_context_high_frequency_script.exists()

    summary_codes = set(_load_validator_error_codes(summary_script).values())
    contract_codes = set(_load_validator_error_codes(contract_script).values())
    placeholder_markers_codes = set(_load_validator_error_codes(placeholder_markers_script).values())
    profile_suggestion_actions_codes = set(_load_validator_error_codes(profile_suggestion_actions_script).values())
    alertmanager_route_consistency_codes = set(_load_validator_error_codes(alertmanager_route_consistency_script).values())
    notification_retry_runbook_codes = set(_load_validator_error_codes(notification_retry_runbook_script).values())
    error_context_high_frequency_codes = set(_load_validator_error_codes(error_context_high_frequency_script).values())

    assert summary_codes
    assert contract_codes
    assert placeholder_markers_codes
    assert profile_suggestion_actions_codes
    assert alertmanager_route_consistency_codes
    assert notification_retry_runbook_codes
    assert error_context_high_frequency_codes
    assert all(code.startswith("summary_schema_") for code in summary_codes)
    assert all(code.startswith("summary_contract_") for code in contract_codes)
    assert all(code.startswith("placeholder_markers_") for code in placeholder_markers_codes)
    assert all(code.startswith("profile_suggestion_actions_") for code in profile_suggestion_actions_codes)
    assert all(code.startswith("alertmanager_route_consistency_") for code in alertmanager_route_consistency_codes)
    assert all(code.startswith("notification_retry_runbook_") for code in notification_retry_runbook_codes)
    assert all(code.startswith("error_context_high_frequency_") for code in error_context_high_frequency_codes)


def test_validator_error_code_catalog_covers_all_script_error_codes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    summary_script = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    contract_script = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    placeholder_markers_script = backend_root / "scripts" / "validate-validator-placeholder-markers.py"
    profile_suggestion_actions_script = backend_root / "scripts" / "validate-profile-suggestion-actions-schema.py"
    alertmanager_route_consistency_script = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    notification_retry_runbook_script = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    error_context_high_frequency_script = (
        backend_root / "scripts" / "validate-validator-error-context-high-frequency-schema.py"
    )

    assert catalog_file.exists()
    catalog_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    catalog_codes = {
        code
        for group in (
            "summary_schema",
            "summary_contract",
            "placeholder_markers",
            "profile_suggestion_actions",
            "alertmanager_route_consistency",
            "notification_retry_runbook",
            "error_context_high_frequency",
        )
        for code in catalog_payload.get(group, {}).keys()
    }

    script_codes: set[str] = set()
    for script_file in (
        summary_script,
        contract_script,
        placeholder_markers_script,
        profile_suggestion_actions_script,
        alertmanager_route_consistency_script,
        notification_retry_runbook_script,
        error_context_high_frequency_script,
    ):
        assert script_file.exists()
        content = script_file.read_text(encoding="utf-8")
        script_codes.update(VALIDATOR_CODE_PATTERN.findall(content))
        script_codes.update(_load_validator_error_codes(script_file).values())

    missing_codes = sorted(script_codes.difference(catalog_codes))
    assert not missing_codes


def test_validator_error_code_catalog_covers_alertmanager_route_consistency_codes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    alertmanager_script = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"

    assert catalog_file.exists()
    assert alertmanager_script.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert "alertmanager_route_consistency" in payload

    expected_codes = set(_load_validator_error_codes(alertmanager_script).values())
    assert expected_codes
    assert expected_codes.issubset(set(payload["alertmanager_route_consistency"].keys()))


def test_validator_error_code_catalog_covers_notification_retry_runbook_codes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    runbook_script = backend_root / "scripts" / "validate-notification-retry-runbook.py"

    assert catalog_file.exists()
    assert runbook_script.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert "notification_retry_runbook" in payload

    expected_codes = set(_load_validator_error_codes(runbook_script).values())
    assert expected_codes
    assert expected_codes.issubset(set(payload["notification_retry_runbook"].keys()))


def test_validator_error_code_catalog_covers_error_context_high_frequency_codes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    error_context_script = backend_root / "scripts" / "validate-validator-error-context-high-frequency-schema.py"

    assert catalog_file.exists()
    assert error_context_script.exists()

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert "error_context_high_frequency" in payload

    expected_codes = set(_load_validator_error_codes(error_context_script).values())
    assert expected_codes
    assert expected_codes.issubset(set(payload["error_context_high_frequency"].keys()))


def test_summary_schema_validator_script_passes_default_schema() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "schema is valid" in completed.stdout.lower()


def test_summary_schema_validator_script_fails_on_invalid_json(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    assert validate_script_file.exists()

    invalid_schema_file = tmp_path / "invalid-schema.json"
    invalid_schema_file.write_text("{not-json", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(validate_script_file), "--schema-file", str(invalid_schema_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "failed to parse json" in completed.stderr.lower()


def test_summary_schema_validator_script_fails_on_schema_version_mismatch(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    source_schema_file = backend_root / "config" / "schemas" / "strict-gate-summary.schema.json"
    assert validate_script_file.exists()
    assert source_schema_file.exists()

    schema_payload = json.loads(source_schema_file.read_text(encoding="utf-8"))
    schema_payload["properties"]["schema_version"]["const"] = "2"
    mismatched_schema_file = tmp_path / "mismatched-schema.json"
    mismatched_schema_file.write_text(json.dumps(schema_payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(validate_script_file), "--schema-file", str(mismatched_schema_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "schema_version mismatch" in completed.stderr.lower()


def test_summary_schema_validator_script_passes_default_example_payload() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "example payload is valid" in completed.stdout.lower()


def test_summary_schema_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-output",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["validator"] == "validate-strict-gate-summary-schema"
    assert payload["status"] == "ok"
    assert payload["schema_version"] >= "1"
    assert payload["schema_file"].endswith("strict-gate-summary.schema.json")
    assert payload["example_file"].endswith("strict-gate-summary.example.json")


def test_summary_schema_validator_script_fails_on_invalid_example_payload(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    source_example_file = backend_root / "config" / "schemas" / "strict-gate-summary.example.json"
    assert validate_script_file.exists()
    assert source_example_file.exists()

    example_payload = json.loads(source_example_file.read_text(encoding="utf-8"))
    example_payload.pop("modules", None)
    invalid_example_file = tmp_path / "invalid-example.json"
    invalid_example_file.write_text(json.dumps(example_payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(validate_script_file), "--example-file", str(invalid_example_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "example payload validation failed" in completed.stderr.lower()


def test_profile_suggestion_actions_schema_validator_script_passes_default_files() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-profile-suggestion-actions-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "schema is valid" in completed.stdout.lower()
    assert "example payload is valid" in completed.stdout.lower()
    assert "helper actions are valid" in completed.stdout.lower()


def test_profile_suggestion_actions_schema_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-profile-suggestion-actions-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-output",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["validator"] == "validate-profile-suggestion-actions-schema"
    assert payload["status"] == "ok"
    assert payload["schema_file"].endswith("profile-suggestion-actions.schema.json")
    assert payload["example_file"].endswith("profile-suggestion-actions.example.json")
    assert payload["helper_file"].endswith("profile_suggestion_helpers.py")
    assert payload["example_action_count"] >= 1


def test_profile_suggestion_actions_schema_validator_script_json_errors_for_invalid_example(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-profile-suggestion-actions-schema.py"
    source_example_file = backend_root / "config" / "schemas" / "profile-suggestion-actions.example.json"
    assert validate_script_file.exists()
    assert source_example_file.exists()

    invalid_example_payload = json.loads(source_example_file.read_text(encoding="utf-8"))
    invalid_example_payload[0].pop("action", None)
    invalid_example_file = tmp_path / "invalid-profile-suggestion-actions-example.json"
    invalid_example_file.write_text(
        json.dumps(invalid_example_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--example-file",
            str(invalid_example_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-profile-suggestion-actions-schema"
    assert payload["code"] == "profile_suggestion_actions_example_validation_failed"
    assert "example payload validation failed" in payload["message"].lower()


def test_profile_suggestion_actions_schema_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-profile-suggestion-actions-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--unknown-flag",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-profile-suggestion-actions-schema"
    assert payload["code"] == "profile_suggestion_actions_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_profile_suggestion_actions_schema_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-profile-suggestion-actions-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--schema-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-profile-suggestion-actions-schema"
    assert payload["code"] == "profile_suggestion_actions_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--schema-file" in payload["context"]["argv"]


def _extract_app_version_from_file(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    match = re.search(r'version="([^"]+)"', content)
    assert match is not None
    return match.group(1)


def test_summary_contract_changelog_validator_script_passes_default_files() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "contract changelog is valid" in completed.stdout.lower()


def test_summary_contract_changelog_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-output",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["validator"] == "validate-summary-contract-changelog"
    assert payload["status"] == "ok"
    assert payload["schema_version"] >= "1"
    assert payload["schema_file"].endswith("strict-gate-summary.schema.json")
    assert payload["changelog_file"].endswith("CHANGELOG.md")


def test_summary_contract_changelog_validator_script_fails_without_schema_version_note(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    app_file = backend_root / "src" / "app" / "main.py"
    assert validate_script_file.exists()
    assert app_file.exists()

    app_version = _extract_app_version_from_file(path=app_file)

    temp_app_file = tmp_path / "main.py"
    temp_app_file.write_text(f'app = FastAPI(version="{app_version}")\n', encoding="utf-8")

    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                f"## [{app_version}] - 2026-02-19",
                "",
                "### Changed",
                "",
                "- Dummy line without schema version marker.",
            ]
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--changelog-file",
            str(changelog_file),
            "--app-file",
            str(temp_app_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "missing summary schema version note" in completed.stderr.lower()


def test_summary_contract_changelog_validator_script_json_errors_for_missing_schema_note(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    app_file = backend_root / "src" / "app" / "main.py"
    assert validate_script_file.exists()
    assert app_file.exists()

    app_version = _extract_app_version_from_file(path=app_file)
    temp_app_file = tmp_path / "main.py"
    temp_app_file.write_text(f'app = FastAPI(version="{app_version}")\n', encoding="utf-8")

    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                f"## [{app_version}] - 2026-02-19",
                "",
                "### Changed",
                "",
                "- Dummy line without schema version marker.",
            ]
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--changelog-file",
            str(changelog_file),
            "--app-file",
            str(temp_app_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-summary-contract-changelog"
    assert payload["code"] == "summary_contract_missing_summary_schema_version_note"


def test_summary_contract_changelog_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--unknown-flag",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-summary-contract-changelog"
    assert payload["code"] == "summary_contract_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_summary_contract_changelog_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--schema-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-summary-contract-changelog"
    assert payload["code"] == "summary_contract_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--schema-file" in payload["context"]["argv"]


def test_summary_contract_changelog_validator_script_json_errors_for_version_mismatch(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    assert validate_script_file.exists()

    temp_app_file = tmp_path / "main.py"
    temp_app_file.write_text('app = FastAPI(version="0.0.0-test")\n', encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--app-file",
            str(temp_app_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-summary-contract-changelog"
    assert payload["code"] == "summary_contract_changelog_app_version_mismatch"


def test_summary_contract_changelog_validator_json_error_code_uses_prefix(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    assert validate_script_file.exists()

    temp_app_file = tmp_path / "main.py"
    temp_app_file.write_text('app = FastAPI(version="0.0.0-test")\n', encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--app-file",
            str(temp_app_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["code"].startswith("summary_contract_")


def test_summary_schema_validator_script_fails_on_inconsistent_totals(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    source_example_file = backend_root / "config" / "schemas" / "strict-gate-summary.example.json"
    assert validate_script_file.exists()
    assert source_example_file.exists()

    example_payload = json.loads(source_example_file.read_text(encoding="utf-8"))
    example_payload["changed_files_count"] = 99
    invalid_example_file = tmp_path / "invalid-totals-example.json"
    invalid_example_file.write_text(json.dumps(example_payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(validate_script_file), "--example-file", str(invalid_example_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "changed_files_count mismatch" in completed.stderr.lower()


def test_summary_schema_validator_script_fails_on_module_total_mismatch(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    source_example_file = backend_root / "config" / "schemas" / "strict-gate-summary.example.json"
    assert validate_script_file.exists()
    assert source_example_file.exists()

    example_payload = json.loads(source_example_file.read_text(encoding="utf-8"))
    example_payload["modules"]["strict"]["changed_alerts_count"] = 9
    invalid_example_file = tmp_path / "invalid-module-example.json"
    invalid_example_file.write_text(json.dumps(example_payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(validate_script_file), "--example-file", str(invalid_example_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "module total mismatch for strict" in completed.stderr.lower()


def test_summary_schema_validator_script_json_errors_mode_outputs_structured_payload(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    source_example_file = backend_root / "config" / "schemas" / "strict-gate-summary.example.json"
    assert validate_script_file.exists()
    assert source_example_file.exists()

    example_payload = json.loads(source_example_file.read_text(encoding="utf-8"))
    example_payload["changed_files_count"] = 99
    invalid_example_file = tmp_path / "invalid-json-errors-example.json"
    invalid_example_file.write_text(json.dumps(example_payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--example-file",
            str(invalid_example_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-strict-gate-summary-schema"
    assert payload["code"] == "summary_schema_changed_files_count_mismatch"
    assert payload["context"]["expected"] == 1
    assert payload["context"]["actual"] == 99


def test_summary_schema_validator_json_error_code_uses_prefix(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    source_example_file = backend_root / "config" / "schemas" / "strict-gate-summary.example.json"
    assert validate_script_file.exists()
    assert source_example_file.exists()

    example_payload = json.loads(source_example_file.read_text(encoding="utf-8"))
    example_payload["changed_files_count"] = 99
    invalid_example_file = tmp_path / "invalid-prefix-example.json"
    invalid_example_file.write_text(json.dumps(example_payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--example-file",
            str(invalid_example_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["code"].startswith("summary_schema_")


def test_summary_schema_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--unknown-flag",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-strict-gate-summary-schema"
    assert payload["code"] == "summary_schema_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_summary_schema_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--schema-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-strict-gate-summary-schema"
    assert payload["code"] == "summary_schema_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--schema-file" in payload["context"]["argv"]


def test_prometheus_rules_check_fails_in_strict_mode_when_promtool_missing() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    check_file = backend_root / "scripts" / "check-prometheus-rules.sh"
    assert check_file.exists()

    env = dict(os.environ)
    env["PROMTOOL_BIN"] = "__missing_promtool_binary__"
    env["PROMTOOL_REQUIRED"] = "1"
    completed = subprocess.run(
        ["bash", str(check_file)],
        cwd=backend_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "promtool not found" in completed.stderr


def test_prometheus_rules_check_outputs_validated_rules_summary() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    check_file = backend_root / "scripts" / "check-prometheus-rules.sh"
    rules_dir = backend_root / "monitoring" / "prometheus" / "rules"
    assert check_file.exists()
    assert rules_dir.exists()

    expected_count = len(sorted(rules_dir.glob("*.yml"))) + len(sorted(rules_dir.glob("*.yaml")))
    assert expected_count > 0

    env = dict(os.environ)
    env["PROMTOOL_BIN"] = "echo"
    completed = subprocess.run(
        ["bash", str(check_file)],
        cwd=backend_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert f"validated {expected_count} rule file(s)" in completed.stderr


def test_github_actions_refactor_ci_example_includes_promtool_install_and_ci_run() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    workflow_file = backend_root / "ci" / "github-actions" / "refactor-backend-ci.example.yml"

    assert workflow_file.exists()

    content = workflow_file.read_text(encoding="utf-8")
    assert "Install promtool" in content
    assert "PROMTOOL_VERSION:" not in content
    assert "PROMTOOL_SHA256:" not in content
    assert "bash refactor/backend/scripts/install-promtool.sh" in content
    assert "apt-get install -y prometheus" not in content
    assert "cd refactor/backend" in content
    assert "bash scripts/ci.sh" in content
    assert 'PROMTOOL_REQUIRED: "1"' in content
    assert 'PROMTOOL_VALIDATE_REMOTE: "1"' in content
    assert 'PROMTOOL_VALIDATE_REMOTE_MODE: "strict"' in content


def test_github_actions_refactor_ci_workflow_exists_and_targets_backend_paths() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    repository_root = Path(__file__).resolve().parents[4]
    workflow_file = repository_root / ".github" / "workflows" / "refactor-backend-ci.yml"

    assert backend_root.exists()
    assert workflow_file.exists()

    content = workflow_file.read_text(encoding="utf-8")
    assert 'name: "Refactor Backend CI"' in content
    assert "paths:" in content
    assert '- "refactor/backend/**"' in content
    assert '- "refactor/docs/**"' in content
    assert "Install promtool" in content
    assert "PROMTOOL_VERSION:" not in content
    assert "PROMTOOL_SHA256:" not in content
    assert "bash refactor/backend/scripts/install-promtool.sh" in content
    assert "apt-get install -y prometheus" not in content
    assert "bash scripts/ci.sh" in content
    assert 'PROMTOOL_VALIDATE_REMOTE: "1"' in content
    assert 'PROMTOOL_VALIDATE_REMOTE_MODE: "strict"' in content


def test_promtool_installer_config_file_exists_with_pinned_defaults() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    config_file = backend_root / "config" / "promtool-installer.defaults"
    assert config_file.exists()

    content = config_file.read_text(encoding="utf-8")
    assert f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}" in content
    assert f"PROMTOOL_DEFAULT_SHA256_LINUX_AMD64={PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}" in content
    assert f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}" in content


def test_promtool_installer_script_exists_and_verifies_checksum() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    install_script_file = backend_root / "scripts" / "install-promtool.sh"
    assert install_script_file.exists()

    content = install_script_file.read_text(encoding="utf-8")
    assert "PROMTOOL_CONFIG_FILE" in content
    assert "PROMTOOL_DEFAULT_VERSION" in content
    assert "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64" in content
    assert "PROMTOOL_DEFAULT_SHA256_LINUX_ARM64" in content
    assert "source" in content
    assert "github.com/prometheus/prometheus/releases/download" in content
    assert "sha256sum -c -" in content
    assert "tar -xzf" in content
    assert "install" in content


def test_promtool_installer_script_supports_multi_arch_auto_detection() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    install_script_file = backend_root / "scripts" / "install-promtool.sh"
    assert install_script_file.exists()

    content = install_script_file.read_text(encoding="utf-8")
    assert "uname -m" in content
    assert "x86_64" in content
    assert "linux-amd64" in content
    assert "aarch64" in content
    assert "arm64" in content
    assert "linux-arm64" in content
    assert "unsupported machine architecture" in content


def test_promtool_installer_script_dry_run_auto_detects_x86_64() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    install_script_file = backend_root / "scripts" / "install-promtool.sh"
    assert install_script_file.exists()

    env = dict(os.environ)
    env["PROMTOOL_MACHINE_ARCH"] = "x86_64"
    env["PROMTOOL_DRY_RUN"] = "1"
    completed = subprocess.run(
        ["bash", str(install_script_file)],
        cwd=backend_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "platform: linux-amd64" in completed.stderr
    assert "dry run enabled" in completed.stderr


def test_promtool_installer_script_dry_run_auto_detects_arm64() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    install_script_file = backend_root / "scripts" / "install-promtool.sh"
    assert install_script_file.exists()

    env = dict(os.environ)
    env["PROMTOOL_MACHINE_ARCH"] = "arm64"
    env["PROMTOOL_DRY_RUN"] = "1"
    completed = subprocess.run(
        ["bash", str(install_script_file)],
        cwd=backend_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "platform: linux-arm64" in completed.stderr
    assert "dry run enabled" in completed.stderr


def test_promtool_installer_script_fails_for_unsupported_arch() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    install_script_file = backend_root / "scripts" / "install-promtool.sh"
    assert install_script_file.exists()

    env = dict(os.environ)
    env["PROMTOOL_MACHINE_ARCH"] = "riscv64"
    env["PROMTOOL_DRY_RUN"] = "1"
    completed = subprocess.run(
        ["bash", str(install_script_file)],
        cwd=backend_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "unsupported machine architecture" in completed.stderr


def test_promtool_installer_config_validation_passes_with_default_config() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    config_file = backend_root / "config" / "promtool-installer.defaults"
    assert validate_script_file.exists()
    assert config_file.exists()

    env = dict(os.environ)
    env["PROMTOOL_CONFIG_FILE"] = str(config_file)
    completed = subprocess.run(
        ["bash", str(validate_script_file)],
        cwd=backend_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "config is valid" in completed.stderr


def test_promtool_installer_config_validation_fails_for_invalid_checksum() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        config_file = Path(tmp_dir) / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    "PROMTOOL_DEFAULT_VERSION=2.52.0",
                    "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64=not-a-checksum",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    assert completed.returncode != 0
    assert "must be a 64-character lowercase hex string" in completed.stderr


def test_promtool_installer_config_validation_remote_check_passes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        config_file = Path(tmp_dir) / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_AMD64={PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = Path(tmp_dir) / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_SHA256SUMS_URL"] = f"file://{sha256sums_file}"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    assert completed.returncode == 0
    assert "remote checksum validation passed" in completed.stderr


def test_promtool_installer_config_validation_remote_check_fails_on_mismatch() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        config_file = Path(tmp_dir) / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    (
                        "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64="
                        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    ),
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = Path(tmp_dir) / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_SHA256SUMS_URL"] = f"file://{sha256sums_file}"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    assert completed.returncode != 0
    assert "checksum mismatch for" in completed.stderr


def test_promtool_installer_config_validation_remote_fetch_retries_and_succeeds() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_AMD64={PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = tmp_path / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        mock_bin_dir = tmp_path / "mock-bin"
        mock_bin_dir.mkdir(parents=True, exist_ok=True)
        curl_file = mock_bin_dir / "curl"
        curl_file.write_text(
            """#!/usr/bin/env bash
set -euo pipefail

attempt_file="${PROMTOOL_TEST_CURL_ATTEMPT_FILE:?}"
log_file="${PROMTOOL_TEST_CURL_LOG_FILE:?}"
source_file="${PROMTOOL_TEST_CURL_SOURCE_FILE:?}"
fail_until="${PROMTOOL_TEST_CURL_FAIL_UNTIL:-0}"

attempt=0
if [[ -f "${attempt_file}" ]]; then
  attempt="$(cat "${attempt_file}")"
fi
attempt=$((attempt + 1))
echo "${attempt}" > "${attempt_file}"

printf "attempt=%s args=%s\\n" "${attempt}" "$*" >> "${log_file}"

output_file=""
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -o)
      output_file="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ "${attempt}" -le "${fail_until}" ]]; then
  exit 22
fi

cp "${source_file}" "${output_file}"
""",
            encoding="utf-8",
        )
        curl_file.chmod(0o755)

        attempt_file = tmp_path / "curl-attempts.txt"
        log_file = tmp_path / "curl-log.txt"

        env = dict(os.environ)
        env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_SHA256SUMS_URL"] = "https://example.invalid/sha256sums.txt"
        env["PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS"] = "3"
        env["PROMTOOL_REMOTE_FETCH_CONNECT_TIMEOUT_SECONDS"] = "7"
        env["PROMTOOL_REMOTE_FETCH_TIMEOUT_SECONDS"] = "21"
        env["PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS"] = "0"
        env["PROMTOOL_TEST_CURL_ATTEMPT_FILE"] = str(attempt_file)
        env["PROMTOOL_TEST_CURL_LOG_FILE"] = str(log_file)
        env["PROMTOOL_TEST_CURL_SOURCE_FILE"] = str(sha256sums_file)
        env["PROMTOOL_TEST_CURL_FAIL_UNTIL"] = "1"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        attempt_count = attempt_file.read_text(encoding="utf-8").strip()
        curl_log = log_file.read_text(encoding="utf-8")

    assert completed.returncode == 0
    assert "remote checksum validation passed" in completed.stderr
    assert attempt_count == "2"
    assert "--connect-timeout 7" in curl_log
    assert "--max-time 21" in curl_log


def test_promtool_installer_config_validation_remote_fetch_fails_after_max_attempts() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_AMD64={PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = tmp_path / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        mock_bin_dir = tmp_path / "mock-bin"
        mock_bin_dir.mkdir(parents=True, exist_ok=True)
        curl_file = mock_bin_dir / "curl"
        curl_file.write_text(
            """#!/usr/bin/env bash
set -euo pipefail

attempt_file="${PROMTOOL_TEST_CURL_ATTEMPT_FILE:?}"
fail_until="${PROMTOOL_TEST_CURL_FAIL_UNTIL:-0}"

attempt=0
if [[ -f "${attempt_file}" ]]; then
  attempt="$(cat "${attempt_file}")"
fi
attempt=$((attempt + 1))
echo "${attempt}" > "${attempt_file}"

if [[ "${attempt}" -le "${fail_until}" ]]; then
  exit 22
fi
""",
            encoding="utf-8",
        )
        curl_file.chmod(0o755)

        attempt_file = tmp_path / "curl-attempts.txt"
        env = dict(os.environ)
        env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_SHA256SUMS_URL"] = "https://example.invalid/sha256sums.txt"
        env["PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS"] = "2"
        env["PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS"] = "0"
        env["PROMTOOL_TEST_CURL_ATTEMPT_FILE"] = str(attempt_file)
        env["PROMTOOL_TEST_CURL_FAIL_UNTIL"] = "9"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        attempt_count = attempt_file.read_text(encoding="utf-8").strip()

    assert completed.returncode != 0
    assert "failed to fetch sha256sums after 2 attempt(s)" in completed.stderr
    assert attempt_count == "2"


def test_promtool_installer_config_validation_remote_fetch_uses_fresh_cache() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_AMD64={PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        cache_file = tmp_path / "cache" / "promtool-sha256sums.txt"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        cache_meta_file = Path(f"{cache_file}.meta")
        cache_meta_file.write_text(f"{int(time.time())}\n", encoding="utf-8")

        mock_bin_dir = tmp_path / "mock-bin"
        mock_bin_dir.mkdir(parents=True, exist_ok=True)
        curl_file = mock_bin_dir / "curl"
        curl_file.write_text(
            """#!/usr/bin/env bash
set -euo pipefail

attempt_file="${PROMTOOL_TEST_CURL_ATTEMPT_FILE:?}"
attempt=0
if [[ -f "${attempt_file}" ]]; then
  attempt="$(cat "${attempt_file}")"
fi
attempt=$((attempt + 1))
echo "${attempt}" > "${attempt_file}"
exit 22
""",
            encoding="utf-8",
        )
        curl_file.chmod(0o755)

        attempt_file = tmp_path / "curl-attempts.txt"
        env = dict(os.environ)
        env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_SHA256SUMS_URL"] = "https://example.invalid/sha256sums.txt"
        env["PROMTOOL_REMOTE_FETCH_CACHE_FILE"] = str(cache_file)
        env["PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS"] = "3600"
        env["PROMTOOL_TEST_CURL_ATTEMPT_FILE"] = str(attempt_file)
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        curl_called = attempt_file.exists()

    assert completed.returncode == 0
    assert "using cached sha256sums metadata" in completed.stderr
    assert "remote checksum validation passed" in completed.stderr
    assert not curl_called


def test_promtool_installer_config_validation_remote_fetch_refreshes_stale_cache() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_AMD64={PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        source_sha256sums_file = tmp_path / "sha256sums-source.txt"
        source_sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        cache_file = tmp_path / "cache" / "promtool-sha256sums.txt"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            "badbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadb  prometheus-2.52.0.linux-amd64.tar.gz\n",
            encoding="utf-8",
        )
        cache_meta_file = Path(f"{cache_file}.meta")
        stale_epoch = int(time.time()) - 7200
        cache_meta_file.write_text(f"{stale_epoch}\n", encoding="utf-8")

        mock_bin_dir = tmp_path / "mock-bin"
        mock_bin_dir.mkdir(parents=True, exist_ok=True)
        curl_file = mock_bin_dir / "curl"
        curl_file.write_text(
            """#!/usr/bin/env bash
set -euo pipefail

attempt_file="${PROMTOOL_TEST_CURL_ATTEMPT_FILE:?}"
source_file="${PROMTOOL_TEST_CURL_SOURCE_FILE:?}"

attempt=0
if [[ -f "${attempt_file}" ]]; then
  attempt="$(cat "${attempt_file}")"
fi
attempt=$((attempt + 1))
echo "${attempt}" > "${attempt_file}"

output_file=""
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -o)
      output_file="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

cp "${source_file}" "${output_file}"
""",
            encoding="utf-8",
        )
        curl_file.chmod(0o755)

        attempt_file = tmp_path / "curl-attempts.txt"
        env = dict(os.environ)
        env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_SHA256SUMS_URL"] = "https://example.invalid/sha256sums.txt"
        env["PROMTOOL_REMOTE_FETCH_CACHE_FILE"] = str(cache_file)
        env["PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS"] = "60"
        env["PROMTOOL_TEST_CURL_ATTEMPT_FILE"] = str(attempt_file)
        env["PROMTOOL_TEST_CURL_SOURCE_FILE"] = str(source_sha256sums_file)
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        attempt_count = attempt_file.read_text(encoding="utf-8").strip()
        refreshed_meta_epoch = int(cache_meta_file.read_text(encoding="utf-8").strip())
        refreshed_cache_content = cache_file.read_text(encoding="utf-8")
        source_cache_content = source_sha256sums_file.read_text(encoding="utf-8")

    assert completed.returncode == 0
    assert "cached sha256sums metadata is stale" in completed.stderr
    assert "updated sha256sums cache" in completed.stderr
    assert attempt_count == "1"
    assert refreshed_meta_epoch >= stale_epoch
    assert refreshed_cache_content == source_cache_content


def test_promtool_installer_config_validation_remote_soft_mode_ignores_mismatch() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    (
                        "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64="
                        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    ),
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = tmp_path / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "soft"
        env["PROMTOOL_SHA256SUMS_URL"] = f"file://{sha256sums_file}"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    assert completed.returncode == 0
    assert "remote checksum validation failed in soft mode" in completed.stderr
    assert "checksum mismatch for" in completed.stderr
    assert "metric remote_soft_fallback_total=1" in completed.stderr


def test_promtool_installer_config_validation_fails_for_invalid_remote_mode() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    env = dict(os.environ)
    env["PROMTOOL_VALIDATE_REMOTE"] = "1"
    env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "invalid-mode"
    completed = subprocess.run(
        ["bash", str(validate_script_file)],
        cwd=backend_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "PROMTOOL_VALIDATE_REMOTE_MODE must be one of: strict, soft" in completed.stderr


def test_promtool_installer_config_validation_soft_mode_writes_audit_record() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    (
                        "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64="
                        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    ),
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = tmp_path / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        audit_file = tmp_path / "audit" / "remote-soft-fallback.log"

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "soft"
        env["PROMTOOL_SHA256SUMS_URL"] = f"file://{sha256sums_file}"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_FILE"] = str(audit_file)
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        audit_content = audit_file.read_text(encoding="utf-8")

    assert completed.returncode == 0
    assert "wrote soft-mode audit record" in completed.stderr
    assert "mode=soft" in audit_content
    assert f"version={PROMTOOL_DEFAULT_VERSION}" in audit_content
    assert "reason=checksum mismatch for" in audit_content


def test_promtool_installer_config_validation_soft_mode_audit_trims_to_max_lines() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    (
                        "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64="
                        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    ),
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = tmp_path / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        audit_file = tmp_path / "audit" / "remote-soft-fallback.log"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        audit_file.write_text(
            "\n".join(
                [
                    "2026-02-19T00:00:00Z\tmode=soft\tversion=2.52.0\turl=x\treason=old-1",
                    "2026-02-19T00:10:00Z\tmode=soft\tversion=2.52.0\turl=x\treason=old-2",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "soft"
        env["PROMTOOL_SHA256SUMS_URL"] = f"file://{sha256sums_file}"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_FILE"] = str(audit_file)
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES"] = "2"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        retained_lines = [line for line in audit_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert completed.returncode == 0
    assert "trimmed soft-mode audit file to last 2 line(s)" in completed.stderr
    assert len(retained_lines) == 2
    assert "reason=old-2" in retained_lines[0]
    assert "reason=checksum mismatch for" in retained_lines[1]


def test_promtool_installer_config_validation_fails_for_invalid_soft_audit_max_lines() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_AMD64={PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "soft"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_FILE"] = str(tmp_path / "audit.log")
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES"] = "-1"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    assert completed.returncode != 0
    assert "PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES must be a non-negative integer" in completed.stderr


def test_promtool_installer_config_validation_soft_mode_audit_trims_to_max_bytes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    (
                        "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64="
                        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    ),
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = tmp_path / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        audit_file = tmp_path / "audit" / "remote-soft-fallback.log"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        audit_file.write_text(
            "\n".join(
                [
                    "2026-02-19T00:00:00Z\tmode=soft\tversion=2.52.0\turl=x\treason=" + "old-audit-entry-" * 12,
                    "2026-02-19T00:10:00Z\tmode=soft\tversion=2.52.0\turl=x\treason=" + "old-audit-entry-" * 12,
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "soft"
        env["PROMTOOL_SHA256SUMS_URL"] = f"file://{sha256sums_file}"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_FILE"] = str(audit_file)
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES"] = "0"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES"] = "280"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        audit_bytes_size = len(audit_file.read_bytes())
        audit_content = audit_file.read_text(encoding="utf-8")

    assert completed.returncode == 0
    assert "trimmed soft-mode audit file to last 280 byte(s)" in completed.stderr
    assert audit_bytes_size <= 280
    assert "reason=checksum mismatch for" in audit_content


def test_promtool_installer_config_validation_soft_mode_audit_prunes_by_retention_days() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    (
                        "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64="
                        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    ),
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = tmp_path / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        audit_file = tmp_path / "audit" / "remote-soft-fallback.log"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        audit_file.write_text(
            "\n".join(
                [
                    "2000-01-01T00:00:00Z\tmode=soft\tversion=2.52.0\turl=x\treason=old-prune",
                    "2099-01-01T00:00:00Z\tmode=soft\tversion=2.52.0\turl=x\treason=future-keep",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "soft"
        env["PROMTOOL_SHA256SUMS_URL"] = f"file://{sha256sums_file}"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_FILE"] = str(audit_file)
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES"] = "0"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES"] = "0"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_RETENTION_DAYS"] = "1"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        retained_lines = [line for line in audit_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert completed.returncode == 0
    assert "pruned soft-mode audit file by retention window 1 day(s)" in completed.stderr
    assert all("reason=old-prune" not in line for line in retained_lines)
    assert any("reason=future-keep" in line for line in retained_lines)
    assert any("reason=checksum mismatch for" in line for line in retained_lines)


def test_promtool_installer_config_validation_soft_mode_retention_days_fallback_without_python() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    (
                        "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64="
                        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    ),
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sha256sums_file = tmp_path / "sha256sums.txt"
        sha256sums_file.write_text(
            "\n".join(
                [
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz",
                    f"{PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}  prometheus-{PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        audit_file = tmp_path / "audit" / "remote-soft-fallback.log"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        audit_file.write_text(
            "\n".join(
                [
                    "2000-01-01T00:00:00Z\tmode=soft\tversion=2.52.0\turl=x\treason=old-prune",
                    "2099-01-01T00:00:00Z\tmode=soft\tversion=2.52.0\turl=x\treason=future-keep",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        mock_bin_dir = tmp_path / "mock-bin"
        mock_bin_dir.mkdir(parents=True, exist_ok=True)

        python3_file = mock_bin_dir / "python3"
        python3_file.write_text("#!/usr/bin/env bash\nexit 127\n", encoding="utf-8")
        python3_file.chmod(0o755)

        python_file = mock_bin_dir / "python"
        python_file.write_text("#!/usr/bin/env bash\nexit 127\n", encoding="utf-8")
        python_file.chmod(0o755)

        date_file = mock_bin_dir / "date"
        date_file.write_text(
            """#!/usr/bin/env bash
set -euo pipefail

if [[ "$*" == *"-d 1 days ago"* ]]; then
  printf "2025-01-01T00:00:00Z\\n"
  exit 0
fi

printf "2026-02-19T12:00:00Z\\n"
""",
            encoding="utf-8",
        )
        date_file.chmod(0o755)

        env = dict(os.environ)
        env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "soft"
        env["PROMTOOL_SHA256SUMS_URL"] = f"file://{sha256sums_file}"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_FILE"] = str(audit_file)
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES"] = "0"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES"] = "0"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_RETENTION_DAYS"] = "1"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        retained_lines = [line for line in audit_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert completed.returncode == 0
    assert "pruned soft-mode audit file by retention window 1 day(s)" in completed.stderr
    assert all("reason=old-prune" not in line for line in retained_lines)
    assert any("reason=future-keep" in line for line in retained_lines)


def test_promtool_installer_config_validation_fails_for_invalid_soft_audit_max_bytes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-promtool-installer-config.sh"
    assert validate_script_file.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = tmp_path / "promtool-installer.defaults"
        config_file.write_text(
            "\n".join(
                [
                    f"PROMTOOL_DEFAULT_VERSION={PROMTOOL_DEFAULT_VERSION}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_AMD64={PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64}",
                    f"PROMTOOL_DEFAULT_SHA256_LINUX_ARM64={PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PROMTOOL_CONFIG_FILE"] = str(config_file)
        env["PROMTOOL_VALIDATE_REMOTE"] = "1"
        env["PROMTOOL_VALIDATE_REMOTE_MODE"] = "soft"
        env["PROMTOOL_REMOTE_SOFT_AUDIT_FILE"] = str(tmp_path / "audit.log")
        env["PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES"] = "-2"
        completed = subprocess.run(
            ["bash", str(validate_script_file)],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    assert completed.returncode != 0
    assert "PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES must be a non-negative integer" in completed.stderr
