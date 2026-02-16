import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app


def _create_chat_session_with_messages(client: TestClient) -> str:
    created = client.post("/api/v2/chat/sessions", json={"user_id": "u-context", "memory_policy": "summary_v1"})
    assert created.status_code == 201
    session_id = created.json()["session_id"]
    m1 = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "趋势向上分批买入，回撤控制仓位"},
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


def test_analysis_includes_active_strategy_binding_context() -> None:
    client = TestClient(create_app())
    strategy_id = _create_active_strategy(client, strategy_type="analysis")
    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "stock_analysis_v1",
            "prompt_refs": ["prompt.analysis.reply@1"],
            "effective_scope": {"symbols": ["600519"], "report_type": "detailed"},
        },
    )
    assert bound.status_code == 201
    binding_id = bound.json()["binding_id"]

    created = client.post("/api/v2/analysis/jobs", json={"symbol": "600519", "report_type": "detailed"})
    assert created.status_code == 202
    job_id = created.json()["job_id"]
    queried = client.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    strategy_context = queried.json()["result"]["report"]["meta"]["strategy_context"]
    assert strategy_context["binding_id"] == binding_id
    assert strategy_context["strategy_id"] == strategy_id
    assert strategy_context["flow_id"] == "stock_analysis_v1"


def test_chat_tool_trace_includes_active_strategy_binding_context() -> None:
    client = TestClient(create_app())
    strategy_id = _create_active_strategy(client, strategy_type="analysis")
    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "chat_reply_v1",
            "prompt_refs": ["prompt.chat.reply@strategy"],
            "effective_scope": {"scope": "global"},
        },
    )
    assert bound.status_code == 201

    session = client.post("/api/v2/chat/sessions", json={"user_id": "u-chat-bind", "memory_policy": "summary_v1"})
    assert session.status_code == 201
    session_id = session.json()["session_id"]
    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "请给我一个趋势与仓位控制建议"},
    )
    assert replied.status_code == 200
    tool_trace = replied.json()["assistant"]["tool_trace"]
    assert tool_trace["strategy_id"] == strategy_id
    assert tool_trace["strategy_binding_id"] == bound.json()["binding_id"]
    assert tool_trace["strategy_flow_id"] == "chat_reply_v1"


def test_chat_uses_strategy_bound_prompt_ref_when_available() -> None:
    client = TestClient(create_app())

    # Prepare default prompt template.
    default_template = client.post(
        "/api/v2/prompts/templates",
        json={"prompt_id": "prompt.chat.reply", "name": "chat default", "module": "chat"},
    )
    assert default_template.status_code == 201
    default_version = client.post(
        "/api/v2/prompts/templates/prompt.chat.reply/versions",
        json={
            "content": "DEFAULT_PROMPT Q={{question}} K={{knowledge_hint}} M={{memory_hint}}",
            "variables": ["question", "knowledge_hint", "memory_hint"],
            "output_schema": "chat_reply_v1",
        },
    )
    assert default_version.status_code == 201
    default_publish = client.post("/api/v2/prompts/templates/prompt.chat.reply/versions/1/publish")
    assert default_publish.status_code == 200

    # Prepare strategy prompt template.
    strategy_template = client.post(
        "/api/v2/prompts/templates",
        json={"prompt_id": "prompt.chat.reply.strategy", "name": "chat strategy", "module": "chat"},
    )
    assert strategy_template.status_code == 201
    strategy_version = client.post(
        "/api/v2/prompts/templates/prompt.chat.reply.strategy/versions",
        json={
            "content": "STRATEGY_PROMPT Q={{question}} K={{knowledge_hint}} M={{memory_hint}}",
            "variables": ["question", "knowledge_hint", "memory_hint"],
            "output_schema": "chat_reply_v1",
        },
    )
    assert strategy_version.status_code == 201
    strategy_publish = client.post("/api/v2/prompts/templates/prompt.chat.reply.strategy/versions/1/publish")
    assert strategy_publish.status_code == 200

    strategy_id = _create_active_strategy(client, strategy_type="analysis")
    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "chat_reply_v1",
            "prompt_refs": ["prompt.chat.reply.strategy@1"],
            "effective_scope": {"scope": "global"},
        },
    )
    assert bound.status_code == 201

    session = client.post("/api/v2/chat/sessions", json={"user_id": "u-chat-prompt", "memory_policy": "summary_v1"})
    assert session.status_code == 201
    session_id = session.json()["session_id"]
    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "请给我一个趋势与仓位控制建议"},
    )
    assert replied.status_code == 200
    assistant = replied.json()["assistant"]
    assert assistant["tool_trace"]["prompt_ref"] == "prompt.chat.reply.strategy@1"
    assert "STRATEGY_PROMPT" in assistant["content"]


