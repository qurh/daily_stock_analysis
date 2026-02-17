import json
import threading
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app
from app.persistence.sqlite_db import SQLiteDatabase
from app.services.prompt_lock_audit_service import PromptLockAuditService


def _create_chat_session_with_messages(client: TestClient) -> str:
    created = client.post("/api/v2/chat/sessions", json={"user_id": "u-audit", "memory_policy": "summary_v1"})
    assert created.status_code == 201
    session_id = created.json()["session_id"]
    m1 = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "趋势上行时分批买入，回撤控制仓位"},
    )
    assert m1.status_code == 200
    m2 = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "放量突破且风险可控时再增持"},
    )
    assert m2.status_code == 200
    return session_id


def _create_active_strategy(client: TestClient, strategy_type: str = "analysis") -> str:
    session_id = _create_chat_session_with_messages(client)
    distilled = client.post("/api/v2/strategy/cognition/distill", json={"session_id": session_id})
    assert distilled.status_code == 201
    memo_id = distilled.json()["memo_id"]
    reviewed = client.post(
        f"/api/v2/strategy/cognition/{memo_id}/review", json={"action": "approve", "reviewer": "qrh"}
    )
    assert reviewed.status_code == 200
    extracted = client.post("/api/v2/strategy/extract", json={"strategy_type": strategy_type})
    assert extracted.status_code == 201
    strategy_id = extracted.json()["strategy_id"]

    now = datetime.now(timezone.utc).isoformat()
    backtest_job_id = str(uuid4())
    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO backtest_jobs (
                job_id, scope, symbol, eval_window_days, status, progress, metrics_json,
                engine_version, started_at, ended_at, created_at, updated_at
            )
            VALUES (?, 'market', NULL, 10, 'completed', 100, ?, 'v1', ?, ?, ?, ?)
            """,
            (
                backtest_job_id,
                json.dumps({"sample_size": 12, "win_rate_pct": 72.5}, ensure_ascii=False),
                now,
                now,
                now,
                now,
            ),
        )
    published = client.post(
        f"/api/v2/strategy/{strategy_id}/publish",
        json={"backtest_job_id": backtest_job_id},
    )
    assert published.status_code == 200
    return strategy_id


def test_prompt_lock_chat_failure_is_recorded_and_queryable(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_REF_LOCK_MODE", "strict")
    client = TestClient(create_app())

    template = client.post(
        "/api/v2/prompts/templates",
        json={"prompt_id": "prompt.chat.reply.strategy", "name": "chat strategy", "module": "chat"},
    )
    assert template.status_code == 201
    version = client.post(
        "/api/v2/prompts/templates/prompt.chat.reply.strategy/versions",
        json={
            "content": "CHAT_STRATEGY_V1 Q={{question}}",
            "variables": ["question", "knowledge_hint", "memory_hint"],
            "output_schema": "chat_reply_v1",
        },
    )
    assert version.status_code == 201
    publish = client.post("/api/v2/prompts/templates/prompt.chat.reply.strategy/versions/1/publish")
    assert publish.status_code == 200

    strategy_id = _create_active_strategy(client)
    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "chat_reply_v1",
            "prompt_refs": ["prompt.chat.reply.strategy@2"],
            "effective_scope": {"scope": "global"},
        },
    )
    assert bound.status_code == 201

    session = client.post("/api/v2/chat/sessions", json={"user_id": "u-audit-chat", "memory_policy": "summary_v1"})
    assert session.status_code == 201
    session_id = session.json()["session_id"]
    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "请给我一个趋势建议"},
    )
    assert replied.status_code == 409

    queried = client.get(
        "/api/v2/prompt-lock/events",
        params={"flow_id": "chat_reply_v1", "source_type": "chat"},
    )
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["count"] >= 1
    item = payload["items"][0]
    assert item["flow_id"] == "chat_reply_v1"
    assert item["source_type"] == "chat"
    assert item["source_id"] == session_id
    assert item["lock_mode"] == "strict"
    assert len(item["failures"]) >= 1


def test_prompt_lock_summary_aggregates_failure_reasons(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_REF_LOCK_MODE", "strict")
    client = TestClient(create_app())

    strategy_id = _create_active_strategy(client)
    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "stock_analysis_v1",
            "prompt_refs": ["prompt.analysis.reply.strategy@3"],
            "effective_scope": {"symbols": ["600519"], "report_type": "detailed"},
        },
    )
    assert bound.status_code == 201

    created = client.post("/api/v2/analysis/jobs", json={"symbol": "600519", "report_type": "detailed"})
    assert created.status_code == 202
    assert created.json()["status"] == "failed"

    summary = client.get(
        "/api/v2/prompt-lock/failures/summary",
        params={"flow_id": "stock_analysis_v1"},
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["total_events"] >= 1
    assert payload["total_failures"] >= 1
    assert any("requested_version_unavailable" in item["reason"] for item in payload["reason_counts"])


def test_prompt_lock_events_support_last_hours_filter() -> None:
    client = TestClient(create_app())

    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(hours=30)).isoformat()
    new_time = now.isoformat()
    old_event_id = str(uuid4())
    new_event_id = str(uuid4())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'old-source', ?, ?, ?)
            """,
            (
                old_event_id,
                json.dumps(["prompt.chat.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "old_reason"}], ensure_ascii=False
                ),
                old_time,
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'new-source', ?, ?, ?)
            """,
            (
                new_event_id,
                json.dumps(["prompt.chat.reply.strategy@3"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@3", "reason": "new_reason"}], ensure_ascii=False
                ),
                new_time,
            ),
        )

    queried = client.get(
        "/api/v2/prompt-lock/events",
        params={"flow_id": "chat_reply_v1", "source_type": "chat", "last_hours": 1},
    )
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["count"] == 1
    assert payload["items"][0]["source_id"] == "new-source"


def test_prompt_lock_summary_supports_last_hours_filter() -> None:
    client = TestClient(create_app())

    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(hours=48)).isoformat()
    new_time = now.isoformat()

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'stock_analysis_v1', 'strict', 'analysis', 'old-job', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.analysis.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.analysis.reply.strategy@2", "reason": "requested_version_unavailable:old"}],
                    ensure_ascii=False,
                ),
                old_time,
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'stock_analysis_v1', 'strict', 'analysis', 'new-job', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.analysis.reply.strategy@4"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.analysis.reply.strategy@4", "reason": "requested_version_unavailable:new"}],
                    ensure_ascii=False,
                ),
                new_time,
            ),
        )

    summary = client.get(
        "/api/v2/prompt-lock/failures/summary",
        params={"flow_id": "stock_analysis_v1", "source_type": "analysis", "last_hours": 1},
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["total_events"] == 1
    assert payload["total_failures"] == 1
    assert payload["reason_counts"][0]["reason"].endswith(":new")


def test_prompt_lock_events_supports_absolute_time_range_filter() -> None:
    client = TestClient(create_app())

    now = datetime.now(timezone.utc)
    older_time = (now - timedelta(hours=4)).isoformat()
    middle_time = (now - timedelta(hours=2)).isoformat()
    newer_time = (now - timedelta(minutes=10)).isoformat()

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'older-source', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "older_reason"}], ensure_ascii=False
                ),
                older_time,
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'middle-source', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "middle_reason"}], ensure_ascii=False
                ),
                middle_time,
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'newer-source', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@3"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@3", "reason": "newer_reason"}], ensure_ascii=False
                ),
                newer_time,
            ),
        )

    start_at = (now - timedelta(hours=3)).isoformat()
    end_at = (now - timedelta(hours=1)).isoformat()
    queried = client.get(
        "/api/v2/prompt-lock/events",
        params={
            "flow_id": "chat_reply_v1",
            "source_type": "chat",
            "start_at": start_at,
            "end_at": end_at,
        },
    )
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["count"] == 1
    assert payload["items"][0]["source_id"] == "middle-source"


def test_prompt_lock_summary_supports_absolute_time_range_filter() -> None:
    client = TestClient(create_app())

    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(hours=3)).isoformat()
    new_time = (now - timedelta(minutes=20)).isoformat()

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'stock_analysis_v1', 'strict', 'analysis', 'old-job', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.analysis.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.analysis.reply.strategy@2", "reason": "requested_version_unavailable:old"}],
                    ensure_ascii=False,
                ),
                old_time,
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'stock_analysis_v1', 'strict', 'analysis', 'new-job', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.analysis.reply.strategy@4"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.analysis.reply.strategy@4", "reason": "requested_version_unavailable:new"}],
                    ensure_ascii=False,
                ),
                new_time,
            ),
        )

    start_at = (now - timedelta(hours=1)).isoformat()
    end_at = now.isoformat()
    summary = client.get(
        "/api/v2/prompt-lock/failures/summary",
        params={
            "flow_id": "stock_analysis_v1",
            "source_type": "analysis",
            "start_at": start_at,
            "end_at": end_at,
        },
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["total_events"] == 1
    assert payload["total_failures"] == 1
    assert payload["reason_counts"][0]["reason"].endswith(":new")


def test_prompt_lock_events_rejects_invalid_time_range() -> None:
    client = TestClient(create_app())

    now = datetime.now(timezone.utc)
    start_at = now.isoformat()
    end_at = (now - timedelta(hours=1)).isoformat()
    queried = client.get(
        "/api/v2/prompt-lock/events",
        params={
            "flow_id": "chat_reply_v1",
            "source_type": "chat",
            "start_at": start_at,
            "end_at": end_at,
        },
    )
    assert queried.status_code == 400
    assert "start_at must be less than or equal to end_at" in queried.json()["detail"]


def test_prompt_lock_summary_rejects_invalid_time_range() -> None:
    client = TestClient(create_app())

    now = datetime.now(timezone.utc)
    start_at = now.isoformat()
    end_at = (now - timedelta(hours=1)).isoformat()
    summary = client.get(
        "/api/v2/prompt-lock/failures/summary",
        params={
            "flow_id": "stock_analysis_v1",
            "source_type": "analysis",
            "start_at": start_at,
            "end_at": end_at,
        },
    )
    assert summary.status_code == 400
    assert "start_at must be less than or equal to end_at" in summary.json()["detail"]


def test_prompt_lock_grouped_summary_supports_dimensions_and_counts() -> None:
    client = TestClient(create_app())

    now = datetime.now(timezone.utc).isoformat()
    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-1', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "binding_inactive"},
                    ],
                    ensure_ascii=False,
                ),
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-2', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "requested_version_unavailable"}],
                    ensure_ascii=False,
                ),
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'stock_analysis_v1', 'strict', 'analysis', 'analysis-1', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.analysis.reply.strategy@3"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.analysis.reply.strategy@3", "reason": "requested_version_unavailable"}],
                    ensure_ascii=False,
                ),
                now,
            ),
        )

    grouped = client.get(
        "/api/v2/prompt-lock/failures/grouped",
        params=[
            ("group_by", "flow_id"),
            ("group_by", "reason"),
        ],
    )
    assert grouped.status_code == 200
    payload = grouped.json()
    assert payload["group_by"] == ["flow_id", "reason"]
    assert payload["total_groups"] == 3
    as_map = {(item["flow_id"], item["reason"]): item["count"] for item in payload["items"]}
    assert as_map[("chat_reply_v1", "requested_version_unavailable")] == 2
    assert as_map[("chat_reply_v1", "binding_inactive")] == 1
    assert as_map[("stock_analysis_v1", "requested_version_unavailable")] == 1


def test_prompt_lock_grouped_summary_supports_absolute_time_filter() -> None:
    client = TestClient(create_app())

    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(hours=3)).isoformat()
    new_time = (now - timedelta(minutes=15)).isoformat()
    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'old-chat', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "requested_version_unavailable:old"}],
                    ensure_ascii=False,
                ),
                old_time,
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'new-chat', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "requested_version_unavailable:new"}],
                    ensure_ascii=False,
                ),
                new_time,
            ),
        )

    grouped = client.get(
        "/api/v2/prompt-lock/failures/grouped",
        params={
            "flow_id": "chat_reply_v1",
            "source_type": "chat",
            "group_by": "reason",
            "start_at": (now - timedelta(hours=1)).isoformat(),
            "end_at": now.isoformat(),
        },
    )
    assert grouped.status_code == 200
    payload = grouped.json()
    assert payload["total_groups"] == 1
    assert payload["items"][0]["reason"].endswith(":new")
    assert payload["items"][0]["count"] == 1


def test_prompt_lock_grouped_summary_rejects_invalid_group_by() -> None:
    client = TestClient(create_app())
    grouped = client.get(
        "/api/v2/prompt-lock/failures/grouped",
        params={"group_by": "unknown_dimension"},
    )
    assert grouped.status_code == 400
    assert "Unsupported group_by dimension" in grouped.json()["detail"]


def test_prompt_lock_failure_trends_supports_hour_granularity() -> None:
    client = TestClient(create_app())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-1', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "binding_inactive"},
                    ],
                    ensure_ascii=False,
                ),
                "2026-02-16T10:10:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-2', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "requested_version_unavailable"}],
                    ensure_ascii=False,
                ),
                "2026-02-16T10:40:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-3', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@3"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@3", "reason": "requested_version_unavailable"}],
                    ensure_ascii=False,
                ),
                "2026-02-16T11:05:00+00:00",
            ),
        )

    trends = client.get(
        "/api/v2/prompt-lock/failures/trends",
        params={"flow_id": "chat_reply_v1", "source_type": "chat", "granularity": "hour"},
    )
    assert trends.status_code == 200
    payload = trends.json()
    assert payload["granularity"] == "hour"
    assert payload["total_buckets"] == 2
    assert payload["items"][0]["bucket_start"] == "2026-02-16T10:00:00+00:00"
    assert payload["items"][0]["event_count"] == 2
    assert payload["items"][0]["failure_count"] == 3
    assert payload["items"][1]["bucket_start"] == "2026-02-16T11:00:00+00:00"
    assert payload["items"][1]["event_count"] == 1
    assert payload["items"][1]["failure_count"] == 1


def test_prompt_lock_failure_trends_supports_day_granularity_with_time_range() -> None:
    client = TestClient(create_app())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'stock_analysis_v1', 'strict', 'analysis', 'analysis-old', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.analysis.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.analysis.reply.strategy@1", "reason": "requested_version_unavailable"}],
                    ensure_ascii=False,
                ),
                "2026-02-15T23:30:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'stock_analysis_v1', 'strict', 'analysis', 'analysis-new', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.analysis.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [
                        {"prompt_ref": "prompt.analysis.reply.strategy@2", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.analysis.reply.strategy@2", "reason": "binding_inactive"},
                    ],
                    ensure_ascii=False,
                ),
                "2026-02-16T08:10:00+00:00",
            ),
        )

    trends = client.get(
        "/api/v2/prompt-lock/failures/trends",
        params={
            "flow_id": "stock_analysis_v1",
            "source_type": "analysis",
            "granularity": "day",
            "start_at": "2026-02-16T00:00:00+00:00",
            "end_at": "2026-02-16T23:59:59+00:00",
        },
    )
    assert trends.status_code == 200
    payload = trends.json()
    assert payload["granularity"] == "day"
    assert payload["total_buckets"] == 1
    assert payload["items"][0]["bucket_start"] == "2026-02-16T00:00:00+00:00"
    assert payload["items"][0]["event_count"] == 1
    assert payload["items"][0]["failure_count"] == 2


def test_prompt_lock_failure_trends_rejects_invalid_granularity() -> None:
    client = TestClient(create_app())
    trends = client.get(
        "/api/v2/prompt-lock/failures/trends",
        params={"granularity": "minute"},
    )
    assert trends.status_code == 400
    assert "Unsupported granularity" in trends.json()["detail"]


def test_prompt_lock_failure_trends_supports_reason_split() -> None:
    client = TestClient(create_app())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-1', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "binding_inactive"},
                    ],
                    ensure_ascii=False,
                ),
                "2026-02-16T12:10:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-2', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "requested_version_unavailable"}],
                    ensure_ascii=False,
                ),
                "2026-02-16T12:40:00+00:00",
            ),
        )

    trends = client.get(
        "/api/v2/prompt-lock/failures/trends",
        params={
            "flow_id": "chat_reply_v1",
            "source_type": "chat",
            "granularity": "hour",
            "split_by": "reason",
        },
    )
    assert trends.status_code == 200
    payload = trends.json()
    assert payload["split_by"] == "reason"
    assert payload["total_buckets"] == 1
    bucket = payload["items"][0]
    assert bucket["bucket_start"] == "2026-02-16T12:00:00+00:00"
    assert bucket["event_count"] == 2
    assert bucket["failure_count"] == 3
    reason_map = {item["reason"]: item["count"] for item in bucket["reason_counts"]}
    assert reason_map["requested_version_unavailable"] == 2
    assert reason_map["binding_inactive"] == 1


def test_prompt_lock_failure_trends_rejects_invalid_split_by() -> None:
    client = TestClient(create_app())
    trends = client.get(
        "/api/v2/prompt-lock/failures/trends",
        params={"split_by": "source_type"},
    )
    assert trends.status_code == 400
    assert "Unsupported split_by" in trends.json()["detail"]


def test_prompt_lock_failure_trends_supports_reason_top_n() -> None:
    client = TestClient(create_app())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-1', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "binding_inactive"},
                    ],
                    ensure_ascii=False,
                ),
                "2026-02-16T12:10:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-2', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [
                        {"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "timeout_provider"},
                    ],
                    ensure_ascii=False,
                ),
                "2026-02-16T12:40:00+00:00",
            ),
        )

    trends = client.get(
        "/api/v2/prompt-lock/failures/trends",
        params={
            "flow_id": "chat_reply_v1",
            "source_type": "chat",
            "granularity": "hour",
            "split_by": "reason",
            "reason_top_n": 2,
        },
    )
    assert trends.status_code == 200
    payload = trends.json()
    assert payload["split_by"] == "reason"
    assert payload["reason_top_n"] == 2
    bucket = payload["items"][0]
    reason_counts = bucket["reason_counts"]
    assert len(reason_counts) == 2
    assert reason_counts[0]["reason"] == "requested_version_unavailable"
    assert reason_counts[0]["count"] == 3
    assert reason_counts[1]["reason"] == "binding_inactive"
    assert reason_counts[1]["count"] == 1


def test_prompt_lock_overview_aggregates_summary_grouped_and_trends() -> None:
    client = TestClient(create_app())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-1', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "binding_inactive"},
                    ],
                    ensure_ascii=False,
                ),
                "2026-02-16T12:10:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-2', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@2"], ensure_ascii=False),
                json.dumps(
                    [
                        {"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "requested_version_unavailable"},
                        {"prompt_ref": "prompt.chat.reply.strategy@2", "reason": "timeout_provider"},
                    ],
                    ensure_ascii=False,
                ),
                "2026-02-16T12:40:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'stock_analysis_v1', 'strict', 'analysis', 'analysis-1', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.analysis.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.analysis.reply.strategy@1", "reason": "requested_version_unavailable"}],
                    ensure_ascii=False,
                ),
                "2026-02-16T12:20:00+00:00",
            ),
        )

    overview = client.get(
        "/api/v2/prompt-lock/overview",
        params=[
            ("flow_id", "chat_reply_v1"),
            ("source_type", "chat"),
            ("group_by", "reason"),
            ("summary_limit", "10"),
            ("grouped_limit", "10"),
            ("granularity", "hour"),
            ("split_by", "reason"),
            ("reason_top_n", "1"),
            ("trend_limit", "10"),
        ],
    )
    assert overview.status_code == 200
    payload = overview.json()

    assert payload["summary"]["total_events"] == 2
    assert payload["summary"]["total_failures"] == 4

    grouped_map = {item["reason"]: item["count"] for item in payload["grouped"]["items"]}
    assert grouped_map["requested_version_unavailable"] == 2
    assert grouped_map["binding_inactive"] == 1
    assert grouped_map["timeout_provider"] == 1

    trends = payload["trends"]
    assert trends["granularity"] == "hour"
    assert trends["split_by"] == "reason"
    assert trends["reason_top_n"] == 1
    assert trends["total_buckets"] == 1
    assert trends["items"][0]["event_count"] == 2
    assert trends["items"][0]["failure_count"] == 4
    assert len(trends["items"][0]["reason_counts"]) == 1
    assert trends["items"][0]["reason_counts"][0]["reason"] == "requested_version_unavailable"


def test_prompt_lock_overview_supports_include_modules() -> None:
    client = TestClient(create_app())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_lock_events (
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            )
            VALUES (?, 'chat_reply_v1', 'strict', 'chat', 'chat-only', ?, ?, ?)
            """,
            (
                str(uuid4()),
                json.dumps(["prompt.chat.reply.strategy@1"], ensure_ascii=False),
                json.dumps(
                    [{"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "requested_version_unavailable"}],
                    ensure_ascii=False,
                ),
                "2026-02-16T13:10:00+00:00",
            ),
        )

    overview = client.get(
        "/api/v2/prompt-lock/overview",
        params=[
            ("flow_id", "chat_reply_v1"),
            ("source_type", "chat"),
            ("include", "summary"),
            ("include", "trends"),
        ],
    )
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["include"] == ["summary", "trends"]
    assert "summary" in payload
    assert "trends" in payload
    assert "grouped" not in payload


def test_prompt_lock_overview_rejects_invalid_include_module() -> None:
    client = TestClient(create_app())

    overview = client.get(
        "/api/v2/prompt-lock/overview",
        params={"include": "events"},
    )
    assert overview.status_code == 400
    assert "Unsupported include module" in overview.json()["detail"]


def test_prompt_lock_overview_cache_hits_and_invalidates_on_new_event(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "prompt_lock_overview_cache.sqlite3"
    database = SQLiteDatabase(f"sqlite:///{db_file}")
    database.init_schema()
    service = PromptLockAuditService(database=database)

    call_counts = {"summary": 0, "grouped": 0, "trends": 0}

    def _fake_summary(**_: object) -> dict[str, object]:
        call_counts["summary"] += 1
        return {"total_events": 1, "total_failures": 1, "reason_counts": []}

    def _fake_grouped(**_: object) -> dict[str, object]:
        call_counts["grouped"] += 1
        return {"group_by": ["reason"], "total_groups": 1, "items": [{"reason": "x", "count": 1}]}

    def _fake_trends(**_: object) -> dict[str, object]:
        call_counts["trends"] += 1
        return {
            "granularity": "hour",
            "split_by": None,
            "reason_top_n": None,
            "total_buckets": 1,
            "items": [{"bucket_start": "2026-02-16T12:00:00+00:00", "event_count": 1, "failure_count": 1}],
        }

    monkeypatch.setattr(service, "summarize_failures", _fake_summary)
    monkeypatch.setattr(service, "group_failures", _fake_grouped)
    monkeypatch.setattr(service, "failure_trends", _fake_trends)

    first = service.build_overview(
        flow_id="chat_reply_v1",
        source_type="chat",
        include=["summary", "grouped", "trends"],
    )
    second = service.build_overview(
        flow_id="chat_reply_v1",
        source_type="chat",
        include=["summary", "grouped", "trends"],
    )

    assert first == second
    assert call_counts == {"summary": 1, "grouped": 1, "trends": 1}

    service.record_event(
        flow_id="chat_reply_v1",
        lock_mode="strict",
        source_type="chat",
        source_id="session-1",
        requested_prompt_refs=["prompt.chat.reply.strategy@1"],
        failures=[{"prompt_ref": "prompt.chat.reply.strategy@1", "reason": "requested_version_unavailable"}],
    )
    _ = service.build_overview(
        flow_id="chat_reply_v1",
        source_type="chat",
        include=["summary", "grouped", "trends"],
    )
    assert call_counts == {"summary": 2, "grouped": 2, "trends": 2}


def test_prompt_lock_overview_runs_selected_modules_in_parallel(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "prompt_lock_overview_parallel.sqlite3"
    database = SQLiteDatabase(f"sqlite:///{db_file}")
    database.init_schema()
    service = PromptLockAuditService(database=database)

    barrier = threading.Barrier(3)

    def _parallel_summary(**_: object) -> dict[str, object]:
        barrier.wait(timeout=1.0)
        return {"total_events": 0, "total_failures": 0, "reason_counts": []}

    def _parallel_grouped(**_: object) -> dict[str, object]:
        barrier.wait(timeout=1.0)
        return {"group_by": ["reason"], "total_groups": 0, "items": []}

    def _parallel_trends(**_: object) -> dict[str, object]:
        barrier.wait(timeout=1.0)
        return {"granularity": "hour", "split_by": None, "reason_top_n": None, "total_buckets": 0, "items": []}

    monkeypatch.setattr(service, "summarize_failures", _parallel_summary)
    monkeypatch.setattr(service, "group_failures", _parallel_grouped)
    monkeypatch.setattr(service, "failure_trends", _parallel_trends)

    payload = service.build_overview(
        flow_id="chat_reply_v1",
        source_type="chat",
        include=["summary", "grouped", "trends"],
    )
    assert payload["include"] == ["summary", "grouped", "trends"]
    assert "summary" in payload
    assert "grouped" in payload
    assert "trends" in payload


def test_prompt_lock_overview_cache_expires_after_ttl(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "prompt_lock_overview_cache_ttl.sqlite3"
    database = SQLiteDatabase(f"sqlite:///{db_file}")
    database.init_schema()
    service = PromptLockAuditService(
        database=database,
        overview_cache_ttl_sec=1,
    )

    now_ref = {"value": 0.0}
    monkeypatch.setattr(service, "_now_monotonic", lambda: now_ref["value"])
    call_count = {"summary": 0}

    def _fake_summary(**_: object) -> dict[str, object]:
        call_count["summary"] += 1
        return {"total_events": 1, "total_failures": 1, "reason_counts": []}

    monkeypatch.setattr(service, "summarize_failures", _fake_summary)

    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])
    now_ref["value"] = 0.5
    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])
    assert call_count["summary"] == 1

    now_ref["value"] = 2.0
    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])
    assert call_count["summary"] == 2


