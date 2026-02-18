import os
import subprocess
from pathlib import Path


def test_ci_script_invokes_prometheus_rules_check() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    ci_file = backend_root / "scripts" / "ci.sh"
    check_file = backend_root / "scripts" / "check-prometheus-rules.sh"

    assert ci_file.exists()
    assert check_file.exists()

    ci_content = ci_file.read_text(encoding="utf-8")
    check_content = check_file.read_text(encoding="utf-8")

    assert "./scripts/check-prometheus-rules.sh" in ci_content
    assert "promtool check rules" in check_content
    assert "PROMTOOL_REQUIRED" in ci_content
    assert "CI" in ci_content


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
