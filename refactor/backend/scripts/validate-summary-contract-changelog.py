#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "strict-gate-summary.schema.json"
DEFAULT_CHANGELOG_FILE = BACKEND_ROOT.parent / "docs" / "CHANGELOG.md"
DEFAULT_APP_FILE = BACKEND_ROOT / "src" / "app" / "main.py"

APP_VERSION_PATTERN = re.compile(r'version="([^"]+)"')
CHANGELOG_ENTRY_PATTERN = re.compile(r"^## \[([^\]]+)\].*$", re.MULTILINE)
VALIDATOR_ERROR_CODES = {
    "CLI_ARGS_INVALID": "summary_contract_cli_args_invalid",
    "APP_VERSION_NOT_FOUND": "summary_contract_app_version_not_found",
    "SCHEMA_PROPERTIES_MISSING": "summary_contract_schema_properties_missing",
    "SCHEMA_VERSION_FIELD_MISSING": "summary_contract_schema_version_field_missing",
    "SCHEMA_VERSION_CONST_MISSING": "summary_contract_schema_version_const_missing",
    "LATEST_CHANGELOG_ENTRY_NOT_FOUND": "summary_contract_latest_changelog_entry_not_found",
    "MISSING_SUMMARY_SCHEMA_VERSION_NOTE": "summary_contract_missing_summary_schema_version_note",
    "REQUIRED_FILE_NOT_FOUND": "summary_contract_required_file_not_found",
    "CHANGELOG_APP_VERSION_MISMATCH": "summary_contract_changelog_app_version_mismatch",
    "UNEXPECTED_ERROR": "summary_contract_unexpected_error",
}


class SummaryContractValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class _SummaryContractArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise SummaryContractValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: {message}",
            context={"failure_mode": "argparse_error", "argparse_message": message},
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _SummaryContractArgumentParser(description="Validate strict gate summary contract changelog linkage.")
    parser.add_argument("--schema-file", type=Path, default=DEFAULT_SCHEMA_FILE, help="Path to summary schema file.")
    parser.add_argument("--changelog-file", type=Path, default=DEFAULT_CHANGELOG_FILE, help="Path to changelog file.")
    parser.add_argument("--app-file", type=Path, default=DEFAULT_APP_FILE, help="Path to app file with version field.")
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
    except SummaryContractValidationError as exc:
        context = dict(exc.context)
        context.setdefault("argv", list(argv))
        raise SummaryContractValidationError(code=exc.code, message=str(exc), context=context) from exc
    if unknown_args:
        raise SummaryContractValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: unrecognized arguments: {' '.join(unknown_args)}",
            context={"failure_mode": "unknown_args", "unknown_args": unknown_args, "argv": list(argv)},
        )
    return args


def _extract_app_version(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    match = APP_VERSION_PATTERN.search(content)
    if match is None:
        raise SummaryContractValidationError(
            code=VALIDATOR_ERROR_CODES["APP_VERSION_NOT_FOUND"],
            message=f"unable to locate app version in file: {path}",
            context={"path": str(path)},
        )
    return match.group(1)


def _extract_schema_version(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        raise SummaryContractValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_PROPERTIES_MISSING"],
            message="schema missing 'properties' object",
            context={"path": str(path)},
        )
    schema_version = properties.get("schema_version")
    if not isinstance(schema_version, dict):
        raise SummaryContractValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_VERSION_FIELD_MISSING"],
            message="schema missing 'properties.schema_version' object",
            context={"path": str(path)},
        )
    schema_version_const = schema_version.get("const")
    if not isinstance(schema_version_const, str):
        raise SummaryContractValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_VERSION_CONST_MISSING"],
            message="schema missing 'properties.schema_version.const' string",
            context={"path": str(path)},
        )
    return schema_version_const


def _extract_latest_changelog_entry(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8")
    first_match = CHANGELOG_ENTRY_PATTERN.search(content)
    if first_match is None:
        raise SummaryContractValidationError(
            code=VALIDATOR_ERROR_CODES["LATEST_CHANGELOG_ENTRY_NOT_FOUND"],
            message="unable to locate latest changelog entry",
            context={"path": str(path)},
        )
    latest_version = first_match.group(1)
    next_match = CHANGELOG_ENTRY_PATTERN.search(content, first_match.end())
    section_end = next_match.start() if next_match is not None else len(content)
    latest_section = content[first_match.end() : section_end]
    return latest_version, latest_section


def _validate_summary_schema_note(latest_section: str, schema_version: str) -> None:
    note_pattern = re.compile(
        rf"Summary schema version:\s*[`\"']?{re.escape(schema_version)}[`\"']?",
        re.IGNORECASE,
    )
    if note_pattern.search(latest_section) is None:
        raise SummaryContractValidationError(
            code=VALIDATOR_ERROR_CODES["MISSING_SUMMARY_SCHEMA_VERSION_NOTE"],
            message="missing summary schema version note in latest changelog entry",
            context={"expected_schema_version": schema_version},
        )


def main() -> int:
    argv = sys.argv[1:]
    json_errors_requested = "--json-errors" in argv
    json_output_requested = "--json-output" in argv

    try:
        args = _parse_args(argv=argv)
        json_errors_requested = bool(args.json_errors)
        json_output_requested = bool(args.json_output)
        for path in (args.schema_file, args.changelog_file, args.app_file):
            if not path.exists():
                raise SummaryContractValidationError(
                    code=VALIDATOR_ERROR_CODES["REQUIRED_FILE_NOT_FOUND"],
                    message=f"required file not found: {path}",
                    context={"path": str(path)},
                )

        app_version = _extract_app_version(path=args.app_file)
        schema_version = _extract_schema_version(path=args.schema_file)
        changelog_version, latest_section = _extract_latest_changelog_entry(path=args.changelog_file)

        if changelog_version != app_version:
            raise SummaryContractValidationError(
                code=VALIDATOR_ERROR_CODES["CHANGELOG_APP_VERSION_MISMATCH"],
                message=f"changelog/app version mismatch: changelog={changelog_version}, app={app_version}",
                context={"expected": app_version, "actual": changelog_version},
            )

        _validate_summary_schema_note(latest_section=latest_section, schema_version=schema_version)
        if json_output_requested:
            payload = {
                "validator": "validate-summary-contract-changelog",
                "status": "ok",
                "schema_file": str(args.schema_file),
                "changelog_file": str(args.changelog_file),
                "app_file": str(args.app_file),
                "app_version": app_version,
                "schema_version": schema_version,
                "changelog_version": changelog_version,
            }
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[validate-summary-contract-changelog] contract changelog is valid: {args.changelog_file}")
        return 0
    except Exception as exc:
        if json_errors_requested:
            if isinstance(exc, SummaryContractValidationError):
                payload = {
                    "validator": "validate-summary-contract-changelog",
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": "validate-summary-contract-changelog",
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-summary-contract-changelog] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
