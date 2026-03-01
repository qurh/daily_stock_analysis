#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_DIR = BACKEND_ROOT / "monitoring" / "prometheus" / "rules"
DEFAULT_ALERTMANAGER_FILE = BACKEND_ROOT / "monitoring" / "alertmanager" / "refactor-alertmanager-routing.yml"
VALIDATOR_NAME = "validate-alertmanager-route-consistency"

MATCHER_PATTERN = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(=~|!~|!=|=)\s*"([^"]*)"\s*$')
REQUIRED_ALERT_LABELS = ("scope", "domain", "severity")
SUPPORTED_MATCHER_OPERATORS = ("=", "!=", "=~", "!~")
RouteMatcher = tuple[str, str, str]
VALIDATOR_ERROR_CODES = {
    "FILE_NOT_FOUND": "alertmanager_route_consistency_file_not_found",
    "YAML_PARSE_ERROR": "alertmanager_route_consistency_yaml_parse_error",
    "MATCHER_FORMAT_INVALID": "alertmanager_route_consistency_matcher_format_invalid",
    "INVALID_REGEX_MATCHER": "alertmanager_route_consistency_invalid_regex_matcher",
    "RULES_DIR_INVALID": "alertmanager_route_consistency_rules_dir_invalid",
    "NO_RULE_FILES": "alertmanager_route_consistency_no_rule_files",
    "NO_ALERTS": "alertmanager_route_consistency_no_alerts",
    "NO_EXPLICIT_ROUTES": "alertmanager_route_consistency_no_explicit_routes",
    "SHADOWED_ROUTE": "alertmanager_route_consistency_shadowed_route",
    "UNMATCHED_ALERT": "alertmanager_route_consistency_unmatched_alert",
    "AMBIGUOUS_ALERT": "alertmanager_route_consistency_ambiguous_alert",
    "CLI_ARGS_INVALID": "alertmanager_route_consistency_cli_args_invalid",
    "UNEXPECTED_ERROR": "alertmanager_route_consistency_unexpected_error",
}


class AlertmanagerRouteConsistencyValidationError(ValueError):
    def __init__(self, code: str, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class _AlertmanagerArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: {message}",
            context={"failure_mode": "argparse_error", "argparse_message": message},
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _AlertmanagerArgumentParser(
        description="Validate every prometheus alert labels tuple is covered by an explicit alertmanager route."
    )
    parser.add_argument(
        "--rules-dir",
        type=Path,
        default=DEFAULT_RULES_DIR,
        help="Directory containing prometheus alert rule files.",
    )
    parser.add_argument(
        "--alertmanager-file",
        type=Path,
        default=DEFAULT_ALERTMANAGER_FILE,
        help="Path to alertmanager routing yaml file.",
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
    except AlertmanagerRouteConsistencyValidationError as exc:
        context = dict(exc.context)
        context.setdefault("argv", list(argv))
        raise AlertmanagerRouteConsistencyValidationError(
            code=exc.code,
            message=str(exc),
            context=context,
        ) from exc
    if unknown_args:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"],
            message=f"invalid cli arguments: unrecognized arguments: {' '.join(unknown_args)}",
            context={"failure_mode": "unknown_args", "unknown_args": unknown_args, "argv": list(argv)},
        )
    return args


def _load_yaml_file(path: Path) -> Any:
    if not path.exists():
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["FILE_NOT_FOUND"],
            message=f"required file not found: {path}",
            context={"path": str(path)},
        )
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["YAML_PARSE_ERROR"],
            message=f"yaml parse failed: {path}: {exc}",
            context={"path": str(path)},
        ) from exc


