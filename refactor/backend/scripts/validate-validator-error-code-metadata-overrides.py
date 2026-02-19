#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OVERRIDES_FILE = BACKEND_ROOT / "config" / "validator-error-code-metadata-overrides.json"
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "validator-error-code-metadata-overrides.schema.json"
DEFAULT_CATALOG_FILE = BACKEND_ROOT / "config" / "validator-error-codes.json"
VALIDATOR_ERROR_CODES = {
    "OVERRIDES_FILE_NOT_FOUND": "error_code_metadata_overrides_overrides_file_not_found",
    "SCHEMA_FILE_NOT_FOUND": "error_code_metadata_overrides_schema_file_not_found",
    "CATALOG_FILE_NOT_FOUND": "error_code_metadata_overrides_catalog_file_not_found",
    "JSON_PARSE_ERROR": "error_code_metadata_overrides_json_parse_error",
    "PAYLOAD_TYPE_INVALID": "error_code_metadata_overrides_payload_type_invalid",
    "SCHEMA_INVALID": "error_code_metadata_overrides_schema_invalid",
    "SCHEMA_VALIDATION_FAILED": "error_code_metadata_overrides_schema_validation_failed",
    "UNKNOWN_OVERRIDE_GROUP": "error_code_metadata_overrides_unknown_override_group",
    "UNKNOWN_OVERRIDE_CODE": "error_code_metadata_overrides_unknown_override_code",
    "UNEXPECTED_ERROR": "error_code_metadata_overrides_unexpected_error",
}


class MetadataOverridesValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


def _load_json_payload(path: Path, role: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": role},
        ) from exc
    if not isinstance(payload, dict):
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["PAYLOAD_TYPE_INVALID"],
            message=f"{role} payload must be an object",
            context={"path": str(path), "role": role},
        )
    return payload


def _validate_overrides_schema(overrides: dict, schema: dict, schema_file: Path) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_INVALID"],
            message=f"invalid json schema: {schema_file}",
            context={"schema_file": str(schema_file)},
        ) from exc

    try:
        Draft202012Validator(schema).validate(overrides)
    except ValidationError as exc:
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_VALIDATION_FAILED"],
            message="schema validation failed for metadata overrides config",
            context={"validation_path": list(exc.path)},
        ) from exc


def _validate_override_targets(overrides: dict, catalog: dict) -> None:
    for group_name, group_payload in overrides.items():
        if group_name not in catalog:
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["UNKNOWN_OVERRIDE_GROUP"],
                message=f"unknown override group: {group_name}",
                context={"group": group_name},
            )
        for code in group_payload.keys():
            if code not in catalog[group_name]:
                raise MetadataOverridesValidationError(
                    code=VALIDATOR_ERROR_CODES["UNKNOWN_OVERRIDE_CODE"],
                    message=f"unknown override code: {group_name}.{code}",
                    context={"group": group_name, "code": code},
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate validator error-code metadata overrides config.")
    parser.add_argument(
        "--overrides-file",
        type=Path,
        default=DEFAULT_OVERRIDES_FILE,
        help="Path to metadata overrides config file.",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to metadata overrides schema file.",
    )
    parser.add_argument(
        "--catalog-file",
        type=Path,
        default=DEFAULT_CATALOG_FILE,
        help="Path to validator error-code catalog file.",
    )
    parser.add_argument(
        "--json-errors",
        action="store_true",
        help="Emit structured JSON errors to stderr.",
    )
    args = parser.parse_args()

    try:
        if not args.overrides_file.exists():
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["OVERRIDES_FILE_NOT_FOUND"],
                message=f"overrides file not found: {args.overrides_file}",
                context={"path": str(args.overrides_file)},
            )
        if not args.schema_file.exists():
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["SCHEMA_FILE_NOT_FOUND"],
                message=f"schema file not found: {args.schema_file}",
                context={"path": str(args.schema_file)},
            )
        if not args.catalog_file.exists():
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["CATALOG_FILE_NOT_FOUND"],
                message=f"catalog file not found: {args.catalog_file}",
                context={"path": str(args.catalog_file)},
            )

        overrides = _load_json_payload(path=args.overrides_file, role="overrides")
        schema = _load_json_payload(path=args.schema_file, role="schema")
        catalog = _load_json_payload(path=args.catalog_file, role="catalog")
        _validate_overrides_schema(overrides=overrides, schema=schema, schema_file=args.schema_file)
        _validate_override_targets(overrides=overrides, catalog=catalog)
        print(f"[validate-validator-error-code-metadata-overrides] overrides config is valid: {args.overrides_file}")
        return 0
    except Exception as exc:
        if args.json_errors:
            if isinstance(exc, MetadataOverridesValidationError):
                payload = {
                    "validator": "validate-validator-error-code-metadata-overrides",
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": "validate-validator-error-code-metadata-overrides",
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-validator-error-code-metadata-overrides] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
