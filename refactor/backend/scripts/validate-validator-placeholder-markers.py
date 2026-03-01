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
DEFAULT_MARKERS_FILE = BACKEND_ROOT / "config" / "validator-placeholder-markers.json"
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "validator-placeholder-markers.schema.json"
MARKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]*$")
VALIDATOR_ERROR_CODES = {
    "CLI_ARGS_INVALID": "placeholder_markers_cli_args_invalid",
    "JSON_PARSE_ERROR": "placeholder_markers_json_parse_error",
    "PAYLOAD_TYPE_INVALID": "placeholder_markers_payload_type_invalid",
    "MARKERS_LIST_MISSING_OR_EMPTY": "placeholder_markers_markers_list_missing_or_empty",
    "MARKER_NOT_STRING": "placeholder_markers_marker_not_string",
    "MARKER_EMPTY": "placeholder_markers_marker_empty",
    "DUPLICATE_MARKER": "placeholder_markers_duplicate_marker",
    "MARKER_FORMAT_INVALID": "placeholder_markers_marker_format_invalid",
    "SCHEMA_INVALID": "placeholder_markers_schema_invalid",
    "SCHEMA_VALIDATION_FAILED": "placeholder_markers_schema_validation_failed",
    "MARKERS_FILE_NOT_FOUND": "placeholder_markers_markers_file_not_found",
    "SCHEMA_FILE_NOT_FOUND": "placeholder_markers_schema_file_not_found",
    "UNEXPECTED_ERROR": "placeholder_markers_unexpected_error",
}


class PlaceholderMarkersValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class _PlaceholderMarkersArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PlaceholderMarkersValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: {message}",
            context={"failure_mode": "argparse_error", "argparse_message": message},
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _PlaceholderMarkersArgumentParser(
        description="Validate placeholder markers config for validator strict descriptions."
    )
    parser.add_argument(
        "--markers-file",
        type=Path,
        default=DEFAULT_MARKERS_FILE,
        help="Path to placeholder markers config file.",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to placeholder markers schema file.",
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
    except PlaceholderMarkersValidationError as exc:
        context = dict(exc.context)
        context.setdefault("argv", list(argv))
        raise PlaceholderMarkersValidationError(code=exc.code, message=str(exc), context=context) from exc
    if unknown_args:
        raise PlaceholderMarkersValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: unrecognized arguments: {' '.join(unknown_args)}",
            context={"failure_mode": "unknown_args", "unknown_args": unknown_args, "argv": list(argv)},
        )
    return args


def _load_json_payload(path: Path, role: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise PlaceholderMarkersValidationError(
            code=VALIDATOR_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": role},
        ) from exc
    if not isinstance(payload, dict):
        raise PlaceholderMarkersValidationError(
            code=VALIDATOR_ERROR_CODES["PAYLOAD_TYPE_INVALID"],
            message=f"{role} payload must be an object",
            context={"path": str(path), "role": role},
        )
    return payload


def _validate_markers(payload: dict) -> list[str]:
    markers = payload.get("markers")
    if not isinstance(markers, list) or not markers:
        raise PlaceholderMarkersValidationError(
            code=VALIDATOR_ERROR_CODES["MARKERS_LIST_MISSING_OR_EMPTY"],
            message="markers payload must include non-empty markers list",
            context={},
        )

    normalized_markers: list[str] = []
    seen: set[str] = set()
    for raw_marker in markers:
        if not isinstance(raw_marker, str):
            raise PlaceholderMarkersValidationError(
                code=VALIDATOR_ERROR_CODES["MARKER_NOT_STRING"],
                message=f"marker must be a string: {raw_marker}",
                context={"marker": raw_marker},
            )
        marker = raw_marker.strip().upper()
        if not marker:
            raise PlaceholderMarkersValidationError(
                code=VALIDATOR_ERROR_CODES["MARKER_EMPTY"],
                message="marker cannot be empty",
                context={},
            )
        if marker in seen:
            raise PlaceholderMarkersValidationError(
                code=VALIDATOR_ERROR_CODES["DUPLICATE_MARKER"],
                message=f"duplicate marker detected: {marker}",
                context={"marker": marker},
            )
        if MARKER_PATTERN.match(marker) is None:
            raise PlaceholderMarkersValidationError(
                code=VALIDATOR_ERROR_CODES["MARKER_FORMAT_INVALID"],
                message=f"invalid marker format: {marker}",
                context={"marker": marker},
            )
        seen.add(marker)
        normalized_markers.append(marker)
    return normalized_markers


def _validate_against_schema(payload: dict, schema: dict, schema_file: Path) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise PlaceholderMarkersValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_INVALID"],
            message=f"invalid json schema: {schema_file}",
            context={"schema_file": str(schema_file)},
        ) from exc
    try:
        Draft202012Validator(schema).validate(payload)
    except ValidationError as exc:
        raise PlaceholderMarkersValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_VALIDATION_FAILED"],
            message="schema validation failed for marker config",
            context={"validation_path": list(exc.path)},
        ) from exc


def main() -> int:
    argv = sys.argv[1:]
    json_errors_requested = "--json-errors" in argv
    json_output_requested = "--json-output" in argv

    try:
        args = _parse_args(argv=argv)
        json_errors_requested = bool(args.json_errors)
        json_output_requested = bool(args.json_output)
        if not args.markers_file.exists():
            raise PlaceholderMarkersValidationError(
                code=VALIDATOR_ERROR_CODES["MARKERS_FILE_NOT_FOUND"],
                message=f"markers file not found: {args.markers_file}",
                context={"path": str(args.markers_file)},
            )
        if not args.schema_file.exists():
            raise PlaceholderMarkersValidationError(
                code=VALIDATOR_ERROR_CODES["SCHEMA_FILE_NOT_FOUND"],
                message=f"schema file not found: {args.schema_file}",
                context={"path": str(args.schema_file)},
            )
        payload = _load_json_payload(path=args.markers_file, role="markers")
        schema = _load_json_payload(path=args.schema_file, role="schema")
        _validate_against_schema(payload=payload, schema=schema, schema_file=args.schema_file)
        normalized_markers = _validate_markers(payload=payload)
        if json_output_requested:
            success_payload = {
                "validator": "validate-validator-placeholder-markers",
                "status": "ok",
                "markers_file": str(args.markers_file),
                "schema_file": str(args.schema_file),
                "markers_count": len(normalized_markers),
            }
            print(json.dumps(success_payload, ensure_ascii=False))
        else:
            print(f"[validate-validator-placeholder-markers] markers config is valid: {args.markers_file}")
        return 0
    except Exception as exc:
        if json_errors_requested:
            if isinstance(exc, PlaceholderMarkersValidationError):
                payload = {
                    "validator": "validate-validator-placeholder-markers",
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": "validate-validator-placeholder-markers",
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-validator-placeholder-markers] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
