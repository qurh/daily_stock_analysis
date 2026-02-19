#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StrictGateThresholdProfile:
    min_hits: int
    warn_ratio: float
    warn_for: str
    critical_ratio: float
    critical_for: str
    soft_audit_max_lines_for: str
    soft_audit_max_lines_severity: str
    soft_audit_max_bytes_for: str
    soft_audit_max_bytes_severity: str
    soft_audit_rotation_unbounded_for: str
    soft_audit_rotation_unbounded_severity: str


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = BACKEND_ROOT / "config" / "strict-gate-alert-thresholds.json"
DURATION_PATTERN = re.compile(r"^[1-9][0-9]*(ms|s|m|h|d|w|y)$")
VALID_SEVERITIES = {"info", "warning", "critical"}
RULE_FILE_BY_PROFILE = {
    "default": BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.yml",
    "dev": BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.dev.yml",
    "staging": BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.staging.yml",
    "prod": BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.prod.yml",
}


def _parse_min_hits(profile_name: str, raw_value: object) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid min_hits for profile '{profile_name}': {raw_value}") from exc
    if value <= 0:
        raise ValueError(f"min_hits out of range for profile '{profile_name}': {value} (must be > 0)")
    return value


def _parse_ratio(profile_name: str, field_name: str, raw_value: object) -> float:
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid ratio for profile '{profile_name}' field '{field_name}': {raw_value}") from exc
    if value < 0.0 or value > 1.0:
        raise ValueError(
            f"ratio out of range for profile '{profile_name}' field '{field_name}': {value} (must be between 0 and 1)"
        )
    return value


def _parse_duration(profile_name: str, field_name: str, raw_value: object) -> str:
    value = str(raw_value).strip().lower()
    if DURATION_PATTERN.fullmatch(value) is None:
        raise ValueError(
            f"Invalid duration for profile '{profile_name}' field '{field_name}': {raw_value} "
            "(expected pattern like 5m/10m/1h)"
        )
    return value


def _parse_severity(profile_name: str, field_name: str, raw_value: object) -> str:
    value = str(raw_value).strip().lower()
    if value not in VALID_SEVERITIES:
        allowed = ", ".join(sorted(VALID_SEVERITIES))
        raise ValueError(
            f"Invalid severity for profile '{profile_name}' field '{field_name}': {raw_value} "
            f"(allowed: {allowed})"
        )
    return value


def _format_number(value: float | int) -> str:
    numeric = float(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.10f}".rstrip("0").rstrip(".")


def _replace_alert_field(content: str, alert_name: str, field_name: str, value: str) -> str:
    pattern = re.compile(
        rf"(?ms)(^\s*-\s*alert:\s*{re.escape(alert_name)}\s*$.*?^\s*{re.escape(field_name)}:\s*)(.+?)$"
    )
    match = pattern.search(content)
    if match is None:
        raise ValueError(f"Unable to find field {field_name} for alert {alert_name}")
    start_value = match.start(2)
    end_value = match.end(2)
    return f"{content[:start_value]}{value}{content[end_value:]}"


