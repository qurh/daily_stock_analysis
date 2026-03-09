from __future__ import annotations

import importlib
import os
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


class LLMProvider:
    """LLM provider interface."""

    provider_name: str
    model_name: str

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


@dataclass
class LLMProviderError(Exception):
    provider: str
    status_code: int | None
    error_code: str
    error_message: str
    category: str
    retryable: bool

    def __str__(self) -> str:
        return (
            f"provider={self.provider}, status_code={self.status_code}, error_code={self.error_code}, "
            f"category={self.category}, retryable={self.retryable}, message={self.error_message}"
        )


@dataclass
class RetryingLLMProvider(LLMProvider):
    base_provider: LLMProvider
    max_retries: int
    retry_backoff_ms: int

    @property
    def provider_name(self) -> str:
        return self.base_provider.provider_name

    @property
    def model_name(self) -> str:
        return self.base_provider.model_name

    def generate(self, prompt: str) -> str:
        attempt = 0
        while True:
            try:
                return self.base_provider.generate(prompt)
            except LLMProviderError as exc:
                if not exc.retryable or attempt >= self.max_retries:
                    raise
                delay_sec = _calculate_backoff_delay_sec(
                    base_backoff_ms=self.retry_backoff_ms,
                    attempt=attempt,
                )
                if delay_sec > 0:
                    time.sleep(delay_sec)
                attempt += 1


@dataclass
class CircuitBreakerLLMProvider(LLMProvider):
    base_provider: LLMProvider
    failure_threshold: int
    reset_timeout_ms: int
    _consecutive_retryable_failures: int = field(default=0, init=False)
    _opened_at_monotonic: float | None = field(default=None, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    @property
    def provider_name(self) -> str:
        return self.base_provider.provider_name

    @property
    def model_name(self) -> str:
        return self.base_provider.model_name

    def generate(self, prompt: str) -> str:
        if self._is_circuit_open():
            raise self._build_circuit_open_error()
        try:
            result = self.base_provider.generate(prompt)
        except LLMProviderError as exc:
            if exc.retryable:
                self._record_retryable_failure()
            raise
        self._reset_state()
        return result

    def _is_circuit_open(self) -> bool:
        with self._lock:
            if self._opened_at_monotonic is None:
                return False
            elapsed = time.monotonic() - self._opened_at_monotonic
            if elapsed < (self.reset_timeout_ms / 1000.0):
                return True
            self._opened_at_monotonic = None
            self._consecutive_retryable_failures = 0
            return False

    def _record_retryable_failure(self) -> None:
        with self._lock:
            self._consecutive_retryable_failures += 1
            if self._consecutive_retryable_failures >= self.failure_threshold and self._opened_at_monotonic is None:
                self._opened_at_monotonic = time.monotonic()

    def _reset_state(self) -> None:
        with self._lock:
            self._consecutive_retryable_failures = 0
            self._opened_at_monotonic = None

    def _build_circuit_open_error(self) -> LLMProviderError:
        return LLMProviderError(
            provider=self.provider_name,
            status_code=None,
            error_code="CircuitOpen",
            error_message=f"Circuit breaker open for provider: {self.provider_name}",
            category="circuit_open",
            retryable=True,
        )


@dataclass
class KeyPoolLLMProvider(LLMProvider):
    providers: list[LLMProvider]
    _current_index: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    @property
    def provider_name(self) -> str:
        if not self.providers:
            return "unknown"
        return self.providers[0].provider_name

    @property
    def model_name(self) -> str:
        if not self.providers:
            return "unknown"
        return self.providers[0].model_name

    def generate(self, prompt: str) -> str:
        if not self.providers:
            raise ValueError("No providers configured for key pool")
        total = len(self.providers)
        with self._lock:
            start_index = self._current_index
        last_retryable_error: LLMProviderError | None = None

        for offset in range(total):
            index = (start_index + offset) % total
            provider = self.providers[index]
            try:
                result = provider.generate(prompt)
            except LLMProviderError as exc:
                if not exc.retryable:
                    raise
                with self._lock:
                    self._current_index = (index + 1) % total
                last_retryable_error = exc
                continue
            with self._lock:
                self._current_index = index
            return result

        if last_retryable_error is not None:
            raise last_retryable_error
        raise ValueError("No providers configured for key pool")


@dataclass(frozen=True)
class MockLLMProvider(LLMProvider):
    provider_name: str = "mock-llm"
    model_name: str = "mock-v1"

    def generate(self, prompt: str) -> str:
        compact = " ".join(prompt.split())
        if len(compact) > 480:
            compact = f"{compact[:477]}..."
        return f"[{self.provider_name}] {compact}"


@dataclass(frozen=True)
class OpenAICompatibleLLMProvider(LLMProvider):
    provider_name: str
    model_name: str
    api_key: str
    base_url: str
    timeout_sec: float

    def generate(self, prompt: str) -> str:
        try:
            response = httpx.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=self.timeout_sec,
            )
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=None,
                error_code="Timeout",
                error_message=str(exc),
                category="timeout",
                retryable=True,
            ) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=None,
                error_code="RequestError",
                error_message=str(exc),
                category="upstream",
                retryable=True,
            ) from exc

        payload: dict[str, Any] = {}
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                payload = parsed
        except Exception:
            payload = {}

        status_code = getattr(response, "status_code", 200)
        if not isinstance(status_code, int):
            status_code = 200

        if status_code >= 400:
            error_code, error_message = _extract_openai_error(payload=payload)
            category, retryable = _classify_openai_error(
                status_code=status_code,
                error_code=error_code,
                error_message=error_message,
            )
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=status_code,
                error_code=error_code,
                error_message=error_message,
                category=category,
                retryable=retryable,
            )

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=status_code,
                error_code="InvalidPayload",
                error_message="Invalid LLM response payload",
                category="provider_payload",
                retryable=False,
            ) from exc
        if not isinstance(content, str):
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=status_code,
                error_code="InvalidPayload",
                error_message="Invalid LLM response payload",
                category="provider_payload",
                retryable=False,
            )
        return content