def _collect_alerts(rule_files: list[Path]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for rule_file in rule_files:
        payload = _load_yaml_file(rule_file)
        if payload is None:
            continue
        if not isinstance(payload, dict):
            raise ValueError(f"rule payload must be object: {rule_file}")
        groups = payload.get("groups")
        if not isinstance(groups, list):
            raise ValueError(f"rule payload missing groups list: {rule_file}")

        for group in groups:
            if not isinstance(group, dict):
                raise ValueError(f"rule group must be object: {rule_file}")
            rules = group.get("rules")
            if not isinstance(rules, list):
                continue
            for rule in rules:
                if not isinstance(rule, dict):
                    raise ValueError(f"rule item must be object: {rule_file}")
                alert_name = rule.get("alert")
                labels = rule.get("labels")
                if not isinstance(alert_name, str):
                    continue
                if not isinstance(labels, dict):
                    raise ValueError(f"alert labels must be object: alert={alert_name} file={rule_file}")
                normalized_labels: dict[str, str] = {}
                for label_key in REQUIRED_ALERT_LABELS:
                    value = labels.get(label_key)
                    if not isinstance(value, str) or not value:
                        raise ValueError(
                            f"alert label missing/invalid: alert={alert_name} label={label_key} file={rule_file}"
                        )
                    normalized_labels[label_key] = value
                alerts.append(
                    {
                        "alert": alert_name,
                        "labels": normalized_labels,
                        "source_file": str(rule_file),
                    }
                )
    return alerts


def _extract_matchers(route: dict[str, Any], path: str) -> list[RouteMatcher]:
    result: list[RouteMatcher] = []

    exact_match = route.get("match")
    if exact_match is not None:
        if not isinstance(exact_match, dict):
            raise ValueError(f"route.match must be object: {path}")
        for key, value in exact_match.items():
            if not isinstance(key, str):
                raise ValueError(f"route.match key must be string: {path}")
            if not isinstance(value, (str, int, float)):
                raise ValueError(f"route.match value must be scalar: {path} key={key}")
            result.append((key, "=", str(value)))

    matcher_list = route.get("matchers")
    if matcher_list is not None:
        if not isinstance(matcher_list, list):
            raise ValueError(f"route.matchers must be list: {path}")
        for matcher in matcher_list:
            if not isinstance(matcher, str):
                raise ValueError(f"route matcher must be string: {path}")
            parsed = MATCHER_PATTERN.match(matcher)
            if parsed is None:
                raise AlertmanagerRouteConsistencyValidationError(
                    code=VALIDATOR_ERROR_CODES["MATCHER_FORMAT_INVALID"],
                    message=(
                        "unsupported matcher format "
                        f"(expected key<op>\"value\", <op> in {SUPPORTED_MATCHER_OPERATORS}): "
                        f"{path} matcher={matcher}"
                    ),
                    context={"path": path, "matcher": matcher},
                )
            key, operator, value = parsed.group(1), parsed.group(2), parsed.group(3)
            if operator in {"=~", "!~"}:
                try:
                    re.compile(value)
                except re.error as exc:
                    raise AlertmanagerRouteConsistencyValidationError(
                        code=VALIDATOR_ERROR_CODES["INVALID_REGEX_MATCHER"],
                        message=f"invalid regex matcher: {path} matcher={matcher} error={exc}",
                        context={"path": path, "matcher": matcher},
                    ) from exc
            result.append((key, operator, value))

    return result


def _collect_routes(
    route: dict[str, Any],
    inherited_receiver: str | None,
    path: str,
    parent_path: str | None,
) -> list[dict[str, Any]]:
    receiver = route.get("receiver", inherited_receiver)
    if not isinstance(receiver, str) or not receiver:
        raise ValueError(f"route receiver missing/invalid: {path}")

    current = {
        "path": path,
        "parent_path": parent_path,
        "receiver": receiver,
        "matchers": _extract_matchers(route=route, path=path),
        "continue": bool(route.get("continue", False)),
    }
    result = [current]

    child_routes = route.get("routes", [])
    if child_routes is None:
        child_routes = []
    if not isinstance(child_routes, list):
        raise ValueError(f"route.routes must be list: {path}")
    for index, child in enumerate(child_routes):
        if not isinstance(child, dict):
            raise ValueError(f"child route must be object: {path}.routes[{index}]")
        result.extend(
            _collect_routes(
                route=child,
                inherited_receiver=receiver,
                path=f"{path}.routes[{index}]",
                parent_path=path,
            )
        )
    return result


def _load_alertmanager_routes(alertmanager_file: Path) -> tuple[set[str], list[dict[str, Any]]]:
    payload = _load_yaml_file(alertmanager_file)
    if not isinstance(payload, dict):
        raise ValueError(f"alertmanager payload must be object: {alertmanager_file}")

    receivers_payload = payload.get("receivers")
    if not isinstance(receivers_payload, list):
        raise ValueError(f"alertmanager receivers must be list: {alertmanager_file}")

    receiver_names: set[str] = set()
    for entry in receivers_payload:
        if not isinstance(entry, dict):
            raise ValueError(f"alertmanager receiver entry must be object: {alertmanager_file}")
        receiver_name = entry.get("name")
        if not isinstance(receiver_name, str) or not receiver_name:
            raise ValueError(f"alertmanager receiver name missing/invalid: {alertmanager_file}")
        receiver_names.add(receiver_name)

    route_payload = payload.get("route")
    if not isinstance(route_payload, dict):
        raise ValueError(f"alertmanager route must be object: {alertmanager_file}")

    routes = _collect_routes(route=route_payload, inherited_receiver=None, path="route", parent_path=None)
    for route_entry in routes:
        receiver = route_entry["receiver"]
        if receiver not in receiver_names:
            raise ValueError(
                f"route references unknown receiver: path={route_entry['path']} receiver={receiver}"
            )
    return receiver_names, routes


def _route_matches_alert(route: dict[str, Any], alert_labels: dict[str, str]) -> bool:
    matchers: list[RouteMatcher] = route["matchers"]
    for key, operator, value in matchers:
        label_value = alert_labels.get(key)
        if operator == "=":
            if label_value != value:
                return False
            continue
        if operator == "!=":
            if label_value == value:
                return False
            continue
        if operator == "=~":
            if label_value is None:
                return False
            if re.fullmatch(value, label_value) is None:
                return False
            continue
        if operator == "!~":
            if label_value is None:
                continue
            if re.fullmatch(value, label_value) is not None:
                return False
            continue
        raise ValueError(f"unsupported matcher operator at runtime: {operator}")
    return True


def _is_matcher_subset(subset: list[RouteMatcher], superset: list[RouteMatcher]) -> bool:
    return set(subset).issubset(set(superset))


def _find_shadowed_routes(explicit_routes: list[dict[str, Any]]) -> list[str]:
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for route in explicit_routes:
        parent = route["parent_path"]
        if not isinstance(parent, str):
            continue
        by_parent.setdefault(parent, []).append(route)

    shadowed: list[str] = []
    for sibling_routes in by_parent.values():
        for index, earlier in enumerate(sibling_routes):
            if earlier.get("continue", False):
                continue
            earlier_matchers = earlier["matchers"]
            for later in sibling_routes[index + 1 :]:
                later_matchers = later["matchers"]
                if _is_matcher_subset(earlier_matchers, later_matchers):
                    shadowed.append(
                        "shadowed route: "
                        f"{later['path']} is shadowed by {earlier['path']} "
                        f"(receiver={later['receiver']}, shadow_receiver={earlier['receiver']})"
                    )
    return shadowed


def _validate_consistency(rules_dir: Path, alertmanager_file: Path) -> tuple[int, int]:
    if not rules_dir.exists() or not rules_dir.is_dir():
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["RULES_DIR_INVALID"],
            message=f"rules directory not found: {rules_dir}",
            context={"path": str(rules_dir)},
        )
    rule_files = sorted(rules_dir.glob("*.yml")) + sorted(rules_dir.glob("*.yaml"))
    if not rule_files:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["NO_RULE_FILES"],
            message=f"no rule files found in: {rules_dir}",
            context={"path": str(rules_dir)},
        )

    alerts = _collect_alerts(rule_files=rule_files)
    if not alerts:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["NO_ALERTS"],
            message=f"no alerts found in rule files: {rules_dir}",
            context={"path": str(rules_dir)},
        )

    _receiver_names, routes = _load_alertmanager_routes(alertmanager_file=alertmanager_file)
    explicit_routes = [entry for entry in routes if entry["matchers"]]
    if not explicit_routes:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["NO_EXPLICIT_ROUTES"],
            message="no explicit routes found in alertmanager config",
            context={"path": str(alertmanager_file)},
        )

    shadowed = _find_shadowed_routes(explicit_routes=explicit_routes)
    if shadowed:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["SHADOWED_ROUTE"],
            message="; ".join(shadowed),
            context={"count": len(shadowed), "first_failure": shadowed[0]},
        )

    unmatched: list[str] = []
    ambiguous: list[str] = []
    for alert in alerts:
        matched_routes = [
            route for route in explicit_routes if _route_matches_alert(route=route, alert_labels=alert["labels"])
        ]
        if not matched_routes:
            unmatched.append(
                f"unmatched alert: {alert['alert']} labels={alert['labels']} source={alert['source_file']}"
            )
            continue
        if len(matched_routes) > 1:
            routes_text = ", ".join(
                f"{route['path']}@{route['receiver']}" for route in matched_routes
            )
            ambiguous.append(
                "multiple explicit routes matched alert: "
                f"{alert['alert']} labels={alert['labels']} routes=[{routes_text}] source={alert['source_file']}"
            )

    if unmatched:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["UNMATCHED_ALERT"],
            message="; ".join(unmatched),
            context={"count": len(unmatched), "first_failure": unmatched[0]},
        )
    if ambiguous:
        raise AlertmanagerRouteConsistencyValidationError(
            code=VALIDATOR_ERROR_CODES["AMBIGUOUS_ALERT"],
            message="; ".join(ambiguous),
            context={"count": len(ambiguous), "first_failure": ambiguous[0]},
        )

    return len(alerts), len(explicit_routes)


