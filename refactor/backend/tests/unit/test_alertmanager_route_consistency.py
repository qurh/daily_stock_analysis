from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_alertmanager_route_consistency_validator_script_passes_default_files() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert alertmanager_file.exists()

    completed = subprocess.run(
        [sys.executable, str(validate_script_file)],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "all alerts are covered" in completed.stdout.lower()


def test_alertmanager_route_consistency_validator_script_json_output_on_success() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert alertmanager_file.exists()

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
    assert payload["validator"] == "validate-alertmanager-route-consistency"
    assert payload["status"] == "ok"
    assert payload["rules_dir"].endswith("monitoring/prometheus/rules")
    assert payload["alertmanager_file"].endswith("refactor-alertmanager-routing.yml")
    assert payload["alert_count"] >= 1
    assert payload["explicit_route_count"] >= 1


def test_alertmanager_route_consistency_validator_script_fails_when_notification_route_missing(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    source_alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert source_alertmanager_file.exists()

    drifted_alertmanager_file = tmp_path / "refactor-alertmanager-routing.yml"
    drifted_alertmanager_file.write_text(
        source_alertmanager_file.read_text(encoding="utf-8").replace(
            'domain="retry-governance"',
            'domain="retry-governance-missing"',
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--alertmanager-file",
            str(drifted_alertmanager_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "unmatched alert" in completed.stderr.lower() or "unmatched alert" in completed.stdout.lower()


def test_alertmanager_route_consistency_validator_script_fails_when_alert_matches_multiple_explicit_routes(
    tmp_path: Path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    source_alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert source_alertmanager_file.exists()

    drifted_alertmanager_file = tmp_path / "refactor-alertmanager-routing.yml"
    drifted_alertmanager_file.write_text(
        source_alertmanager_file.read_text(encoding="utf-8").replace(
            "  routes:\n",
            (
                "  routes:\n"
                "    - matchers:\n"
                "        - scope=\"notification\"\n"
                "      continue: true\n"
                "      receiver: refactor-default-receiver\n"
            ),
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--alertmanager-file",
            str(drifted_alertmanager_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "multiple explicit routes" in completed.stderr.lower() or (
        "multiple explicit routes" in completed.stdout.lower()
    )


def test_alertmanager_route_consistency_validator_script_fails_when_later_route_is_shadowed_even_without_alert_hits(
    tmp_path: Path,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    source_alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert source_alertmanager_file.exists()

    drifted_alertmanager_file = tmp_path / "refactor-alertmanager-routing.yml"
    drifted_alertmanager_file.write_text(
        source_alertmanager_file.read_text(encoding="utf-8").replace(
            "  routes:\n",
            (
                "  routes:\n"
                "    - matchers:\n"
                "        - scope=\"ghost\"\n"
                "      receiver: refactor-default-receiver\n"
                "    - matchers:\n"
                "        - scope=\"ghost\"\n"
                "        - domain=\"ghost-domain\"\n"
                "      receiver: refactor-default-receiver\n"
            ),
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--alertmanager-file",
            str(drifted_alertmanager_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "shadowed route" in completed.stderr.lower() or "shadowed route" in completed.stdout.lower()


def test_alertmanager_route_consistency_validator_script_supports_regex_and_not_regex_matchers(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    source_alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert source_alertmanager_file.exists()

    drifted_alertmanager_file = tmp_path / "refactor-alertmanager-routing.yml"
    drifted_alertmanager_file.write_text(
        source_alertmanager_file.read_text(encoding="utf-8").replace(
            (
                "    - matchers:\n"
                "        - scope=\"notification\"\n"
                "        - domain=\"retry-governance\"\n"
            ),
            (
                "    - matchers:\n"
                "        - scope=~\"^notification$\"\n"
                "        - domain!~\"^other-domain$\"\n"
            ),
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--alertmanager-file",
            str(drifted_alertmanager_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "all alerts are covered" in completed.stdout.lower()


def test_alertmanager_route_consistency_validator_script_fails_for_invalid_regex_matcher(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    source_alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert source_alertmanager_file.exists()

    drifted_alertmanager_file = tmp_path / "refactor-alertmanager-routing.yml"
    drifted_alertmanager_file.write_text(
        source_alertmanager_file.read_text(encoding="utf-8").replace(
            'scope="notification"',
            'scope=~"[notification"',
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--alertmanager-file",
            str(drifted_alertmanager_file),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "invalid regex" in completed.stderr.lower() or "invalid regex" in completed.stdout.lower()


def test_alertmanager_route_consistency_validator_script_json_errors_for_unmatched_alert(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    source_alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert source_alertmanager_file.exists()

    drifted_alertmanager_file = tmp_path / "refactor-alertmanager-routing.yml"
    drifted_alertmanager_file.write_text(
        source_alertmanager_file.read_text(encoding="utf-8").replace(
            'domain="retry-governance"',
            'domain="retry-governance-missing"',
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--alertmanager-file",
            str(drifted_alertmanager_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-alertmanager-route-consistency"
    assert payload["code"] == "alertmanager_route_consistency_unmatched_alert"
    assert "unmatched alert" in payload["message"].lower()


def test_alertmanager_route_consistency_validator_script_json_errors_for_invalid_regex_matcher(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    source_alertmanager_file = backend_root / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
    assert validate_script_file.exists()
    assert source_alertmanager_file.exists()

    drifted_alertmanager_file = tmp_path / "refactor-alertmanager-routing.yml"
    drifted_alertmanager_file.write_text(
        source_alertmanager_file.read_text(encoding="utf-8").replace(
            'scope="notification"',
            'scope=~"[notification"',
            1,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--alertmanager-file",
            str(drifted_alertmanager_file),
            "--json-errors",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-alertmanager-route-consistency"
    assert payload["code"] == "alertmanager_route_consistency_invalid_regex_matcher"
    assert "invalid regex" in payload["message"].lower()


def test_alertmanager_route_consistency_validator_script_json_errors_for_unknown_args() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
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
    assert payload["validator"] == "validate-alertmanager-route-consistency"
    assert payload["code"] == "alertmanager_route_consistency_cli_args_invalid"
    assert payload["context"]["unknown_args"] == ["--unknown-flag"]


def test_alertmanager_route_consistency_validator_script_json_errors_for_missing_arg_value() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    validate_script_file = backend_root / "scripts" / "validate-alertmanager-route-consistency.py"
    assert validate_script_file.exists()

    completed = subprocess.run(
        [
            sys.executable,
            str(validate_script_file),
            "--json-errors",
            "--alertmanager-file",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stderr)
    assert payload["validator"] == "validate-alertmanager-route-consistency"
    assert payload["code"] == "alertmanager_route_consistency_cli_args_invalid"
    assert payload["context"]["failure_mode"] == "argparse_error"
    assert "--alertmanager-file" in payload["context"]["argv"]


def test_ci_script_invokes_alertmanager_route_consistency_validator() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    ci_script_file = backend_root / "scripts" / "ci.sh"
    assert ci_script_file.exists()

    content = ci_script_file.read_text(encoding="utf-8")
    assert "./scripts/validate-alertmanager-route-consistency.py" in content