def test_prompt_lock_overview_cache_respects_max_size(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "prompt_lock_overview_cache_size.sqlite3"
    database = SQLiteDatabase(f"sqlite:///{db_file}")
    database.init_schema()
    service = PromptLockAuditService(
        database=database,
        overview_cache_ttl_sec=60,
        overview_cache_max_size=1,
    )

    call_count = {"summary": 0}

    def _fake_summary(**_: object) -> dict[str, object]:
        call_count["summary"] += 1
        return {"total_events": call_count["summary"], "total_failures": 1, "reason_counts": []}

    monkeypatch.setattr(service, "summarize_failures", _fake_summary)

    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])
    _ = service.build_overview(flow_id="stock_analysis_v1", source_type="analysis", include=["summary"])
    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])
    assert call_count["summary"] == 3


def test_prompt_lock_overview_parallel_timeout_degrades_and_skips_cache(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "prompt_lock_overview_parallel_timeout.sqlite3"
    database = SQLiteDatabase(f"sqlite:///{db_file}")
    database.init_schema()
    service = PromptLockAuditService(
        database=database,
        overview_cache_ttl_sec=60,
        overview_cache_max_size=128,
        overview_module_timeout_sec=0.005,
    )

    call_counts = {"summary": 0, "grouped": 0, "trends": 0}

    def _fast_summary(**_: object) -> dict[str, object]:
        call_counts["summary"] += 1
        return {"total_events": 1, "total_failures": 1, "reason_counts": []}

    def _slow_grouped(**_: object) -> dict[str, object]:
        call_counts["grouped"] += 1
        time.sleep(0.05)
        return {"group_by": ["reason"], "total_groups": 1, "items": [{"reason": "x", "count": 1}]}

    def _fast_trends(**_: object) -> dict[str, object]:
        call_counts["trends"] += 1
        return {"granularity": "hour", "split_by": None, "reason_top_n": None, "total_buckets": 0, "items": []}

    monkeypatch.setattr(service, "summarize_failures", _fast_summary)
    monkeypatch.setattr(service, "group_failures", _slow_grouped)
    monkeypatch.setattr(service, "failure_trends", _fast_trends)

    first = service.build_overview(
        flow_id="chat_reply_v1",
        source_type="chat",
        include=["summary", "grouped", "trends"],
    )
    second = service.build_overview(
        flow_id="chat_reply_v1",
        source_type="chat",
        include=["summary", "grouped", "trends"],
    )

    assert first["degraded"] is True
    assert second["degraded"] is True
    assert any(item["module"] == "grouped" and item["code"] == "timeout" for item in first["module_errors"])
    assert first["grouped"]["items"] == []
    assert first["summary"]["total_events"] == 1
    assert "trends" in first
    assert call_counts["summary"] == 2


def test_prompt_lock_overview_parallel_timeout_supports_module_override(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "prompt_lock_overview_parallel_timeout_override.sqlite3"
    database = SQLiteDatabase(f"sqlite:///{db_file}")
    database.init_schema()
    service = PromptLockAuditService(
        database=database,
        overview_cache_ttl_sec=60,
        overview_cache_max_size=128,
        overview_module_timeout_sec=1.0,
        overview_module_timeouts_sec={"grouped": 0.005},
    )

    def _fast_summary(**_: object) -> dict[str, object]:
        return {"total_events": 1, "total_failures": 1, "reason_counts": []}

    def _slow_grouped(**_: object) -> dict[str, object]:
        time.sleep(0.05)
        return {"group_by": ["reason"], "total_groups": 1, "items": [{"reason": "x", "count": 1}]}

    def _fast_trends(**_: object) -> dict[str, object]:
        return {"granularity": "hour", "split_by": None, "reason_top_n": None, "total_buckets": 0, "items": []}

    monkeypatch.setattr(service, "summarize_failures", _fast_summary)
    monkeypatch.setattr(service, "group_failures", _slow_grouped)
    monkeypatch.setattr(service, "failure_trends", _fast_trends)

    payload = service.build_overview(
        flow_id="chat_reply_v1",
        source_type="chat",
        include=["summary", "grouped", "trends"],
    )

    assert payload["degraded"] is True
    assert any(item["module"] == "grouped" and item["code"] == "timeout" for item in payload["module_errors"])
    assert payload["summary"]["total_events"] == 1
    assert payload["grouped"]["items"] == []


def test_prompt_lock_overview_metrics_tracks_timeout_and_cache_hit(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "prompt_lock_overview_metrics.sqlite3"
    database = SQLiteDatabase(f"sqlite:///{db_file}")
    database.init_schema()
    service = PromptLockAuditService(
        database=database,
        overview_cache_ttl_sec=60,
        overview_cache_max_size=128,
        overview_module_timeout_sec=1.0,
        overview_module_timeouts_sec={"grouped": 0.005},
    )

    def _fast_summary(**_: object) -> dict[str, object]:
        return {"total_events": 1, "total_failures": 1, "reason_counts": []}

    def _slow_grouped(**_: object) -> dict[str, object]:
        time.sleep(0.05)
        return {"group_by": ["reason"], "total_groups": 1, "items": [{"reason": "x", "count": 1}]}

    def _fast_trends(**_: object) -> dict[str, object]:
        return {"granularity": "hour", "split_by": None, "reason_top_n": None, "total_buckets": 0, "items": []}

    monkeypatch.setattr(service, "summarize_failures", _fast_summary)
    monkeypatch.setattr(service, "group_failures", _slow_grouped)
    monkeypatch.setattr(service, "failure_trends", _fast_trends)

    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary", "grouped", "trends"])

    monkeypatch.setattr(service, "group_failures", lambda **_: {"group_by": ["reason"], "total_groups": 0, "items": []})
    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])
    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])

    metrics = service.get_overview_metrics()
    assert metrics["request_total"] == 3
    assert metrics["degraded_total"] == 1
    assert metrics["cache_hit_total"] == 1

    grouped = metrics["module_stats"]["grouped"]
    assert grouped["run_total"] == 1
    assert grouped["timeout_total"] == 1
    assert grouped["degraded_total"] == 1

    summary = metrics["module_stats"]["summary"]
    assert summary["run_total"] == 2
    assert summary["success_total"] == 2


