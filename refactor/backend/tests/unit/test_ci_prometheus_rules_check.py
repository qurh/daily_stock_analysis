import os
import subprocess
import tempfile
from pathlib import Path

PROMTOOL_DEFAULT_VERSION = "2.52.0"
PROMTOOL_ARCHIVE_SHA256_LINUX_AMD64 = "7f31c5d6474bbff3e514e627e0b7a7fbbd4e5cea3f315fd0b76cad50be4c1ba3"
PROMTOOL_ARCHIVE_SHA256_LINUX_ARM64 = "b503c0f552e381d7d3f84dfd275166bf07c74f99c428ffed69447d4ab3259901"


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
    assert "PROMTOOL_VERSION:" not in content
    assert "PROMTOOL_SHA256:" not in content
    assert "bash refactor/backend/scripts/install-promtool.sh" in content
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
    assert "PROMTOOL_VERSION:" not in content
    assert "PROMTOOL_SHA256:" not in content
    assert "bash refactor/backend/scripts/install-promtool.sh" in content
    assert "apt-get install -y prometheus" not in content
    assert "bash scripts/ci.sh" in content


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
