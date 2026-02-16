import sys
import types

import pytest

from app.llm.provider import LLMProvider, LLMProviderError, create_llm_provider


def test_create_openai_compatible_provider_requires_api_key() -> None:
    with pytest.raises(ValueError, match="LLM API key is required"):
        create_llm_provider(
            provider_name="openai-compatible",
            model_name="gpt-4o-mini",
            api_key=None,
            base_url="https://api.openai.com/v1",
            timeout_sec=30,
        )


def test_openai_compatible_provider_generate(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        @staticmethod
        def json() -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "real llm output",
                        }
                    }
                ]
            }

    def fake_post(url: str, *, headers: dict[str, str], json: dict[str, object], timeout: float) -> FakeResponse:
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.llm.provider.httpx.post", fake_post)

    provider = create_llm_provider(
        provider_name="openai-compatible",
        model_name="gpt-4o-mini",
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
        timeout_sec=15,
    )
    result = provider.generate("Prompt body")

    assert result == "real llm output"
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Authorization"] == "Bearer sk-test"
    assert headers["Content-Type"] == "application/json"
    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["model"] == "gpt-4o-mini"
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][0]["content"] == "Prompt body"
    assert captured["timeout"] == 15


def test_create_dashscope_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DashScope API key is required"):
        create_llm_provider(
            provider_name="dashscope",
            model_name="qwen-plus",
            api_key=None,
            dashscope_api_key=None,
        )


def test_dashscope_provider_generate(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 200
        code = None
        message = None
        output = types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(
                        reasoning_content="analysis reasoning",
                        content="dashscope output",
                    )
                )
            ]
        )

    class FakeGeneration:
        @staticmethod
        def call(**kwargs: object) -> FakeResponse:
            captured.update(kwargs)
            return FakeResponse()

    fake_dashscope = types.SimpleNamespace(
        base_http_api_url="",
        Generation=FakeGeneration,
    )
    monkeypatch.setitem(sys.modules, "dashscope", fake_dashscope)

    provider = create_llm_provider(
        provider_name="dashscope",
        model_name="qwen-plus",
        dashscope_api_key="dashscope-key",
        dashscope_base_http_api_url="https://dashscope.aliyuncs.com/api/v1",
        dashscope_enable_thinking=True,
    )
    result = provider.generate("Prompt body")

    assert result == "dashscope output"
    assert fake_dashscope.base_http_api_url == "https://dashscope.aliyuncs.com/api/v1"
    assert captured["api_key"] == "dashscope-key"
    assert captured["model"] == "qwen-plus"
    assert captured["result_format"] == "message"
    assert captured["enable_thinking"] is True
    messages = captured["messages"]
    assert isinstance(messages, list)
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Prompt body"


def test_dashscope_provider_error_layering(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 429
        code = "Throttling"
        message = "Rate limit exceeded."

    class FakeGeneration:
        @staticmethod
        def call(**kwargs: object) -> FakeResponse:
            return FakeResponse()

    fake_dashscope = types.SimpleNamespace(
        base_http_api_url="",
        Generation=FakeGeneration,
    )
    monkeypatch.setitem(sys.modules, "dashscope", fake_dashscope)

    provider = create_llm_provider(
        provider_name="dashscope",
        model_name="qwen-plus",
        dashscope_api_key="dashscope-key",
    )
    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate("Prompt body")

    error = exc_info.value
    assert error.provider == "dashscope"
    assert error.status_code == 429
    assert error.error_code == "Throttling"
    assert error.category == "rate_limit"
    assert error.retryable is True


def test_retryable_provider_error_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr("app.llm.provider.time.sleep", lambda s: sleep_calls.append(s))
    monkeypatch.setattr("app.llm.provider.random.uniform", lambda a, b: 1.0)

    class FlakyProvider(LLMProvider):
        provider_name = "flaky"
        model_name = "v1"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, prompt: str) -> str:  # noqa: ARG002
            self.calls += 1
            if self.calls < 3:
                raise LLMProviderError(
                    provider="dashscope",
                    status_code=429,
                    error_code="Throttling",
                    error_message="Rate limit exceeded.",
                    category="rate_limit",
                    retryable=True,
                )
            return "ok"

    provider = FlakyProvider()
    retrying = create_llm_provider(
        provider_name="mock-llm",
        model_name="mock-v1",
        max_retries=2,
        retry_backoff_ms=10,
        base_provider_override=provider,
    )
    result = retrying.generate("hello")
    assert result == "ok"
    assert provider.calls == 3
    assert sleep_calls == [0.01, 0.02]