def test_prompt_lock_overview_metrics_endpoint_returns_current_counters(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_LOCK_OVERVIEW_MODULE_TIMEOUT_SEC", "0.005")
    client = TestClient(create_app())
    service: PromptLockAuditService = client.app.state.prompt_lock_audit_service

    monkeypatch.setattr(
        service,
        "summarize_failures",
        lambda **_: {"total_events": 1, "total_failures": 1, "reason_counts": []},
    )

    def _slow_grouped(**_: object) -> dict[str, object]:
        time.sleep(0.05)
        return {"group_by": ["reason"], "total_groups": 1, "items": [{"reason": "x", "count": 1}]}

    monkeypatch.setattr(service, "group_failures", _slow_grouped)
    monkeypatch.setattr(
        service,
        "failure_trends",
        lambda **_: {"granularity": "hour", "split_by": None, "reason_top_n": None, "total_buckets": 0, "items": []},
    )

    degraded = client.get(
        "/api/v2/prompt-lock/overview",
        params=[("include", "summary"), ("include", "grouped"), ("include", "trends")],
    )
    assert degraded.status_code == 200
    assert degraded.json()["degraded"] is True

    metrics = client.get("/api/v2/prompt-lock/overview/metrics")
    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload["request_total"] >= 1
    assert payload["degraded_total"] >= 1
    assert payload["module_stats"]["grouped"]["timeout_total"] >= 1


def test_prompt_lock_overview_metrics_prometheus_text_contains_expected_series(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "prompt_lock_overview_prometheus_metrics.sqlite3"
    database = SQLiteDatabase(f"sqlite:///{db_file}")
    database.init_schema()
    service = PromptLockAuditService(
        database=database,
        overview_cache_ttl_sec=60,
        overview_cache_max_size=128,
    )

    monkeypatch.setattr(
        service,
        "summarize_failures",
        lambda **_: {"total_events": 1, "total_failures": 1, "reason_counts": []},
    )
    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])
    _ = service.build_overview(flow_id="chat_reply_v1", source_type="chat", include=["summary"])

    text = service.get_overview_metrics_prometheus()
    assert "refactor_prompt_lock_overview_request_total 2" in text
    assert "refactor_prompt_lock_overview_cache_hit_total 1" in text
    assert 'refactor_prompt_lock_overview_module_run_total{module="summary"} 1' in text
    assert "refactor_prompt_lock_overview_degraded_rate 0.0" in text