def main() -> int:
    argv = sys.argv[1:]
    json_errors_requested = "--json-errors" in argv
    json_output_requested = "--json-output" in argv

    try:
        args = _parse_args(argv=argv)
        json_errors_requested = bool(args.json_errors)
        json_output_requested = bool(args.json_output)
        alert_count, route_count = _validate_consistency(
            rules_dir=args.rules_dir,
            alertmanager_file=args.alertmanager_file,
        )
        if json_output_requested:
            payload = {
                "validator": VALIDATOR_NAME,
                "status": "ok",
                "rules_dir": str(args.rules_dir),
                "alertmanager_file": str(args.alertmanager_file),
                "alert_count": alert_count,
                "explicit_route_count": route_count,
            }
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(
                "[validate-alertmanager-route-consistency] all alerts are covered by explicit alertmanager routes: "
                f"{alert_count} alerts, {route_count} explicit routes."
            )
        return 0
    except Exception as exc:
        if json_errors_requested:
            if isinstance(exc, AlertmanagerRouteConsistencyValidationError):
                payload = {
                    "validator": VALIDATOR_NAME,
                    "code": exc.code,
                    "message": str(exc),
                    "context": exc.context,
                }
            else:
                payload = {
                    "validator": VALIDATOR_NAME,
                    "code": VALIDATOR_ERROR_CODES["UNEXPECTED_ERROR"],
                    "message": str(exc),
                    "context": {},
                }
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"[validate-alertmanager-route-consistency] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
