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
    assert 'PROMTOOL_VALIDATE_REMOTE: "1"' in content


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