@dataclass(frozen=True)
class DashScopeLLMProvider(LLMProvider):
    provider_name: str
    model_name: str
    api_key: str
    base_http_api_url: str
    enable_thinking: bool

    def generate(self, prompt: str) -> str:
        try:
            dashscope_module = importlib.import_module("dashscope")
        except ImportError as exc:
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=None,
                error_code="DependencyMissing",
                error_message="dashscope package is required for provider: dashscope",
                category="dependency",
                retryable=False,
            ) from exc

        generation = getattr(dashscope_module, "Generation", None)
        if generation is None or not hasattr(generation, "call"):
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=None,
                error_code="InvalidSDK",
                error_message="Invalid dashscope SDK: missing Generation.call",
                category="dependency",
                retryable=False,
            )

        dashscope_module.base_http_api_url = self.base_http_api_url
        response = generation.call(
            api_key=self.api_key,
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            result_format="message",
            enable_thinking=self.enable_thinking,
        )

        status_code = getattr(response, "status_code", None)
        if status_code != 200:
            error_code = getattr(response, "code", "unknown")
            error_message = getattr(response, "message", "unknown")
            category, retryable = _classify_dashscope_error(
                status_code=status_code,
                error_code=error_code,
                error_message=error_message,
            )
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=status_code,
                error_code=str(error_code),
                error_message=str(error_message),
                category=category,
                retryable=retryable,
            )

        try:
            content = response.output.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=200,
                error_code="InvalidPayload",
                error_message="Invalid DashScope response payload",
                category="provider_payload",
                retryable=False,
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError(
                provider=self.provider_name,
                status_code=200,
                error_code="InvalidPayload",
                error_message="Invalid DashScope response payload",
                category="provider_payload",
                retryable=False,
            )
        return content


def _classify_dashscope_error(status_code: int | None, error_code: str, error_message: str) -> tuple[str, bool]:
    code = (error_code or "").lower()
    message = (error_message or "").lower()

    if status_code == 429 or "throttl" in code or "ratelimit" in code:
        return "rate_limit", True

    if status_code is not None and status_code >= 500:
        return "upstream", True
    if code in {"internalerror", "serviceunavailable", "gatewaytimeout", "requesttimeout"}:
        return "upstream", True

    if code in {"invalidapikey", "accessdenied", "unauthorized", "forbidden"}:
        return "auth", False

    if code == "invalidparameter" and "model" in message and "exist" in message:
        return "model_config", False
    if code == "invalidparameter":
        return "invalid_request", False

    return "unknown", False


def _extract_openai_error(payload: dict[str, Any]) -> tuple[str, str]:
    error = payload.get("error")
    if isinstance(error, dict):
        code = str(error.get("code") or "unknown")
        message = str(error.get("message") or "unknown")
        return code, message
    return "unknown", "unknown"


def _classify_openai_error(status_code: int | None, error_code: str, error_message: str) -> tuple[str, bool]:
    code = (error_code or "").lower()
    message = (error_message or "").lower()

    if status_code == 429 or "rate" in code or "quota" in code:
        return "rate_limit", True
    if status_code is not None and status_code >= 500:
        return "upstream", True
    if status_code in {401, 403} or code in {"invalid_api_key", "unauthorized", "forbidden"}:
        return "auth", False
    if status_code == 404 and "model" in message:
        return "model_config", False
    if status_code == 400:
        return "invalid_request", False

    return "unknown", False


def _calculate_backoff_delay_sec(base_backoff_ms: int, attempt: int) -> float:
    if base_backoff_ms <= 0:
        return 0.0
    jitter_factor = random.uniform(0.8, 1.2)
    return (base_backoff_ms / 1000.0) * (2**attempt) * jitter_factor


def _read_csv_env(name: str) -> list[str]:
    raw = os.getenv(name)
    if raw is None:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _normalize_key_candidates(primary_key: str | None, key_candidates: list[str] | None = None) -> list[str]:
    items: list[str] = []
    for key in key_candidates or []:
        normalized = str(key).strip()
        if normalized and normalized not in items:
            items.append(normalized)
    normalized_primary = (primary_key or "").strip()
    if normalized_primary and normalized_primary not in items:
        items.append(normalized_primary)
    return items


