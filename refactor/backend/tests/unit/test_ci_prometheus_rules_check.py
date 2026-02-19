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
    assert 'PROMTOOL_VERSION: "2.52.0"' in content
    assert "github.com/prometheus/prometheus/releases/download" in content
    assert "tar -xzf" in content
    assert "sudo install" in content
    assert "apt-get install -y prometheus" not in content
    assert "cd refactor/backend" in content
    assert "bash scripts/ci.sh" in content
    assert 'PROMTOOL_REQUIRED: "1"' in content


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
    assert 'PROMTOOL_VERSION: "2.52.0"' in content
    assert "github.com/prometheus/prometheus/releases/download" in content
    assert "apt-get install -y prometheus" not in content
    assert "bash scripts/ci.sh" in content
