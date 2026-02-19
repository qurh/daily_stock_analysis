#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_FILE = BACKEND_ROOT / "config" / "validator-error-codes.json"
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
    args = parser.parse_args()

    try:
        existing_catalog = _load_existing_catalog(path=args.output_file)
        generated_catalog = _build_catalog(existing_catalog=existing_catalog)
        generated_content = _render_catalog(catalog=generated_catalog)

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
            print(f"[sync-validator-error-codes] catalog is in sync: {args.output_file}")
            return 0

        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(generated_content, encoding="utf-8")
        print(f"[sync-validator-error-codes] catalog updated: {args.output_file}")
        return 0
    except Exception as exc:
        print(f"[sync-validator-error-codes] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
