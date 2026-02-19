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
VALIDATOR_SCRIPT_FILES = {
    "summary_schema": BACKEND_ROOT / "scripts" / "validate-strict-gate-summary-schema.py",
    "summary_contract": BACKEND_ROOT / "scripts" / "validate-summary-contract-changelog.py",
}


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


def _load_existing_catalog(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"catalog payload must be an object: {path}")

    catalog: dict[str, dict[str, str]] = {}
    for group_name, group_payload in payload.items():
        if not isinstance(group_name, str) or not isinstance(group_payload, dict):
            continue
        catalog[group_name] = {}
        for code, description in group_payload.items():
            if isinstance(code, str) and isinstance(description, str):
                catalog[group_name][code] = description
    return catalog


def _build_catalog(existing_catalog: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    catalog: dict[str, dict[str, str]] = {}
    for group_name, script_file in VALIDATOR_SCRIPT_FILES.items():
        if not script_file.exists():
            raise FileNotFoundError(f"validator script not found: {script_file}")
        codes = _load_validator_registry_codes(script_file=script_file)
        existing_group = existing_catalog.get(group_name, {})
        group_catalog: dict[str, str] = {}
        for code in codes:
            existing_description = existing_group.get(code)
            if isinstance(existing_description, str) and existing_description.strip():
                group_catalog[code] = existing_description
            else:
                group_catalog[code] = f"TODO: document {code}."
        catalog[group_name] = group_catalog
    return catalog


def _render_catalog(catalog: dict[str, dict[str, str]]) -> str:
    return json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"


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
            continue
        seen.add(marker_value)
        normalized.append(marker_value)
    return normalized


def _build_placeholder_pattern(markers: list[str]) -> re.Pattern[str]:
    escaped_markers = [re.escape(marker) for marker in markers]
    return re.compile(r"^\s*(" + "|".join(escaped_markers) + r")\s*:", re.IGNORECASE)


def _collect_placeholder_violations(
    catalog: dict[str, dict[str, str]],
    placeholder_pattern: re.Pattern[str],
) -> list[tuple[str, str, str, str]]:
    violations: list[tuple[str, str, str, str]] = []
    for group_name, group_payload in catalog.items():
        for code, description in group_payload.items():
            match = placeholder_pattern.match(description)
            if match is None:
                continue
            marker = match.group(1).upper()
            violations.append((group_name, code, marker, description.strip()))
    return sorted(violations, key=lambda item: (item[0], item[1]))


def _format_placeholder_error(
    violations: list[tuple[str, str, str, str]],
    markers: list[str],
) -> str:
    lines = [
        "[sync-validator-error-codes] placeholder descriptions are not allowed.",
        "[sync-validator-error-codes] markers: " + ", ".join(markers),
        "[sync-validator-error-codes] violations:",
    ]
    for group_name, code, marker, description in violations:
        lines.append(f"[sync-validator-error-codes] - {group_name}.{code} ({marker}) -> {description}")
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
    args = parser.parse_args()

    try:
        existing_catalog = _load_existing_catalog(path=args.output_file)
        generated_catalog = _build_catalog(existing_catalog=existing_catalog)
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
