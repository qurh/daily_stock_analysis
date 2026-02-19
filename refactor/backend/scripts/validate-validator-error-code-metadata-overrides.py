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
DEFAULT_OVERRIDES_FILE = BACKEND_ROOT / "config" / "validator-error-code-metadata-overrides.json"
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "validator-error-code-metadata-overrides.schema.json"
DEFAULT_CATALOG_FILE = BACKEND_ROOT / "config" / "validator-error-codes.json"
DEFAULT_PLACEHOLDER_MARKERS_FILE = BACKEND_ROOT / "config" / "validator-placeholder-markers.json"
DEFAULT_LINT_CONFIG_FILE = BACKEND_ROOT / "config" / "validator-error-code-metadata-lint.json"
LINT_PROFILE_ENV_VAR = "LINT_PROFILE"
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
    "LINT_CONFIG_FILE_NOT_FOUND": "error_code_metadata_overrides_lint_config_file_not_found",
    "LINT_CONFIG_INVALID": "error_code_metadata_overrides_lint_config_invalid",
    "LINT_PROFILE_NOT_FOUND": "error_code_metadata_overrides_lint_profile_not_found",
    "PLACEHOLDER_MARKERS_FILE_NOT_FOUND": "error_code_metadata_overrides_placeholder_markers_file_not_found",
    "PLACEHOLDER_MARKERS_INVALID": "error_code_metadata_overrides_placeholder_markers_invalid",
    "PLACEHOLDER_TEXT_DETECTED": "error_code_metadata_overrides_placeholder_text_detected",
    "REMEDIATION_QUALITY_INVALID": "error_code_metadata_overrides_remediation_quality_invalid",
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


def _resolve_lint_profile(payload: dict, lint_profile: str | None, path: Path) -> dict:
    profiles = payload.get("profiles")
    if profiles is None:
        if lint_profile is not None:
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["LINT_PROFILE_NOT_FOUND"],
                message=f"lint profile not found: {lint_profile}",
                context={"path": str(path), "lint_profile": lint_profile, "available_profiles": []},
            )
        return payload

    if not isinstance(profiles, dict) or not profiles:
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["LINT_CONFIG_INVALID"],
            message=f"invalid lint config profiles: {path}",
            context={"path": str(path), "field": "profiles"},
        )

    selected_profile = lint_profile or payload.get("default_profile")
    if not isinstance(selected_profile, str) or not selected_profile.strip():
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["LINT_CONFIG_INVALID"],
            message=f"invalid lint config default_profile: {path}",
            context={"path": str(path), "field": "default_profile"},
        )
    selected_profile = selected_profile.strip()
    profile_payload = profiles.get(selected_profile)
    if not isinstance(profile_payload, dict):
        available_profiles = sorted(profiles.keys())
        suggested_profiles = get_close_matches(selected_profile, available_profiles, n=3, cutoff=0.5)
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["LINT_PROFILE_NOT_FOUND"],
            message=f"lint profile not found: {selected_profile}",
            context={
                "path": str(path),
                "lint_profile": selected_profile,
                "available_profiles": available_profiles,
                "suggested_profiles": suggested_profiles,
            },
        )
    return profile_payload


def _load_lint_config(path: Path, lint_profile: str | None = None) -> tuple[int, re.Pattern[str]]:
    if not path.exists():
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["LINT_CONFIG_FILE_NOT_FOUND"],
            message=f"lint config file not found: {path}",
            context={"path": str(path)},
        )
    payload = _load_json_payload(path=path, role="lint_config")
    payload = _resolve_lint_profile(payload=payload, lint_profile=lint_profile, path=path)
    min_remediation_length = payload.get("min_remediation_length")
    action_verbs = payload.get("action_verbs")

    if not isinstance(min_remediation_length, int) or min_remediation_length < 1:
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["LINT_CONFIG_INVALID"],
            message=f"invalid lint config min_remediation_length: {path}",
            context={"path": str(path), "field": "min_remediation_length"},
        )
    if not isinstance(action_verbs, list) or not action_verbs:
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["LINT_CONFIG_INVALID"],
            message=f"invalid lint config action_verbs: {path}",
            context={"path": str(path), "field": "action_verbs"},
        )

    normalized_verbs: list[str] = []
    seen: set[str] = set()
    for item in action_verbs:
        if not isinstance(item, str) or not item.strip():
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["LINT_CONFIG_INVALID"],
                message=f"invalid lint config action verb: {path}",
                context={"path": str(path), "field": "action_verbs", "value": item},
            )
        verb = item.strip().lower()
        if verb in seen:
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["LINT_CONFIG_INVALID"],
                message=f"duplicate lint config action verb: {verb}",
                context={"path": str(path), "field": "action_verbs", "value": verb},
            )
        seen.add(verb)
        normalized_verbs.append(verb)

    action_pattern = re.compile(r"\b(" + "|".join(re.escape(item) for item in normalized_verbs) + r")\b", re.IGNORECASE)
    return min_remediation_length, action_pattern


