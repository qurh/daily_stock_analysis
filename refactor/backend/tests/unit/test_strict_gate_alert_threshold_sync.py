import json
import subprocess
import sys
from pathlib import Path


def _base_threshold_config(backend_root: Path) -> dict:
    config_file = backend_root / "config" / "strict-gate-alert-thresholds.json"
    return json.loads(config_file.read_text(encoding="utf-8"))


def _write_threshold_config(tmp_path: Path, payload: dict) -> Path:
    config_file = tmp_path / "strict-gate-alert-thresholds.json"
    config_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return config_file


def test_strict_gate_alert_threshold_config_has_required_profiles() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    config_file = backend_root / "config" / "strict-gate-alert-thresholds.json"

    assert config_file.exists()
    payload = json.loads(config_file.read_text(encoding="utf-8"))
    profiles = payload.get("profiles")
    assert isinstance(profiles, dict)

    for profile_name in ("default", "dev", "staging", "prod"):
        profile = profiles.get(profile_name)
        assert isinstance(profile, dict), f"missing profile: {profile_name}"
        for key in ("min_hits", "warn_ratio", "warn_for", "critical_ratio", "critical_for"):
            assert key in profile, f"missing key {key} in profile {profile_name}"
        for key in (
            "soft_audit_max_lines_for",
            "soft_audit_max_lines_severity",
            "soft_audit_max_bytes_for",
            "soft_audit_max_bytes_severity",
            "soft_audit_rotation_unbounded_for",
            "soft_audit_rotation_unbounded_severity",
            "governance_warn_for",
            "governance_warn_severity",
            "governance_critical_for",
            "governance_critical_severity",
            "governance_normalization_for",
            "governance_normalization_severity",
        ):
            assert key in profile, f"missing key {key} in profile {profile_name}"


def test_strict_gate_alert_threshold_sync_check_mode_passes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"

    result = subprocess.run(
        [sys.executable, str(sync_script), "--check"],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "strict gate alert threshold sync check failed.\n" f"stdout:\n{result.stdout}\n" f"stderr:\n{result.stderr}"
    )


def test_strict_gate_alert_threshold_sync_supports_profile_check_mode() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"

    result = subprocess.run(
        [sys.executable, str(sync_script), "--check", "--profile", "dev"],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "strict gate alert threshold profile check failed.\n" f"stdout:\n{result.stdout}\n" f"stderr:\n{result.stderr}"
    )


def test_strict_gate_alert_threshold_sync_rejects_unknown_profile() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"

    result = subprocess.run(
        [sys.executable, str(sync_script), "--check", "--profile", "qa"],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "invalid choice" in result.stderr.lower() or "unknown profile" in result.stderr.lower()


def test_strict_gate_alert_threshold_sync_rejects_invalid_duration_format(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"
    payload = _base_threshold_config(backend_root)
    payload["profiles"]["dev"]["warn_for"] = "15minutes"
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [sys.executable, str(sync_script), "--check", "--config", str(config_file)],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "invalid duration" in result.stderr.lower()


def test_strict_gate_alert_threshold_sync_rejects_invalid_severity_enum(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"
    payload = _base_threshold_config(backend_root)
    payload["profiles"]["staging"]["soft_audit_max_lines_severity"] = "urgent"
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [sys.executable, str(sync_script), "--check", "--config", str(config_file)],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "invalid severity" in result.stderr.lower()


def test_strict_gate_alert_threshold_sync_rejects_out_of_range_ratio(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"
    payload = _base_threshold_config(backend_root)
    payload["profiles"]["prod"]["critical_ratio"] = 1.5
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [sys.executable, str(sync_script), "--check", "--config", str(config_file)],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "out of range" in result.stderr.lower()


def test_strict_gate_alert_threshold_sync_rejects_critical_ratio_below_warn_ratio(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"
    payload = _base_threshold_config(backend_root)
    payload["profiles"]["default"]["warn_ratio"] = 0.7
    payload["profiles"]["default"]["critical_ratio"] = 0.5
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [sys.executable, str(sync_script), "--check", "--config", str(config_file)],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "must be >=" in result.stderr.lower()


def test_strict_gate_alert_threshold_sync_dry_run_outputs_diff_without_writing(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"
    dev_rule_file = (
        backend_root / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.dev.yml"
    )

    original_content = dev_rule_file.read_text(encoding="utf-8")

    payload = _base_threshold_config(backend_root)
    payload["profiles"]["dev"]["warn_for"] = "6m"
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [sys.executable, str(sync_script), "--dry-run", "--profile", "dev", "--config", str(config_file)],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "--- " in result.stdout
    assert "+++ " in result.stdout
    assert "@@" in result.stdout
    assert dev_rule_file.read_text(encoding="utf-8") == original_content


def test_strict_gate_alert_threshold_sync_check_and_dry_run_fails_when_out_of_sync(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"

    payload = _base_threshold_config(backend_root)
    payload["profiles"]["dev"]["warn_for"] = "6m"
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [sys.executable, str(sync_script), "--check", "--dry-run", "--profile", "dev", "--config", str(config_file)],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "out of sync" in result.stdout.lower()


def test_strict_gate_alert_threshold_sync_summary_only_outputs_compact_summary(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"

    payload = _base_threshold_config(backend_root)
    payload["profiles"]["dev"]["warn_for"] = "6m"
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [
            sys.executable,
            str(sync_script),
            "--dry-run",
            "--summary-only",
            "--profile",
            "dev",
            "--config",
            str(config_file),
        ],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "summary:" in result.stdout.lower()
    assert "refactor-threshold-governance-alerts.dev.yml" in result.stdout
    assert "@@" not in result.stdout
    assert "--- a/" not in result.stdout
    assert "+++ b/" not in result.stdout


def test_strict_gate_alert_threshold_sync_summary_only_requires_dry_run(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"

    payload = _base_threshold_config(backend_root)
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [sys.executable, str(sync_script), "--summary-only", "--profile", "dev", "--config", str(config_file)],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "requires --dry-run" in result.stderr.lower()


def test_strict_gate_alert_threshold_sync_summary_only_json_outputs_machine_readable_summary(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"

    payload = _base_threshold_config(backend_root)
    payload["profiles"]["dev"]["warn_for"] = "6m"
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [
            sys.executable,
            str(sync_script),
            "--dry-run",
            "--summary-only",
            "--summary-format",
            "json",
            "--profile",
            "dev",
            "--config",
            str(config_file),
        ],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    summary = json.loads(result.stdout)
    assert summary["changed_files_count"] == 1
    assert summary["total_added_lines"] >= 1
    assert summary["total_removed_lines"] >= 0
    assert len(summary["files"]) == 1
    assert summary["files"][0]["path"].endswith("refactor-threshold-governance-alerts.dev.yml")


def test_strict_gate_alert_threshold_sync_summary_format_requires_summary_only(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_script = backend_root / "scripts" / "sync-strict-gate-alert-thresholds.py"

    payload = _base_threshold_config(backend_root)
    config_file = _write_threshold_config(tmp_path=tmp_path, payload=payload)

    result = subprocess.run(
        [
            sys.executable,
            str(sync_script),
            "--dry-run",
            "--summary-format",
            "json",
            "--profile",
            "dev",
            "--config",
            str(config_file),
        ],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "requires --summary-only" in result.stderr.lower()
