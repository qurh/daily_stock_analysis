#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULE_FILE = BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-notification-retry-alerts.yml"
DEFAULT_DEV_RULE_FILE = (
    BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-notification-retry-alerts.dev.yml"
)
DEFAULT_STAGING_RULE_FILE = (
    BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-notification-retry-alerts.staging.yml"
)
DEFAULT_PROD_RULE_FILE = (
    BACKEND_ROOT / "monitoring" / "prometheus" / "rules" / "refactor-notification-retry-alerts.prod.yml"
)
DEFAULT_RUNBOOK_FILE = BACKEND_ROOT.parent / "docs" / "runbooks" / "2026-02-20-notification-retry-alert-runbook.md"
VALIDATOR_NAME = "validate-notification-retry-runbook"
VALIDATOR_ERROR_CODES = {
    "FILE_NOT_FOUND": "notification_retry_runbook_file_not_found",
    "BASELINE_PARSE_FAILED": "notification_retry_runbook_baseline_parse_failed",
    "BASELINE_MISMATCH": "notification_retry_runbook_baseline_mismatch",
    "CLI_ARGS_INVALID": "notification_retry_runbook_cli_args_invalid",
    "UNEXPECTED_ERROR": "notification_retry_runbook_unexpected_error",
}

RULE_PATTERNS: dict[str, re.Pattern[str]] = {
    "retry_success_warn": re.compile(
        r"alert:\s*RefactorNotificationRetrySuccessRatioWarn[\s\S]*?"
        r"expr:\s*refactor_notification_retry_attempts_total\s*>=\s*(\d+)\s*"
        r"and\s*refactor_notification_retry_success_ratio\s*<\s*([0-9.]+)[\s\S]*?"
        r"for:\s*([0-9]+m)",
        re.MULTILINE,
    ),
    "retry_success_critical": re.compile(
        r"alert:\s*RefactorNotificationRetrySuccessRatioCritical[\s\S]*?"
        r"expr:\s*refactor_notification_retry_attempts_total\s*>=\s*(\d+)\s*"
        r"and\s*refactor_notification_retry_success_ratio\s*<\s*([0-9.]+)[\s\S]*?"
        r"for:\s*([0-9]+m)",
        re.MULTILINE,
    ),
    "auto_retry_failure_warn": re.compile(
        r"alert:\s*RefactorNotificationAutoRetryFinalFailureRatioWarn[\s\S]*?"
        r"expr:\s*refactor_notification_auto_retry_deliveries_total\s*>=\s*(\d+)\s*"
        r"and\s*refactor_notification_auto_retry_final_failure_ratio\s*>=\s*([0-9.]+)[\s\S]*?"
        r"for:\s*([0-9]+m)",
        re.MULTILINE,
    ),
    "auto_retry_failure_critical": re.compile(
        r"alert:\s*RefactorNotificationAutoRetryFinalFailureRatioCritical[\s\S]*?"
        r"expr:\s*refactor_notification_auto_retry_deliveries_total\s*>=\s*(\d+)\s*"
        r"and\s*refactor_notification_auto_retry_final_failure_ratio\s*>=\s*([0-9.]+)[\s\S]*?"
        r"for:\s*([0-9]+m)",
        re.MULTILINE,
    ),
}

RUNBOOK_PROD_BASELINE_PATTERNS: dict[str, re.Pattern[str]] = {
    "retry_success_warn": re.compile(
        r"retry success ratio warn:\s*attempts\s*`>=\s*(\d+)`\s*"
        r"and success ratio\s*`<\s*([0-9.]+)`\s*for\s*`([0-9]+m)`",
        re.IGNORECASE,
    ),
    "retry_success_critical": re.compile(
        r"retry success ratio critical:\s*attempts\s*`>=\s*(\d+)`\s*"
        r"and success ratio\s*`<\s*([0-9.]+)`\s*for\s*`([0-9]+m)`",
        re.IGNORECASE,
    ),
    "auto_retry_failure_warn": re.compile(
        r"auto-retry final failure ratio warn:\s*deliveries\s*`>=\s*(\d+)`\s*"
        r"and final failure ratio\s*`>=\s*([0-9.]+)`\s*for\s*`([0-9]+m)`",
        re.IGNORECASE,
    ),
    "auto_retry_failure_critical": re.compile(
        r"auto-retry final failure ratio critical:\s*deliveries\s*`>=\s*(\d+)`\s*"
        r"and final failure ratio\s*`>=\s*([0-9.]+)`\s*for\s*`([0-9]+m)`",
        re.IGNORECASE,
    ),
}

