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
DEFAULT_CATALOG_FILE = BACKEND_ROOT / "config" / "validator-error-codes.json"
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "validator-error-codes.schema.json"
VALIDATOR_ERROR_CODES = {
    "CATALOG_FILE_NOT_FOUND": "error_code_catalog_catalog_file_not_found",
    "SCHEMA_FILE_NOT_FOUND": "error_code_catalog_schema_file_not_found",
    "JSON_PARSE_ERROR": "error_code_catalog_json_parse_error",
    "PAYLOAD_TYPE_INVALID": "error_code_catalog_payload_type_invalid",
    "SCHEMA_INVALID": "error_code_catalog_schema_invalid",
    "SCHEMA_VALIDATION_FAILED": "error_code_catalog_schema_validation_failed",
    "CODE_PREFIX_MISMATCH": "error_code_catalog_code_prefix_mismatch",
    "UNEXPECTED_ERROR": "error_code_catalog_unexpected_error",
}


class ErrorCodeCatalogValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


def _load_json_payload(path: Path, role: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise ErrorCodeCatalogValidationError(
            code=VALIDATOR_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": role},
        ) from exc
    if not isinstance(payload, dict):
        raise ErrorCodeCatalogValidationError(
            code=VALIDATOR_ERROR_CODES["PAYLOAD_TYPE_INVALID"],
            message=f"{role} payload must be an object",
            context={"path": str(path), "role": role},
        )
    return payload


def _validate_against_schema(catalog: dict, schema: dict, schema_file: Path) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ErrorCodeCatalogValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_INVALID"],
            message=f"invalid json schema: {schema_file}",
            context={"schema_file": str(schema_file)},
        ) from exc

    try:
        Draft202012Validator(schema).validate(catalog)
    except ValidationError as exc:
        raise ErrorCodeCatalogValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_VALIDATION_FAILED"],
            message="schema validation failed for validator error code catalog",
            context={"validation_path": list(exc.path)},
        ) from exc


def _validate_code_prefix(catalog: dict[str, dict[str, dict[str, str]]]) -> None:
    for group_name, group_payload in catalog.items():
        for code in group_payload.keys():
            required_prefix = f"{group_name}_"
            if not code.startswith(required_prefix):
                raise ErrorCodeCatalogValidationError(
                    code=VALIDATOR_ERROR_CODES["CODE_PREFIX_MISMATCH"],
                    message=f"error code prefix mismatch: {group_name}.{code}",
                    context={
                        "group": group_name,
                        "code": code,
                        "expected_prefix": required_prefix,
                    },
                )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate validator error code catalog JSON schema and naming conventions."
    )
    parser.add_argument(
        "--catalog-file",
        type=Path,
        default=DEFAULT_CATALOG_FILE,
        help="Path to validator error code catalog file.",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to validator error code catalog schema file.",
    )
    parser.add_argument(
        "--json-errors",
        action="store_true",
        help="Emit structured JSON errors to stderr.",
    )
    args = parser.parse_args()

    try:
        if not args.catalog_file.exists():
            raise ErrorCodeCatalogValidationError(
                code=VALIDATOR_ERROR_CODES["CATALOG_FILE_NOT_FOUND"],
                message=f"catalog file not found: {args.catalog_file}",
                context={"path": str(args.catalog_file)},
            )
        if not args.schema_file.exists():
            raise ErrorCodeCatalogValidationError(
                code=VALIDATOR_ERROR_CODES["SCHEMA_FILE_NOT_FOUND"],
                message=f"schema file not found: {args.schema_file}",
                context={"path": str(args.schema_file)},
            )

        catalog = _load_json_payload(path=args.catalog_file, role="catalog")
        schema = _load_json_payload(path=args.schema_file, role="schema")
        _validate_against_schema(catalog=catalog, schema=schema, schema_file=args.schema_file)
        _validate_code_prefix(catalog=catalog)

        print(f"[validate-validator-error-code-catalog] catalog is valid: {args.catalog_file}")
        return 0
    except Exception as exc:
        if args.json_errors:
            if isinstance(exc, ErrorCodeCatalogValidationError):
                payload = {
                    "validator": "validate-validator-error-code-catalog",
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": "validate-validator-error-code-catalog",
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-validator-error-code-catalog] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