def test_non_retryable_provider_error_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr("app.llm.provider.time.sleep", lambda s: sleep_calls.append(s))

    class BrokenProvider(LLMProvider):
        provider_name = "broken"
        model_name = "v1"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, prompt: str) -> str:  # noqa: ARG002
            self.calls += 1
            raise LLMProviderError(
                provider="dashscope",
                status_code=400,
                error_code="InvalidParameter",
                error_message="Model not exist.",
                category="model_config",
                retryable=False,
            )

    provider = BrokenProvider()
    retrying = create_llm_provider(
        provider_name="mock-llm",
        model_name="mock-v1",
        max_retries=3,
        retry_backoff_ms=10,
        base_provider_override=provider,
    )
    with pytest.raises(LLMProviderError):
        retrying.generate("hello")
    assert provider.calls == 1
    assert sleep_calls == []


def test_circuit_breaker_opens_after_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    now = {"value": 0.0}
    monkeypatch.setattr("app.llm.provider.time.monotonic", lambda: now["value"])

    class AlwaysRetryableFailProvider(LLMProvider):
        provider_name = "dashscope"
        model_name = "qwen-plus"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, prompt: str) -> str:  # noqa: ARG002
            self.calls += 1
            raise LLMProviderError(
                provider="dashscope",
                status_code=429,
                error_code="Throttling",
                error_message="Rate limit exceeded.",
                category="rate_limit",
                retryable=True,
            )

    provider = AlwaysRetryableFailProvider()
    guarded = create_llm_provider(
        provider_name="mock-llm",
        model_name="mock-v1",
        base_provider_override=provider,
        circuit_failure_threshold=2,
        circuit_reset_timeout_ms=1000,
    )

    with pytest.raises(LLMProviderError):
        guarded.generate("p1")
    with pytest.raises(LLMProviderError):
        guarded.generate("p2")

    error: LLMProviderError
    with pytest.raises(LLMProviderError) as exc_info:
        guarded.generate("p3")
    error = exc_info.value
    assert error.category == "circuit_open"
    assert error.error_code == "CircuitOpen"
    assert error.retryable is True
    assert provider.calls == 2


def test_circuit_breaker_recovers_after_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    now = {"value": 0.0}
    monkeypatch.setattr("app.llm.provider.time.monotonic", lambda: now["value"])

    class FlakyProvider(LLMProvider):
        provider_name = "dashscope"
        model_name = "qwen-plus"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, prompt: str) -> str:  # noqa: ARG002
            self.calls += 1
            if self.calls <= 2:
                raise LLMProviderError(
                    provider="dashscope",
                    status_code=503,
                    error_code="ServiceUnavailable",
                    error_message="temporary issue",
                    category="upstream",
                    retryable=True,
                )
            return "recovered"

    provider = FlakyProvider()
    guarded = create_llm_provider(
        provider_name="mock-llm",
        model_name="mock-v1",
        base_provider_override=provider,
        circuit_failure_threshold=2,
        circuit_reset_timeout_ms=1000,
    )

    with pytest.raises(LLMProviderError):
        guarded.generate("p1")
    with pytest.raises(LLMProviderError):
        guarded.generate("p2")
    with pytest.raises(LLMProviderError):
        guarded.generate("p3")

    now["value"] = 1.1
    assert guarded.generate("p4") == "recovered"
