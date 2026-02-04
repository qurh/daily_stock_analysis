"""AI Router - Multi-Model Support.

Supports:
- Multiple AI providers (Google, OpenAI, DeepSeek, Qwen)
- Streaming responses
- Automatic failover
"""

import json
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime

import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class StreamEvent:
    """Stream event types."""

    CONTENT = "content"
    DONE = "done"
    ERROR = "error"


class AIRouter:
    """AI Model Router for multi-model support."""

    def __init__(self):
        self.settings = get_settings()
        self.model_configs = self._load_model_configs()

    def _load_model_configs(self) -> Dict[str, Dict]:
        """Load model configurations from settings."""
        return {
            "gemini-2.0-flash": {
                "provider": "google",
                "api_key": self.settings.GEMINI_API_KEY,
                "model": self.settings.GEMINI_MODEL or "gemini-2.0-flash-exp",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "supports_streaming": False,
            },
            "qwen-plus": {
                "provider": "tongyi",
                "api_key": self.settings.DASHSCOPE_API_KEY,
                "model": self.settings.DASHSCOPE_MODEL or "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "supports_streaming": True,
            },
            "deepseek-chat": {
                "provider": "deepseek",
                "api_key": self.settings.DEEPSEEK_API_KEY,
                "model": self.settings.DEEPSEEK_MODEL or "deepseek-chat",
                "base_url": self.settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com",
                "supports_streaming": True,
            },
            "gpt-4o": {
                "provider": "openai",
                "api_key": self.settings.OPENAI_API_KEY,
                "model": self.settings.OPENAI_MODEL or "gpt-4o",
                "base_url": self.settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
                "supports_streaming": True,
            },
            "gemini-1.5-flash": {
                "provider": "google",
                "api_key": self.settings.GEMINI_API_KEY,
                "model": "gemini-1.5-flash",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "supports_streaming": False,
            },
        }

    def get_default_model(self) -> str:
        """Get default model."""
        return "gemini-2.0-flash"

    def select_model(
        self,
        task_type: str = "general",
        prefer_fast: bool = False,
    ) -> str:
        """Select best model for task."""
        fast_models = ["gemini-2.0-flash", "gemini-1.5-flash", "qwen-plus"]
        quality_models = ["gpt-4o", "deepseek-chat"]

        if prefer_fast:
            for model in fast_models:
                if self._is_available(model):
                    return model

        if self._is_available("gemini-2.0-flash"):
            return "gemini-2.0-flash"

        for model in self.model_configs:
            if self._is_available(model):
                return model

        return self.get_default_model()

    async def generate(
        self,
        message: str,
        context: List[Dict[str, str]] = None,
        sources: List[Dict[str, Any]] = None,
        model: Optional[str] = None,
        stream: bool = True,
    ) -> str:
        """Generate response using selected model."""
        config = self._get_model_config(model or self.get_default_model())

        if config["provider"] == "google":
            return await self._call_gemini(message, context, config)
        elif config["provider"] == "openai":
            return await self._call_openai(message, context, config, stream=False)
        elif config["provider"] == "tongyi":
            return await self._call_qwen(message, context, config, stream=False)
        elif config["provider"] == "deepseek":
            return await self._call_deepseek(message, context, config, stream=False)
        else:
            raise ValueError(f"Unknown provider: {config['provider']}")

    async def generate_stream(
        self,
        message: str,
        context: List[Dict[str, str]] = None,
        sources: List[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        config = self._get_model_config(model or self.get_default_model())

        provider = config["provider"]
        if provider == "openai":
            async for chunk in self._call_openai_stream(message, context, config):
                yield chunk
        elif provider == "deepseek":
            async for chunk in self._call_deepseek_stream(message, context, config):
                yield chunk
        elif provider == "tongyi":
            async for chunk in self._call_qwen_stream(message, context, config):
                yield chunk
        else:
            response = await self.generate(message, context, sources, model, stream=False)
            yield response
            yield f"data: {StreamEvent.DONE}\n\n"

    async def _call_gemini(
        self,
        message: str,
        context: List[Dict[str, str]],
        config: Dict,
    ) -> str:
        """Call Google Gemini API."""
        if not config["api_key"]:
            logger.warning("Gemini API key not configured")
            return "AI model not configured. Please set GEMINI_API_KEY."

        async with httpx.AsyncClient(timeout=120.0) as client:
            url = f"{config['base_url']}/models/{config['model']}:generateContent"
            headers = {"Content-Type": "application/json"}
            params = {"key": config["api_key"]}

            prompt_parts = []
            if context:
                for msg in context:
                    prompt_parts.append(f"{msg['role']}: {msg['content']}")

            prompt_parts.append(f"user: {message}")

            if sources:
                prompt_parts.append("\n\nRelevant context:")
                for source in sources[:3]:
                    prompt_parts.append(f"- {source.get('content', '')[:500]}")

            payload = {
                "contents": [{"parts": [{"text": "\n".join(prompt_parts)}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
            }

            response = await client.post(url, json=payload, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_openai(
        self,
        message: str,
        context: List[Dict[str, str]],
        config: Dict,
        stream: bool,
    ) -> str:
        """Call OpenAI API."""
        if not config["api_key"]:
            return "AI model not configured. Please set OPENAI_API_KEY."

        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json",
            }

            messages = []
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": config["model"],
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
                "stream": stream,
            }

            response = await client.post(
                f"{config['base_url']}/chat/completions",
                json=payload, headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_openai_stream(
        self,
        message: str,
        context: List[Dict[str, str]],
        config: Dict,
    ) -> AsyncGenerator[str, None]:
        """Call OpenAI API with streaming."""
        if not config["api_key"]:
            yield "AI model not configured."
            return

        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json",
            }

            messages = []
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": config["model"],
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
                "stream": True,
            }

            async with client.stream(
                "POST",
                f"{config['base_url']}/chat/completions",
                json=payload, headers=headers,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            yield f"data: {StreamEvent.DONE}\n\n"
                            break

                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def _call_qwen(
        self,
        message: str,
        context: List[Dict[str, str]],
        config: Dict,
        stream: bool,
    ) -> str:
        """Call Alibaba Qwen API."""
        if not config["api_key"]:
            return "AI model not configured. Please set DASHSCOPE_API_KEY."

        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {"Content-Type": "application/json"}

            messages = []
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": config["model"],
                "input": {"messages": messages},
                "parameters": {"temperature": 0.7, "max_tokens": 2048},
            }

            response = await client.post(
                f"{config['base_url']}/chat/completions",
                json=payload, headers=headers,
                auth=("apikey", config["api_key"]),
            )
            response.raise_for_status()

            data = response.json()
            return data["output"]["text"]

    async def _call_qwen_stream(
        self,
        message: str,
        context: List[Dict[str, str]],
        config: Dict,
    ) -> AsyncGenerator[str, None]:
        """Call Qwen API with streaming."""
        if not config["api_key"]:
            yield "AI model not configured."
            return

        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {"Content-Type": "application/json"}

            messages = []
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": config["model"],
                "input": {"messages": messages, "parameters": {"incremental_output": True}},
                "parameters": {"temperature": 0.7, "max_tokens": 2048},
            }

            async with client.stream(
                "POST",
                f"{config['base_url']}/chat/completions",
                json=payload, headers=headers,
                auth=("apikey", config["api_key"]),
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            yield f"data: {StreamEvent.DONE}\n\n"
                            break

                        try:
                            chunk = json.loads(data)
                            content = chunk.get("output", {}).get("text", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def _call_deepseek(
        self,
        message: str,
        context: List[Dict[str, str]],
        config: Dict,
        stream: bool,
    ) -> str:
        """Call DeepSeek API."""
        if not config["api_key"]:
            return "AI model not configured. Please set DEEPSEEK_API_KEY."

        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {"Content-Type": "application/json"}

            messages = []
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": config["model"],
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
                "stream": stream,
            }

            response = await client.post(
                f"{config['base_url']}/chat/completions",
                json=payload, headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_deepseek_stream(
        self,
        message: str,
        context: List[Dict[str, str]],
        config: Dict,
    ) -> AsyncGenerator[str, None]:
        """Call DeepSeek API with streaming."""
        if not config["api_key"]:
            yield "AI model not configured."
            return

        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {"Content-Type": "application/json"}

            messages = []
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": config["model"],
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
                "stream": True,
            }

            async with client.stream(
                "POST",
                f"{config['base_url']}/chat/completions",
                json=payload, headers=headers,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            yield f"data: {StreamEvent.DONE}\n\n"
                            break

                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    def _get_model_config(self, model: str) -> Dict:
        """Get model configuration."""
        return self.model_configs.get(model, self.model_configs[self.get_default_model()])

    def _is_available(self, model: str) -> bool:
        """Check if model is available (has API key configured)."""
        config = self.model_configs.get(model)
        if not config:
            return False
        return bool(config.get("api_key"))

    def get_available_models(self) -> List[Dict]:
        """Get list of available models."""
        return [
            {
                "id": model_id,
                "name": config["model"].replace("-", " ").title(),
                "provider": config["provider"],
                "supports_streaming": config.get("supports_streaming", False),
                "enabled": self._is_available(model_id),
            }
            for model_id, config in self.model_configs.items()
        ]
