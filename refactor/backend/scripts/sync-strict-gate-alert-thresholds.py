#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
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
    governance_warn_for: str
    governance_warn_severity: str
    governance_critical_for: str
    governance_critical_severity: str
    governance_normalization_for: str
    governance_normalization_severity: str


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = BACKEND_ROOT / "config" / "strict-gate-alert-thresholds.json"
DURATION_PATTERN = re.compile(r"^[1-9][0-9]*(ms|s|m|h|d|w|y)$")
VALID_SEVERITIES = {"info", "warning", "critical"}
RULE_FILE_BY_PROFILE = {
    "default": BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.yml",
    "dev": BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.dev.yml",
    "staging": BACKEND_ROOT
    / "monitoring"
    / "prometheus"
    / "rules"
    / "refactor-threshold-governance-alerts.staging.yml",
    "prod": BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.prod.yml",
}
ALERTS_BY_MODULE = {
    "strict": (
        "RefactorStrategyPublishStrictGateBlockRatioWarn",
        "RefactorStrategyPublishStrictGateBlockRatioCritical",
    ),
    "governance": (
        "RefactorThresholdGovernanceWarn",
        "RefactorThresholdGovernanceCritical",
        "RefactorThresholdGovernanceNormalizationApplied",
    ),
    "soft_audit": (
        "RefactorPromtoolSoftAuditMaxLinesExceeded",
        "RefactorPromtoolSoftAuditMaxBytesExceeded",
        "RefactorPromtoolSoftAuditRotationUnbounded",
    ),
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
            f"Invalid severity for profile '{profile_name}' field '{field_name}': {raw_value} " f"(allowed: {allowed})"
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
            "governance_warn_for",
            "governance_warn_severity",
            "governance_critical_for",
            "governance_critical_severity",
            "governance_normalization_for",
            "governance_normalization_severity",
        )
        for field in required_fields:
            if field not in raw_profile:
                raise ValueError(f"Missing field '{field}' in profile '{profile_name}'")

        min_hits = _parse_min_hits(profile_name=profile_name, raw_value=raw_profile["min_hits"])
        warn_ratio = _parse_ratio(
            profile_name=profile_name, field_name="warn_ratio", raw_value=raw_profile["warn_ratio"]
        )
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
            warn_for=_parse_duration(
                profile_name=profile_name, field_name="warn_for", raw_value=raw_profile["warn_for"]
            ),
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
            governance_warn_for=_parse_duration(
                profile_name=profile_name,
                field_name="governance_warn_for",
                raw_value=raw_profile["governance_warn_for"],
            ),
            governance_warn_severity=_parse_severity(
                profile_name=profile_name,
                field_name="governance_warn_severity",
                raw_value=raw_profile["governance_warn_severity"],
            ),
            governance_critical_for=_parse_duration(
                profile_name=profile_name,
                field_name="governance_critical_for",
                raw_value=raw_profile["governance_critical_for"],
            ),
            governance_critical_severity=_parse_severity(
                profile_name=profile_name,
                field_name="governance_critical_severity",
                raw_value=raw_profile["governance_critical_severity"],
            ),
            governance_normalization_for=_parse_duration(
                profile_name=profile_name,
                field_name="governance_normalization_for",
                raw_value=raw_profile["governance_normalization_for"],
            ),
            governance_normalization_severity=_parse_severity(
                profile_name=profile_name,
                field_name="governance_normalization_severity",
                raw_value=raw_profile["governance_normalization_severity"],
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
        alert_name="RefactorThresholdGovernanceWarn",
        field_name="for",
        value=profile.governance_warn_for,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorThresholdGovernanceWarn",
        field_name="severity",
        value=profile.governance_warn_severity,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorThresholdGovernanceCritical",
        field_name="for",
        value=profile.governance_critical_for,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorThresholdGovernanceCritical",
        field_name="severity",
        value=profile.governance_critical_severity,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorThresholdGovernanceNormalizationApplied",
        field_name="for",
        value=profile.governance_normalization_for,
    )
    updated = _replace_alert_field(
        content=updated,
        alert_name="RefactorThresholdGovernanceNormalizationApplied",
        field_name="severity",
        value=profile.governance_normalization_severity,
    )
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


def _build_unified_diff(original: str, rendered: str, relative_path: str) -> str:
    diff_lines = difflib.unified_diff(
        original.splitlines(),
        rendered.splitlines(),
        fromfile=f"a/{relative_path}",
        tofile=f"b/{relative_path}",
        lineterm="",
    )
    return "\n".join(diff_lines)


def _extract_alert_block(content: str, alert_name: str) -> str:
    pattern = re.compile(rf"(?ms)^\s*-\s*alert:\s*{re.escape(alert_name)}\s*$.*?(?=^\s*-\s*alert:\s|\Z)")
    match = pattern.search(content)
    if match is None:
        return ""
    return match.group(0)


def _diff_module_alert_counts(original: str, rendered: str) -> dict[str, int]:
    module_counts = {module_name: 0 for module_name in ALERTS_BY_MODULE}
    for module_name, alert_names in ALERTS_BY_MODULE.items():
        for alert_name in alert_names:
            if _extract_alert_block(content=original, alert_name=alert_name) != _extract_alert_block(
                content=rendered, alert_name=alert_name
            ):
                module_counts[module_name] += 1
    return module_counts


