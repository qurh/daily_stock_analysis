#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import runpy
import sys
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "profile-suggestion-actions.schema.json"
DEFAULT_EXAMPLE_FILE = BACKEND_ROOT / "config" / "schemas" / "profile-suggestion-actions.example.json"
DEFAULT_HELPER_FILE = BACKEND_ROOT / "scripts" / "profile_suggestion_helpers.py"
VALIDATOR_ERROR_CODES = {
    "FILE_NOT_FOUND": "profile_suggestion_actions_file_not_found",
    "JSON_PARSE_ERROR": "profile_suggestion_actions_json_parse_error",
    "SCHEMA_INVALID": "profile_suggestion_actions_schema_invalid",
    "EXAMPLE_VALIDATION_FAILED": "profile_suggestion_actions_example_validation_failed",
    "HELPER_CONTRACT_FAILED": "profile_suggestion_actions_helper_contract_failed",
    "CLI_ARGS_INVALID": "profile_suggestion_actions_cli_args_invalid",
    "UNEXPECTED_ERROR": "profile_suggestion_actions_unexpected_error",
}


class ProfileSuggestionActionsSchemaValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class _ProfileSuggestionArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ProfileSuggestionActionsSchemaValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: {message}",
            context={"failure_mode": "argparse_error", "argparse_message": message},
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _ProfileSuggestionArgumentParser(description="Validate profile suggestion actions schema and helper outputs.")
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to profile suggestion actions schema JSON file.",
    )
    parser.add_argument(
        "--example-file",
        type=Path,
        default=DEFAULT_EXAMPLE_FILE,
        help="Path to profile suggestion actions example JSON file.",
    )
    parser.add_argument(
        "--helper-file",
        type=Path,
        default=DEFAULT_HELPER_FILE,
        help="Path to profile suggestion helper Python file.",
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
    except ProfileSuggestionActionsSchemaValidationError as exc:
        context = dict(exc.context)
        context.setdefault("argv", list(argv))
        raise ProfileSuggestionActionsSchemaValidationError(
            code=exc.code,
            message=str(exc),
            context=context,
        ) from exc
    if unknown_args:
        raise ProfileSuggestionActionsSchemaValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: unrecognized arguments: {' '.join(unknown_args)}",
            context={"failure_mode": "unknown_args", "unknown_args": unknown_args, "argv": list(argv)},
        )
    return args


