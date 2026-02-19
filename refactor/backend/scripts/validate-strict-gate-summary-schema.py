#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from json import JSONDecodeError
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "strict-gate-summary.schema.json"
DEFAULT_SYNC_SCRIPT_FILE = BACKEND_ROOT / "scripts" / "sync-strict-gate-alert-thresholds.py"
EXPECTED_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
SUMMARY_SCHEMA_VERSION_PATTERN = re.compile(r'^SUMMARY_SCHEMA_VERSION\s*=\s*"([^"]+)"\s*$')


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise ValueError(f"failed to parse json: {path}") from exc


def _validate_contract(schema: dict) -> None:
    if schema.get("$schema") != EXPECTED_SCHEMA_DRAFT:
        raise ValueError(f"invalid $schema value, expected: {EXPECTED_SCHEMA_DRAFT}")
    required_fields = {
        "schema_version",
        "changed_files_count",
        "total_added_lines",
        "total_removed_lines",
        "files",
        "modules",
    }
    required = schema.get("required")
    if not isinstance(required, list):
        raise ValueError("schema field 'required' must be a list")
    missing = sorted(required_fields.difference(set(required)))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"schema missing required fields: {missing_text}")


def _extract_sync_summary_schema_version(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SUMMARY_SCHEMA_VERSION_PATTERN.match(line.strip())
        if match is not None:
            return match.group(1)
    raise ValueError(f"missing SUMMARY_SCHEMA_VERSION in sync script: {path}")


def _extract_schema_payload_version(schema: dict) -> str:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("schema field 'properties' must be an object")
    schema_version_field = properties.get("schema_version")
    if not isinstance(schema_version_field, dict):
        raise ValueError("schema field 'properties.schema_version' must be an object")
    schema_version_const = schema_version_field.get("const")
    if not isinstance(schema_version_const, str):
        raise ValueError("schema field 'properties.schema_version.const' must be a string")
    return schema_version_const


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate strict gate summary JSON schema.")
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to strict gate summary schema JSON file.",
    )
    parser.add_argument(
        "--sync-script-file",
        type=Path,
        default=DEFAULT_SYNC_SCRIPT_FILE,
        help="Path to sync-strict-gate-alert-thresholds.py for SUMMARY_SCHEMA_VERSION check.",
    )
    args = parser.parse_args()

    if not args.schema_file.exists():
        raise FileNotFoundError(f"schema file not found: {args.schema_file}")
    if not args.sync_script_file.exists():
        raise FileNotFoundError(f"sync script file not found: {args.sync_script_file}")

    schema = _load_json(path=args.schema_file)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ValueError(f"invalid json schema: {args.schema_file}") from exc

    _validate_contract(schema=schema)
    schema_version = _extract_schema_payload_version(schema=schema)
    sync_summary_schema_version = _extract_sync_summary_schema_version(path=args.sync_script_file)
    if schema_version != sync_summary_schema_version:
        raise ValueError(f"schema_version mismatch: schema={schema_version}, sync_script={sync_summary_schema_version}")
    print(f"[validate-strict-gate-summary-schema] schema is valid: {args.schema_file}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[validate-strict-gate-summary-schema] {exc}", file=sys.stderr)
        sys.exit(1)