def _load_placeholder_markers(path: Path) -> list[str]:
    if not path.exists():
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["PLACEHOLDER_MARKERS_FILE_NOT_FOUND"],
            message=f"placeholder markers file not found: {path}",
            context={"path": str(path)},
        )
    payload = _load_json_payload(path=path, role="placeholder_markers")
    markers = payload.get("markers")
    if not isinstance(markers, list) or not markers:
        raise MetadataOverridesValidationError(
            code=VALIDATOR_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
            message=f"placeholder markers payload must include non-empty markers list: {path}",
            context={"path": str(path)},
        )
    normalized: list[str] = []
    seen: set[str] = set()
    for marker in markers:
        if not isinstance(marker, str) or not marker.strip():
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
                message=f"invalid placeholder marker: {marker}",
                context={"path": str(path), "marker": marker},
            )
        marker_value = marker.strip().upper()
        if marker_value in seen:
            raise MetadataOverridesValidationError(
                code=VALIDATOR_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
                message=f"duplicate placeholder marker: {marker_value}",
                context={"path": str(path), "marker": marker_value},
            )
        seen.add(marker_value)
        normalized.append(marker_value)
    return normalized


def _build_placeholder_pattern(markers: list[str]) -> re.Pattern[str]:
    escaped_markers = [re.escape(marker) for marker in markers]
    return re.compile(r"^\s*(" + "|".join(escaped_markers) + r")\s*:", re.IGNORECASE)


def _validate_placeholder_text(overrides: dict, placeholder_pattern: re.Pattern[str]) -> None:
    for group_name, group_payload in overrides.items():
        for code, code_payload in group_payload.items():
            for field_name in ("description", "remediation"):
                field_value = code_payload.get(field_name)
                if not isinstance(field_value, str):
                    continue
                match = placeholder_pattern.match(field_value)
                if match is None:
                    continue
                marker = match.group(1).upper()
                raise MetadataOverridesValidationError(
                    code=VALIDATOR_ERROR_CODES["PLACEHOLDER_TEXT_DETECTED"],
                    message=f"placeholder text detected in metadata override: {group_name}.{code}.{field_name}",
                    context={
                        "group": group_name,
                        "code": code,
                        "field": field_name,
                        "marker": marker,
                    },
                )


def _validate_remediation_quality(
    overrides: dict,
    min_remediation_length: int,
    actionable_remediation_pattern: re.Pattern[str],
) -> None:
    for group_name, group_payload in overrides.items():
        for code, code_payload in group_payload.items():
            remediation = code_payload.get("remediation")
            if not isinstance(remediation, str):
                continue
            remediation_value = remediation.strip()
            if (
                len(remediation_value) < min_remediation_length
                or actionable_remediation_pattern.search(remediation_value) is None
            ):
                raise MetadataOverridesValidationError(
                    code=VALIDATOR_ERROR_CODES["REMEDIATION_QUALITY_INVALID"],
                    message=f"remediation text is not actionable enough: {group_name}.{code}.remediation",
                    context={
                        "group": group_name,
                        "code": code,
                        "field": "remediation",
                    },
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
        "--placeholder-markers-file",
        type=Path,
        default=DEFAULT_PLACEHOLDER_MARKERS_FILE,
        help="Path to placeholder markers config file.",
    )
    parser.add_argument(
        "--lint-config-file",
        type=Path,
        default=DEFAULT_LINT_CONFIG_FILE,
        help="Path to metadata lint config file.",
    )
    parser.add_argument(
        "--lint-profile",
        type=str,
        default=None,
        help="Optional lint profile name when lint config contains profiles.",
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
        min_remediation_length, actionable_remediation_pattern = _load_lint_config(
            path=args.lint_config_file,
            lint_profile=effective_lint_profile,
        )
        placeholder_markers = _load_placeholder_markers(path=args.placeholder_markers_file)
        placeholder_pattern = _build_placeholder_pattern(markers=placeholder_markers)
        _validate_placeholder_text(overrides=overrides, placeholder_pattern=placeholder_pattern)
        _validate_remediation_quality(
            overrides=overrides,
            min_remediation_length=min_remediation_length,
            actionable_remediation_pattern=actionable_remediation_pattern,
        )
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
