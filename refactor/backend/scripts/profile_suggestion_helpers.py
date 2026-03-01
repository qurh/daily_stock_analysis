#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from difflib import get_close_matches
from pathlib import Path
import shlex

SUPPORTED_SUGGESTED_ACTIONS = {
    "copy_command": {"required_fields": ("command",)},
    "use_profile": {"required_fields": ("profile",)},
    "show_profiles": {"required_fields": ("profiles",)},
    "migrate_profile_mode": {"required_fields": ("config_snippet",)},
}


def build_profile_suggestion_payload(
    selected_profile: str,
    available_profiles: list[str],
    command_prefix: str,
    profile_label: str = "lint profile",
    profile_cli_arg: str = "--lint-profile",
) -> tuple[str, str, str, list[str], str | None, str | None]:
    suggested_profiles = get_close_matches(selected_profile, available_profiles, n=3, cutoff=0.5)
    suggested_cli_args = f"{profile_cli_arg} {suggested_profiles[0]}" if suggested_profiles else None
    suggested_command = f"{command_prefix} {suggested_cli_args}" if suggested_cli_args else None
    message = f"{profile_label} not found: {selected_profile}"
    if suggested_profiles:
        fallback_reason = "close_match"
        suggestion_level = "hint"
        message += f". Did you mean: {', '.join(suggested_profiles)}?"
        message += f" Try: {suggested_cli_args}"
    elif available_profiles:
        fallback_reason = "no_close_match"
        suggestion_level = "warning"
        message += f". Available profiles: {', '.join(available_profiles)}."
    else:
        fallback_reason = "no_profiles_available"
        suggestion_level = "error"
    return message, fallback_reason, suggestion_level, suggested_profiles, suggested_cli_args, suggested_command


def build_ordered_available_profiles(profiles: dict, default_profile: str | None) -> list[str]:
    ordered_profiles = sorted(profiles.keys())
    if isinstance(default_profile, str) and default_profile in profiles:
        ordered_profiles = [default_profile] + [item for item in ordered_profiles if item != default_profile]
    return ordered_profiles


def shell_quote(value: str | Path) -> str:
    return shlex.quote(str(value))


def build_profile_mode_config_snippet(flat_config: dict, selected_profile: str) -> dict:
    profile_payload = {
        key: deepcopy(value)
        for key, value in flat_config.items()
        if key not in {"default_profile", "profiles"}
    }
    return {
        "default_profile": selected_profile,
        "profiles": {
            selected_profile: profile_payload,
        },
    }


def validate_suggested_actions_contract(actions: list[dict]) -> None:
    if not isinstance(actions, list):
        raise ValueError("suggested_actions must be a list")

    for index, action_payload in enumerate(actions):
        if not isinstance(action_payload, dict):
            raise ValueError(f"suggested_actions[{index}] must be an object")

        action_name = action_payload.get("action")
        if not isinstance(action_name, str) or not action_name.strip():
            raise ValueError("missing required field: action")

        action_rule = SUPPORTED_SUGGESTED_ACTIONS.get(action_name)
        if action_rule is None:
            raise ValueError(f"unsupported action: {action_name}")

        required_fields = action_rule["required_fields"]
        for required_field in required_fields:
            if required_field not in action_payload:
                raise ValueError(f"missing required field: {required_field}")

        if action_name == "copy_command":
            if not isinstance(action_payload["command"], str) or not action_payload["command"].strip():
                raise ValueError("invalid field type: command")
        elif action_name == "use_profile":
            if not isinstance(action_payload["profile"], str) or not action_payload["profile"].strip():
                raise ValueError("invalid field type: profile")
        elif action_name == "show_profiles":
            profiles = action_payload["profiles"]
            if not isinstance(profiles, list) or not all(isinstance(item, str) for item in profiles):
                raise ValueError("invalid field type: profiles")
        elif action_name == "migrate_profile_mode":
            if not isinstance(action_payload["config_snippet"], dict):
                raise ValueError("invalid field type: config_snippet")


def build_suggested_actions_for_profile_not_found(
    fallback_reason: str,
    suggested_profiles: list[str],
    available_profiles: list[str],
    suggested_command: str | None,
    suggested_config_snippet: dict | None = None,
) -> list[dict]:
    actions: list[dict]
    if fallback_reason == "close_match":
        actions = []
        if suggested_command is not None:
            actions.append({"action": "copy_command", "command": suggested_command})
        if suggested_profiles:
            actions.append({"action": "use_profile", "profile": suggested_profiles[0]})
    elif fallback_reason == "no_close_match":
        actions = [{"action": "show_profiles", "profiles": available_profiles}]
    elif fallback_reason == "no_profiles_config" and suggested_config_snippet is not None:
        actions = [{"action": "migrate_profile_mode", "config_snippet": suggested_config_snippet}]
    else:
        actions = []

    validate_suggested_actions_contract(actions)
    return actions
