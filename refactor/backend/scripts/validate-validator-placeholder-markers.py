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


class PlaceholderMarkersValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


def _load_json_payload(path: Path, role: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise PlaceholderMarkersValidationError(
            code="placeholder_markers_json_parse_error",
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": role},
        ) from exc
    if not isinstance(payload, dict):
        raise PlaceholderMarkersValidationError(
            code="placeholder_markers_payload_type_invalid",
            message=f"{role} payload must be an object",
            context={"path": str(path), "role": role},
        )
    return payload


def _validate_markers(payload: dict) -> list[str]:
    markers = payload.get("markers")
    if not isinstance(markers, list) or not markers:
        raise PlaceholderMarkersValidationError(
            code="placeholder_markers_markers_list_missing_or_empty",
            message="markers payload must include non-empty markers list",
            context={},
        )

    normalized_markers: list[str] = []
    seen: set[str] = set()
    for raw_marker in markers:
        if not isinstance(raw_marker, str):
            raise PlaceholderMarkersValidationError(
                code="placeholder_markers_marker_not_string",
                message=f"marker must be a string: {raw_marker}",
                context={"marker": raw_marker},
            )
        marker = raw_marker.strip().upper()
        if not marker:
            raise PlaceholderMarkersValidationError(
                code="placeholder_markers_marker_empty",
                message="marker cannot be empty",
                context={},
            )
        if marker in seen:
            raise PlaceholderMarkersValidationError(
                code="placeholder_markers_duplicate_marker",
                message=f"duplicate marker detected: {marker}",
                context={"marker": marker},
            )
        if MARKER_PATTERN.match(marker) is None:
            raise PlaceholderMarkersValidationError(
                code="placeholder_markers_marker_format_invalid",
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
            code="placeholder_markers_schema_invalid",
            message=f"invalid json schema: {schema_file}",
            context={"schema_file": str(schema_file)},
        ) from exc
    try:
        Draft202012Validator(schema).validate(payload)
    except ValidationError as exc:
        raise PlaceholderMarkersValidationError(
            code="placeholder_markers_schema_validation_failed",
            message="schema validation failed for marker config",
            context={"validation_path": list(exc.path)},
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(
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
    args = parser.parse_args()

    try:
        if not args.markers_file.exists():
            raise PlaceholderMarkersValidationError(
                code="placeholder_markers_markers_file_not_found",
                message=f"markers file not found: {args.markers_file}",
                context={"path": str(args.markers_file)},
            )
        if not args.schema_file.exists():
            raise PlaceholderMarkersValidationError(
                code="placeholder_markers_schema_file_not_found",
                message=f"schema file not found: {args.schema_file}",
                context={"path": str(args.schema_file)},
            )
        payload = _load_json_payload(path=args.markers_file, role="markers")
        schema = _load_json_payload(path=args.schema_file, role="schema")
        _validate_against_schema(payload=payload, schema=schema, schema_file=args.schema_file)
        _validate_markers(payload=payload)
        print(f"[validate-validator-placeholder-markers] markers config is valid: {args.markers_file}")
        return 0
    except Exception as exc:
        if args.json_errors:
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
                    "code": "placeholder_markers_unexpected_error",
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-validator-placeholder-markers] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
