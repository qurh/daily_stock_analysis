from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_validator_error_context_high_frequency_validator_script_passes_default_files() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-context-high-frequency-schema.py"
    schema_file = backend_root / "config" / "schemas" / "validator-error-context-high-frequency.schema.json"
    samples_file = backend_root / "config" / "validator-error-context-high-frequency-samples.json"

    assert validate_script_file.exists()
    assert schema_file.exists()
    assert samples_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "samples are valid" in completed.stdout.lower()


def test_validator_error_context_high_frequency_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-context-high-frequency-schema.py"
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
    assert payload["validator"] == "validate-validator-error-context-high-frequency-schema"
    assert payload["status"] == "ok"
    assert payload["schema_file"].endswith("validator-error-context-high-frequency.schema.json")
    assert payload["samples_file"].endswith("validator-error-context-high-frequency-samples.json")
    assert payload["sample_count"] >= 1


def test_validator_error_context_high_frequency_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-context-high-frequency-schema.py"
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
    assert payload["validator"] == "validate-validator-error-context-high-frequency-schema"
    assert payload["code"] == "error_context_high_frequency_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_validator_error_context_high_frequency_validator_script_json_errors_for_missing_schema_file(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-context-high-frequency-schema.py"
    assert validate_script_file.exists()

    missing_schema_file = tmp_path / "missing-error-context.schema.json"
    assert not missing_schema_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--schema-file",
            str(missing_schema_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-context-high-frequency-schema"
    assert payload["code"] == "error_context_high_frequency_schema_file_not_found"
    assert payload["context"]["path"] == str(missing_schema_file)


def test_validator_error_context_high_frequency_validator_script_json_errors_for_sample_schema_validation_failure(
    tmp_path: Path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-validator-error-context-high-frequency-schema.py"
    assert validate_script_file.exists()

    invalid_samples_file = tmp_path / "invalid-error-context-samples.json"
    invalid_samples_file.write_text(
        json.dumps(
            [
                {
                    "validator": "validate-summary-contract-changelog",
                    "code": "summary_contract_required_file_not_found",
                    "message": "required file not found: /tmp/missing-main.py",
                    "context": {},
                }
            ],
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--samples-file",
            str(invalid_samples_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-validator-error-context-high-frequency-schema"
    assert payload["code"] == "error_context_high_frequency_sample_schema_validation_failed"
    assert payload["context"]["sample_index"] == 0
    assert isinstance(payload["context"]["validation_path"], list)