def _diff_line_stats(original: str, rendered: str) -> tuple[int, int]:
    added = 0
    removed = 0
    for line in difflib.unified_diff(original.splitlines(), rendered.splitlines(), lineterm=""):
        if line.startswith("+++ ") or line.startswith("--- ") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def _build_summary_payload(change_summaries: list[tuple[str, int, int, dict[str, int]]]) -> dict:
    total_added = sum(entry[1] for entry in change_summaries)
    total_removed = sum(entry[2] for entry in change_summaries)
    module_totals = {module_name: 0 for module_name in ALERTS_BY_MODULE}
    for _, _, _, file_module_counts in change_summaries:
        for module_name in ALERTS_BY_MODULE:
            module_totals[module_name] += file_module_counts.get(module_name, 0)
    return {
        "changed_files_count": len(change_summaries),
        "total_added_lines": total_added,
        "total_removed_lines": total_removed,
        "files": [
            {
                "path": relative_path,
                "added_lines": added,
                "removed_lines": removed,
                "modules": {
                    module_name: {"changed_alerts_count": file_module_counts.get(module_name, 0)}
                    for module_name in ALERTS_BY_MODULE
                },
            }
            for relative_path, added, removed, file_module_counts in change_summaries
        ],
        "modules": {
            module_name: {"changed_alerts_count": module_totals[module_name]} for module_name in ALERTS_BY_MODULE
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync strict gate alert thresholds into Prometheus rule profiles.")
    parser.add_argument("--check", action="store_true", help="Check mode: fail if any file is out of sync.")
    parser.add_argument("--dry-run", action="store_true", help="Print unified diff without writing files.")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="With --dry-run, print compact change summary instead of unified diff content.",
    )
    parser.add_argument(
        "--summary-format",
        choices=("text", "json"),
        default="text",
        help="Summary output format. Non-text format requires --summary-only.",
    )
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Path to threshold config JSON file.")
    parser.add_argument(
        "--profile",
        action="append",
        choices=sorted(RULE_FILE_BY_PROFILE.keys()),
        help="Only sync/check selected profile(s). Repeatable.",
    )
    args = parser.parse_args()

    if args.summary_only and not args.dry_run:
        raise ValueError("--summary-only requires --dry-run")
    if args.summary_format != "text" and not args.summary_only:
        raise ValueError("--summary-format requires --summary-only")

    profiles = _load_profiles(args.config)
    selected_profiles = list(args.profile or RULE_FILE_BY_PROFILE.keys())

    changed_files: list[Path] = []
    diff_outputs: list[str] = []
    change_summaries: list[tuple[str, int, int, dict[str, int]]] = []
    for profile_name in selected_profiles:
        rule_file = RULE_FILE_BY_PROFILE[profile_name]
        if not rule_file.exists():
            raise FileNotFoundError(f"Rule file not found: {rule_file}")

        original = rule_file.read_text(encoding="utf-8")
        rendered = _render_profile(content=original, profile=profiles[profile_name])
        if rendered != original:
            changed_files.append(rule_file)
            relative_path = str(rule_file.relative_to(BACKEND_ROOT))
            added, removed = _diff_line_stats(original=original, rendered=rendered)
            module_counts = _diff_module_alert_counts(original=original, rendered=rendered)
            change_summaries.append((relative_path, added, removed, module_counts))
            if args.dry_run:
                if not args.summary_only:
                    diff_outputs.append(
                        _build_unified_diff(original=original, rendered=rendered, relative_path=relative_path)
                    )
            if not args.check and not args.dry_run:
                rule_file.write_text(rendered, encoding="utf-8")

    summary_payload: dict | None = None
    if args.dry_run and args.summary_only:
        summary_payload = _build_summary_payload(change_summaries=change_summaries)
        if args.summary_format == "json":
            print(json.dumps(summary_payload, ensure_ascii=False))
        elif changed_files:
            print(
                f"[sync-strict-gate-alert-thresholds] summary: {summary_payload['changed_files_count']} file(s) changed, "
                f"+{summary_payload['total_added_lines']}/-{summary_payload['total_removed_lines']} line(s)."
            )
            for file_summary in summary_payload["files"]:
                print(
                    f"[sync-strict-gate-alert-thresholds] {file_summary['path']}: "
                    f"+{file_summary['added_lines']}/-{file_summary['removed_lines']}"
                )
            print(
                "[sync-strict-gate-alert-thresholds] modules: "
                + ", ".join(
                    f"{module_name}={summary_payload['modules'][module_name]['changed_alerts_count']}"
                    for module_name in ALERTS_BY_MODULE
                )
            )

    for diff_output in diff_outputs:
        print(diff_output)

    if changed_files and args.check:
        if not (args.dry_run and args.summary_only and args.summary_format == "json"):
            for file_path in changed_files:
                rel = file_path.relative_to(BACKEND_ROOT)
                print(f"[sync-strict-gate-alert-thresholds] out of sync: {rel}")
            print("[sync-strict-gate-alert-thresholds] run script without --check to update files.")
        return 1

    if args.dry_run and args.summary_only and args.summary_format == "json":
        return 0

    if changed_files and not args.check and not args.dry_run:
        for file_path in changed_files:
            rel = file_path.relative_to(BACKEND_ROOT)
            print(f"[sync-strict-gate-alert-thresholds] updated: {rel}")
    elif changed_files and args.dry_run:
        print("[sync-strict-gate-alert-thresholds] dry-run completed; no files were written.")
    else:
        print("[sync-strict-gate-alert-thresholds] all strict gate threshold rules are in sync.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[sync-strict-gate-alert-thresholds] {exc}", file=sys.stderr)
        sys.exit(1)