RUNBOOK_MATRIX_PATTERNS: dict[str, str] = {
    "retry_success_warn": (
        r"\|\s*{profile}\s*\|\s*retry success ratio warn\s*\|\s*attempts\s*>=\s*(\d+)\s*\|\s*"
        r"success ratio\s*<\s*([0-9.]+)\s*\|\s*([0-9]+m)\s*\|"
    ),
    "retry_success_critical": (
        r"\|\s*{profile}\s*\|\s*retry success ratio critical\s*\|\s*attempts\s*>=\s*(\d+)\s*\|\s*"
        r"success ratio\s*<\s*([0-9.]+)\s*\|\s*([0-9]+m)\s*\|"
    ),
    "auto_retry_failure_warn": (
        r"\|\s*{profile}\s*\|\s*auto-retry final failure ratio warn\s*\|\s*deliveries\s*>=\s*(\d+)\s*\|\s*"
        r"final failure ratio\s*>=\s*([0-9.]+)\s*\|\s*([0-9]+m)\s*\|"
    ),
    "auto_retry_failure_critical": (
        r"\|\s*{profile}\s*\|\s*auto-retry final failure ratio critical\s*\|\s*deliveries\s*>=\s*(\d+)\s*\|\s*"
        r"final failure ratio\s*>=\s*([0-9.]+)\s*\|\s*([0-9]+m)\s*\|"
    ),
}

MATRIX_PROFILES: tuple[str, ...] = ("dev", "staging", "prod")


class NotificationRetryRunbookValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class _RunbookArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise NotificationRetryRunbookValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: {message}",
            context={"failure_mode": "argparse_error", "argparse_message": message},
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _RunbookArgumentParser(
        description="Validate notification retry runbook baseline matches prometheus alert rules."
    )
    parser.add_argument(
        "--rule-file",
        "--default-rule-file",
        dest="default_rule_file",
        type=Path,
        default=DEFAULT_RULE_FILE,
        help="Path to notification default alert rule file.",
    )
    parser.add_argument(
        "--dev-rule-file",
        type=Path,
        default=DEFAULT_DEV_RULE_FILE,
        help="Path to notification dev alert rule file.",
    )
    parser.add_argument(
        "--staging-rule-file",
        type=Path,
        default=DEFAULT_STAGING_RULE_FILE,
        help="Path to notification staging alert rule file.",
    )
    parser.add_argument(
        "--prod-rule-file",
        type=Path,
        default=DEFAULT_PROD_RULE_FILE,
        help="Path to notification prod alert rule file.",
    )
    parser.add_argument(
        "--runbook-file",
        type=Path,
        default=DEFAULT_RUNBOOK_FILE,
        help="Path to notification runbook file.",
    )
    parser.add_argument(
        "--json-errors",
        action="store_true",
        help="Emit structured JSON errors to stderr.",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Emit structured JSON success payload to stdout.",
    )
    return parser


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = _build_parser()
    try:
        args, unknown_args = parser.parse_known_args(argv)
    except NotificationRetryRunbookValidationError as exc:
        context = dict(exc.context)
        context.setdefault("argv", list(argv))
        raise NotificationRetryRunbookValidationError(code=exc.code, message=str(exc), context=context) from exc
    if unknown_args:
        raise NotificationRetryRunbookValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: unrecognized arguments: {' '.join(unknown_args)}",
            context={"failure_mode": "unknown_args", "unknown_args": unknown_args, "argv": list(argv)},
        )
    return args


def _extract_baseline(
    content: str, patterns: dict[str, re.Pattern[str]], source: str
) -> dict[str, tuple[str, str, str]]:
    baseline: dict[str, tuple[str, str, str]] = {}
    for key, pattern in patterns.items():
        match = pattern.search(content)
        if match is None:
            raise NotificationRetryRunbookValidationError(
                code=VALIDATOR_ERROR_CODES["BASELINE_PARSE_FAILED"],
                message=f"{source} parse failed: missing baseline for {key}",
                context={"source": source, "key": key},
            )
        baseline[key] = (match.group(1), match.group(2), match.group(3))
    return baseline


def _extract_runbook_matrix_baseline(content: str, profile: str) -> dict[str, tuple[str, str, str]]:
    baseline: dict[str, tuple[str, str, str]] = {}
    escaped_profile = re.escape(profile)
    for key, pattern_template in RUNBOOK_MATRIX_PATTERNS.items():
        pattern = re.compile(pattern_template.format(profile=escaped_profile), re.IGNORECASE)
        match = pattern.search(content)
        if match is None:
            raise NotificationRetryRunbookValidationError(
                code=VALIDATOR_ERROR_CODES["BASELINE_PARSE_FAILED"],
                message=f"runbook parse failed: missing matrix baseline for profile={profile}, key={key}",
                context={"source": "runbook-matrix", "profile": profile, "key": key},
            )
        baseline[key] = (match.group(1), match.group(2), match.group(3))
    return baseline