def test_prompt_lock_overview_metrics_prometheus_endpoint_returns_text(monkeypatch) -> None:
    client = TestClient(create_app())
    service: PromptLockAuditService = client.app.state.prompt_lock_audit_service
    monkeypatch.setattr(
        service,
        "summarize_failures",
        lambda **_: {"total_events": 1, "total_failures": 1, "reason_counts": []},
    )
    _ = client.get("/api/v2/prompt-lock/overview", params={"include": "summary"})

    response = client.get("/api/v2/prompt-lock/overview/metrics/prometheus")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "refactor_prompt_lock_overview_request_total" in response.text


def test_global_metrics_endpoint_includes_prompt_lock_and_build_info(monkeypatch) -> None:
    client = TestClient(create_app())
    service: PromptLockAuditService = client.app.state.prompt_lock_audit_service
    monkeypatch.setattr(
        service,
        "summarize_failures",
        lambda **_: {"total_events": 1, "total_failures": 1, "reason_counts": []},
    )
    _ = client.get("/api/v2/prompt-lock/overview", params={"include": "summary"})

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "refactor_backend_build_info" in response.text
    assert "refactor_prompt_lock_overview_request_total" in response.text


def test_global_metrics_endpoint_includes_backtest_and_optimization_status_counts() -> None:
    client = TestClient(create_app())
    now = datetime.now(timezone.utc).isoformat()

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO backtest_jobs (
                job_id, scope, symbol, eval_window_days, status, progress, metrics_json,
                engine_version, started_at, ended_at, created_at, updated_at
            ) VALUES (?, 'market', NULL, 10, 'completed', 100, ?, 'v1', ?, ?, ?, ?)
            """,
            (str(uuid4()), json.dumps({"sample_size": 1}, ensure_ascii=False), now, now, now, now),
        )
        conn.execute(
            """
            INSERT INTO backtest_jobs (
                job_id, scope, symbol, eval_window_days, status, progress, metrics_json,
                engine_version, started_at, ended_at, created_at, updated_at
            ) VALUES (?, 'market', NULL, 10, 'running', 50, ?, 'v1', ?, NULL, ?, ?)
            """,
            (str(uuid4()), json.dumps({}, ensure_ascii=False), now, now, now),
        )
        conn.execute(
            """
            INSERT INTO optimization_jobs (
                job_id, trigger_source, reason, backtest_job_id, status,
                feature_set_json, result_json, created_at, updated_at
            ) VALUES (?, 'manual', NULL, NULL, 'queued', NULL, NULL, ?, ?)
            """,
            (str(uuid4()), now, now),
        )
        conn.execute(
            """
            INSERT INTO optimization_jobs (
                job_id, trigger_source, reason, backtest_job_id, status,
                feature_set_json, result_json, created_at, updated_at
            ) VALUES (?, 'event', NULL, NULL, 'completed', ?, ?, ?, ?)
            """,
            (str(uuid4()), json.dumps({}, ensure_ascii=False), json.dumps({}, ensure_ascii=False), now, now),
        )

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    body = response.text
    assert 'refactor_backtest_jobs_total{status="completed"} 1' in body
    assert 'refactor_backtest_jobs_total{status="running"} 1' in body
    assert 'refactor_optimization_jobs_total{status="queued"} 1' in body
    assert 'refactor_optimization_jobs_total{status="completed"} 1' in body


def test_global_metrics_endpoint_includes_analysis_and_workflow_status_counts() -> None:
    client = TestClient(create_app())
    now = datetime.now(timezone.utc).isoformat()

    execution_id_1 = str(uuid4())
    execution_id_2 = str(uuid4())
    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO workflow_executions (
                execution_id, flow_id, input_json, status, output_json, created_at, updated_at
            ) VALUES (?, 'stock_analysis_v1', ?, 'succeeded', ?, ?, ?)
            """,
            (execution_id_1, json.dumps({}, ensure_ascii=False), json.dumps({}, ensure_ascii=False), now, now),
        )
        conn.execute(
            """
            INSERT INTO workflow_executions (
                execution_id, flow_id, input_json, status, output_json, created_at, updated_at
            ) VALUES (?, 'chat_reply_v1', ?, 'running', NULL, ?, ?)
            """,
            (execution_id_2, json.dumps({}, ensure_ascii=False), now, now),
        )
        conn.execute(
            """
            INSERT INTO analysis_jobs (
                job_id, symbol, report_type, status, result_json, execution_id, created_at, updated_at
            ) VALUES (?, '600519', 'standard', 'succeeded', ?, ?, ?, ?)
            """,
            (str(uuid4()), json.dumps({"report": {}}, ensure_ascii=False), execution_id_1, now, now),
        )
        conn.execute(
            """
            INSERT INTO analysis_jobs (
                job_id, symbol, report_type, status, result_json, execution_id, created_at, updated_at
            ) VALUES (?, '000001', 'brief', 'failed', ?, ?, ?, ?)
            """,
            (str(uuid4()), json.dumps({"error": "x"}, ensure_ascii=False), execution_id_2, now, now),
        )

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    body = response.text
    assert 'refactor_analysis_jobs_total{status="succeeded"} 1' in body
    assert 'refactor_analysis_jobs_total{status="failed"} 1' in body
    assert 'refactor_workflow_executions_total{status="succeeded"} 1' in body
    assert 'refactor_workflow_executions_total{status="running"} 1' in body


