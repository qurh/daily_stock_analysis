#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import os
import re
import runpy
import sys
from contextlib import redirect_stderr
from json import JSONDecodeError
from pathlib import Path

from profile_suggestion_helpers import (
    build_ordered_available_profiles as _build_ordered_available_profiles,
    build_profile_mode_config_snippet as _build_profile_mode_config_snippet,
    build_profile_suggestion_payload as _build_profile_suggestion_payload,
    build_suggested_actions_for_profile_not_found as _build_suggested_actions_for_profile_not_found,
    shell_quote as _shell_quote,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_FILE = BACKEND_ROOT / "config" / "validator-error-codes.json"
DEFAULT_PLACEHOLDER_MARKERS_FILE = BACKEND_ROOT / "config" / "validator-placeholder-markers.json"
DEFAULT_METADATA_OVERRIDES_FILE = BACKEND_ROOT / "config" / "validator-error-code-metadata-overrides.json"
METADATA_OVERRIDES_PROFILE_ENV_VAR = "METADATA_OVERRIDES_PROFILE"
SYNC_ERROR_CODES = {
    "JSON_PARSE_ERROR": "error_code_sync_validator_error_codes_json_parse_error",
    "PAYLOAD_INVALID": "error_code_sync_validator_error_codes_payload_invalid",
    "CATALOG_FILE_NOT_FOUND": "error_code_sync_validator_error_codes_catalog_file_not_found",
    "CATALOG_FILE_READ_FAILED": "error_code_sync_validator_error_codes_catalog_file_read_failed",
    "OUTPUT_PARENT_CREATE_FAILED": "error_code_sync_validator_error_codes_output_parent_create_failed",
    "OUTPUT_WRITE_FAILED": "error_code_sync_validator_error_codes_output_write_failed",
    "CATALOG_NOT_IN_SYNC": "error_code_sync_validator_error_codes_catalog_not_in_sync",
    "METADATA_OVERRIDES_PROFILE_NOT_FOUND": "error_code_sync_validator_error_codes_metadata_overrides_profile_not_found",
    "METADATA_OVERRIDES_FILE_NOT_FOUND": "error_code_sync_validator_error_codes_metadata_overrides_file_not_found",
    "METADATA_OVERRIDES_FILE_READ_FAILED": "error_code_sync_validator_error_codes_metadata_overrides_file_read_failed",
    "VALIDATOR_SCRIPT_FILE_NOT_FOUND": "error_code_sync_validator_error_codes_validator_script_file_not_found",
    "VALIDATOR_REGISTRY_MISSING": "error_code_sync_validator_error_codes_validator_registry_missing",
    "VALIDATOR_REGISTRY_INVALID": "error_code_sync_validator_error_codes_validator_registry_invalid",
    "VALIDATOR_REGISTRY_LOAD_FAILED": "error_code_sync_validator_error_codes_validator_registry_load_failed",
    "UNKNOWN_OVERRIDE_GROUP": "error_code_sync_validator_error_codes_unknown_override_group",
    "UNKNOWN_OVERRIDE_CODE": "error_code_sync_validator_error_codes_unknown_override_code",
    "PLACEHOLDER_MARKERS_FILE_NOT_FOUND": "error_code_sync_validator_error_codes_placeholder_markers_file_not_found",
    "PLACEHOLDER_MARKERS_READ_FAILED": "error_code_sync_validator_error_codes_placeholder_markers_read_failed",
    "PLACEHOLDER_MARKERS_INVALID": "error_code_sync_validator_error_codes_placeholder_markers_invalid",
    "PLACEHOLDER_TEXT_DETECTED": "error_code_sync_validator_error_codes_placeholder_text_detected",
    "UNEXPECTED_ERROR": "error_code_sync_validator_error_codes_unexpected_error",
}
VALIDATOR_SCRIPT_FILES = {
    "summary_schema": BACKEND_ROOT / "scripts" / "validate-strict-gate-summary-schema.py",
    "summary_contract": BACKEND_ROOT / "scripts" / "validate-summary-contract-changelog.py",
    "placeholder_markers": BACKEND_ROOT / "scripts" / "validate-validator-placeholder-markers.py",
    "profile_suggestion_actions": BACKEND_ROOT / "scripts" / "validate-profile-suggestion-actions-schema.py",
    "alertmanager_route_consistency": BACKEND_ROOT / "scripts" / "validate-alertmanager-route-consistency.py",
    "notification_retry_runbook": BACKEND_ROOT / "scripts" / "validate-notification-retry-runbook.py",
    "error_context_high_frequency": (
        BACKEND_ROOT / "scripts" / "validate-validator-error-context-high-frequency-schema.py"
    ),
}
ALLOWED_OVERRIDE_FIELDS = {"description", "severity", "remediation"}
VALID_SEVERITY_LEVELS = {"info", "warning", "error", "critical"}
DEFAULT_ENTRY_SEVERITY = "error"
DEFAULT_ENTRY_REMEDIATION = "Review validator output and update configuration or input data for this error."


class SyncValidatorErrorCodesError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


def _infer_default_severity(code: str) -> str:
    if code.endswith("_unexpected_error"):
        return "critical"
    return DEFAULT_ENTRY_SEVERITY


def _infer_default_remediation(code: str) -> str:
    if code.endswith("_json_parse_error"):
        return "Fix JSON syntax/encoding in the target file and rerun the validator."
    if code.endswith("_file_not_found"):
        return "Ensure the target file path exists and is readable in the current environment."
    if code.endswith("_schema_invalid"):
        return "Fix schema definition to satisfy JSON Schema Draft 2020-12 requirements."
    if "schema_validation_failed" in code:
        return "Update payload fields to satisfy schema constraints and required properties."
    if code.endswith("_unexpected_error"):
        return "Check stack trace and validator logs, then patch runtime defect before retry."
    return DEFAULT_ENTRY_REMEDIATION


def _resolve_severity(existing_severity: object, code: str) -> str:
    inferred = _infer_default_severity(code=code)
    if not isinstance(existing_severity, str) or not existing_severity.strip():
        return inferred
    current = existing_severity.strip()
    # Upgrade legacy default when a more specific severity is now available.
    if current == DEFAULT_ENTRY_SEVERITY and inferred != DEFAULT_ENTRY_SEVERITY:
        return inferred
    return current


def _resolve_remediation(existing_remediation: object, code: str) -> str:
    inferred = _infer_default_remediation(code=code)
    if not isinstance(existing_remediation, str) or not existing_remediation.strip():
        return inferred
    current = existing_remediation.strip()
    # Upgrade legacy generic remediation to specific code-level guidance.
    if current == DEFAULT_ENTRY_REMEDIATION and inferred != DEFAULT_ENTRY_REMEDIATION:
        return inferred
    return current


def _load_validator_registry_codes(script_file: Path, group_name: str) -> list[str]:
    try:
        namespace = runpy.run_path(str(script_file))
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["VALIDATOR_REGISTRY_LOAD_FAILED"],
            message=f"failed to load validator registry: {script_file}",
            context={
                "group": group_name,
                "path": str(script_file),
                "stage": "validator_registry_loading",
                "exception_type": type(exc).__name__,
                "failure_mode": "system_exit",
                "exit_code": exit_code,
            },
        ) from exc
    except Exception as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["VALIDATOR_REGISTRY_LOAD_FAILED"],
            message=f"failed to load validator registry: {script_file}",
            context={
                "group": group_name,
                "path": str(script_file),
                "stage": "validator_registry_loading",
                "exception_type": type(exc).__name__,
                "failure_mode": "exception",
            },
        ) from exc
    payload = namespace.get("VALIDATOR_ERROR_CODES")
    if not isinstance(payload, dict) or not payload:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["VALIDATOR_REGISTRY_MISSING"],
            message=f"missing VALIDATOR_ERROR_CODES registry: {script_file}",
            context={
                "group": group_name,
                "path": str(script_file),
                "stage": "validator_registry_validation",
                "failure_mode": "missing_registry",
            },
        )

    codes: list[str] = []
    for name, code in payload.items():
        if not isinstance(name, str) or not isinstance(code, str):
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["VALIDATOR_REGISTRY_INVALID"],
                message=f"invalid registry item in {script_file}: {name}={code}",
                context={
                    "group": group_name,
                    "path": str(script_file),
                    "stage": "validator_registry_validation",
                    "failure_mode": "invalid_registry_item",
                    "registry_key": name,
                },
            )
        codes.append(code)
    return sorted(set(codes))


