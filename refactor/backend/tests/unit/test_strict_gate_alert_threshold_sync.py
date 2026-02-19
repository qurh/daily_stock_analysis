import json
import subprocess
import sys
from pathlib import Path


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
