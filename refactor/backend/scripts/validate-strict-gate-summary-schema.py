#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from json import JSONDecodeError
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "strict-gate-summary.schema.json"
DEFAULT_EXAMPLE_FILE = BACKEND_ROOT / "config" / "schemas" / "strict-gate-summary.example.json"
DEFAULT_SYNC_SCRIPT_FILE = BACKEND_ROOT / "scripts" / "sync-strict-gate-alert-thresholds.py"
EXPECTED_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
SUMMARY_SCHEMA_VERSION_PATTERN = re.compile(r'^SUMMARY_SCHEMA_VERSION\s*=\s*"([^"]+)"\s*$')
VALIDATOR_ERROR_CODES = {
    "CLI_ARGS_INVALID": "summary_schema_cli_args_invalid",
    "JSON_PARSE_ERROR": "summary_schema_json_parse_error",
    "EXAMPLE_PAYLOAD_SCHEMA_VALIDATION_FAILED": "summary_schema_example_payload_schema_validation_failed",
    "EXAMPLE_SCHEMA_VERSION_MISMATCH": "summary_schema_example_schema_version_mismatch",
    "FILES_TYPE_INVALID": "summary_schema_files_type_invalid",
    "MODULES_TYPE_INVALID": "summary_schema_modules_type_invalid",
    "CHANGED_FILES_COUNT_MISMATCH": "summary_schema_changed_files_count_mismatch",
    "TOTAL_ADDED_LINES_MISMATCH": "summary_schema_total_added_lines_mismatch",
    "TOTAL_REMOVED_LINES_MISMATCH": "summary_schema_total_removed_lines_mismatch",
    "MODULE_TOTAL_MISMATCH_STRICT": "summary_schema_module_total_mismatch_strict",
    "MODULE_TOTAL_MISMATCH_GOVERNANCE": "summary_schema_module_total_mismatch_governance",
    "MODULE_TOTAL_MISMATCH_SOFT_AUDIT": "summary_schema_module_total_mismatch_soft_audit",
    "UNEXPECTED_ERROR": "summary_schema_unexpected_error",
}
MODULE_TOTAL_MISMATCH_CODE_BY_NAME = {
    "strict": VALIDATOR_ERROR_CODES["MODULE_TOTAL_MISMATCH_STRICT"],
    "governance": VALIDATOR_ERROR_CODES["MODULE_TOTAL_MISMATCH_GOVERNANCE"],
    "soft_audit": VALIDATOR_ERROR_CODES["MODULE_TOTAL_MISMATCH_SOFT_AUDIT"],
}


class SummarySchemaValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class _SummarySchemaArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: {message}",
            context={"failure_mode": "argparse_error", "argparse_message": message},
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _SummarySchemaArgumentParser(description="Validate strict gate summary JSON schema.")
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to strict gate summary schema JSON file.",
    )
    parser.add_argument(
        "--sync-script-file",
        type=Path,
        default=DEFAULT_SYNC_SCRIPT_FILE,
        help="Path to sync-strict-gate-alert-thresholds.py for SUMMARY_SCHEMA_VERSION check.",
    )
    parser.add_argument(
        "--example-file",
        type=Path,
        default=DEFAULT_EXAMPLE_FILE,
        help="Path to strict gate summary example payload JSON file.",
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
    except SummarySchemaValidationError as exc:
        context = dict(exc.context)
        context.setdefault("argv", list(argv))
        raise SummarySchemaValidationError(code=exc.code, message=str(exc), context=context) from exc
    if unknown_args:
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: unrecognized arguments: {' '.join(unknown_args)}",
            context={"failure_mode": "unknown_args", "unknown_args": unknown_args, "argv": list(argv)},
        )
    return args


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path)},
        ) from exc


def _validate_contract(schema: dict) -> None:
    if schema.get("$schema") != EXPECTED_SCHEMA_DRAFT:
        raise ValueError(f"invalid $schema value, expected: {EXPECTED_SCHEMA_DRAFT}")
    required_fields = {
        "schema_version",
        "changed_files_count",
        "total_added_lines",
        "total_removed_lines",
        "files",
        "modules",
    }
    required = schema.get("required")
    if not isinstance(required, list):
        raise ValueError("schema field 'required' must be a list")
    missing = sorted(required_fields.difference(set(required)))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"schema missing required fields: {missing_text}")


