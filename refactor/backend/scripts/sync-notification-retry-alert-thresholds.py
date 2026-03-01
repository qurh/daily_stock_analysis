#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_FILE = BACKEND_ROOT / "config" / "notification-retry-alert-thresholds.json"
DEFAULT_RULES_DIR = BACKEND_ROOT / "monitoring" / "prometheus" / "rules"
DEFAULT_RUNBOOK_FILE = BACKEND_ROOT.parent / "docs" / "runbooks" / "2026-02-20-notification-retry-alert-runbook.md"

RULE_FILE_BY_PROFILE: dict[str, str] = {
    "dev": "refactor-notification-retry-alerts.dev.yml",
    "staging": "refactor-notification-retry-alerts.staging.yml",
    "prod": "refactor-notification-retry-alerts.prod.yml",
}
DEFAULT_RULE_FILE = "refactor-notification-retry-alerts.yml"

RULE_ORDER: tuple[str, ...] = (
    "retry_success_warn",
    "retry_success_critical",
    "auto_retry_failure_warn",
    "auto_retry_failure_critical",
)

PROFILE_ORDER: tuple[str, ...] = ("dev", "staging", "prod")

RULE_SPECS: dict[str, dict[str, str]] = {
    "retry_success_warn": {
        "alert": "RefactorNotificationRetrySuccessRatioWarn",
        "sample_metric": "refactor_notification_retry_attempts_total",
        "metric": "refactor_notification_retry_success_ratio",
        "operator": "<",
        "summary": "Notification retry success ratio is warning",
        "description": (
            "Manual notification retry success ratio stayed below {threshold} "
            "with at least {min_samples} attempts for {duration}."
        ),
    },
    "retry_success_critical": {
        "alert": "RefactorNotificationRetrySuccessRatioCritical",
        "sample_metric": "refactor_notification_retry_attempts_total",
        "metric": "refactor_notification_retry_success_ratio",
        "operator": "<",
        "summary": "Notification retry success ratio is critical",
        "description": (
            "Manual notification retry success ratio stayed below {threshold} "
            "with at least {min_samples} attempts for {duration}."
        ),
    },
    "auto_retry_failure_warn": {
        "alert": "RefactorNotificationAutoRetryFinalFailureRatioWarn",
        "sample_metric": "refactor_notification_auto_retry_deliveries_total",
        "metric": "refactor_notification_auto_retry_final_failure_ratio",
        "operator": ">=",
        "summary": "Notification auto-retry final failure ratio is warning",
        "description": (
            "Auto-retried deliveries final failure ratio stayed at or above {threshold} "
            "with at least {min_samples} samples for {duration}."
        ),
    },
    "auto_retry_failure_critical": {
        "alert": "RefactorNotificationAutoRetryFinalFailureRatioCritical",
        "sample_metric": "refactor_notification_auto_retry_deliveries_total",
        "metric": "refactor_notification_auto_retry_final_failure_ratio",
        "operator": ">=",
        "summary": "Notification auto-retry final failure ratio is critical",
        "description": (
            "Auto-retried deliveries final failure ratio stayed at or above {threshold} "
            "with at least {min_samples} samples for {duration}."
        ),
    },
}

RUNBOOK_RULE_TEXT: dict[str, dict[str, str]] = {
    "retry_success_warn": {
        "signal": "retry success ratio warn",
        "sample_label": "attempts",
        "threshold_label": "success ratio",
    },
    "retry_success_critical": {
        "signal": "retry success ratio critical",
        "sample_label": "attempts",
        "threshold_label": "success ratio",
    },
    "auto_retry_failure_warn": {
        "signal": "auto-retry final failure ratio warn",
        "sample_label": "deliveries",
        "threshold_label": "final failure ratio",
    },
    "auto_retry_failure_critical": {
        "signal": "auto-retry final failure ratio critical",
        "sample_label": "deliveries",
        "threshold_label": "final failure ratio",
    },
}

RUNBOOK_THRESHOLD_SECTION_START = "<!-- notification-retry-thresholds:start -->"
RUNBOOK_THRESHOLD_SECTION_END = "<!-- notification-retry-thresholds:end -->"

REQUIRED_RULE_KEYS = ("min_samples", "threshold", "duration", "severity")


def _load_config(config_file: Path) -> dict[str, object]:
    if not config_file.exists():
        raise ValueError(f"config file not found: {config_file}")
    try:
        payload = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"config json parse failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("config payload must be object")
    return payload