def _wrap_provider_with_resilience(
    provider: LLMProvider,
    max_retries: int,
    retry_backoff_ms: int,
    circuit_failure_threshold: int,
    circuit_reset_timeout_ms: int,
) -> LLMProvider:
    wrapped: LLMProvider = provider
    if max_retries > 0:
        wrapped = RetryingLLMProvider(
            base_provider=wrapped,
            max_retries=max_retries,
            retry_backoff_ms=retry_backoff_ms,
        )
    if circuit_failure_threshold > 0:
        wrapped = CircuitBreakerLLMProvider(
            base_provider=wrapped,
            failure_threshold=circuit_failure_threshold,
            reset_timeout_ms=max(circuit_reset_timeout_ms, 0),
        )
    return wrapped


def _build_key_pool_provider(
    providers: list[LLMProvider],
    max_retries: int,
    retry_backoff_ms: int,
    circuit_failure_threshold: int,
    circuit_reset_timeout_ms: int,
) -> LLMProvider:
    wrapped_providers = [
        _wrap_provider_with_resilience(
            provider=provider,
            max_retries=max_retries,
            retry_backoff_ms=retry_backoff_ms,
            circuit_failure_threshold=circuit_failure_threshold,
            circuit_reset_timeout_ms=circuit_reset_timeout_ms,
        )
        for provider in providers
    ]
    if len(wrapped_providers) == 1:
        return wrapped_providers[0]
    return KeyPoolLLMProvider(providers=wrapped_providers)


def create_llm_provider(
    provider_name: str,
    model_name: str,
    api_key: str | None = None,
    api_keys: list[str] | None = None,
    base_url: str = "https://api.openai.com/v1",
    timeout_sec: float = 30.0,
    dashscope_api_key: str | None = None,
    dashscope_api_keys: list[str] | None = None,
    dashscope_base_http_api_url: str = "https://dashscope.aliyuncs.com/api/v1",
    dashscope_enable_thinking: bool = False,
    max_retries: int = 0,
    retry_backoff_ms: int = 100,
    circuit_failure_threshold: int = 0,
    circuit_reset_timeout_ms: int = 30000,
    base_provider_override: LLMProvider | None = None,
) -> LLMProvider:
    if base_provider_override is not None:
        return _wrap_provider_with_resilience(
            provider=base_provider_override,
            max_retries=max_retries,
            retry_backoff_ms=retry_backoff_ms,
            circuit_failure_threshold=circuit_failure_threshold,
            circuit_reset_timeout_ms=circuit_reset_timeout_ms,
        )
    elif provider_name == "mock-llm":
        return _wrap_provider_with_resilience(
            provider=MockLLMProvider(provider_name=provider_name, model_name=model_name),
            max_retries=max_retries,
            retry_backoff_ms=retry_backoff_ms,
            circuit_failure_threshold=circuit_failure_threshold,
            circuit_reset_timeout_ms=circuit_reset_timeout_ms,
        )
    elif provider_name in {"openai-compatible", "openai"}:
        normalized_keys = _normalize_key_candidates(
            primary_key=api_key,
            key_candidates=api_keys,
        )
        if not normalized_keys:
            raise ValueError(f"LLM API key is required for provider: {provider_name}")
        return _build_key_pool_provider(
            providers=[
                OpenAICompatibleLLMProvider(
                    provider_name=provider_name,
                    model_name=model_name,
                    api_key=key,
                    base_url=base_url,
                    timeout_sec=timeout_sec,
                )
                for key in normalized_keys
            ],
            max_retries=max_retries,
            retry_backoff_ms=retry_backoff_ms,
            circuit_failure_threshold=circuit_failure_threshold,
            circuit_reset_timeout_ms=circuit_reset_timeout_ms,
        )
    elif provider_name in {"dashscope", "dashscope-sdk"}:
        normalized_keys = _normalize_key_candidates(
            primary_key=(dashscope_api_key or api_key or os.getenv("DASHSCOPE_API_KEY")),
            key_candidates=(dashscope_api_keys or []) + _read_csv_env("DASHSCOPE_API_KEYS"),
        )
        if not normalized_keys:
            raise ValueError("DashScope API key is required for provider: dashscope")
        return _build_key_pool_provider(
            providers=[
                DashScopeLLMProvider(
                    provider_name=provider_name,
                    model_name=model_name,
                    api_key=key,
                    base_http_api_url=dashscope_base_http_api_url,
                    enable_thinking=dashscope_enable_thinking,
                )
                for key in normalized_keys
            ],
            max_retries=max_retries,
            retry_backoff_ms=retry_backoff_ms,
            circuit_failure_threshold=circuit_failure_threshold,
            circuit_reset_timeout_ms=circuit_reset_timeout_ms,
        )
    else:
        raise ValueError(f"Unsupported llm provider: {provider_name}")
