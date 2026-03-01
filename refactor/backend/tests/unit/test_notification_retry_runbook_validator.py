from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_notification_retry_runbook_validator_script_passes_default_files() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "runbook is consistent" in completed.stdout.lower()
    assert "default/dev/staging/prod" in completed.stdout.lower()


def test_notification_retry_runbook_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
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
    assert payload["validator"] == "validate-notification-retry-runbook"
    assert payload["status"] == "ok"
    assert payload["default_rule_file"].endswith("refactor-notification-retry-alerts.yml")
    assert payload["prod_rule_file"].endswith("refactor-notification-retry-alerts.prod.yml")
    assert payload["runbook_file"].endswith("notification-retry-alert-runbook.md")
    assert payload["profile_count"] == 3


def test_notification_retry_runbook_validator_script_fails_when_runbook_threshold_drift(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    assert validate_script_file.exists()

    default_rule_file = backend_root / "monitoring" / "prometheus" / "rules" / "refactor-notification-retry-alerts.yml"
    default_runbook_file = (
        backend_root.parent / "docs" / "runbooks" / "2026-02-20-notification-retry-alert-runbook.md"
    )

    drifted_runbook_file = tmp_path / "drifted-runbook.md"
    drifted_runbook_file.write_text(
        default_runbook_file.read_text(encoding="utf-8").replace(
            "success ratio `< 0.6`",
            "success ratio `< 0.61`",
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--rule-file",
            str(default_rule_file),
            "--runbook-file",
            str(drifted_runbook_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "mismatch" in completed.stderr.lower()


def test_notification_retry_runbook_validator_script_fails_when_runbook_matrix_drift(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    assert validate_script_file.exists()

    default_runbook_file = (
        backend_root.parent / "docs" / "runbooks" / "2026-02-20-notification-retry-alert-runbook.md"
    )
    drifted_runbook_file = tmp_path / "drifted-runbook-matrix.md"
    drifted_runbook_file.write_text(
        default_runbook_file.read_text(encoding="utf-8").replace(
            "| dev | retry success ratio warn | attempts >= 10 | success ratio < 0.7 | 5m |",
            "| dev | retry success ratio warn | attempts >= 10 | success ratio < 0.71 | 5m |",
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--runbook-file",
            str(drifted_runbook_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "rule:dev" in completed.stderr


def test_notification_retry_runbook_validator_script_fails_when_default_rule_drifts_from_prod(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    assert validate_script_file.exists()

    default_rule_file = backend_root / "monitoring" / "prometheus" / "rules" / "refactor-notification-retry-alerts.yml"
    drifted_default_rule_file = tmp_path / "drifted-default-rule.yml"
    drifted_default_rule_file.write_text(
        default_rule_file.read_text(encoding="utf-8").replace(
            "refactor_notification_retry_success_ratio < 0.6",
            "refactor_notification_retry_success_ratio < 0.61",
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--rule-file",
            str(drifted_default_rule_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "rule:default" in completed.stderr


def test_notification_retry_runbook_validator_script_json_errors_for_mismatch(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    assert validate_script_file.exists()

    default_runbook_file = (
        backend_root.parent / "docs" / "runbooks" / "2026-02-20-notification-retry-alert-runbook.md"
    )
    drifted_runbook_file = tmp_path / "drifted-runbook-json-errors.md"
    drifted_runbook_file.write_text(
        default_runbook_file.read_text(encoding="utf-8").replace(
            "| dev | retry success ratio warn | attempts >= 10 | success ratio < 0.7 | 5m |",
            "| dev | retry success ratio warn | attempts >= 10 | success ratio < 0.71 | 5m |",
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--runbook-file",
            str(drifted_runbook_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-notification-retry-runbook"
    assert payload["code"] == "notification_retry_runbook_baseline_mismatch"
    assert "mismatch" in payload["message"].lower()


def test_notification_retry_runbook_validator_script_json_errors_for_missing_file(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    assert validate_script_file.exists()

    missing_runbook_file = tmp_path / "missing-runbook.md"
    assert not missing_runbook_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--runbook-file",
            str(missing_runbook_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-notification-retry-runbook"
    assert payload["code"] == "notification_retry_runbook_file_not_found"
    assert payload["context"]["path"] == str(missing_runbook_file)


def test_notification_retry_runbook_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
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
    assert payload["validator"] == "validate-notification-retry-runbook"
    assert payload["code"] == "notification_retry_runbook_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_notification_retry_runbook_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-notification-retry-runbook.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--rule-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-notification-retry-runbook"
    assert payload["code"] == "notification_retry_runbook_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--rule-file" in payload["context"]["argv"]


def test_ci_script_invokes_notification_retry_runbook_validator() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    ci_script_file = backend_root / "scripts" / "ci.sh"
    assert ci_script_file.exists()

    content = ci_script_file.read_text(encoding="utf-8")
    assert "./scripts/validate-notification-retry-runbook.py" in content