def _load_profiles(path: Path) -> dict[str, StrictGateThresholdProfile]:
    if not path.exists():
        raise FileNotFoundError(f"Strict gate threshold config not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, dict):
        raise ValueError("Config field 'profiles' must be an object")

    profiles: dict[str, StrictGateThresholdProfile] = {}
    for profile_name in RULE_FILE_BY_PROFILE:
        raw_profile = raw_profiles.get(profile_name)
        if not isinstance(raw_profile, dict):
            raise ValueError(f"Missing profile definition: {profile_name}")

        required_fields = (
            "min_hits",
            "warn_ratio",
            "warn_for",
            "critical_ratio",
            "critical_for",
            "soft_audit_max_lines_for",
            "soft_audit_max_lines_severity",
            "soft_audit_max_bytes_for",
            "soft_audit_max_bytes_severity",
            "soft_audit_rotation_unbounded_for",
            "soft_audit_rotation_unbounded_severity",
        )
        for field in required_fields:
            if field not in raw_profile:
                raise ValueError(f"Missing field '{field}' in profile '{profile_name}'")

        min_hits = _parse_min_hits(profile_name=profile_name, raw_value=raw_profile["min_hits"])
        warn_ratio = _parse_ratio(profile_name=profile_name, field_name="warn_ratio", raw_value=raw_profile["warn_ratio"])
        critical_ratio = _parse_ratio(
            profile_name=profile_name, field_name="critical_ratio", raw_value=raw_profile["critical_ratio"]
        )
        if critical_ratio < warn_ratio:
            raise ValueError(
                f"ratio out of range for profile '{profile_name}': critical_ratio {critical_ratio} "
                f"must be >= warn_ratio {warn_ratio}"
            )

        profiles[profile_name] = StrictGateThresholdProfile(
            min_hits=min_hits,
            warn_ratio=warn_ratio,
            warn_for=_parse_duration(profile_name=profile_name, field_name="warn_for", raw_value=raw_profile["warn_for"]),
            critical_ratio=critical_ratio,
            critical_for=_parse_duration(
                profile_name=profile_name, field_name="critical_for", raw_value=raw_profile["critical_for"]
            ),
            soft_audit_max_lines_for=_parse_duration(
                profile_name=profile_name,
                field_name="soft_audit_max_lines_for",
                raw_value=raw_profile["soft_audit_max_lines_for"],
            ),
            soft_audit_max_lines_severity=_parse_severity(
                profile_name=profile_name,
                field_name="soft_audit_max_lines_severity",
                raw_value=raw_profile["soft_audit_max_lines_severity"],
            ),
            soft_audit_max_bytes_for=_parse_duration(
                profile_name=profile_name,
                field_name="soft_audit_max_bytes_for",
                raw_value=raw_profile["soft_audit_max_bytes_for"],
            ),
            soft_audit_max_bytes_severity=_parse_severity(
                profile_name=profile_name,
                field_name="soft_audit_max_bytes_severity",
                raw_value=raw_profile["soft_audit_max_bytes_severity"],
            ),
            soft_audit_rotation_unbounded_for=_parse_duration(
                profile_name=profile_name,
                field_name="soft_audit_rotation_unbounded_for",
                raw_value=raw_profile["soft_audit_rotation_unbounded_for"],
            ),
            soft_audit_rotation_unbounded_severity=_parse_severity(
                profile_name=profile_name,
                field_name="soft_audit_rotation_unbounded_severity",
                raw_value=raw_profile["soft_audit_rotation_unbounded_severity"],
            ),
        )
    return profiles


def _render_profile(content: str, profile: StrictGateThresholdProfile) -> str:
    warn_expr = (
        f"refactor_strategy_publish_strict_gate_hits_total >= {_format_number(profile.min_hits)} and "
        f"refactor_strategy_publish_strict_gate_block_ratio >= {_format_number(profile.warn_ratio)}"
    )
    critical_expr = (
        f"refactor_strategy_publish_strict_gate_hits_total >= {_format_number(profile.min_hits)} and "
        f"refactor_strategy_publish_strict_gate_block_ratio >= {_format_number(profile.critical_ratio)}"
    )

    updated = content
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorStrategyPublishStrictGateBlockRatioWarn",
        field_name="expr",
        value=warn_expr,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorStrategyPublishStrictGateBlockRatioWarn",
        field_name="for",
        value=profile.warn_for,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorStrategyPublishStrictGateBlockRatioCritical",
        field_name="expr",
        value=critical_expr,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorStrategyPublishStrictGateBlockRatioCritical",
        field_name="for",
        value=profile.critical_for,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorPromtoolSoftAuditMaxLinesExceeded",
        field_name="for",
        value=profile.soft_audit_max_lines_for,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorPromtoolSoftAuditMaxLinesExceeded",
        field_name="severity",
        value=profile.soft_audit_max_lines_severity,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorPromtoolSoftAuditMaxBytesExceeded",
        field_name="for",
        value=profile.soft_audit_max_bytes_for,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorPromtoolSoftAuditMaxBytesExceeded",
        field_name="severity",
        value=profile.soft_audit_max_bytes_severity,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorPromtoolSoftAuditRotationUnbounded",
        field_name="for",
        value=profile.soft_audit_rotation_unbounded_for,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorPromtoolSoftAuditRotationUnbounded",
        field_name="severity",
        value=profile.soft_audit_rotation_unbounded_severity,
    )
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync strict gate alert thresholds into Prometheus rule profiles.")
    parser.add_argument("--check", action="store_true", help="Check mode: fail if any file is out of sync.")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Path to threshold config JSON file.")
    parser.add_argument(
        "--profile",
        action="append",
        choices=sorted(RULE_FILE_BY_PROFILE.keys()),
        help="Only sync/check selected profile(s). Repeatable.",
    )
    args = parser.parse_args()

    profiles = _load_profiles(args.config)
    selected_profiles = list(args.profile or RULE_FILE_BY_PROFILE.keys())

    changed_files: list[Path] = []
    for profile_name in selected_profiles:
        rule_file = RULE_FILE_BY_PROFILE[profile_name]
        if not rule_file.exists():
            raise FileNotFoundError(f"Rule file not found: {rule_file}")

        original = rule_file.read_text(encoding="utf-8")
        rendered = _render_profile(content=original, profile=profiles[profile_name])
        if rendered != original:
            changed_files.append(rule_file)
            if not args.check:
                rule_file.write_text(rendered, encoding="utf-8")

    if changed_files and args.check:
        for file_path in changed_files:
            rel = file_path.relative_to(BACKEND_ROOT)
            print(f"[sync-strict-gate-alert-thresholds] out of sync: {rel}")
        print("[sync-strict-gate-alert-thresholds] run script without --check to update files.")
        return 1

    if changed_files and not args.check:
        for file_path in changed_files:
            rel = file_path.relative_to(BACKEND_ROOT)
            print(f"[sync-strict-gate-alert-thresholds] updated: {rel}")
    else:
        print("[sync-strict-gate-alert-thresholds] all strict gate threshold rules are in sync.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[sync-strict-gate-alert-thresholds] {exc}", file=sys.stderr)
        sys.exit(1)