def _load_json(path: Path, role: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise ProfileSuggestionActionsSchemaValidationError(
            code=VALIDATOR_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": role},
        ) from exc


def _load_helper_functions(helper_file: Path) -> tuple[Any, Any, Any]:
    namespace = runpy.run_path(str(helper_file))
    build_profile_suggestion_payload = namespace.get("build_profile_suggestion_payload")
    build_suggested_actions_for_profile_not_found = namespace.get("build_suggested_actions_for_profile_not_found")
    build_profile_mode_config_snippet = namespace.get("build_profile_mode_config_snippet")
    if not callable(build_profile_suggestion_payload):
        raise ProfileSuggestionActionsSchemaValidationError(
            code=VALIDATOR_ERROR_CODES["HELPER_CONTRACT_FAILED"],
            message=f"missing helper function: build_profile_suggestion_payload in {helper_file}",
            context={"helper_file": str(helper_file)},
        )
    if not callable(build_suggested_actions_for_profile_not_found):
        raise ProfileSuggestionActionsSchemaValidationError(
            code=VALIDATOR_ERROR_CODES["HELPER_CONTRACT_FAILED"],
            message=f"missing helper function: build_suggested_actions_for_profile_not_found in {helper_file}",
            context={"helper_file": str(helper_file)},
        )
    if not callable(build_profile_mode_config_snippet):
        raise ProfileSuggestionActionsSchemaValidationError(
            code=VALIDATOR_ERROR_CODES["HELPER_CONTRACT_FAILED"],
            message=f"missing helper function: build_profile_mode_config_snippet in {helper_file}",
            context={"helper_file": str(helper_file)},
        )
    return (
        build_profile_suggestion_payload,
        build_suggested_actions_for_profile_not_found,
        build_profile_mode_config_snippet,
    )


def _validate_helper_examples(helper_file: Path, schema: dict) -> None:
    (
        build_profile_suggestion_payload,
        build_suggested_actions_for_profile_not_found,
        build_profile_mode_config_snippet,
    ) = _load_helper_functions(helper_file=helper_file)

    validator = Draft202012Validator(schema)

    (
        _message,
        fallback_reason,
        _suggestion_level,
        suggested_profiles,
        _suggested_cli_args,
        suggested_command,
    ) = build_profile_suggestion_payload(
        selected_profile="prdo",
        available_profiles=["prod", "dev"],
        command_prefix="python3 scripts/validate-validator-error-code-metadata-lint.py --lint-config-file /tmp/a.json",
    )
    close_actions = build_suggested_actions_for_profile_not_found(
        fallback_reason=fallback_reason,
        suggested_profiles=suggested_profiles,
        available_profiles=["prod", "dev"],
        suggested_command=suggested_command,
    )
    no_close_actions = build_suggested_actions_for_profile_not_found(
        fallback_reason="no_close_match",
        suggested_profiles=[],
        available_profiles=["prod", "dev"],
        suggested_command=None,
    )
    profile_mode_snippet = build_profile_mode_config_snippet(
        flat_config={"min_remediation_length": 12, "action_verbs": ["verify"]},
        selected_profile="dev",
    )
    no_profile_actions = build_suggested_actions_for_profile_not_found(
        fallback_reason="no_profiles_config",
        suggested_profiles=[],
        available_profiles=[],
        suggested_command=None,
        suggested_config_snippet=profile_mode_snippet,
    )

    for case_name, payload in (
        ("close_match", close_actions),
        ("no_close_match", no_close_actions),
        ("no_profiles_config", no_profile_actions),
    ):
        try:
            validator.validate(payload)
        except ValidationError as exc:
            raise ProfileSuggestionActionsSchemaValidationError(
                code=VALIDATOR_ERROR_CODES["HELPER_CONTRACT_FAILED"],
                message=f"helper actions validation failed: {case_name}",
                context={"case": case_name, "validation_path": list(exc.path)},
            ) from exc


def main() -> int:
    argv = sys.argv[1:]
    json_errors_requested = "--json-errors" in argv
    json_output_requested = "--json-output" in argv

    try:
        args = _parse_args(argv=argv)
        json_errors_requested = bool(args.json_errors)
        json_output_requested = bool(args.json_output)
        for role, file_path in (
            ("schema", args.schema_file),
            ("example", args.example_file),
            ("helper", args.helper_file),
        ):
            if not file_path.exists():
                raise ProfileSuggestionActionsSchemaValidationError(
                    code=VALIDATOR_ERROR_CODES["FILE_NOT_FOUND"],
                    message=f"{role} file not found: {file_path}",
                    context={"path": str(file_path), "role": role},
                )

        schema = _load_json(path=args.schema_file, role="schema")
        example_payload = _load_json(path=args.example_file, role="example")
        if not isinstance(schema, dict):
            raise ProfileSuggestionActionsSchemaValidationError(
                code=VALIDATOR_ERROR_CODES["SCHEMA_INVALID"],
                message=f"schema payload must be an object: {args.schema_file}",
                context={"path": str(args.schema_file)},
            )
        if not isinstance(example_payload, list):
            raise ProfileSuggestionActionsSchemaValidationError(
                code=VALIDATOR_ERROR_CODES["EXAMPLE_VALIDATION_FAILED"],
                message=f"example payload must be an array: {args.example_file}",
                context={"path": str(args.example_file)},
            )

        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise ProfileSuggestionActionsSchemaValidationError(
                code=VALIDATOR_ERROR_CODES["SCHEMA_INVALID"],
                message=f"invalid json schema: {args.schema_file}",
                context={"path": str(args.schema_file)},
            ) from exc

        validator = Draft202012Validator(schema)
        try:
            validator.validate(example_payload)
        except ValidationError as exc:
            raise ProfileSuggestionActionsSchemaValidationError(
                code=VALIDATOR_ERROR_CODES["EXAMPLE_VALIDATION_FAILED"],
                message="example payload validation failed",
                context={"path": str(args.example_file), "validation_path": list(exc.path)},
            ) from exc

        _validate_helper_examples(helper_file=args.helper_file, schema=schema)

        if json_output_requested:
            payload = {
                "validator": "validate-profile-suggestion-actions-schema",
                "status": "ok",
                "schema_file": str(args.schema_file),
                "example_file": str(args.example_file),
                "helper_file": str(args.helper_file),
                "example_action_count": len(example_payload),
            }
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[validate-profile-suggestion-actions-schema] schema is valid: {args.schema_file}")
            print(f"[validate-profile-suggestion-actions-schema] example payload is valid: {args.example_file}")
            print("[validate-profile-suggestion-actions-schema] helper actions are valid against schema.")
        return 0
    except Exception as exc:
        if json_errors_requested:
            if isinstance(exc, ProfileSuggestionActionsSchemaValidationError):
                payload = {
                    "validator": "validate-profile-suggestion-actions-schema",
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": "validate-profile-suggestion-actions-schema",
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-profile-suggestion-actions-schema] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