def test_chat_strict_prompt_lock_mode_rejects_missing_bound_version(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_REF_LOCK_MODE", "strict")
    client = TestClient(create_app())

    strategy_template = client.post(
        "/api/v2/prompts/templates",
        json={"prompt_id": "prompt.chat.reply.strategy", "name": "chat strategy", "module": "chat"},
    )
    assert strategy_template.status_code == 201
    strategy_version = client.post(
        "/api/v2/prompts/templates/prompt.chat.reply.strategy/versions",
        json={
            "content": "STRATEGY_PROMPT_V1 Q={{question}}",
            "variables": ["question", "knowledge_hint", "memory_hint"],
            "output_schema": "chat_reply_v1",
        },
    )
    assert strategy_version.status_code == 201
    strategy_publish = client.post("/api/v2/prompts/templates/prompt.chat.reply.strategy/versions/1/publish")
    assert strategy_publish.status_code == 200

    strategy_id = _create_active_strategy(client, strategy_type="analysis")
    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "chat_reply_v1",
            "prompt_refs": ["prompt.chat.reply.strategy@2"],
            "effective_scope": {"scope": "global"},
        },
    )
    assert bound.status_code == 201

    session = client.post("/api/v2/chat/sessions", json={"user_id": "u-chat-strict", "memory_policy": "summary_v1"})
    assert session.status_code == 201
    session_id = session.json()["session_id"]
    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "请给我一个趋势建议"},
    )
    assert replied.status_code == 409
    detail = replied.json()["detail"]
    assert detail["error_code"] == "PROMPT_LOCK_ERROR"
    assert detail["lock_mode"] == "strict"
    assert detail["flow_id"] == "chat_reply_v1"
    assert detail["requested_prompt_refs"] == ["prompt.chat.reply.strategy@2"]
    assert len(detail["failures"]) >= 1
    assert detail["failures"][0]["prompt_ref"] == "prompt.chat.reply.strategy@2"


def test_chat_binding_lenient_overrides_global_strict_mode(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_REF_LOCK_MODE", "strict")
    client = TestClient(create_app())

    strategy_template = client.post(
        "/api/v2/prompts/templates",
        json={"prompt_id": "prompt.chat.reply.strategy", "name": "chat strategy", "module": "chat"},
    )
    assert strategy_template.status_code == 201
    strategy_version = client.post(
        "/api/v2/prompts/templates/prompt.chat.reply.strategy/versions",
        json={
            "content": "STRATEGY_PROMPT_V1 Q={{question}}",
            "variables": ["question", "knowledge_hint", "memory_hint"],
            "output_schema": "chat_reply_v1",
        },
    )
    assert strategy_version.status_code == 201
    strategy_publish = client.post("/api/v2/prompts/templates/prompt.chat.reply.strategy/versions/1/publish")
    assert strategy_publish.status_code == 200

    strategy_id = _create_active_strategy(client, strategy_type="analysis")
    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "chat_reply_v1",
            "prompt_refs": ["prompt.chat.reply.strategy@2"],
            "prompt_lock_mode": "lenient",
            "effective_scope": {"scope": "global"},
        },
    )
    assert bound.status_code == 201

    session = client.post(
        "/api/v2/chat/sessions",
        json={"user_id": "u-chat-lenient-override", "memory_policy": "summary_v1"},
    )
    assert session.status_code == 201
    session_id = session.json()["session_id"]
    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "请给我一个趋势建议"},
    )
    assert replied.status_code == 200
    assistant = replied.json()["assistant"]
    assert assistant["tool_trace"]["prompt_ref"] == "prompt.chat.reply.strategy@1"


def test_analysis_strict_prompt_lock_mode_rejects_missing_bound_version(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_REF_LOCK_MODE", "strict")
    client = TestClient(create_app())

    strategy_id = _create_active_strategy(client, strategy_type="analysis")
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
    job_id = created.json()["job_id"]
    queried = client.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["status"] == "failed"
    detail = payload["result"]["error"]
    assert detail["error_code"] == "PROMPT_LOCK_ERROR"
    assert detail["lock_mode"] == "strict"
    assert detail["flow_id"] == "stock_analysis_v1"
    assert detail["requested_prompt_refs"] == ["prompt.analysis.reply.strategy@3"]
    assert len(detail["failures"]) >= 1
    assert detail["failures"][0]["prompt_ref"] == "prompt.analysis.reply.strategy@3"


def test_analysis_binding_lenient_overrides_global_strict_mode(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_REF_LOCK_MODE", "strict")
    client = TestClient(create_app())

    template = client.post(
        "/api/v2/prompts/templates",
        json={"prompt_id": "prompt.analysis.reply.strategy", "name": "analysis strategy", "module": "analysis"},
    )
    assert template.status_code == 201
    version = client.post(
        "/api/v2/prompts/templates/prompt.analysis.reply.strategy/versions",
        json={
            "content": "ANALYSIS_PROMPT_V1 S={{symbol}} R={{report_type}}",
            "variables": ["symbol", "report_type"],
            "output_schema": "analysis_report_v1",
        },
    )
    assert version.status_code == 201
    publish = client.post("/api/v2/prompts/templates/prompt.analysis.reply.strategy/versions/1/publish")
    assert publish.status_code == 200

    strategy_id = _create_active_strategy(client, strategy_type="analysis")
    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "stock_analysis_v1",
            "prompt_refs": ["prompt.analysis.reply.strategy@3"],
            "prompt_lock_mode": "lenient",
            "effective_scope": {"symbols": ["600519"], "report_type": "detailed"},
        },
    )
    assert bound.status_code == 201

    created = client.post("/api/v2/analysis/jobs", json={"symbol": "600519", "report_type": "detailed"})
    assert created.status_code == 202
    assert created.json()["status"] == "succeeded"
    job_id = created.json()["job_id"]
    queried = client.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["status"] == "succeeded"
    meta = payload["result"]["report"]["meta"]
    assert meta["prompt_ref"] == "prompt.analysis.reply.strategy@1"