def _assert_file_exists(path: Path) -> None:
    if not path.exists():
        raise NotificationRetryRunbookValidationError(
            code=VALIDATOR_ERROR_CODES["FILE_NOT_FOUND"],
            message=f"required file not found: {path}",
            context={"path": str(path)},
        )


def _compare_baseline(
    *,
    left_name: str,
    left_baseline: dict[str, tuple[str, str, str]],
    right_name: str,
    right_baseline: dict[str, tuple[str, str, str]],
) -> list[str]:
    mismatches: list[str] = []
    for key in RULE_PATTERNS:
        if left_baseline[key] != right_baseline[key]:
            mismatches.append(
                f"{key} mismatch: {left_name}={left_baseline[key]} {right_name}={right_baseline[key]}"
            )
    return mismatches


def _validate_consistency(
    *,
    default_rule_file: Path,
    dev_rule_file: Path,
    staging_rule_file: Path,
    prod_rule_file: Path,
    runbook_file: Path,
) -> None:
    _assert_file_exists(default_rule_file)
    _assert_file_exists(dev_rule_file)
    _assert_file_exists(staging_rule_file)
    _assert_file_exists(prod_rule_file)
    _assert_file_exists(runbook_file)

    runbook_content = runbook_file.read_text(encoding="utf-8")
    rule_files: dict[str, Path] = {
        "dev": dev_rule_file,
        "staging": staging_rule_file,
        "prod": prod_rule_file,
    }

    mismatches: list[str] = []
    rule_baselines: dict[str, dict[str, tuple[str, str, str]]] = {}

    for profile in MATRIX_PROFILES:
        rule_content = rule_files[profile].read_text(encoding="utf-8")
        rule_baseline = _extract_baseline(rule_content, RULE_PATTERNS, f"rule:{profile}")
        runbook_baseline = _extract_runbook_matrix_baseline(runbook_content, profile)
        mismatches.extend(
            _compare_baseline(
                left_name=f"rule:{profile}",
                left_baseline=rule_baseline,
                right_name=f"runbook-matrix:{profile}",
                right_baseline=runbook_baseline,
            )
        )
        rule_baselines[profile] = rule_baseline

    runbook_prod_baseline = _extract_baseline(
        runbook_content,
        RUNBOOK_PROD_BASELINE_PATTERNS,
        "runbook-prod-baseline",
    )
    mismatches.extend(
        _compare_baseline(
            left_name="rule:prod",
            left_baseline=rule_baselines["prod"],
            right_name="runbook-prod-baseline",
            right_baseline=runbook_prod_baseline,
        )
    )

    default_rule_baseline = _extract_baseline(
        default_rule_file.read_text(encoding="utf-8"),
        RULE_PATTERNS,
        "rule:default",
    )
    mismatches.extend(
        _compare_baseline(
            left_name="rule:default",
            left_baseline=default_rule_baseline,
            right_name="rule:prod",
            right_baseline=rule_baselines["prod"],
        )
    )

    if mismatches:
        raise NotificationRetryRunbookValidationError(
            code=VALIDATOR_ERROR_CODES["BASELINE_MISMATCH"],
            message=f"runbook/rule baseline mismatch: {'; '.join(mismatches)}",
            context={"mismatch_count": len(mismatches), "first_mismatch": mismatches[0]},
        )


def main() -> int:
    argv = sys.argv[1:]
    json_errors_requested = "--json-errors" in argv
    json_output_requested = "--json-output" in argv

    try:
        args = _parse_args(argv=argv)
        json_errors_requested = bool(args.json_errors)
        json_output_requested = bool(args.json_output)
        _validate_consistency(
            default_rule_file=args.default_rule_file,
            dev_rule_file=args.dev_rule_file,
            staging_rule_file=args.staging_rule_file,
            prod_rule_file=args.prod_rule_file,
            runbook_file=args.runbook_file,
        )
        if json_output_requested:
            payload = {
                "validator": VALIDATOR_NAME,
                "status": "ok",
                "default_rule_file": str(args.default_rule_file),
                "dev_rule_file": str(args.dev_rule_file),
                "staging_rule_file": str(args.staging_rule_file),
                "prod_rule_file": str(args.prod_rule_file),
                "runbook_file": str(args.runbook_file),
                "profile_count": len(MATRIX_PROFILES),
            }
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(
                "[validate-notification-retry-runbook] runbook is consistent with alert rules "
                f"(default/dev/staging/prod): {args.runbook_file}"
            )
        return 0
    except Exception as exc:
        if json_errors_requested:
            if isinstance(exc, NotificationRetryRunbookValidationError):
                payload = {
                    "validator": VALIDATOR_NAME,
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": VALIDATOR_NAME,
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-notification-retry-runbook] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