def _validate_profile_rule(profile_name: str, rule_key: str, value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"profile={profile_name} rule={rule_key} must be object")
    for key in REQUIRED_RULE_KEYS:
        if key not in value:
            raise ValueError(f"profile={profile_name} rule={rule_key} missing key: {key}")

    min_samples_value = value["min_samples"]
    threshold_value = value["threshold"]
    duration_value = value["duration"]
    severity_value = value["severity"]

    if not isinstance(min_samples_value, int) or min_samples_value <= 0:
        raise ValueError(f"profile={profile_name} rule={rule_key} min_samples must be positive int")
    if not isinstance(duration_value, str) or not duration_value.endswith("m"):
        raise ValueError(f"profile={profile_name} rule={rule_key} duration must be '<number>m'")
    if not isinstance(severity_value, str) or severity_value not in {"info", "warning", "critical"}:
        raise ValueError(f"profile={profile_name} rule={rule_key} severity invalid: {severity_value}")
    threshold_text = str(threshold_value)
    try:
        float(threshold_text)
    except ValueError as exc:
        raise ValueError(f"profile={profile_name} rule={rule_key} threshold must be numeric") from exc

    return {
        "min_samples": str(min_samples_value),
        "threshold": threshold_text,
        "duration": duration_value,
        "severity": severity_value,
    }


def _normalize_config(payload: dict[str, object]) -> dict[str, dict[str, dict[str, str]]]:
    default_profile = payload.get("default_profile")
    profiles = payload.get("profiles")
    if not isinstance(default_profile, str):
        raise ValueError("default_profile must be string")
    if default_profile not in RULE_FILE_BY_PROFILE:
        raise ValueError(f"default_profile must be one of: {', '.join(sorted(RULE_FILE_BY_PROFILE))}")
    if not isinstance(profiles, dict):
        raise ValueError("profiles must be object")

    normalized_profiles: dict[str, dict[str, dict[str, str]]] = {}
    for profile_name in RULE_FILE_BY_PROFILE:
        raw_profile = profiles.get(profile_name)
        if not isinstance(raw_profile, dict):
            raise ValueError(f"profiles.{profile_name} must be object")

        normalized_rules: dict[str, dict[str, str]] = {}
        for rule_key in RULE_ORDER:
            if rule_key not in raw_profile:
                raise ValueError(f"profiles.{profile_name} missing rule: {rule_key}")
            normalized_rules[rule_key] = _validate_profile_rule(
                profile_name=profile_name,
                rule_key=rule_key,
                value=raw_profile[rule_key],
            )
        normalized_profiles[profile_name] = normalized_rules

    normalized_profiles["default"] = normalized_profiles[default_profile]
    return normalized_profiles


def _render_rule_block(rule_key: str, values: dict[str, str]) -> list[str]:
    spec = RULE_SPECS[rule_key]
    expr = (
        f"{spec['sample_metric']} >= {values['min_samples']} and "
        f"{spec['metric']} {spec['operator']} {values['threshold']}"
    )
    description = spec["description"].format(
        threshold=values["threshold"],
        min_samples=values["min_samples"],
        duration=values["duration"],
    )
    return [
        f"      - alert: {spec['alert']}",
        f"        expr: {expr}",
        f"        for: {values['duration']}",
        "        labels:",
        f"          severity: {values['severity']}",
        "          scope: notification",
        "          domain: retry-governance",
        "        annotations:",
        f"          summary: \"{spec['summary']}\"",
        f"          description: \"{description}\"",
    ]


def _render_profile_file(profile_name: str, rules: dict[str, dict[str, str]]) -> str:
    suffix = "" if profile_name == "default" else f"-{profile_name}"
    lines = [
        "groups:",
        f"  - name: refactor-notification-retry-alerts{suffix}",
        "    rules:",
    ]
    for index, rule_key in enumerate(RULE_ORDER):
        if index > 0:
            lines.append("")
        lines.extend(_render_rule_block(rule_key=rule_key, values=rules[rule_key]))
    return "\n".join(lines) + "\n"


def _build_rule_target_content(normalized_profiles: dict[str, dict[str, dict[str, str]]]) -> dict[str, str]:
    return {
        DEFAULT_RULE_FILE: _render_profile_file(profile_name="default", rules=normalized_profiles["default"]),
        RULE_FILE_BY_PROFILE["dev"]: _render_profile_file(profile_name="dev", rules=normalized_profiles["dev"]),
        RULE_FILE_BY_PROFILE["staging"]: _render_profile_file(
            profile_name="staging", rules=normalized_profiles["staging"]
        ),
        RULE_FILE_BY_PROFILE["prod"]: _render_profile_file(profile_name="prod", rules=normalized_profiles["prod"]),
    }


def _render_runbook_prod_baseline_line(rule_key: str, values: dict[str, str]) -> str:
    text = RUNBOOK_RULE_TEXT[rule_key]
    operator = RULE_SPECS[rule_key]["operator"]
    return (
        f"- {text['signal']}: {text['sample_label']} `>= {values['min_samples']}` and "
        f"{text['threshold_label']} `{operator} {values['threshold']}` for `{values['duration']}`"
    )


def _render_runbook_matrix_row(profile: str, rule_key: str, values: dict[str, str]) -> str:
    text = RUNBOOK_RULE_TEXT[rule_key]
    operator = RULE_SPECS[rule_key]["operator"]
    sample_gate = f"{text['sample_label']} >= {values['min_samples']}"
    threshold_text = f"{text['threshold_label']} {operator} {values['threshold']}"
    return (
        f"| {profile} | {text['signal']} | {sample_gate} | {threshold_text} | {values['duration']} |"
    )


