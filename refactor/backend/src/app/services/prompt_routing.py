from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.prompt_service import PromptService


@dataclass(frozen=True)
class PromptLockFailure:
    prompt_ref: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "prompt_ref": self.prompt_ref,
            "reason": self.reason,
        }


class PromptLockError(RuntimeError):
    """Raised when prompt lock mode is strict and bound refs cannot be resolved."""

    def __init__(
        self,
        flow_id: str,
        lock_mode: str,
        requested_prompt_refs: list[str],
        failures: list[PromptLockFailure],
    ) -> None:
        self.error_code = "PROMPT_LOCK_ERROR"
        self.code = "PROMPT-LOCK-001"
        self.flow_id = flow_id
        self.lock_mode = lock_mode
        self.requested_prompt_refs = requested_prompt_refs
        self.failures = failures
        super().__init__(f"{self.code}: strict prompt lock failed for flow={flow_id}")

    def to_detail(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "code": self.code,
            "flow_id": self.flow_id,
            "lock_mode": self.lock_mode,
            "requested_prompt_refs": self.requested_prompt_refs,
            "failures": [item.to_dict() for item in self.failures],
            "message": str(self),
        }


def normalize_lock_mode(raw_mode: Any, default: str = "lenient") -> str:
    normalized_default = str(default or "lenient").strip().lower()
    if normalized_default not in {"strict", "lenient"}:
        normalized_default = "lenient"
    normalized = str(raw_mode or normalized_default).strip().lower()
    if normalized not in {"strict", "lenient"}:
        return normalized_default
    return normalized


def normalize_prompt_refs(strategy_context: dict[str, Any] | None) -> list[str]:
    if not strategy_context:
        return []
    refs = strategy_context.get("prompt_refs", [])
    return [str(item).strip() for item in refs if str(item).strip()]


def parse_prompt_ref(prompt_ref: Any) -> tuple[str, int | None]:
    text = str(prompt_ref or "").strip()
    if not text:
        return "", None
    if "@" not in text:
        return text, None

    prompt_id, version_text = text.split("@", 1)
    normalized_prompt_id = prompt_id.strip()
    normalized_version = version_text.strip()
    if not normalized_prompt_id:
        return "", None
    if not normalized_version:
        return normalized_prompt_id, None
    if not normalized_version.isdigit():
        raise ValueError(f"Invalid prompt ref version: {prompt_ref}")
    return normalized_prompt_id, int(normalized_version)


def resolve_binding_prompt(
    prompt_service: PromptService,
    prompt_refs: list[str],
    variables: dict[str, str],
    lock_mode: str,
) -> tuple[dict[str, str] | None, list[PromptLockFailure]]:
    failures: list[PromptLockFailure] = []
    for prompt_ref in prompt_refs:
        try:
            prompt_id, requested_version = parse_prompt_ref(prompt_ref=prompt_ref)
        except ValueError as exc:
            failures.append(PromptLockFailure(prompt_ref=prompt_ref, reason=f"invalid_prompt_ref:{exc}"))
            continue

        if not prompt_id:
            failures.append(PromptLockFailure(prompt_ref=prompt_ref, reason="empty_prompt_id"))
            continue

        if requested_version is None:
            try:
                rendered = prompt_service.render_active_prompt(
                    prompt_id=prompt_id,
                    variables=variables,
                )
                return (
                    {
                        "prompt_ref": rendered["prompt_ref"],
                        "rendered_prompt": rendered["rendered_prompt"],
                    },
                    failures,
                )
            except (KeyError, ValueError) as exc:
                failures.append(PromptLockFailure(prompt_ref=prompt_ref, reason=f"active_unavailable:{exc}"))
                continue

        try:
            rendered = prompt_service.render_prompt_version(
                prompt_id=prompt_id,
                version=requested_version,
                variables=variables,
            )
            return (
                {
                    "prompt_ref": rendered["prompt_ref"],
                    "rendered_prompt": rendered["rendered_prompt"],
                },
                failures,
            )
        except (KeyError, ValueError) as exc:
            failures.append(PromptLockFailure(prompt_ref=prompt_ref, reason=f"requested_version_unavailable:{exc}"))
            if lock_mode == "strict":
                continue
            try:
                rendered = prompt_service.render_active_prompt(
                    prompt_id=prompt_id,
                    variables=variables,
                )
                return (
                    {
                        "prompt_ref": rendered["prompt_ref"],
                        "rendered_prompt": rendered["rendered_prompt"],
                    },
                    failures,
                )
            except (KeyError, ValueError) as fallback_exc:
                failures.append(
                    PromptLockFailure(
                        prompt_ref=prompt_ref,
                        reason=f"active_fallback_unavailable:{fallback_exc}",
                    )
                )
                continue
    return None, failures