def test_global_metrics_endpoint_includes_knowledge_chat_memory_metrics() -> None:
    client = TestClient(create_app())
    now = datetime.now(timezone.utc).isoformat()
    session_id = str(uuid4())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO knowledge_documents (
                doc_id, title, source_type, raw_markdown, optimized_markdown, status, tags_json, created_at, updated_at
            ) VALUES (?, 'doc-a', 'upload', '# a', '# a', 'ingested', ?, ?, ?)
            """,
            (str(uuid4()), json.dumps(["ai"], ensure_ascii=False), now, now),
        )
        conn.execute(
            """
            INSERT INTO knowledge_documents (
                doc_id, title, source_type, raw_markdown, optimized_markdown, status, tags_json, created_at, updated_at
            ) VALUES (?, 'doc-b', 'upload', '# b', '# b', 'optimized', ?, ?, ?)
            """,
            (str(uuid4()), json.dumps([], ensure_ascii=False), now, now),
        )
        conn.execute(
            """
            INSERT INTO conversation_sessions (
                session_id, user_id, memory_policy, status, created_at, updated_at
            ) VALUES (?, 'u1', 'summary_v1', 'active', ?, ?)
            """,
            (session_id, now, now),
        )
        conn.execute(
            """
            INSERT INTO memory_summaries (
                summary_id, session_id, covered_range, summary_text, embedding_ref, created_at
            ) VALUES (?, ?, '1-2', 'summary', 'emb-1', ?)
            """,
            (str(uuid4()), session_id, now),
        )
        conn.execute(
            """
            INSERT INTO long_term_memory_entries (
                entry_id, topic, content, score, source_session_id, created_at
            ) VALUES (?, 'risk', 'risk control', 0.8, ?, ?)
            """,
            (str(uuid4()), session_id, now),
        )

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    body = response.text
    assert 'refactor_knowledge_documents_total{status="ingested"} 1' in body
    assert 'refactor_knowledge_documents_total{status="optimized"} 1' in body
    assert 'refactor_conversation_sessions_total{status="active"} 1' in body
    assert "refactor_memory_summaries_total 1" in body
    assert "refactor_long_term_memory_entries_total 1" in body


def test_global_metrics_endpoint_includes_message_and_chunk_metrics() -> None:
    client = TestClient(create_app())
    now = datetime.now(timezone.utc).isoformat()
    session_id = str(uuid4())
    doc_id = str(uuid4())

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO conversation_sessions (
                session_id, user_id, memory_policy, status, created_at, updated_at
            ) VALUES (?, 'u1', 'summary_v1', 'active', ?, ?)
            """,
            (session_id, now, now),
        )
        conn.execute(
            """
            INSERT INTO conversation_messages (
                message_id, session_id, role, content, citations_json, tool_trace_json, token_count, created_at
            ) VALUES (?, ?, 'user', 'hello', ?, ?, 8, ?)
            """,
            (str(uuid4()), session_id, json.dumps([], ensure_ascii=False), json.dumps([], ensure_ascii=False), now),
        )
        conn.execute(
            """
            INSERT INTO conversation_messages (
                message_id, session_id, role, content, citations_json, tool_trace_json, token_count, created_at
            ) VALUES (?, ?, 'assistant', 'hi', ?, ?, 12, ?)
            """,
            (str(uuid4()), session_id, json.dumps([], ensure_ascii=False), json.dumps([], ensure_ascii=False), now),
        )
        conn.execute(
            """
            INSERT INTO knowledge_documents (
                doc_id, title, source_type, raw_markdown, optimized_markdown, status, tags_json, created_at, updated_at
            ) VALUES (?, 'doc-a', 'upload', '# a', '# a', 'ingested', ?, ?, ?)
            """,
            (doc_id, json.dumps([], ensure_ascii=False), now, now),
        )
        conn.execute(
            """
            INSERT INTO knowledge_chunks (
                chunk_id, doc_id, section_path, content, summary, token_count, embedding_ref, created_at
            ) VALUES (?, ?, 'root', 'content-a', 'sum-a', 21, 'emb-a', ?)
            """,
            (str(uuid4()), doc_id, now),
        )
        conn.execute(
            """
            INSERT INTO knowledge_chunks (
                chunk_id, doc_id, section_path, content, summary, token_count, embedding_ref, created_at
            ) VALUES (?, ?, 'root/2', 'content-b', 'sum-b', 34, 'emb-b', ?)
            """,
            (str(uuid4()), doc_id, now),
        )

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    body = response.text
    assert "refactor_conversation_messages_total 2" in body
    assert 'refactor_conversation_messages_by_role_total{role="assistant"} 1' in body
    assert 'refactor_conversation_messages_by_role_total{role="user"} 1' in body
    assert "refactor_knowledge_chunks_total 2" in body
    assert "refactor_knowledge_chunks_token_count_total 55" in body