def _load_existing_catalog(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    if not path.exists():
        return {}
    try:
        raw_content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["CATALOG_FILE_READ_FAILED"],
            message=f"failed to read catalog file: {path}",
            context={
                "path": str(path),
                "exception_type": type(exc).__name__,
                "failure_mode": "catalog_file_read_failed",
            },
        ) from exc
    except UnicodeDecodeError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": "existing_catalog", "exception_type": type(exc).__name__},
        ) from exc
    try:
        payload = json.loads(raw_content)
    except JSONDecodeError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": "existing_catalog", "exception_type": type(exc).__name__},
        ) from exc
    if not isinstance(payload, dict):
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
            message=f"catalog payload must be an object: {path}",
            context={"path": str(path), "role": "existing_catalog"},
        )

    catalog: dict[str, dict[str, dict[str, str]]] = {}
    for group_name, group_payload in payload.items():
        if not isinstance(group_name, str) or not isinstance(group_payload, dict):
            continue
        catalog[group_name] = {}
        for code, entry_payload in group_payload.items():
            if not isinstance(code, str):
                continue
            if isinstance(entry_payload, str):
                catalog[group_name][code] = {"description": entry_payload}
                continue
            if not isinstance(entry_payload, dict):
                continue
            entry: dict[str, str] = {}
            for field_name in ("description", "severity", "remediation"):
                field_value = entry_payload.get(field_name)
                if isinstance(field_value, str):
                    entry[field_name] = field_value
            if entry:
                catalog[group_name][code] = entry
    return catalog


