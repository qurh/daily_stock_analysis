from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.services.analysis_service import AnalysisService
from app.main import create_app
from app.services.notification_service import ChannelPlugin, NotificationHub, NotificationMessage


class _FakePlugin(ChannelPlugin):
    def __init__(
        self,
        channel: str,
        display_name: str,
        enabled: bool = True,
        failure_message: str | None = None,
        fail_times: int = 0,
    ) -> None:
        self.channel = channel
        self.display_name = display_name
        self._enabled = enabled
        self._failure_message = failure_message
        self._fail_times = max(fail_times, 0)
        self._send_count = 0

    def is_enabled(self) -> tuple[bool, str | None]:
        if self._enabled:
            return True, None
        return False, "not_configured"

    def send(self, title: str, content: str) -> dict[str, Any]:
        self._send_count += 1
        if self._send_count <= self._fail_times:
            raise RuntimeError(f"retryable_failure_{self._send_count}")
        if self._failure_message is not None:
            raise RuntimeError(self._failure_message)
        return {"status": "delivered", "provider_message_id": f"{self.channel}-ok"}


def _create_client_with_fake_hub(hub: NotificationHub | None = None) -> TestClient:
    app = create_app()
    app.state.notification_service = hub or NotificationHub(
        database=app.state.database,
        plugins=[
            _FakePlugin(channel="wechat", display_name="企业微信", enabled=True),
            _FakePlugin(channel="feishu", display_name="飞书", enabled=True, failure_message="boom"),
            _FakePlugin(channel="telegram", display_name="Telegram", enabled=False),
        ],
    )
    return TestClient(app)


def test_notification_hub_send_partial_failure_isolated() -> None:
    hub = NotificationHub(
        plugins=[
            _FakePlugin(channel="wechat", display_name="企业微信", enabled=True),
            _FakePlugin(channel="feishu", display_name="飞书", enabled=True, failure_message="network_error"),
        ]
    )
    report = hub.send(message=NotificationMessage(title="Daily", content="hello world"))
    assert report["summary"]["attempted"] == 2
    assert report["summary"]["succeeded"] == 1
    assert report["summary"]["failed"] == 1
    by_channel = {item["channel"]: item for item in report["items"]}
    assert by_channel["wechat"]["status"] == "delivered"
    assert by_channel["feishu"]["status"] == "failed"
    assert "network_error" in by_channel["feishu"]["error_message"]


def test_notifications_channels_list_and_preview() -> None:
    client = _create_client_with_fake_hub()
    channels = client.get("/api/v2/notifications/channels")
    assert channels.status_code == 200
    payload = channels.json()
    assert payload["count"] == 3
    enabled = {item["channel"]: item["enabled"] for item in payload["items"]}
    assert enabled["wechat"] is True
    assert enabled["telegram"] is False

    preview = client.post(
        "/api/v2/notifications/preview",
        json={"title": "Preview", "content": "stock update", "channels": ["wechat", "feishu"]},
    )
    assert preview.status_code == 200
    preview_payload = preview.json()
    assert preview_payload["count"] == 2
    assert {item["channel"] for item in preview_payload["items"]} == {"wechat", "feishu"}


def test_notifications_send_and_channel_test_endpoint() -> None:
    client = _create_client_with_fake_hub()
    send_resp = client.post(
        "/api/v2/notifications/send",
        json={"title": "Send", "content": "daily report"},
    )
    assert send_resp.status_code == 200
    send_payload = send_resp.json()
    assert send_payload["summary"]["attempted"] == 2
    assert send_payload["summary"]["failed"] == 1
    assert send_payload["summary"]["succeeded"] == 1

    test_resp = client.post(
        "/api/v2/notifications/channels/test",
        json={"channel": "wechat", "title": "Ping", "content": "healthcheck"},
    )
    assert test_resp.status_code == 200
    assert test_resp.json()["result"]["status"] == "delivered"


def test_notifications_send_persists_delivery_records_and_queryable() -> None:
    client = _create_client_with_fake_hub()
    send_resp = client.post(
        "/api/v2/notifications/send",
        json={"title": "Persist", "content": "save records"},
    )
    assert send_resp.status_code == 200
    report = send_resp.json()
    assert report["summary"]["attempted"] == 2

    deliveries = client.get("/api/v2/notifications/deliveries")
    assert deliveries.status_code == 200
    payload = deliveries.json()
    assert payload["count"] == 3
    channels = {item["channel"] for item in payload["items"]}
    assert channels == {"wechat", "feishu", "telegram"}
    assert any(item["status"] == "skipped" for item in payload["items"])
    assert any(item["status"] == "failed" for item in payload["items"])
    assert any(item["status"] == "delivered" for item in payload["items"])


