import json
import os
import re
import runpy
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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
    assert "./scripts/validate-strict-gate-summary-schema.py" in ci_content
    assert "./scripts/validate-summary-contract-changelog.py" in ci_content
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
    assert isinstance(payload["summary_schema"], dict)
    assert isinstance(payload["summary_contract"], dict)
    assert isinstance(payload["placeholder_markers"], dict)
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


def test_validator_error_code_metadata_lint_validator_script_supports_profiled_lint_config(tmp_path) -> None:
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

    assert summary_script.exists()
    assert contract_script.exists()
    assert placeholder_markers_script.exists()

    summary_codes = set(_load_validator_error_codes(summary_script).values())
    contract_codes = set(_load_validator_error_codes(contract_script).values())
    placeholder_markers_codes = set(_load_validator_error_codes(placeholder_markers_script).values())

    assert summary_codes
    assert contract_codes
    assert placeholder_markers_codes
    assert all(code.startswith("summary_schema_") for code in summary_codes)
    assert all(code.startswith("summary_contract_") for code in contract_codes)
    assert all(code.startswith("placeholder_markers_") for code in placeholder_markers_codes)


def test_validator_error_code_catalog_covers_all_script_error_codes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    catalog_file = backend_root / "config" / "validator-error-codes.json"
    summary_script = backend_root / "scripts" / "validate-strict-gate-summary-schema.py"
    contract_script = backend_root / "scripts" / "validate-summary-contract-changelog.py"
    placeholder_markers_script = backend_root / "scripts" / "validate-validator-placeholder-markers.py"

    assert catalog_file.exists()
    catalog_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    catalog_codes = {
        code
        for group in ("summary_schema", "summary_contract", "placeholder_markers")
        for code in catalog_payload.get(group, {}).keys()
    }

    script_codes: set[str] = set()
    for script_file in (summary_script, contract_script, placeholder_markers_script):
        assert script_file.exists()
        content = script_file.read_text(encoding="utf-8")
        script_codes.update(VALIDATOR_CODE_PATTERN.findall(content))
        script_codes.update(_load_validator_error_codes(script_file).values())

    missing_codes = sorted(script_codes.difference(catalog_codes))
    assert not missing_codes


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