def _build_catalog_entry(existing_entry: object, code: str) -> dict[str, str]:
    entry: dict[str, str] = {
        "description": f"TODO: document {code}.",
        "severity": _infer_default_severity(code=code),
        "remediation": _infer_default_remediation(code=code),
    }
    if isinstance(existing_entry, str):
        if existing_entry.strip():
            entry["description"] = existing_entry
        return entry
    if not isinstance(existing_entry, dict):
        return entry

    existing_description = existing_entry.get("description")
    if isinstance(existing_description, str) and existing_description.strip():
        entry["description"] = existing_description

    entry["severity"] = _resolve_severity(existing_severity=existing_entry.get("severity"), code=code)
    entry["remediation"] = _resolve_remediation(existing_remediation=existing_entry.get("remediation"), code=code)
    return entry


def _build_catalog(existing_catalog: dict[str, dict[str, dict[str, str]]]) -> dict[str, dict[str, dict[str, str]]]:
    catalog: dict[str, dict[str, dict[str, str]]] = {}
    for group_name, script_file in VALIDATOR_SCRIPT_FILES.items():
        if not script_file.exists():
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["VALIDATOR_SCRIPT_FILE_NOT_FOUND"],
                message=f"validator script not found: {script_file}",
                context={"group": group_name, "path": str(script_file)},
            )
        codes = _load_validator_registry_codes(script_file=script_file, group_name=group_name)
        existing_group = existing_catalog.get(group_name, {})
        group_catalog: dict[str, dict[str, str]] = {}
        for code in codes:
            group_catalog[code] = _build_catalog_entry(existing_entry=existing_group.get(code), code=code)
        catalog[group_name] = group_catalog
    return catalog


def _render_catalog(catalog: dict[str, dict[str, dict[str, str]]]) -> str:
    return json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"


