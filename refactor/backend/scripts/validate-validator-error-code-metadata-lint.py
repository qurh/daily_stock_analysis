#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from difflib import get_close_matches
from json import JSONDecodeError
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LINT_CONFIG_FILE = BACKEND_ROOT / "config" / "validator-error-code-metadata-lint.json"
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "validator-error-code-metadata-lint.schema.json"
ACTION_VERB_PATTERN = re.compile(r"^[a-z][a-z_-]*$")
LINT_PROFILE_ENV_VAR = "LINT_PROFILE"
VALIDATOR_ERROR_CODES = {
    "LINT_CONFIG_FILE_NOT_FOUND": "error_code_metadata_lint_lint_config_file_not_found",
    "SCHEMA_FILE_NOT_FOUND": "error_code_metadata_lint_schema_file_not_found",
    "JSON_PARSE_ERROR": "error_code_metadata_lint_json_parse_error",
    "PAYLOAD_TYPE_INVALID": "error_code_metadata_lint_payload_type_invalid",
    "SCHEMA_INVALID": "error_code_metadata_lint_schema_invalid",
    "SCHEMA_VALIDATION_FAILED": "error_code_metadata_lint_schema_validation_failed",
    "PROFILE_NOT_FOUND": "error_code_metadata_lint_profile_not_found",
    "ACTION_VERB_FORMAT_INVALID": "error_code_metadata_lint_action_verb_format_invalid",
    "ACTION_VERB_DUPLICATE_CASE_INSENSITIVE": "error_code_metadata_lint_action_verb_duplicate_case_insensitive",
    "UNEXPECTED_ERROR": "error_code_metadata_lint_unexpected_error",
}


class MetadataLintValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


def _load_json_payload(path: Path, role: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise MetadataLintValidationError(
            code=VALIDATOR_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": role},
        ) from exc
    if not isinstance(payload, dict):
        raise MetadataLintValidationError(
            code=VALIDATOR_ERROR_CODES["PAYLOAD_TYPE_INVALID"],
            message=f"{role} payload must be an object",
            context={"path": str(path), "role": role},
        )
    return payload


def _validate_schema(lint_config: dict, schema: dict, schema_file: Path) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise MetadataLintValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_INVALID"],
            message=f"invalid json schema: {schema_file}",
            context={"schema_file": str(schema_file)},
        ) from exc

    try:
        Draft202012Validator(schema).validate(lint_config)
    except ValidationError as exc:
        raise MetadataLintValidationError(
            code=VALIDATOR_ERROR_CODES["SCHEMA_VALIDATION_FAILED"],
            message="schema validation failed for metadata lint config",
            context={"validation_path": list(exc.path)},
        ) from exc


def _validate_action_verbs(lint_config: dict) -> None:
    action_verbs = lint_config.get("action_verbs")
    assert isinstance(action_verbs, list)
    seen: set[str] = set()
    for item in action_verbs:
        assert isinstance(item, str)
        verb = item.strip().lower()
        if ACTION_VERB_PATTERN.match(verb) is None:
            raise MetadataLintValidationError(
                code=VALIDATOR_ERROR_CODES["ACTION_VERB_FORMAT_INVALID"],
                message=f"invalid action verb format: {item}",
                context={"action_verb": item},
            )
        if verb in seen:
            raise MetadataLintValidationError(
                code=VALIDATOR_ERROR_CODES["ACTION_VERB_DUPLICATE_CASE_INSENSITIVE"],
                message=f"duplicate action verb detected (case-insensitive): {item}",
                context={"action_verb": item},
            )
        seen.add(verb)


def _resolve_lint_profile(lint_config: dict, lint_profile: str | None) -> tuple[dict, str | None]:
    profiles = lint_config.get("profiles")
    if profiles is None:
        if lint_profile is not None:
            raise MetadataLintValidationError(
                code=VALIDATOR_ERROR_CODES["PROFILE_NOT_FOUND"],
                message=f"lint profile not found: {lint_profile}",
                context={"lint_profile": lint_profile, "available_profiles": []},
            )
        return lint_config, None

    assert isinstance(profiles, dict)
    selected_profile = lint_profile or lint_config.get("default_profile")
    assert isinstance(selected_profile, str)
    profile_payload = profiles.get(selected_profile)
    if not isinstance(profile_payload, dict):
        available_profiles = sorted(profiles.keys())
        suggested_profiles = get_close_matches(selected_profile, available_profiles, n=3, cutoff=0.5)
        message = f"lint profile not found: {selected_profile}"
        if suggested_profiles:
            message += f". Did you mean: {', '.join(suggested_profiles)}?"
            message += f" Try: --lint-profile {suggested_profiles[0]}"
        raise MetadataLintValidationError(
            code=VALIDATOR_ERROR_CODES["PROFILE_NOT_FOUND"],
            message=message,
            context={
                "lint_profile": selected_profile,
                "available_profiles": available_profiles,
                "suggested_profiles": suggested_profiles,
            },
        )
    return profile_payload, selected_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate validator error-code metadata lint config.")
    parser.add_argument(
        "--lint-config-file",
        type=Path,
        default=DEFAULT_LINT_CONFIG_FILE,
        help="Path to metadata lint config file.",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to metadata lint schema file.",
    )
    parser.add_argument(
        "--lint-profile",
        type=str,
        default=None,
        help="Optional lint profile name when config contains profiles.",
    )
    parser.add_argument(
        "--json-errors",
        action="store_true",
        help="Emit structured JSON errors to stderr.",
    )
    args = parser.parse_args()
    env_lint_profile = os.getenv(LINT_PROFILE_ENV_VAR)
    effective_lint_profile = args.lint_profile if args.lint_profile is not None else env_lint_profile

    try:
        if not args.lint_config_file.exists():
            raise MetadataLintValidationError(
                code=VALIDATOR_ERROR_CODES["LINT_CONFIG_FILE_NOT_FOUND"],
                message=f"lint config file not found: {args.lint_config_file}",
                context={"path": str(args.lint_config_file)},
            )
        if not args.schema_file.exists():
            raise MetadataLintValidationError(
                code=VALIDATOR_ERROR_CODES["SCHEMA_FILE_NOT_FOUND"],
                message=f"schema file not found: {args.schema_file}",
                context={"path": str(args.schema_file)},
            )
        lint_config = _load_json_payload(path=args.lint_config_file, role="lint_config")
        schema = _load_json_payload(path=args.schema_file, role="schema")
        _validate_schema(lint_config=lint_config, schema=schema, schema_file=args.schema_file)
        selected_lint_config, selected_profile = _resolve_lint_profile(
            lint_config=lint_config,
            lint_profile=effective_lint_profile,
        )
        _validate_action_verbs(lint_config=selected_lint_config)
        profile_suffix = f" (profile={selected_profile})" if selected_profile is not None else ""
        print(
            "[validate-validator-error-code-metadata-lint] "
            f"lint config is valid: {args.lint_config_file}{profile_suffix}"
        )
        return 0
    except Exception as exc:
        if args.json_errors:
            if isinstance(exc, MetadataLintValidationError):
                payload = {
                    "validator": "validate-validator-error-code-metadata-lint",
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": "validate-validator-error-code-metadata-lint",
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-validator-error-code-metadata-lint] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