def _render_runbook_threshold_section(normalized_profiles: dict[str, dict[str, dict[str, str]]]) -> str:
    lines = [RUNBOOK_THRESHOLD_SECTION_START, "Prod baseline:"]
    for rule_key in RULE_ORDER:
        lines.append(
            _render_runbook_prod_baseline_line(
                rule_key=rule_key,
                values=normalized_profiles["prod"][rule_key],
            )
        )

    lines.extend(
        [
            "",
            "Profile baseline matrix:",
            "",
            "| profile | signal | sample gate | threshold | duration |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    for profile in PROFILE_ORDER:
        for rule_key in RULE_ORDER:
            lines.append(
                _render_runbook_matrix_row(
                    profile=profile,
                    rule_key=rule_key,
                    values=normalized_profiles[profile][rule_key],
                )
            )

    lines.append(RUNBOOK_THRESHOLD_SECTION_END)
    return "\n".join(lines)


def _replace_runbook_threshold_section(runbook_content: str, threshold_section: str) -> str:
    start_index = runbook_content.find(RUNBOOK_THRESHOLD_SECTION_START)
    if start_index < 0:
        raise ValueError(f"runbook marker not found: {RUNBOOK_THRESHOLD_SECTION_START}")

    end_index = runbook_content.find(RUNBOOK_THRESHOLD_SECTION_END)
    if end_index < 0:
        raise ValueError(f"runbook marker not found: {RUNBOOK_THRESHOLD_SECTION_END}")

    end_index = end_index + len(RUNBOOK_THRESHOLD_SECTION_END)
    return runbook_content[:start_index] + threshold_section + runbook_content[end_index:]


def _build_runbook_target_content(
    normalized_profiles: dict[str, dict[str, dict[str, str]]],
    runbook_file: Path,
) -> str:
    if not runbook_file.exists():
        raise ValueError(f"runbook file not found: {runbook_file}")
    runbook_content = runbook_file.read_text(encoding="utf-8")
    threshold_section = _render_runbook_threshold_section(normalized_profiles)
    return _replace_runbook_threshold_section(runbook_content=runbook_content, threshold_section=threshold_section)


def _check_rules_in_sync(target_content: dict[str, str], rules_dir: Path) -> list[str]:
    out_of_sync: list[str] = []
    for filename, expected in target_content.items():
        output_file = rules_dir / filename
        if not output_file.exists():
            out_of_sync.append(f"{filename} (missing)")
            continue
        current = output_file.read_text(encoding="utf-8")
        if current != expected:
            out_of_sync.append(filename)
    return out_of_sync


def _write_rule_files(target_content: dict[str, str], rules_dir: Path) -> None:
    rules_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in target_content.items():
        output_file = rules_dir / filename
        output_file.write_text(content, encoding="utf-8")
        print(f"[sync-notification-retry-alert-thresholds] updated: {output_file}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync notification retry alert rule files and runbook thresholds from a single config."
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        default=DEFAULT_CONFIG_FILE,
        help="Path to notification retry alert threshold config json.",
    )
    parser.add_argument(
        "--rules-dir",
        type=Path,
        default=DEFAULT_RULES_DIR,
        help="Directory containing notification retry alert rule files.",
    )
    parser.add_argument(
        "--runbook-file",
        type=Path,
        default=DEFAULT_RUNBOOK_FILE,
        help="Path to notification retry runbook file.",
    )
    parser.add_argument("--check", action="store_true", help="Fail when generated content differs from files on disk.")
    args = parser.parse_args()

    try:
        config_payload = _load_config(args.config_file)
        normalized_profiles = _normalize_config(config_payload)
        rule_target_content = _build_rule_target_content(normalized_profiles)
        runbook_target_content = _build_runbook_target_content(
            normalized_profiles=normalized_profiles,
            runbook_file=args.runbook_file,
        )

        if args.check:
            out_of_sync = _check_rules_in_sync(target_content=rule_target_content, rules_dir=args.rules_dir)
            current_runbook_content = args.runbook_file.read_text(encoding="utf-8")
            if current_runbook_content != runbook_target_content:
                out_of_sync.append(f"runbook: {args.runbook_file}")

            if out_of_sync:
                for item in out_of_sync:
                    print(f"[sync-notification-retry-alert-thresholds] out of sync: {item}")
                print("[sync-notification-retry-alert-thresholds] run script without --check to update files.")
                return 1

            print(
                "[sync-notification-retry-alert-thresholds] all notification retry alert files and runbook are in sync."
            )
            return 0

        _write_rule_files(target_content=rule_target_content, rules_dir=args.rules_dir)
        args.runbook_file.write_text(runbook_target_content, encoding="utf-8")
        print(f"[sync-notification-retry-alert-thresholds] updated: {args.runbook_file}")
        return 0
    except Exception as exc:
        print(f"[sync-notification-retry-alert-thresholds] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