def _extract_sync_summary_schema_version(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SUMMARY_SCHEMA_VERSION_PATTERN.match(line.strip())
        if match is not None:
            return match.group(1)
    raise ValueError(f"missing SUMMARY_SCHEMA_VERSION in sync script: {path}")


def _extract_schema_payload_version(schema: dict) -> str:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("schema field 'properties' must be an object")
    schema_version_field = properties.get("schema_version")
    if not isinstance(schema_version_field, dict):
        raise ValueError("schema field 'properties.schema_version' must be an object")
    schema_version_const = schema_version_field.get("const")
    if not isinstance(schema_version_const, str):
        raise ValueError("schema field 'properties.schema_version.const' must be a string")
    return schema_version_const


def _validate_example_payload(example_payload: dict, schema: dict, expected_version: str) -> None:
    try:
        Draft202012Validator(schema).validate(example_payload)
    except ValidationError as exc:
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["EXAMPLE_PAYLOAD_SCHEMA_VALIDATION_FAILED"],
            message="example payload validation failed",
            context={"validation_path": list(exc.path)},
        ) from exc
    if example_payload.get("schema_version") != expected_version:
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["EXAMPLE_SCHEMA_VERSION_MISMATCH"],
            message=(
                f"example payload schema_version mismatch: "
                f"example={example_payload.get('schema_version')}, expected={expected_version}"
            ),
            context={
                "expected": expected_version,
                "actual": example_payload.get("schema_version"),
            },
        )

    files = example_payload.get("files")
    modules = example_payload.get("modules")
    if not isinstance(files, list):
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["FILES_TYPE_INVALID"],
            message="example payload consistency check failed: files must be a list",
        )
    if not isinstance(modules, dict):
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["MODULES_TYPE_INVALID"],
            message="example payload consistency check failed: modules must be an object",
        )

    changed_files_count = example_payload.get("changed_files_count")
    expected_files_count = len(files)
    if changed_files_count != expected_files_count:
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["CHANGED_FILES_COUNT_MISMATCH"],
            message=(
                f"example payload consistency check failed: "
                f"changed_files_count mismatch (expected={expected_files_count}, actual={changed_files_count})"
            ),
            context={"expected": expected_files_count, "actual": changed_files_count},
        )

    total_added_lines = sum(item.get("added_lines", 0) for item in files if isinstance(item, dict))
    total_removed_lines = sum(item.get("removed_lines", 0) for item in files if isinstance(item, dict))
    summary_total_added = example_payload.get("total_added_lines")
    summary_total_removed = example_payload.get("total_removed_lines")
    if summary_total_added != total_added_lines:
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["TOTAL_ADDED_LINES_MISMATCH"],
            message=(
                f"example payload consistency check failed: "
                f"total_added_lines mismatch (expected={total_added_lines}, actual={summary_total_added})"
            ),
            context={"expected": total_added_lines, "actual": summary_total_added},
        )
    if summary_total_removed != total_removed_lines:
        raise SummarySchemaValidationError(
            code=VALIDATOR_ERROR_CODES["TOTAL_REMOVED_LINES_MISMATCH"],
            message=(
                f"example payload consistency check failed: "
                f"total_removed_lines mismatch (expected={total_removed_lines}, actual={summary_total_removed})"
            ),
            context={"expected": total_removed_lines, "actual": summary_total_removed},
        )

    module_names = ("strict", "governance", "soft_audit")
    for module_name in module_names:
        module_total = modules.get(module_name, {}).get("changed_alerts_count")
        file_total = 0
        for item in files:
            if not isinstance(item, dict):
                continue
            item_modules = item.get("modules")
            if isinstance(item_modules, dict):
                file_total += item_modules.get(module_name, {}).get("changed_alerts_count", 0)
        if module_total != file_total:
            raise SummarySchemaValidationError(
                code=MODULE_TOTAL_MISMATCH_CODE_BY_NAME[module_name],
                message=(
                    f"example payload consistency check failed: "
                    f"module total mismatch for {module_name} (expected={file_total}, actual={module_total})"
                ),
                context={"module": module_name, "expected": file_total, "actual": module_total},
            )


def main() -> int:
    argv = sys.argv[1:]
    json_errors_requested = "--json-errors" in argv
    json_output_requested = "--json-output" in argv
    try:
        args = _parse_args(argv=argv)
        json_errors_requested = bool(args.json_errors)
        json_output_requested = bool(args.json_output)
        if not args.schema_file.exists():
            raise FileNotFoundError(f"schema file not found: {args.schema_file}")
        if not args.sync_script_file.exists():
            raise FileNotFoundError(f"sync script file not found: {args.sync_script_file}")
        if not args.example_file.exists():
            raise FileNotFoundError(f"example payload file not found: {args.example_file}")

        schema = _load_json(path=args.schema_file)
        example_payload = _load_json(path=args.example_file)
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise ValueError(f"invalid json schema: {args.schema_file}") from exc

        _validate_contract(schema=schema)
        schema_version = _extract_schema_payload_version(schema=schema)
        sync_summary_schema_version = _extract_sync_summary_schema_version(path=args.sync_script_file)
        if schema_version != sync_summary_schema_version:
            raise ValueError(
                f"schema_version mismatch: schema={schema_version}, sync_script={sync_summary_schema_version}"
            )
        _validate_example_payload(example_payload=example_payload, schema=schema, expected_version=schema_version)
        if json_output_requested:
            payload = {
                "validator": "validate-strict-gate-summary-schema",
                "status": "ok",
                "schema_file": str(args.schema_file),
                "sync_script_file": str(args.sync_script_file),
                "example_file": str(args.example_file),
                "schema_version": schema_version,
            }
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[validate-strict-gate-summary-schema] schema is valid: {args.schema_file}")
            print(f"[validate-strict-gate-summary-schema] example payload is valid: {args.example_file}")
        return 0
    except Exception as exc:
        if json_errors_requested:
            if isinstance(exc, SummarySchemaValidationError):
                payload = {
                    "validator": "validate-strict-gate-summary-schema",
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": "validate-strict-gate-summary-schema",
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-strict-gate-summary-schema] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
