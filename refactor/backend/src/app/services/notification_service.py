from __future__ import annotations

import os
import smtplib
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any, Callable, Sequence
from uuid import uuid4

import httpx

from app.persistence.sqlite_db import SQLiteDatabase
from app.shared.error_codes import ErrorCode


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_str(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class NotificationMessage:
    title: str
    content: str


class ChannelPlugin:
    """Channel plugin protocol base class."""

    channel: str
    display_name: str

    def is_enabled(self) -> tuple[bool, str | None]:
        raise NotImplementedError

    def send(self, title: str, content: str) -> dict[str, Any]:
        raise NotImplementedError


class NotificationFormatter:
    """Channel-aware formatter with lightweight byte-size limits."""

    def __init__(self, default_max_bytes: int = 60000) -> None:
        self._default_max_bytes = default_max_bytes
        self._channel_max_bytes: dict[str, int] = {
            "feishu": _env_int("FEISHU_MAX_BYTES", 20000),
            "wechat": _env_int("WECHAT_MAX_BYTES", 4000),
        }

    def render(self, channel: str, message: NotificationMessage) -> str:
        text = f"{message.title}\n\n{message.content}".strip()
        max_bytes = self._channel_max_bytes.get(channel, self._default_max_bytes)
        return _truncate_utf8_bytes(text=text, max_bytes=max_bytes)


class NotificationHub:
    """Hub that manages channel discovery, rendering, and fan-out dispatch."""

    def __init__(
        self,
        plugins: Sequence[ChannelPlugin] | None = None,
        formatter: NotificationFormatter | None = None,
        database: SQLiteDatabase | None = None,
        max_retries: int | None = None,
        retry_backoff_ms: int | None = None,
    ) -> None:
        self._plugins: list[ChannelPlugin] = list(plugins or _build_default_plugins())
        self._plugin_map: dict[str, ChannelPlugin] = {plugin.channel: plugin for plugin in self._plugins}
        self._formatter = formatter or NotificationFormatter()
        self._database = database
        self._max_retries = max(
            int(max_retries if max_retries is not None else _env_int("NOTIFICATION_SEND_MAX_RETRIES", 0)),
            0,
        )
        self._retry_backoff_ms = max(
            int(
                retry_backoff_ms
                if retry_backoff_ms is not None
                else _env_int("NOTIFICATION_RETRY_BACKOFF_MS", 0)
            ),
            0,
        )

    def list_channels(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for plugin in self._plugins:
            enabled, reason = plugin.is_enabled()
            items.append(
                {
                    "channel": plugin.channel,
                    "display_name": plugin.display_name,
                    "enabled": enabled,
                    "reason": reason,
                }
            )
        return {"items": items, "count": len(items)}

    def preview(self, message: NotificationMessage, channels: list[str] | None = None) -> dict[str, Any]:
        selected = self._select_plugins(channels=channels)
        items: list[dict[str, Any]] = []
        for plugin in selected:
            rendered = self._formatter.render(channel=plugin.channel, message=message)
            enabled, reason = plugin.is_enabled()
            items.append(
                {
                    "channel": plugin.channel,
                    "display_name": plugin.display_name,
                    "enabled": enabled,
                    "reason": reason,
                    "title": message.title,
                    "content": rendered,
                    "byte_size": len(rendered.encode("utf-8")),
                }
            )
        return {"items": items, "count": len(items)}

    def send(
        self,
        message: NotificationMessage,
        channels: list[str] | None = None,
        source_type: str = "api",
        source_id: str | None = None,
        retry_of_delivery_id: str | None = None,
    ) -> dict[str, Any]:
        selected = self._select_plugins(channels=channels)
        items: list[dict[str, Any]] = []
        summary = {"attempted": 0, "succeeded": 0, "failed": 0, "skipped": 0, "retried": 0}
        message_id = str(uuid4())
        created_at = _utc_now()

        for plugin in selected:
            rendered = self._formatter.render(channel=plugin.channel, message=message)
            enabled, reason = plugin.is_enabled()
            if not enabled:
                summary["skipped"] += 1
                item = {
                    "channel": plugin.channel,
                    "display_name": plugin.display_name,
                    "status": "skipped",
                    "error_code": ErrorCode.NTF_CHANNEL_001.value,
                    "error_message": reason or "channel not enabled",
                    "source_type": source_type,
                    "source_id": source_id,
                    "message_id": message_id,
                    "created_at": created_at,
                    "attempt_count": 0,
                    "retry_count": 0,
                    "retry_of_delivery_id": retry_of_delivery_id,
                }
                items.append(item)
                self._persist_delivery(
                    {
                        "message_id": message_id,
                        "source_type": source_type,
                        "source_id": source_id,
                        "channel": plugin.channel,
                        "status": "skipped",
                        "error_code": ErrorCode.NTF_CHANNEL_001.value,
                        "error_message": reason or "channel not enabled",
                        "provider_message_id": None,
                        "payload_preview": rendered,
                        "created_at": created_at,
                        "attempt_count": 0,
                        "retry_of_delivery_id": retry_of_delivery_id,
                    }
                )
                continue

            summary["attempted"] += 1
            outcome = self._send_with_retry(
                plugin=plugin,
                title=message.title,
                content=rendered,
            )
            if outcome["status"] == "delivered":
                summary["succeeded"] += 1
            else:
                summary["failed"] += 1
            if outcome["retry_count"] > 0:
                summary["retried"] += 1

            item = {
                "channel": plugin.channel,
                "display_name": plugin.display_name,
                "status": outcome["status"],
                "provider_message_id": outcome["provider_message_id"],
                "error_code": outcome["error_code"],
                "error_message": outcome["error_message"],
                "source_type": source_type,
                "source_id": source_id,
                "message_id": message_id,
                "created_at": created_at,
                "attempt_count": outcome["attempt_count"],
                "retry_count": outcome["retry_count"],
                "retry_of_delivery_id": retry_of_delivery_id,
            }
            items.append(item)
            self._persist_delivery(
                {
                    "message_id": message_id,
                    "source_type": source_type,
                    "source_id": source_id,
                    "channel": plugin.channel,
                    "status": outcome["status"],
                    "provider_message_id": outcome["provider_message_id"],
                    "error_code": outcome["error_code"],
                    "error_message": outcome["error_message"],
                    "payload_preview": rendered,
                    "created_at": created_at,
                    "attempt_count": outcome["attempt_count"],
                    "retry_of_delivery_id": retry_of_delivery_id,
                }
            )

        return {"summary": summary, "items": items, "message_id": message_id, "created_at": created_at}

    def test_channel(
        self,
        channel: str,
        title: str = "Notification Channel Test",
        content: str = "notification hub test message",
    ) -> dict[str, Any]:
        report = self.send(
            message=NotificationMessage(title=title, content=content),
            channels=[channel],
            source_type="channel_test",
            source_id=channel,
        )
        if not report["items"]:
            raise ValueError(f"{ErrorCode.NTF_CHANNEL_001.value}: channel not found: {channel}")
        return {"channel": channel, "result": report["items"][0]}

    def retry_delivery(
        self,
        delivery_id: str,
        title: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        if self._database is None:
            raise RuntimeError("notification delivery persistence is not enabled")
        with self._database.connection() as conn:
            row = conn.execute(
                """
                SELECT delivery_id, channel, payload_preview
                FROM notification_deliveries
                WHERE delivery_id = ?
                """,
                (delivery_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Notification delivery not found: {delivery_id}")

        channel = str(row["channel"])
        normalized_title = (title or "").strip()
        normalized_content = (content or "").strip()
        preview_title, preview_content = self._parse_preview_payload(row["payload_preview"])
        retry_title = normalized_title or preview_title or f"Delivery Retry {delivery_id}"
        retry_content = normalized_content or preview_content or f"retry_of_delivery_id: {delivery_id}"
        report = self.send(
            message=NotificationMessage(title=retry_title, content=retry_content),
            channels=[channel],
            source_type="delivery_retry",
            source_id=delivery_id,
            retry_of_delivery_id=delivery_id,
        )
        return {"retry_of_delivery_id": delivery_id, "report": report}

    def list_deliveries(
        self,
        source_type: str | None = None,
        source_id: str | None = None,
        channel: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        if self._database is None:
            return {"items": [], "count": 0}
        safe_limit = max(min(int(limit), 500), 1)
        query = """
            SELECT delivery_id, message_id, source_type, source_id, channel, status,
                   error_code, error_message, provider_message_id, payload_preview, created_at,
                   attempt_count, retry_of_delivery_id
            FROM notification_deliveries
            WHERE 1 = 1
        """
        params: list[Any] = []
        if source_type:
            query += " AND source_type = ?"
            params.append(source_type)
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        if channel:
            query += " AND channel = ?"
            params.append(channel)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(safe_limit)
        with self._database.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        items = [
            {
                "delivery_id": row["delivery_id"],
                "message_id": row["message_id"],
                "source_type": row["source_type"],
                "source_id": row["source_id"],
                "channel": row["channel"],
                "display_name": (
                    self._plugin_map[row["channel"]].display_name
                    if row["channel"] in self._plugin_map
                    else row["channel"]
                ),
                "status": row["status"],
                "error_code": row["error_code"],
                "error_message": row["error_message"],
                "provider_message_id": row["provider_message_id"],
                "payload_preview": row["payload_preview"],
                "created_at": row["created_at"],
                "attempt_count": int(row["attempt_count"] or 1),
                "retry_count": max(int(row["attempt_count"] or 1) - 1, 0),
                "retry_of_delivery_id": row["retry_of_delivery_id"],
            }
            for row in rows
        ]
        return {"items": items, "count": len(items)}

    def _send_with_retry(self, plugin: ChannelPlugin, title: str, content: str) -> dict[str, Any]:
        max_attempts = self._max_retries + 1
        for attempt in range(1, max_attempts + 1):
            try:
                result = plugin.send(title=title, content=content)
                status = str(result.get("status") or "delivered")
                if status == "delivered":
                    return {
                        "status": "delivered",
                        "provider_message_id": result.get("provider_message_id"),
                        "error_code": None,
                        "error_message": None,
                        "attempt_count": attempt,
                        "retry_count": attempt - 1,
                    }
                error_code = result.get("error_code") or ErrorCode.NTF_RETRY_004.value
                error_message = result.get("error_message") or f"delivery status={status}"
                if attempt < max_attempts:
                    self._wait_retry_backoff(retry_count=attempt)
                    continue
                return {
                    "status": "failed",
                    "provider_message_id": result.get("provider_message_id"),
                    "error_code": error_code,
                    "error_message": error_message,
                    "attempt_count": attempt,
                    "retry_count": attempt - 1,
                }
            except Exception as exc:
                if attempt < max_attempts:
                    self._wait_retry_backoff(retry_count=attempt)
                    continue
                return {
                    "status": "failed",
                    "provider_message_id": None,
                    "error_code": ErrorCode.NTF_SEND_003.value,
                    "error_message": str(exc),
                    "attempt_count": attempt,
                    "retry_count": attempt - 1,
                }
        return {
            "status": "failed",
            "provider_message_id": None,
            "error_code": ErrorCode.NTF_RETRY_004.value,
            "error_message": "unexpected_retry_state",
            "attempt_count": max_attempts,
            "retry_count": max_attempts - 1,
        }

    def _wait_retry_backoff(self, retry_count: int) -> None:
        if self._retry_backoff_ms <= 0:
            return
        delay_sec = (self._retry_backoff_ms * max(retry_count, 1)) / 1000.0
        time.sleep(delay_sec)

    def _select_plugins(self, channels: list[str] | None) -> list[ChannelPlugin]:
        if not channels:
            return list(self._plugins)
        selected: list[ChannelPlugin] = []
        unknown: list[str] = []
        for channel in channels:
            normalized = str(channel).strip().lower()
            plugin = self._plugin_map.get(normalized)
            if plugin is None:
                unknown.append(normalized)
                continue
            selected.append(plugin)
        if unknown:
            joined = ", ".join(unknown)
            raise ValueError(f"{ErrorCode.NTF_CHANNEL_001.value}: unknown channels: {joined}")
        return selected

    def _persist_delivery(self, record: dict[str, Any]) -> None:
        if self._database is None:
            return
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO notification_deliveries (
                    delivery_id, message_id, source_type, source_id, channel, status,
                    error_code, error_message, provider_message_id, payload_preview, created_at,
                    attempt_count, retry_of_delivery_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    record["message_id"],
                    record["source_type"],
                    record.get("source_id"),
                    record["channel"],
                    record["status"],
                    record.get("error_code"),
                    record.get("error_message"),
                    record.get("provider_message_id"),
                    record.get("payload_preview"),
                    record["created_at"],
                    max(int(record.get("attempt_count", 1)), 0),
                    record.get("retry_of_delivery_id"),
                ),
            )

    @staticmethod
    def _parse_preview_payload(payload_preview: Any) -> tuple[str | None, str | None]:
        if not isinstance(payload_preview, str):
            return None, None
        text = payload_preview.strip()
        if not text:
            return None, None
        if "\n\n" in text:
            title, content = text.split("\n\n", 1)
            return title.strip() or None, content.strip() or None
        return text, text


class _WebhookPlugin(ChannelPlugin):
    def __init__(
        self,
        channel: str,
        display_name: str,
        endpoint: str | None,
        payload_builder: Callable[[str, str], dict[str, Any]],
        timeout_sec: float,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.channel = channel
        self.display_name = display_name
        self._endpoint = endpoint
        self._payload_builder = payload_builder
        self._timeout_sec = timeout_sec
        self._headers = headers or {}

    def is_enabled(self) -> tuple[bool, str | None]:
        if self._endpoint:
            return True, None
        return False, "not_configured"

    def send(self, title: str, content: str) -> dict[str, Any]:
        if not self._endpoint:
            raise RuntimeError("channel not configured")
        payload = self._payload_builder(title, content)
        response = httpx.post(
            self._endpoint,
            json=payload,
            headers=self._headers,
            timeout=self._timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"http_status={response.status_code}")
        return {"status": "delivered", "provider_message_id": response.headers.get("x-request-id")}


class _TelegramPlugin(ChannelPlugin):
    channel = "telegram"
    display_name = "Telegram"

    def __init__(
        self,
        bot_token: str | None,
        chat_id: str | None,
        message_thread_id: str | None,
        timeout_sec: float,
    ) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._message_thread_id = message_thread_id
        self._timeout_sec = timeout_sec

    def is_enabled(self) -> tuple[bool, str | None]:
        if self._bot_token and self._chat_id:
            return True, None
        return False, "not_configured"

    def send(self, title: str, content: str) -> dict[str, Any]:
        if not self._bot_token or not self._chat_id:
            raise RuntimeError("channel not configured")
        payload: dict[str, Any] = {
            "chat_id": self._chat_id,
            "text": f"{title}\n\n{content}",
        }
        if self._message_thread_id:
            payload["message_thread_id"] = self._message_thread_id
        endpoint = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        response = httpx.post(endpoint, json=payload, timeout=self._timeout_sec)
        if response.status_code >= 400:
            raise RuntimeError(f"http_status={response.status_code}")
        payload = response.json()
        message_id = None
        if isinstance(payload, dict):
            result = payload.get("result")
            if isinstance(result, dict):
                message_id = result.get("message_id")
        return {"status": "delivered", "provider_message_id": message_id}


class _EmailPlugin(ChannelPlugin):
    channel = "email"
    display_name = "Email"

    _SMTP_CONFIGS: dict[str, dict[str, Any]] = {
        "qq.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
        "foxmail.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
        "163.com": {"server": "smtp.163.com", "port": 465, "ssl": True},
        "126.com": {"server": "smtp.126.com", "port": 465, "ssl": True},
        "gmail.com": {"server": "smtp.gmail.com", "port": 587, "ssl": False},
        "outlook.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
        "hotmail.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    }

    def __init__(self, sender: str | None, password: str | None, receivers: list[str] | None = None) -> None:
        self._sender = sender
        self._password = password
        self._receivers = [item for item in (receivers or []) if item]

    def is_enabled(self) -> tuple[bool, str | None]:
        if self._sender and self._password:
            return True, None
        return False, "not_configured"

    def send(self, title: str, content: str) -> dict[str, Any]:
        if not self._sender or not self._password:
            raise RuntimeError("channel not configured")
        recipients = self._receivers or [self._sender]
        smtp_conf = self._detect_smtp(self._sender)
        message = MIMEMultipart()
        message["From"] = formataddr((str(Header("daily_stock_analysis", "utf-8")), self._sender))
        message["To"] = ",".join(recipients)
        message["Subject"] = Header(title, "utf-8")
        message.attach(MIMEText(content, "plain", "utf-8"))

        if smtp_conf["ssl"]:
            server = smtplib.SMTP_SSL(smtp_conf["server"], smtp_conf["port"], timeout=10)
        else:
            server = smtplib.SMTP(smtp_conf["server"], smtp_conf["port"], timeout=10)
            server.starttls()
        try:
            server.login(self._sender, self._password)
            server.sendmail(self._sender, recipients, message.as_string())
        finally:
            server.quit()
        return {"status": "delivered", "provider_message_id": None}

    def _detect_smtp(self, sender: str) -> dict[str, Any]:
        domain = sender.split("@")[-1].lower()
        return self._SMTP_CONFIGS.get(domain, {"server": f"smtp.{domain}", "port": 465, "ssl": True})


class _PushOverPlugin(ChannelPlugin):
    channel = "pushover"
    display_name = "Pushover"

    def __init__(self, user_key: str | None, api_token: str | None, timeout_sec: float) -> None:
        self._user_key = user_key
        self._api_token = api_token
        self._timeout_sec = timeout_sec

    def is_enabled(self) -> tuple[bool, str | None]:
        if self._user_key and self._api_token:
            return True, None
        return False, "not_configured"

    def send(self, title: str, content: str) -> dict[str, Any]:
        if not self._user_key or not self._api_token:
            raise RuntimeError("channel not configured")
        response = httpx.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": self._api_token, "user": self._user_key, "title": title, "message": content},
            timeout=self._timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"http_status={response.status_code}")
        return {"status": "delivered", "provider_message_id": None}


class _PushPlusPlugin(ChannelPlugin):
    channel = "pushplus"
    display_name = "PushPlus"

    def __init__(self, token: str | None, timeout_sec: float) -> None:
        self._token = token
        self._timeout_sec = timeout_sec

    def is_enabled(self) -> tuple[bool, str | None]:
        if self._token:
            return True, None
        return False, "not_configured"

    def send(self, title: str, content: str) -> dict[str, Any]:
        if not self._token:
            raise RuntimeError("channel not configured")
        response = httpx.post(
            "http://www.pushplus.plus/send",
            json={"token": self._token, "title": title, "content": content, "template": "markdown"},
            timeout=self._timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"http_status={response.status_code}")
        return {"status": "delivered", "provider_message_id": None}


class _ServerChan3Plugin(ChannelPlugin):
    channel = "serverchan3"
    display_name = "Server酱3"

    def __init__(self, sendkey: str | None, timeout_sec: float) -> None:
        self._sendkey = sendkey
        self._timeout_sec = timeout_sec

    def is_enabled(self) -> tuple[bool, str | None]:
        if self._sendkey:
            return True, None
        return False, "not_configured"

    def send(self, title: str, content: str) -> dict[str, Any]:
        if not self._sendkey:
            raise RuntimeError("channel not configured")
        endpoint = f"https://sctapi.ftqq.com/{self._sendkey}.send"
        response = httpx.post(endpoint, data={"title": title, "desp": content}, timeout=self._timeout_sec)
        if response.status_code >= 400:
            raise RuntimeError(f"http_status={response.status_code}")
        return {"status": "delivered", "provider_message_id": None}


class _CustomWebhookPlugin(ChannelPlugin):
    channel = "custom"
    display_name = "Custom Webhook"

    def __init__(self, urls: list[str], bearer_token: str | None, timeout_sec: float) -> None:
        self._urls = urls
        self._bearer_token = bearer_token
        self._timeout_sec = timeout_sec

    def is_enabled(self) -> tuple[bool, str | None]:
        if self._urls:
            return True, None
        return False, "not_configured"

    def send(self, title: str, content: str) -> dict[str, Any]:
        if not self._urls:
            raise RuntimeError("channel not configured")
        headers: dict[str, str] = {}
        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        for url in self._urls:
            response = httpx.post(
                url,
                json={"title": title, "content": content, "text": f"{title}\n\n{content}"},
                headers=headers,
                timeout=self._timeout_sec,
            )
            if response.status_code >= 400:
                raise RuntimeError(f"url={url}, http_status={response.status_code}")
        return {"status": "delivered", "provider_message_id": None}


def _build_default_plugins() -> list[ChannelPlugin]:
    timeout_sec = max(_env_float("NOTIFICATION_HTTP_TIMEOUT_SEC", 10.0), 1.0)
    telegram_bot_token = _env_str("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = _env_str("TELEGRAM_CHAT_ID")
    telegram_message_thread_id = _env_str("TELEGRAM_MESSAGE_THREAD_ID")
    email_receivers_raw = _env_str("EMAIL_RECEIVERS")
    custom_webhook_raw = _env_str("CUSTOM_WEBHOOK_URLS")

    discord_webhook = _env_str("DISCORD_WEBHOOK_URL")
    discord_bot_token = _env_str("DISCORD_BOT_TOKEN")
    discord_channel_id = _env_str("DISCORD_MAIN_CHANNEL_ID")
    discord_endpoint: str | None
    discord_payload_builder: Callable[[str, str], dict[str, Any]]
    discord_headers: dict[str, str]
    if discord_webhook:
        discord_endpoint = discord_webhook
        discord_payload_builder = lambda title, content: {"content": f"{title}\n\n{content}"}
        discord_headers = {}
    elif discord_bot_token and discord_channel_id:
        discord_endpoint = f"https://discord.com/api/v10/channels/{discord_channel_id}/messages"
        discord_payload_builder = lambda title, content: {"content": f"{title}\n\n{content}"}
        discord_headers = {"Authorization": f"Bot {discord_bot_token}"}
    else:
        discord_endpoint = None
        discord_payload_builder = lambda title, content: {"content": f"{title}\n\n{content}"}
        discord_headers = {}

    astrbot_url = _env_str("ASTRBOT_URL") or _env_str("ASTRBOT_WEBHOOK_URL")
    astrbot_token = _env_str("ASTRBOT_TOKEN")
    astrbot_headers: dict[str, str] = {}
    if astrbot_token:
        astrbot_headers["Authorization"] = f"Bearer {astrbot_token}"

    return [
        _WebhookPlugin(
            channel="wechat",
            display_name="企业微信",
            endpoint=_env_str("WECHAT_WEBHOOK_URL"),
            payload_builder=lambda title, content: {
                "msgtype": "markdown",
                "markdown": {"content": f"## {title}\n\n{content}"},
            },
            timeout_sec=timeout_sec,
        ),
        _WebhookPlugin(
            channel="feishu",
            display_name="飞书",
            endpoint=_env_str("FEISHU_WEBHOOK_URL"),
            payload_builder=lambda title, content: {"msg_type": "text", "content": {"text": f"{title}\n\n{content}"}},
            timeout_sec=timeout_sec,
        ),
        _TelegramPlugin(
            bot_token=telegram_bot_token,
            chat_id=telegram_chat_id,
            message_thread_id=telegram_message_thread_id,
            timeout_sec=timeout_sec,
        ),
        _EmailPlugin(
            sender=_env_str("EMAIL_SENDER"),
            password=_env_str("EMAIL_PASSWORD"),
            receivers=_split_csv(email_receivers_raw),
        ),
        _PushOverPlugin(
            user_key=_env_str("PUSHOVER_USER_KEY"),
            api_token=_env_str("PUSHOVER_API_TOKEN"),
            timeout_sec=timeout_sec,
        ),
        _PushPlusPlugin(
            token=_env_str("PUSHPLUS_TOKEN"),
            timeout_sec=timeout_sec,
        ),
        _ServerChan3Plugin(
            sendkey=_env_str("SERVERCHAN3_SENDKEY"),
            timeout_sec=timeout_sec,
        ),
        _CustomWebhookPlugin(
            urls=_split_csv(custom_webhook_raw),
            bearer_token=_env_str("CUSTOM_WEBHOOK_BEARER_TOKEN"),
            timeout_sec=timeout_sec,
        ),
        _WebhookPlugin(
            channel="discord",
            display_name="Discord",
            endpoint=discord_endpoint,
            payload_builder=discord_payload_builder,
            timeout_sec=timeout_sec,
            headers=discord_headers,
        ),
        _WebhookPlugin(
            channel="astrbot",
            display_name="AstrBot",
            endpoint=astrbot_url,
            payload_builder=lambda title, content: {"title": title, "content": content},
            timeout_sec=timeout_sec,
            headers=astrbot_headers,
        ),
    ]


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _truncate_utf8_bytes(text: str, max_bytes: int) -> str:
    if max_bytes <= 0:
        return text
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    marker = "\n\n...(truncated)"
    marker_bytes = marker.encode("utf-8")
    allowed = max(max_bytes - len(marker_bytes), 0)
    truncated = encoded[:allowed]
    while True:
        try:
            decoded = truncated.decode("utf-8")
            return decoded + marker
        except UnicodeDecodeError:
            if not truncated:
                return marker
            truncated = truncated[:-1]
