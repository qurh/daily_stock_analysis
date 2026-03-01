from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _copy_rule_files(source_dir: Path, target_dir: Path) -> None:
    for filename in (
        "refactor-notification-retry-alerts.yml",
        "refactor-notification-retry-alerts.dev.yml",
        "refactor-notification-retry-alerts.staging.yml",
        "refactor-notification-retry-alerts.prod.yml",
    ):
        (target_dir / filename).write_text((source_dir / filename).read_text(encoding="utf-8"), encoding="utf-8")


def _copy_runbook_file(source_file: Path, target_file: Path) -> None:
    target_file.write_text(source_file.read_text(encoding="utf-8"), encoding="utf-8")


def test_notification_retry_alert_threshold_sync_script_check_passes_default_files() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-notification-retry-alert-thresholds.py"
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
    assert "runbook" in completed.stdout.lower()


def test_notification_retry_alert_threshold_sync_script_check_fails_when_profile_rule_drifts(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-notification-retry-alert-thresholds.py"
    assert sync_script_file.exists()

    config_file = backend_root / "config" / "notification-retry-alert-thresholds.json"
    source_rules_dir = backend_root / "monitoring" / "prometheus" / "rules"
    isolated_rules_dir = tmp_path / "rules"
    isolated_rules_dir.mkdir(parents=True, exist_ok=True)
    _copy_rule_files(source_rules_dir, isolated_rules_dir)

    drifted_file = isolated_rules_dir / "refactor-notification-retry-alerts.dev.yml"
    drifted_file.write_text(
        drifted_file.read_text(encoding="utf-8").replace(
            "refactor_notification_retry_success_ratio < 0.7",
            "refactor_notification_retry_success_ratio < 0.71",
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--config-file",
            str(config_file),
            "--rules-dir",
            str(isolated_rules_dir),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "out of sync" in completed.stdout.lower() or "out of sync" in completed.stderr.lower()


def test_notification_retry_alert_threshold_sync_script_check_fails_when_runbook_drifts(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script_file = backend_root / "scripts" / "sync-notification-retry-alert-thresholds.py"
    assert sync_script_file.exists()

    config_file = backend_root / "config" / "notification-retry-alert-thresholds.json"
    source_runbook_file = backend_root.parent / "docs" / "runbooks" / "2026-02-20-notification-retry-alert-runbook.md"
    isolated_runbook_file = tmp_path / "notification-retry-alert-runbook.md"
    _copy_runbook_file(source_runbook_file, isolated_runbook_file)

    isolated_runbook_file.write_text(
        isolated_runbook_file.read_text(encoding="utf-8").replace(
            "success ratio `< 0.6`",
            "success ratio `< 0.61`",
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(sync_script_file),
            "--check",
            "--config-file",
            str(config_file),
            "--runbook-file",
            str(isolated_runbook_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "out of sync" in completed.stdout.lower() or "out of sync" in completed.stderr.lower()
    assert "runbook" in completed.stdout.lower() or "runbook" in completed.stderr.lower()


def test_ci_script_invokes_notification_retry_alert_threshold_sync_check() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    ci_script_file = backend_root / "scripts" / "ci.sh"
    assert ci_script_file.exists()

    content = ci_script_file.read_text(encoding="utf-8")
    assert "./scripts/sync-notification-retry-alert-thresholds.py --check" in content
