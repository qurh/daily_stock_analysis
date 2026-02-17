from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expected_direction(analysis_job_id: str, symbol: str, eval_window_days: int) -> str:
    seed = f"{analysis_job_id}:{symbol}:{eval_window_days}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()
    raw_value = int(digest[:8], 16)
    change_pct = ((raw_value % 2001) - 1000) / 100.0
    if abs(change_pct) <= 2.0:
        return "hold"
    return "long" if change_pct > 0 else "short"


def _create_chat_session_with_messages(client: TestClient) -> str:
    created = client.post("/api/v2/chat/sessions", json={"user_id": "u-m3-loop", "memory_policy": "summary_v1"})
    assert created.status_code == 201
    session_id = created.json()["session_id"]
    first = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "趋势向上时分批建仓，注意回撤控制。"},
    )
    assert first.status_code == 200
    second = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "放量突破再加仓，跌破关键位降低仓位。"},
    )
    assert second.status_code == 200
    return session_id


def _seed_analysis_jobs_for_backtest(client: TestClient, eval_window_days: int = 10) -> None:
    symbols = ["600519", "000001", "300750", "601318", "002594", "688981"]
    with client.app.state.database.connection() as conn:
        for symbol in symbols:
            analysis_job_id = str(uuid4())
            direction = _expected_direction(
                analysis_job_id=analysis_job_id,
                symbol=symbol,
                eval_window_days=eval_window_days,
            )
            result = {
                "report": {
                    "meta": {
                        "stock_code": symbol,
                        "report_type": "detailed",
                        "direction": direction,
                    },
                    "dashboard": {"signals": [], "risk_flags": []},
                }
            }
            now = _utc_now()
            conn.execute(
                """
                INSERT INTO analysis_jobs (
                    job_id, symbol, report_type, status, result_json, execution_id, created_at, updated_at
                )
                VALUES (?, ?, 'detailed', 'succeeded', ?, NULL, ?, ?)
                """,
                (analysis_job_id, symbol, json.dumps(result, ensure_ascii=False), now, now),
            )


def test_m3_strategy_backtest_publish_rollback_rehearsal_loop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_file = tmp_path / "m3-acceptance-loop.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("QUEUE_AUTO_PROCESS", "true")
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setenv("CHROMA_COLLECTION", "m3_loop_knowledge")
    monkeypatch.setenv("MEMORY_COLLECTION", "m3_loop_memory")

    from app.main import create_app

    client = TestClient(create_app())

    session_id = _create_chat_session_with_messages(client=client)

    distilled = client.post("/api/v2/strategy/cognition/distill", json={"session_id": session_id})
    assert distilled.status_code == 201
    memo_id = distilled.json()["memo_id"]
    assert distilled.json()["status"] == "review_pending"

    reviewed = client.post(
        f"/api/v2/strategy/cognition/{memo_id}/review",
        json={"action": "approve", "reviewer": "qrh", "editor_notes": "approve for m3 loop rehearsal"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "indexed"
    assert reviewed.json()["knowledge_doc_id"]

    extracted = client.post("/api/v2/strategy/extract", json={"strategy_type": "analysis"})
    assert extracted.status_code == 201
    strategy_id = extracted.json()["strategy_id"]
    assert extracted.json()["status"] == "candidate"

    _seed_analysis_jobs_for_backtest(client=client, eval_window_days=10)

    backtest_created = client.post("/api/v2/backtest/jobs", json={"scope": "market", "eval_window_days": 10})
    assert backtest_created.status_code == 202
    backtest_job_id = backtest_created.json()["job_id"]

    backtest_job = client.get(f"/api/v2/backtest/jobs/{backtest_job_id}")
    assert backtest_job.status_code == 200
    metrics = backtest_job.json()["metrics"]
    assert metrics["sample_size"] >= 6
    assert metrics["win_rate_pct"] >= 50.0

    proposal = client.post(
        "/api/v2/optimization/proposals",
        json={
            "source": "chatbot",
            "target": "strategy.analysis.lifecycle",
            "summary": "promote candidate after passing backtest",
            "diff": {"strategy_id": strategy_id, "backtest_job_id": backtest_job_id},
        },
    )
    assert proposal.status_code == 201
    proposal_id = proposal.json()["proposal_id"]
    assert proposal.json()["status"] == "review_pending"

    approved = client.post(
        f"/api/v2/optimization/proposals/{proposal_id}/approve",
        json={"reviewer": "qrh", "note": "approved in m3 rehearsal"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    published = client.post(
        f"/api/v2/strategy/{strategy_id}/publish",
        json={"backtest_job_id": backtest_job_id},
    )
    assert published.status_code == 200
    assert published.json()["status"] == "active"

    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={"flow_id": "stock_analysis_v1", "effective_scope": {"scope": "global"}},
    )
    assert bound.status_code == 201
    binding_id = bound.json()["binding_id"]
    assert bound.json()["status"] == "active"

    analysis_before = client.post("/api/v2/analysis/jobs", json={"symbol": "600519", "report_type": "detailed"})
    assert analysis_before.status_code == 202
    before_job = client.get(f"/api/v2/jobs/{analysis_before.json()['job_id']}")
    assert before_job.status_code == 200
    before_meta = before_job.json()["result"]["report"]["meta"]
    assert before_meta["strategy_context"]["binding_id"] == binding_id
    assert before_meta["strategy_context"]["strategy_id"] == strategy_id

    rolled_back = client.post(
        f"/api/v2/strategy/{strategy_id}/rollback",
        json={"reason": "manual rollback after rehearsal"},
    )
    assert rolled_back.status_code == 200
    assert rolled_back.json()["status"] == "rolled_back"

    active_bindings = client.get(
        "/api/v2/strategy/bindings",
        params={"flow_id": "stock_analysis_v1", "status": "active"},
    )
    assert active_bindings.status_code == 200
    assert active_bindings.json()["count"] == 0

    analysis_after = client.post("/api/v2/analysis/jobs", json={"symbol": "600519", "report_type": "detailed"})
    assert analysis_after.status_code == 202
    after_job = client.get(f"/api/v2/jobs/{analysis_after.json()['job_id']}")
    assert after_job.status_code == 200
    after_meta = after_job.json()["result"]["report"]["meta"]
    assert "strategy_context" not in after_meta