def _resolve_metadata_overrides_profile(payload: dict, metadata_overrides_profile: str | None, path: Path) -> dict:
    profiles = payload.get("profiles")
    if profiles is None:
        if metadata_overrides_profile is not None:
            selected_profile = metadata_overrides_profile.strip()
            suggested_config_snippet = _build_profile_mode_config_snippet(
                flat_config=payload,
                selected_profile=selected_profile,
            )
            suggested_actions = _build_suggested_actions_for_profile_not_found(
                fallback_reason="no_profiles_config",
                suggested_profiles=[],
                available_profiles=[],
                suggested_command=None,
                suggested_config_snippet=suggested_config_snippet,
            )
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["METADATA_OVERRIDES_PROFILE_NOT_FOUND"],
                message=(
                    f"metadata overrides profile not found: {selected_profile}. "
                    "profile mode is not configured for this overrides config."
                ),
                context={
                    "path": str(path),
                    "metadata_overrides_profile": selected_profile,
                    "available_profiles": [],
                    "fallback_reason": "no_profiles_config",
                    "suggestion_level": "error",
                    "suggested_profiles": [],
                    "suggested_cli_args": None,
                    "suggested_command": None,
                    "suggested_config_snippet": suggested_config_snippet,
                    "suggested_actions": suggested_actions,
                },
            )
        return payload

    if not isinstance(profiles, dict) or not profiles:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
            message=f"invalid metadata overrides profiles payload: {path}",
            context={"path": str(path), "field": "profiles"},
        )

    selected_profile = metadata_overrides_profile or payload.get("default_profile")
    if not isinstance(selected_profile, str) or not selected_profile.strip():
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
            message=f"invalid metadata overrides default_profile: {path}",
            context={"path": str(path), "field": "default_profile"},
        )
    selected_profile = selected_profile.strip()
    profile_payload = profiles.get(selected_profile)
    if not isinstance(profile_payload, dict):
        available_profiles = _build_ordered_available_profiles(
            profiles=profiles,
            default_profile=payload.get("default_profile"),
        )
        (
            message,
            fallback_reason,
            suggestion_level,
            suggested_profiles,
            suggested_cli_args,
            suggested_command,
        ) = _build_profile_suggestion_payload(
            selected_profile=selected_profile,
            available_profiles=available_profiles,
            command_prefix=(
                "python3 scripts/sync-validator-error-codes.py "
                f"--metadata-overrides-file {_shell_quote(path)}"
            ),
            profile_label="metadata overrides profile",
            profile_cli_arg="--metadata-overrides-profile",
        )
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["METADATA_OVERRIDES_PROFILE_NOT_FOUND"],
            message=message,
            context={
                "path": str(path),
                "metadata_overrides_profile": selected_profile,
                "available_profiles": available_profiles,
                "fallback_reason": fallback_reason,
                "suggestion_level": suggestion_level,
                "suggested_profiles": suggested_profiles,
                "suggested_cli_args": suggested_cli_args,
                "suggested_command": suggested_command,
                "suggested_actions": _build_suggested_actions_for_profile_not_found(
                    fallback_reason=fallback_reason,
                    suggested_profiles=suggested_profiles,
                    available_profiles=available_profiles,
                    suggested_command=suggested_command,
                ),
            },
        )
    return profile_payload


def _load_metadata_overrides(
    path: Path,
    metadata_overrides_profile: str | None = None,
) -> dict[str, dict[str, dict[str, str]]]:
    if not path.exists():
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["METADATA_OVERRIDES_FILE_NOT_FOUND"],
            message=f"metadata overrides file not found: {path}",
            context={
                "path": str(path),
                "failure_mode": "metadata_overrides_file_not_found",
            },
        )
    try:
        raw_content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": "metadata_overrides", "exception_type": type(exc).__name__},
        ) from exc
    except OSError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["METADATA_OVERRIDES_FILE_READ_FAILED"],
            message=f"failed to read metadata overrides file: {path}",
            context={
                "path": str(path),
                "exception_type": type(exc).__name__,
                "failure_mode": "metadata_overrides_file_read_failed",
            },
        ) from exc
    try:
        payload = json.loads(raw_content)
    except JSONDecodeError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["JSON_PARSE_ERROR"],
            message=f"failed to parse json: {path}",
            context={"path": str(path), "role": "metadata_overrides", "exception_type": type(exc).__name__},
        ) from exc
    if not isinstance(payload, dict):
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
            message=f"metadata overrides payload must be an object: {path}",
            context={"path": str(path), "role": "metadata_overrides"},
        )
    payload = _resolve_metadata_overrides_profile(
        payload=payload,
        metadata_overrides_profile=metadata_overrides_profile,
        path=path,
    )

    overrides: dict[str, dict[str, dict[str, str]]] = {}
    for group_name, group_payload in payload.items():
        if not isinstance(group_name, str) or not isinstance(group_payload, dict):
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
                message=f"invalid override group payload: {group_name}",
                context={"group": group_name},
            )
        overrides[group_name] = {}
        for code, code_payload in group_payload.items():
            if not isinstance(code, str) or not isinstance(code_payload, dict):
                raise SyncValidatorErrorCodesError(
                    code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
                    message=f"invalid override code payload: {group_name}.{code}",
                    context={"group": group_name, "code": code},
                )
            entry_override: dict[str, str] = {}
            for field_name, field_value in code_payload.items():
                if field_name not in ALLOWED_OVERRIDE_FIELDS:
                    raise SyncValidatorErrorCodesError(
                        code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
                        message=f"invalid override field: {group_name}.{code}.{field_name}",
                        context={"group": group_name, "code": code, "field": field_name},
                    )
                if not isinstance(field_value, str) or not field_value.strip():
                    raise SyncValidatorErrorCodesError(
                        code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
                        message=f"invalid override value: {group_name}.{code}.{field_name}",
                        context={"group": group_name, "code": code, "field": field_name},
                    )
                normalized_value = field_value.strip()
                if field_name == "severity" and normalized_value not in VALID_SEVERITY_LEVELS:
                    raise SyncValidatorErrorCodesError(
                        code=SYNC_ERROR_CODES["PAYLOAD_INVALID"],
                        message=f"invalid override severity: {group_name}.{code}.{normalized_value}",
                        context={"group": group_name, "code": code, "field": field_name},
                    )
                entry_override[field_name] = normalized_value
            if entry_override:
                overrides[group_name][code] = entry_override
    return overrides


