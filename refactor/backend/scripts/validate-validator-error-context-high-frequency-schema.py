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
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "validator-error-context-high-frequency.schema.json"
DEFAULT_SAMPLES_FILE = BACKEND_ROOT / "config" / "validator-error-context-high-frequency-samples.json"
VALIDATOR_NAME = "validate-validator-error-context-high-frequency-schema"
VALIDATOR_ERROR_CODES = {
    "CLI_ARGS_INVALID": "error_context_high_frequency_cli_args_invalid",
    "SCHEMA_FILE_NOT_FOUND": "error_context_high_frequency_schema_file_not_found",
    "SAMPLES_FILE_NOT_FOUND": "error_context_high_frequency_samples_file_not_found",
    "JSON_PARSE_ERROR": "error_context_high_frequency_json_parse_error",
    "SCHEMA_INVALID": "error_context_high_frequency_schema_invalid",
    "SAMPLES_PAYLOAD_INVALID": "error_context_high_frequency_samples_payload_invalid",
    "SAMPLE_SCHEMA_VALIDATION_FAILED": "error_context_high_frequency_sample_schema_validation_failed",
    "UNEXPECTED_ERROR": "error_context_high_frequency_unexpected_error",
}


class ErrorContextHighFrequencyValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class _ErrorContextHighFrequencyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ErrorContextHighFrequencyValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: {message}",
            context={"failure_mode": "argparse_error", "argparse_message": message},
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _ErrorContextHighFrequencyArgumentParser(
        description="Validate high-frequency validator error context schema with sample payloads.",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to high-frequency error context schema JSON file.",
    )
    parser.add_argument(
        "--samples-file",
        type=Path,
        default=DEFAULT_SAMPLES_FILE,
        help="Path to high-frequency error context sample payloads JSON file.",
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
    except ErrorContextHighFrequencyValidationError as exc:
        context = dict(exc.context)
        context.setdefault("argv", list(argv))
        raise ErrorContextHighFrequencyValidationError(code=exc.code, message=str(exc), context=context) from exc
    if unknown_args:
        raise ErrorContextHighFrequencyValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: unrecognized arguments: {' '.join(unknown_args)}",
            context={"failure_mode": "unknown_args", "unknown_args": unknown_args, "argv": list(argv)},
        )
    return args


def _load_json_payload(path: Path, role: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise ErrorContextHighFrequencyValidationError(
            code=VALIDATOR_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": role},
        ) from exc


def _build_schema_validator(schema_payload: object, schema_file: Path) -> Draft202012Validator:
    if not isinstance(schema_payload, dict):
        raise ErrorContextHighFrequencyValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_INVALID"],
            message=f"schema payload must be an object: {schema_file}",
            context={"path": str(schema_file)},
        )
    try:
        Draft202012Validator.check_schema(schema_payload)
    except SchemaError as exc:
        raise ErrorContextHighFrequencyValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_INVALID"],
            message=f"invalid json schema: {schema_file}",
            context={"path": str(schema_file)},
        ) from exc
    return Draft202012Validator(schema_payload)


def _validate_samples(samples_payload: object, validator: Draft202012Validator, samples_file: Path) -> int:
    if not isinstance(samples_payload, list):
        raise ErrorContextHighFrequencyValidationError(
            code=VALIDATOR_ERROR_CODES["SAMPLES_PAYLOAD_INVALID"],
            message=f"samples payload must be a list: {samples_file}",
            context={"path": str(samples_file), "role": "samples"},
        )

    for sample_index, sample_payload in enumerate(samples_payload):
        if not isinstance(sample_payload, dict):
            raise ErrorContextHighFrequencyValidationError(
                code=VALIDATOR_ERROR_CODES["SAMPLES_PAYLOAD_INVALID"],
                message=f"sample payload must be an object: index={sample_index}",
                context={"path": str(samples_file), "role": "samples", "sample_index": sample_index},
            )
        try:
            validator.validate(sample_payload)
        except ValidationError as exc:
            raise ErrorContextHighFrequencyValidationError(
                code=VALIDATOR_ERROR_CODES["SAMPLE_SCHEMA_VALIDATION_FAILED"],
                message=f"sample payload validation failed: index={sample_index}",
                context={
                    "path": str(samples_file),
                    "sample_index": sample_index,
                    "sample_code": sample_payload.get("code"),
                    "validation_path": list(exc.path),
                },
            ) from exc

    return len(samples_payload)


def main() -> int:
    argv = sys.argv[1:]
    json_errors_requested = "--json-errors" in argv
    json_output_requested = "--json-output" in argv
    try:
        args = _parse_args(argv=argv)
        json_errors_requested = bool(args.json_errors)
        json_output_requested = bool(args.json_output)

        if not args.schema_file.exists():
            raise ErrorContextHighFrequencyValidationError(
                code=VALIDATOR_ERROR_CODES["SCHEMA_FILE_NOT_FOUND"],
                message=f"schema file not found: {args.schema_file}",
                context={"path": str(args.schema_file)},
            )
        if not args.samples_file.exists():
            raise ErrorContextHighFrequencyValidationError(
                code=VALIDATOR_ERROR_CODES["SAMPLES_FILE_NOT_FOUND"],
                message=f"samples file not found: {args.samples_file}",
                context={"path": str(args.samples_file)},
            )

        schema_payload = _load_json_payload(path=args.schema_file, role="schema")
        samples_payload = _load_json_payload(path=args.samples_file, role="samples")
        validator = _build_schema_validator(schema_payload=schema_payload, schema_file=args.schema_file)
        sample_count = _validate_samples(samples_payload=samples_payload, validator=validator, samples_file=args.samples_file)

        if json_output_requested:
            payload = {
                "validator": VALIDATOR_NAME,
                "status": "ok",
                "schema_file": str(args.schema_file),
                "samples_file": str(args.samples_file),
                "sample_count": sample_count,
            }
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[{VALIDATOR_NAME}] high-frequency error context schema and samples are valid: {args.samples_file}")
        return 0
    except Exception as exc:
        if json_errors_requested:
            if isinstance(exc, ErrorContextHighFrequencyValidationError):
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
            print(f"[{VALIDATOR_NAME}] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
