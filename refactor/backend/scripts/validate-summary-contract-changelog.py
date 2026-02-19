#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_FILE = BACKEND_ROOT / "config" / "schemas" / "strict-gate-summary.schema.json"
DEFAULT_CHANGELOG_FILE = BACKEND_ROOT.parent / "docs" / "CHANGELOG.md"
DEFAULT_APP_FILE = BACKEND_ROOT / "src" / "app" / "main.py"

APP_VERSION_PATTERN = re.compile(r'version="([^"]+)"')
CHANGELOG_ENTRY_PATTERN = re.compile(r"^## \[([^\]]+)\].*$", re.MULTILINE)


def _extract_app_version(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    match = APP_VERSION_PATTERN.search(content)
    if match is None:
        raise ValueError(f"unable to locate app version in file: {path}")
    return match.group(1)


def _extract_schema_version(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("schema missing 'properties' object")
    schema_version = properties.get("schema_version")
    if not isinstance(schema_version, dict):
        raise ValueError("schema missing 'properties.schema_version' object")
    schema_version_const = schema_version.get("const")
    if not isinstance(schema_version_const, str):
        raise ValueError("schema missing 'properties.schema_version.const' string")
    return schema_version_const


def _extract_latest_changelog_entry(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8")
    first_match = CHANGELOG_ENTRY_PATTERN.search(content)
    if first_match is None:
        raise ValueError("unable to locate latest changelog entry")
    latest_version = first_match.group(1)
    next_match = CHANGELOG_ENTRY_PATTERN.search(content, first_match.end())
    section_end = next_match.start() if next_match is not None else len(content)
    latest_section = content[first_match.end() : section_end]
    return latest_version, latest_section


def _validate_summary_schema_note(latest_section: str, schema_version: str) -> None:
    note_pattern = re.compile(
        rf"Summary schema version:\s*[`\"']?{re.escape(schema_version)}[`\"']?",
        re.IGNORECASE,
    )
    if note_pattern.search(latest_section) is None:
        raise ValueError("missing summary schema version note in latest changelog entry")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate strict gate summary contract changelog linkage.")
    parser.add_argument("--schema-file", type=Path, default=DEFAULT_SCHEMA_FILE, help="Path to summary schema file.")
    parser.add_argument("--changelog-file", type=Path, default=DEFAULT_CHANGELOG_FILE, help="Path to changelog file.")
    parser.add_argument("--app-file", type=Path, default=DEFAULT_APP_FILE, help="Path to app file with version field.")
    args = parser.parse_args()

    for path in (args.schema_file, args.changelog_file, args.app_file):
        if not path.exists():
            raise FileNotFoundError(f"required file not found: {path}")

    app_version = _extract_app_version(path=args.app_file)
    schema_version = _extract_schema_version(path=args.schema_file)
    changelog_version, latest_section = _extract_latest_changelog_entry(path=args.changelog_file)

    if changelog_version != app_version:
        raise ValueError(f"changelog/app version mismatch: changelog={changelog_version}, app={app_version}")

    _validate_summary_schema_note(latest_section=latest_section, schema_version=schema_version)
    print(f"[validate-summary-contract-changelog] contract changelog is valid: {args.changelog_file}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[validate-summary-contract-changelog] {exc}", file=sys.stderr)
        sys.exit(1)