def _apply_metadata_overrides(
    catalog: dict[str, dict[str, dict[str, str]]],
    overrides: dict[str, dict[str, dict[str, str]]],
) -> dict[str, dict[str, dict[str, str]]]:
    for group_name, group_payload in overrides.items():
        if group_name not in catalog:
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["UNKNOWN_OVERRIDE_GROUP"],
                message=f"unknown override group: {group_name}",
                context={"group": group_name},
            )
        for code, entry_override in group_payload.items():
            if code not in catalog[group_name]:
                raise SyncValidatorErrorCodesError(
                    code=SYNC_ERROR_CODES["UNKNOWN_OVERRIDE_CODE"],
                    message=f"unknown override code: {group_name}.{code}",
                    context={"group": group_name, "code": code},
                )
            catalog[group_name][code].update(entry_override)
    return catalog


def _load_placeholder_markers(path: Path) -> list[str]:
    if not path.exists():
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_FILE_NOT_FOUND"],
            message=f"placeholder markers file not found: {path}",
            context={
                "path": str(path),
                "failure_mode": "placeholder_markers_file_not_found",
            },
        )
    try:
        raw_content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
            message=f"failed to parse placeholder markers json: {path}",
            context={"path": str(path), "exception_type": type(exc).__name__},
        ) from exc
    except OSError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_READ_FAILED"],
            message=f"failed to read placeholder markers file: {path}",
            context={
                "path": str(path),
                "exception_type": type(exc).__name__,
                "failure_mode": "placeholder_markers_file_read_failed",
            },
        ) from exc
    try:
        payload = json.loads(raw_content)
    except JSONDecodeError as exc:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
            message=f"failed to parse placeholder markers json: {path}",
            context={"path": str(path), "exception_type": type(exc).__name__},
        ) from exc
    if not isinstance(payload, dict):
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
            message=f"placeholder markers payload must be an object: {path}",
            context={"path": str(path)},
        )
    markers = payload.get("markers")
    if not isinstance(markers, list) or not markers:
        raise SyncValidatorErrorCodesError(
            code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
            message=f"placeholder markers payload must include non-empty markers list: {path}",
            context={"path": str(path)},
        )

    normalized: list[str] = []
    seen: set[str] = set()
    for marker in markers:
        if not isinstance(marker, str):
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
                message=f"placeholder marker must be string: {marker}",
                context={"path": str(path), "marker": marker},
            )
        marker_value = marker.strip().upper()
        if not marker_value:
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
                message="placeholder marker cannot be empty",
                context={"path": str(path)},
            )
        if marker_value in seen:
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["PLACEHOLDER_MARKERS_INVALID"],
                message=f"duplicate marker detected: {marker_value}",
                context={"path": str(path), "marker": marker_value},
            )
        seen.add(marker_value)
        normalized.append(marker_value)
    return normalized


def _build_placeholder_pattern(markers: list[str]) -> re.Pattern[str]:
    escaped_markers = [re.escape(marker) for marker in markers]
    return re.compile(r"^\s*(" + "|".join(escaped_markers) + r")\s*:", re.IGNORECASE)


def _collect_placeholder_violations(
    catalog: dict[str, dict[str, dict[str, str]]],
    placeholder_pattern: re.Pattern[str],
) -> list[tuple[str, str, str, str, str]]:
    violations: list[tuple[str, str, str, str, str]] = []
    for group_name, group_payload in catalog.items():
        for code, entry_payload in group_payload.items():
            for field_name in ("description", "remediation"):
                field_value = entry_payload.get(field_name)
                if not isinstance(field_value, str):
                    continue
                match = placeholder_pattern.match(field_value)
                if match is None:
                    continue
                marker = match.group(1).upper()
                violations.append((group_name, code, field_name, marker, field_value.strip()))
    return sorted(violations, key=lambda item: (item[0], item[1], item[2]))


