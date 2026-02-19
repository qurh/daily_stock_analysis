#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import runpy
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_FILE = BACKEND_ROOT / "config" / "validator-error-codes.json"
DEFAULT_PLACEHOLDER_MARKERS_FILE = BACKEND_ROOT / "config" / "validator-placeholder-markers.json"
DEFAULT_METADATA_OVERRIDES_FILE = BACKEND_ROOT / "config" / "validator-error-code-metadata-overrides.json"
VALIDATOR_SCRIPT_FILES = {
    "summary_schema": BACKEND_ROOT / "scripts" / "validate-strict-gate-summary-schema.py",
    "summary_contract": BACKEND_ROOT / "scripts" / "validate-summary-contract-changelog.py",
    "placeholder_markers": BACKEND_ROOT / "scripts" / "validate-validator-placeholder-markers.py",
}
ALLOWED_OVERRIDE_FIELDS = {"description", "severity", "remediation"}
VALID_SEVERITY_LEVELS = {"info", "warning", "error", "critical"}
DEFAULT_ENTRY_SEVERITY = "error"
DEFAULT_ENTRY_REMEDIATION = "Review validator output and update configuration or input data for this error."


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


def _load_validator_registry_codes(script_file: Path) -> list[str]:
    namespace = runpy.run_path(str(script_file))
    payload = namespace.get("VALIDATOR_ERROR_CODES")
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"missing VALIDATOR_ERROR_CODES registry: {script_file}")

    codes: list[str] = []
    for name, code in payload.items():
        if not isinstance(name, str) or not isinstance(code, str):
            raise ValueError(f"invalid registry item in {script_file}: {name}={code}")
        codes.append(code)
    return sorted(set(codes))


def _load_existing_catalog(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"catalog payload must be an object: {path}")

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
            raise FileNotFoundError(f"validator script not found: {script_file}")
        codes = _load_validator_registry_codes(script_file=script_file)
        existing_group = existing_catalog.get(group_name, {})
        group_catalog: dict[str, dict[str, str]] = {}
        for code in codes:
            group_catalog[code] = _build_catalog_entry(existing_entry=existing_group.get(code), code=code)
        catalog[group_name] = group_catalog
    return catalog


def _render_catalog(catalog: dict[str, dict[str, dict[str, str]]]) -> str:
    return json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"


def _load_metadata_overrides(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(f"metadata overrides file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"metadata overrides payload must be an object: {path}")

    overrides: dict[str, dict[str, dict[str, str]]] = {}
    for group_name, group_payload in payload.items():
        if not isinstance(group_name, str) or not isinstance(group_payload, dict):
            raise ValueError(f"invalid override group payload: {group_name}")
        overrides[group_name] = {}
        for code, code_payload in group_payload.items():
            if not isinstance(code, str) or not isinstance(code_payload, dict):
                raise ValueError(f"invalid override code payload: {group_name}.{code}")
            entry_override: dict[str, str] = {}
            for field_name, field_value in code_payload.items():
                if field_name not in ALLOWED_OVERRIDE_FIELDS:
                    raise ValueError(f"invalid override field: {group_name}.{code}.{field_name}")
                if not isinstance(field_value, str) or not field_value.strip():
                    raise ValueError(f"invalid override value: {group_name}.{code}.{field_name}")
                normalized_value = field_value.strip()
                if field_name == "severity" and normalized_value not in VALID_SEVERITY_LEVELS:
                    raise ValueError(f"invalid override severity: {group_name}.{code}.{normalized_value}")
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
            raise ValueError(f"unknown override group: {group_name}")
        for code, entry_override in group_payload.items():
            if code not in catalog[group_name]:
                raise ValueError(f"unknown override code: {group_name}.{code}")
            catalog[group_name][code].update(entry_override)
    return catalog


def _load_placeholder_markers(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"placeholder markers file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    markers = payload.get("markers")
    if not isinstance(markers, list) or not markers:
        raise ValueError(f"placeholder markers payload must include non-empty markers list: {path}")

    normalized: list[str] = []
    seen: set[str] = set()
    for marker in markers:
        if not isinstance(marker, str):
            raise ValueError(f"placeholder marker must be string: {marker}")
        marker_value = marker.strip().upper()
        if not marker_value:
            raise ValueError("placeholder marker cannot be empty")
        if marker_value in seen:
            raise ValueError(f"duplicate marker detected: {marker_value}")
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


def main() -> int:
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
    args = parser.parse_args()

    try:
        existing_catalog = _load_existing_catalog(path=args.output_file)
        generated_catalog = _build_catalog(existing_catalog=existing_catalog)
        metadata_overrides = _load_metadata_overrides(path=args.metadata_overrides_file)
        generated_catalog = _apply_metadata_overrides(catalog=generated_catalog, overrides=metadata_overrides)
        generated_content = _render_catalog(catalog=generated_catalog)
        placeholder_markers: list[str] = []
        placeholder_pattern: re.Pattern[str] | None = None
        if args.strict_descriptions:
            placeholder_markers = _load_placeholder_markers(path=args.placeholder_markers_file)
            placeholder_pattern = _build_placeholder_pattern(markers=placeholder_markers)

        if args.check:
            if not args.output_file.exists():
                print(
                    f"[sync-validator-error-codes] catalog file not found: {args.output_file}",
                    file=sys.stderr,
                )
                return 1
            existing_content = args.output_file.read_text(encoding="utf-8")
            if existing_content != generated_content:
                print(
                    f"[sync-validator-error-codes] catalog is not in sync: {args.output_file}",
                    file=sys.stderr,
                )
                return 1
            if args.strict_descriptions:
                assert placeholder_pattern is not None
                violations = _collect_placeholder_violations(
                    catalog=generated_catalog,
                    placeholder_pattern=placeholder_pattern,
                )
                if violations:
                    print(
                        _format_placeholder_error(violations=violations, markers=placeholder_markers),
                        file=sys.stderr,
                    )
                    return 1
            print(f"[sync-validator-error-codes] catalog is in sync: {args.output_file}")
            return 0

        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        if args.strict_descriptions:
            assert placeholder_pattern is not None
            violations = _collect_placeholder_violations(
                catalog=generated_catalog,
                placeholder_pattern=placeholder_pattern,
            )
            if violations:
                print(
                    _format_placeholder_error(violations=violations, markers=placeholder_markers),
                    file=sys.stderr,
                )
                return 1
        args.output_file.write_text(generated_content, encoding="utf-8")
        print(f"[sync-validator-error-codes] catalog updated: {args.output_file}")
        return 0
    except Exception as exc:
        print(f"[sync-validator-error-codes] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