def test_analysis_auto_notification_persists_source_binding(monkeypatch) -> None:
    monkeypatch.setenv("ANALYSIS_AUTO_NOTIFY_ENABLED", "true")
    monkeypatch.setenv("ANALYSIS_AUTO_NOTIFY_CHANNELS", "wechat")
    app = create_app()
    fake_hub = NotificationHub(
        database=app.state.database,
        plugins=[_FakePlugin(channel="wechat", display_name="企业微信", enabled=True)],
    )
    app.state.notification_service = fake_hub
    app.state.analysis_service = AnalysisService(
        database=app.state.database,
        workflow_service=app.state.workflow_service,
        task_queue=app.state.task_queue_service,
        strategy_service=app.state.strategy_service,
        prompt_service=app.state.prompt_service,
        prompt_lock_audit_service=app.state.prompt_lock_audit_service,
        default_prompt_lock_mode=app.state.settings.prompt_ref_lock_mode,
        queue_auto_process=app.state.settings.queue_auto_process,
        notification_service=fake_hub,
        auto_notify_enabled=app.state.settings.analysis_auto_notify_enabled,
        auto_notify_channels=app.state.settings.analysis_auto_notify_channels,
    )
    client = TestClient(app)

    created = client.post("/api/v2/analysis/jobs", json={"symbol": "600519", "report_type": "detailed"})
    assert created.status_code == 202
    job_id = created.json()["job_id"]

    deliveries = client.get("/api/v2/notifications/deliveries", params={"source_type": "analysis_job", "source_id": job_id})
    assert deliveries.status_code == 200
    payload = deliveries.json()
    assert payload["count"] >= 1
    assert all(item["source_type"] == "analysis_job" for item in payload["items"])
    assert all(item["source_id"] == job_id for item in payload["items"])


def test_notification_send_retries_before_success_and_persists_attempt_count() -> None:
    app = create_app()
    retry_plugin = _FakePlugin(channel="feishu", display_name="飞书", enabled=True, fail_times=1)
    app.state.notification_service = NotificationHub(
        database=app.state.database,
        plugins=[retry_plugin],
        max_retries=2,
    )
    client = TestClient(app)

    send_resp = client.post(
        "/api/v2/notifications/send",
        json={"title": "Retry", "content": "retry once then success", "channels": ["feishu"]},
    )
    assert send_resp.status_code == 200
    payload = send_resp.json()
    assert payload["summary"]["attempted"] == 1
    assert payload["summary"]["failed"] == 0
    assert payload["summary"]["succeeded"] == 1
    assert payload["items"][0]["status"] == "delivered"
    assert payload["items"][0]["attempt_count"] == 2
    assert payload["items"][0]["retry_count"] == 1

    deliveries = client.get("/api/v2/notifications/deliveries", params={"channel": "feishu"})
    assert deliveries.status_code == 200
    items = deliveries.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "delivered"
    assert items[0]["attempt_count"] == 2
    assert items[0]["retry_count"] == 1


def test_notifications_retry_delivery_endpoint_retries_failed_record() -> None:
    app = create_app()
    plugin = _FakePlugin(channel="feishu", display_name="飞书", enabled=True, fail_times=1)
    app.state.notification_service = NotificationHub(
        database=app.state.database,
        plugins=[plugin],
        max_retries=0,
    )
    client = TestClient(app)

    first_send = client.post(
        "/api/v2/notifications/send",
        json={"title": "RetryAPI", "content": "first attempt should fail", "channels": ["feishu"]},
    )
    assert first_send.status_code == 200
    assert first_send.json()["items"][0]["status"] == "failed"

    failed_rows = client.get("/api/v2/notifications/deliveries", params={"status": "failed"}).json()["items"]
    assert len(failed_rows) == 1
    failed_delivery_id = failed_rows[0]["delivery_id"]

    retry_resp = client.post(f"/api/v2/notifications/deliveries/{failed_delivery_id}/retry")
    assert retry_resp.status_code == 200
    retry_payload = retry_resp.json()
    assert retry_payload["retry_of_delivery_id"] == failed_delivery_id
    assert retry_payload["report"]["summary"]["succeeded"] == 1

    retry_rows = client.get(
        "/api/v2/notifications/deliveries",
        params={"source_type": "delivery_retry", "source_id": failed_delivery_id},
    )
    assert retry_rows.status_code == 200
    items = retry_rows.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "delivered"
    assert items[0]["retry_of_delivery_id"] == failed_delivery_id


def test_pushplus_send_includes_topic_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("PUSHPLUS_TOKEN", "token-123")
    monkeypatch.setenv("PUSHPLUS_TOPIC", "topic-alpha")
    captured: dict[str, Any] = {}

    class _Resp:
        status_code = 200

    def _fake_post(url: str, json: dict[str, Any], timeout: float):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _Resp()

    monkeypatch.setattr("app.services.notification_service.httpx.post", _fake_post)
    hub = NotificationHub()

    report = hub.send(
        message=NotificationMessage(title="PushPlus", content="with topic"),
        channels=["pushplus"],
    )

    assert report["summary"]["attempted"] == 1
    assert report["summary"]["succeeded"] == 1
    assert captured["url"] == "http://www.pushplus.plus/send"
    assert captured["json"]["token"] == "token-123"
    assert captured["json"]["topic"] == "topic-alpha"


def test_pushplus_send_works_without_topic(monkeypatch) -> None:
    monkeypatch.setenv("PUSHPLUS_TOKEN", "token-123")
    monkeypatch.delenv("PUSHPLUS_TOPIC", raising=False)
    captured: dict[str, Any] = {}

    class _Resp:
        status_code = 200

    def _fake_post(url: str, json: dict[str, Any], timeout: float):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _Resp()

    monkeypatch.setattr("app.services.notification_service.httpx.post", _fake_post)
    hub = NotificationHub()

    report = hub.send(
        message=NotificationMessage(title="PushPlus", content="without topic"),
        channels=["pushplus"],
    )

    assert report["summary"]["attempted"] == 1
    assert report["summary"]["succeeded"] == 1
    assert captured["url"] == "http://www.pushplus.plus/send"
    assert captured["json"]["token"] == "token-123"
    assert "topic" not in captured["json"]