def _format_placeholder_error(
    violations: list[tuple[str, str, str, str, str]],
    markers: list[str],
) -> str:
    lines = [
        "[sync-validator-error-codes] placeholder descriptions are not allowed.",
        "[sync-validator-error-codes] markers: " + ", ".join(markers),
        "[sync-validator-error-codes] violations:",
    ]
    for group_name, code, field_name, marker, value in violations:
        lines.append(f"[sync-validator-error-codes] - {group_name}.{code}.{field_name} ({marker}) -> {value}")
    lines.append(
        "[sync-validator-error-codes] remediation: replace placeholder prefix with concrete user-facing description."
    )
    return "\n".join(lines)


def _build_placeholder_violations_context(
    violations: list[tuple[str, str, str, str, str]],
) -> list[dict[str, str]]:
    context_violations: list[dict[str, str]] = []
    for group_name, code, field_name, marker, value in violations:
        context_violations.append(
            {
                "group": group_name,
                "code": code,
                "field": field_name,
                "marker": marker,
                "value": value,
            }
        )
    return context_violations


def main() -> int:
    argv = sys.argv[1:]
    json_errors_requested = "--json-errors" in argv
    parser = argparse.ArgumentParser(
        description="Sync validator error code catalog from validator script registries.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Output catalog file path.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode. Return non-zero if output file is not in sync.",
    )
    parser.add_argument(
        "--placeholder-markers-file",
        type=Path,
        default=DEFAULT_PLACEHOLDER_MARKERS_FILE,
        help="Path to placeholder marker config JSON file.",
    )
    parser.add_argument(
        "--strict-descriptions",
        action="store_true",
        help="Fail if any catalog description is a TODO placeholder.",
    )
    parser.add_argument(
        "--metadata-overrides-file",
        type=Path,
        default=DEFAULT_METADATA_OVERRIDES_FILE,
        help="Path to metadata overrides JSON file.",
    )
    parser.add_argument(
        "--metadata-overrides-profile",
        type=str,
        default=None,
        help="Optional overrides profile name when metadata overrides config contains profiles.",
    )
    parser.add_argument(
        "--json-errors",
        action="store_true",
        help="Emit structured JSON errors to stderr.",
    )
    if json_errors_requested:
        parse_stderr = io.StringIO()
        try:
            with redirect_stderr(parse_stderr):
                args, unknown_args = parser.parse_known_args(argv)
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 1
            if exit_code == 0:
                return 0
            parse_message = f"argument parsing failed: {exc}"
            parse_error_output = parse_stderr.getvalue().strip()
            if parse_error_output:
                parse_message = parse_error_output.splitlines()[-1]
                parse_error_prefix = f"{parser.prog}: error: "
                if parse_message.startswith(parse_error_prefix):
                    parse_message = parse_message[len(parse_error_prefix) :]
            payload = {
                "validator": "sync-validator-error-codes",
                "code": SYNC_ERROR_CODES["UNEXPECTED_ERROR"],
                "message": parse_message,
                "context": {
                    "stage": "argument_parsing",
                    "exception_type": type(exc).__name__,
                    "exit_code": exit_code,
                    "argv": argv,
                    "unknown_args": [],
                },
            }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
            return 1
    else:
        args, unknown_args = parser.parse_known_args(argv)
    if unknown_args:
        message = f"unrecognized arguments: {' '.join(unknown_args)}"
        if json_errors_requested:
            payload = {
                "validator": "sync-validator-error-codes",
                "code": SYNC_ERROR_CODES["UNEXPECTED_ERROR"],
                "message": message,
                "context": {
                    "stage": "argument_parsing",
                    "exception_type": "SystemExit",
                    "exit_code": 2,
                    "argv": argv,
                    "unknown_args": unknown_args,
                },
            }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
            return 1
        parser.error(message)
    env_overrides_profile = os.getenv(METADATA_OVERRIDES_PROFILE_ENV_VAR)
    effective_overrides_profile = (
        args.metadata_overrides_profile if args.metadata_overrides_profile is not None else env_overrides_profile
    )

    try:
        existing_catalog = _load_existing_catalog(path=args.output_file)
        generated_catalog = _build_catalog(existing_catalog=existing_catalog)
        metadata_overrides = _load_metadata_overrides(
            path=args.metadata_overrides_file,
            metadata_overrides_profile=effective_overrides_profile,
        )
        generated_catalog = _apply_metadata_overrides(catalog=generated_catalog, overrides=metadata_overrides)
        generated_content = _render_catalog(catalog=generated_catalog)
        placeholder_markers: list[str] = []
        placeholder_pattern: re.Pattern[str] | None = None
        if args.strict_descriptions:
            placeholder_markers = _load_placeholder_markers(path=args.placeholder_markers_file)
            placeholder_pattern = _build_placeholder_pattern(markers=placeholder_markers)

        if args.check:
            if not args.output_file.exists():
                if args.json_errors:
                    raise SyncValidatorErrorCodesError(
                        code=SYNC_ERROR_CODES["CATALOG_FILE_NOT_FOUND"],
                        message=f"catalog file not found: {args.output_file}",
                        context={"path": str(args.output_file)},
                    )
                print(f"[sync-validator-error-codes] catalog file not found: {args.output_file}", file=sys.stderr)
                return 1
            existing_content = args.output_file.read_text(encoding="utf-8")
            if existing_content != generated_content:
                if args.json_errors:
                    raise SyncValidatorErrorCodesError(
                        code=SYNC_ERROR_CODES["CATALOG_NOT_IN_SYNC"],
                        message=f"catalog is not in sync: {args.output_file}",
                        context={"path": str(args.output_file)},
                    )
                print(f"[sync-validator-error-codes] catalog is not in sync: {args.output_file}", file=sys.stderr)
                return 1
            if args.strict_descriptions:
                assert placeholder_pattern is not None
                violations = _collect_placeholder_violations(
                    catalog=generated_catalog,
                    placeholder_pattern=placeholder_pattern,
                )
                if violations:
                    if args.json_errors:
                        raise SyncValidatorErrorCodesError(
                            code=SYNC_ERROR_CODES["PLACEHOLDER_TEXT_DETECTED"],
                            message="placeholder descriptions are not allowed.",
                            context={
                                "markers": placeholder_markers,
                                "violations": _build_placeholder_violations_context(violations=violations),
                            },
                        )
                    print(_format_placeholder_error(violations=violations, markers=placeholder_markers), file=sys.stderr)
                    return 1
            print(f"[sync-validator-error-codes] catalog is in sync: {args.output_file}")
            return 0

        try:
            args.output_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["OUTPUT_PARENT_CREATE_FAILED"],
                message=f"failed to create output parent directory: {args.output_file.parent}",
                context={
                    "path": str(args.output_file),
                    "parent": str(args.output_file.parent),
                    "exception_type": type(exc).__name__,
                },
            ) from exc
        if args.strict_descriptions:
            assert placeholder_pattern is not None
            violations = _collect_placeholder_violations(
                catalog=generated_catalog,
                placeholder_pattern=placeholder_pattern,
            )
            if violations:
                if args.json_errors:
                    raise SyncValidatorErrorCodesError(
                        code=SYNC_ERROR_CODES["PLACEHOLDER_TEXT_DETECTED"],
                        message="placeholder descriptions are not allowed.",
                        context={
                            "markers": placeholder_markers,
                            "violations": _build_placeholder_violations_context(violations=violations),
                        },
                    )
                print(_format_placeholder_error(violations=violations, markers=placeholder_markers), file=sys.stderr)
                return 1
        try:
            args.output_file.write_text(generated_content, encoding="utf-8")
        except OSError as exc:
            raise SyncValidatorErrorCodesError(
                code=SYNC_ERROR_CODES["OUTPUT_WRITE_FAILED"],
                message=f"failed to write output file: {args.output_file}",
                context={"path": str(args.output_file), "exception_type": type(exc).__name__},
            ) from exc
        print(f"[sync-validator-error-codes] catalog updated: {args.output_file}")
        return 0
    except Exception as exc:
        if args.json_errors:
            if isinstance(exc, SyncValidatorErrorCodesError):
                payload = {
                    "validator": "sync-validator-error-codes",
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": "sync-validator-error-codes",
                    "code": SYNC_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {
                        "stage": "runtime",
                        "exception_type": type(exc).__name__,
                        "exit_code": 1,
                        "argv": argv,
                        "unknown_args": [],
                    },
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[sync-validator-error-codes] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
