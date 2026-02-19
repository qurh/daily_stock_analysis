#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MARKERS_FILE = BACKEND_ROOT / "config" / "validator-placeholder-markers.json"
MARKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]*$")


def _load_payload(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("markers payload must be an object")
    return payload


def _validate_markers(payload: dict) -> list[str]:
    markers = payload.get("markers")
    if not isinstance(markers, list) or not markers:
        raise ValueError("markers payload must include non-empty markers list")

    normalized_markers: list[str] = []
    seen: set[str] = set()
    for raw_marker in markers:
        if not isinstance(raw_marker, str):
            raise ValueError(f"marker must be a string: {raw_marker}")
        marker = raw_marker.strip().upper()
        if not marker:
            raise ValueError("marker cannot be empty")
        if marker in seen:
            raise ValueError(f"duplicate marker detected: {marker}")
        if MARKER_PATTERN.match(marker) is None:
            raise ValueError(f"invalid marker format: {marker}")
        seen.add(marker)
        normalized_markers.append(marker)
    return normalized_markers


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate placeholder markers config for validator strict descriptions."
    )
    parser.add_argument(
        "--markers-file",
        type=Path,
        default=DEFAULT_MARKERS_FILE,
        help="Path to placeholder markers config file.",
    )
    args = parser.parse_args()

    try:
        if not args.markers_file.exists():
            raise FileNotFoundError(f"markers file not found: {args.markers_file}")
        payload = _load_payload(path=args.markers_file)
        _validate_markers(payload=payload)
        print(f"[validate-validator-placeholder-markers] markers config is valid: {args.markers_file}")
        return 0
    except Exception as exc:
        print(f"[validate-validator-placeholder-markers] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