def test_global_metrics_endpoint_includes_backtest_and_optimization_quality_metrics() -> None:
    client = TestClient(create_app())
    now = datetime.now(timezone.utc).isoformat()
    backtest_job_id = str(uuid4())
    analysis_job_ids = [str(uuid4()), str(uuid4()), str(uuid4())]

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO backtest_jobs (
                job_id, scope, symbol, eval_window_days, status, progress, metrics_json,
                engine_version, started_at, ended_at, created_at, updated_at
            ) VALUES (?, 'market', NULL, 10, 'completed', 100, ?, 'v1', ?, ?, ?, ?)
            """,
            (
                backtest_job_id,
                json.dumps({"sample_size": 3, "win_rate_pct": 66.67}, ensure_ascii=False),
                now,
                now,
                now,
                now,
            ),
        )
        for index, analysis_job_id in enumerate(analysis_job_ids):
            conn.execute(
                """
                INSERT INTO analysis_jobs (
                    job_id, symbol, report_type, status, result_json, execution_id, created_at, updated_at
                ) VALUES (?, ?, 'detailed', 'succeeded', ?, NULL, ?, ?)
                """,
                (
                    analysis_job_id,
                    ["600519", "000001", "300750"][index],
                    json.dumps({"report": {"meta": {"stock_code": "x"}}}, ensure_ascii=False),
                    now,
                    now,
                ),
            )
        conn.execute(
            """
            INSERT INTO backtest_records (
                record_id, job_id, analysis_job_id, symbol, direction,
                outcome, return_pct, direction_correct, flags_json, created_at
            ) VALUES (?, ?, ?, '600519', 'long', 'win', 5.0, 1, ?, ?)
            """,
            (str(uuid4()), backtest_job_id, analysis_job_ids[0], json.dumps([], ensure_ascii=False), now),
        )
        conn.execute(
            """
            INSERT INTO backtest_records (
                record_id, job_id, analysis_job_id, symbol, direction,
                outcome, return_pct, direction_correct, flags_json, created_at
            ) VALUES (?, ?, ?, '000001', 'short', 'loss', -2.0, 0, ?, ?)
            """,
            (str(uuid4()), backtest_job_id, analysis_job_ids[1], json.dumps([], ensure_ascii=False), now),
        )
        conn.execute(
            """
            INSERT INTO backtest_records (
                record_id, job_id, analysis_job_id, symbol, direction,
                outcome, return_pct, direction_correct, flags_json, created_at
            ) VALUES (?, ?, ?, '300750', 'hold', 'insufficient_data', NULL, NULL, ?, ?)
            """,
            (
                str(uuid4()),
                backtest_job_id,
                analysis_job_ids[2],
                json.dumps(["insufficient_data"], ensure_ascii=False),
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO optimization_jobs (
                job_id, trigger_source, reason, backtest_job_id, status,
                feature_set_json, result_json, created_at, updated_at
            ) VALUES (?, 'manual', 'weekly review', ?, 'completed', ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                backtest_job_id,
                json.dumps({}, ensure_ascii=False),
                json.dumps({"quality_score": 82.5, "recommendation": "promote_candidate"}, ensure_ascii=False),
                now,
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO optimization_jobs (
                job_id, trigger_source, reason, backtest_job_id, status,
                feature_set_json, result_json, created_at, updated_at
            ) VALUES (?, 'event', 'feedback low', ?, 'completed', ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                backtest_job_id,
                json.dumps({}, ensure_ascii=False),
                json.dumps({"quality_score": 66.5, "recommendation": "optimize_prompt_or_flow"}, ensure_ascii=False),
                now,
                now,
            ),
        )

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    body = response.text
    assert 'refactor_backtest_records_total{outcome="win"} 1' in body
    assert 'refactor_backtest_records_total{outcome="loss"} 1' in body
    assert 'refactor_backtest_records_total{outcome="insufficient_data"} 1' in body
    assert "refactor_backtest_records_return_pct_avg 1.5" in body
    assert "refactor_backtest_records_direction_accuracy_pct 50.0" in body
    assert "refactor_optimization_quality_score_sample_size 2" in body
    assert "refactor_optimization_quality_score_avg 74.5" in body
    assert 'refactor_optimization_recommendations_total{recommendation="promote_candidate"} 1' in body
    assert 'refactor_optimization_recommendations_total{recommendation="optimize_prompt_or_flow"} 1' in body


def test_global_metrics_endpoint_includes_backtest_return_quantiles_and_stddev() -> None:
    client = TestClient(create_app())
    now = datetime.now(timezone.utc).isoformat()
    backtest_job_id = str(uuid4())
    symbols = ["600519", "000001", "300750", "601318", "002594"]
    returns = [1.0, 2.0, 3.0, 4.0, 5.0]

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO backtest_jobs (
                job_id, scope, symbol, eval_window_days, status, progress, metrics_json,
                engine_version, started_at, ended_at, created_at, updated_at
            ) VALUES (?, 'market', NULL, 10, 'completed', 100, ?, 'v1', ?, ?, ?, ?)
            """,
            (
                backtest_job_id,
                json.dumps({"sample_size": 5, "win_rate_pct": 100.0}, ensure_ascii=False),
                now,
                now,
                now,
                now,
            ),
        )
        for idx, symbol in enumerate(symbols):
            analysis_job_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO analysis_jobs (
                    job_id, symbol, report_type, status, result_json, execution_id, created_at, updated_at
                ) VALUES (?, ?, 'detailed', 'succeeded', ?, NULL, ?, ?)
                """,
                (
                    analysis_job_id,
                    symbol,
                    json.dumps({"report": {"meta": {"stock_code": symbol}}}, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO backtest_records (
                    record_id, job_id, analysis_job_id, symbol, direction,
                    outcome, return_pct, direction_correct, flags_json, created_at
                ) VALUES (?, ?, ?, ?, 'long', 'win', ?, 1, ?, ?)
                """,
                (
                    str(uuid4()),
                    backtest_job_id,
                    analysis_job_id,
                    symbol,
                    returns[idx],
                    json.dumps([], ensure_ascii=False),
                    now,
                ),
            )

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    body = response.text
    assert "refactor_backtest_records_return_pct_p50 3.0" in body
    assert "refactor_backtest_records_return_pct_p90 4.6" in body
    assert "refactor_backtest_records_return_pct_p95 4.8" in body
    assert "refactor_backtest_records_return_pct_p99 4.96" in body
    assert "refactor_backtest_records_return_pct_stddev 1.4142" in body
