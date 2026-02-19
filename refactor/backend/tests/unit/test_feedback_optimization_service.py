from fastapi.testclient import TestClient

from app.main import create_app


def _create_analysis_job(client: TestClient, symbol: str) -> str:
    created = client.post(
        "/api/v2/analysis/jobs",
        json={"symbol": symbol, "report_type": "detailed"},
    )
    assert created.status_code == 202
    return created.json()["job_id"]


def test_feedback_record_create_and_list() -> None:
    client = TestClient(create_app())
    created = client.post(
        "/api/v2/feedback/records",
        json={
            "target_type": "analysis",
            "target_id": "analysis-001",
            "score": 4.5,
            "tags": ["clear", "actionable"],
            "comment": "good result",
            "source": "user",
        },
    )
    assert created.status_code == 201
    feedback_id = created.json()["feedback_id"]

    queried = client.get("/api/v2/feedback/records", params={"target_id": "analysis-001"})
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["count"] >= 1
    item = payload["items"][0]
    assert item["feedback_id"] == feedback_id
    assert item["score"] == 4.5
    assert item["source"] == "user"


def test_optimization_trigger_uses_feedback_and_backtest_features() -> None:
    client = TestClient(create_app())
    _create_analysis_job(client, "600519")
    _create_analysis_job(client, "000001")

    backtest_job = client.post("/api/v2/backtest/jobs", json={"scope": "market", "eval_window_days": 10})
    assert backtest_job.status_code == 202
    backtest_job_id = backtest_job.json()["job_id"]

    feedback_inputs = [
        {"target_type": "analysis", "target_id": "a-1", "score": 5, "source": "user"},
        {"target_type": "analysis", "target_id": "a-2", "score": 3, "source": "user"},
        {"target_type": "analysis", "target_id": "a-3", "score": 4, "source": "chatbot"},
    ]
    for payload in feedback_inputs:
        created = client.post("/api/v2/feedback/records", json=payload)
        assert created.status_code == 201

    triggered = client.post(
        "/api/v2/optimization/jobs/trigger",
        json={
            "trigger_source": "manual",
            "reason": "weekly review",
            "backtest_job_id": backtest_job_id,
        },
    )
    assert triggered.status_code == 202
    trigger_payload = triggered.json()
    assert trigger_payload["status"] == "completed"
    assert trigger_payload["feature_set"]["feedback"]["count"] >= 3
    assert trigger_payload["feature_set"]["backtest"]["job_id"] == backtest_job_id
    assert trigger_payload["result"]["quality_score"] is not None


def test_feedback_record_auto_triggers_event_optimization_when_threshold_met(monkeypatch) -> None:
    monkeypatch.setenv("FEEDBACK_EVENT_OPTIMIZATION_ENABLED", "1")
    monkeypatch.setenv("FEEDBACK_EVENT_OPTIMIZATION_MIN_RECORDS", "2")
    monkeypatch.setenv("FEEDBACK_EVENT_OPTIMIZATION_COOLDOWN_SECONDS", "0")

    client = TestClient(create_app())

    first = client.post(
        "/api/v2/feedback/records",
        json={"target_type": "analysis", "target_id": "evt-1", "score": 5, "source": "user"},
    )
    assert first.status_code == 201
    first_payload = first.json()
    assert first_payload["optimization_trigger"]["triggered"] is False
    assert first_payload["optimization_trigger"]["reason"] == "threshold_not_met"

    second = client.post(
        "/api/v2/feedback/records",
        json={"target_type": "analysis", "target_id": "evt-2", "score": 4, "source": "chatbot"},
    )
    assert second.status_code == 201
    second_payload = second.json()
    assert second_payload["optimization_trigger"]["triggered"] is True
    assert second_payload["optimization_trigger"]["job"]["trigger_source"] == "event"
    assert second_payload["optimization_trigger"]["job"]["status"] == "completed"
    assert second_payload["optimization_trigger"]["job"]["result"]["quality_score"] is not None


def test_chatbot_proposal_review_flow() -> None:
    client = TestClient(create_app())
    created = client.post(
        "/api/v2/optimization/proposals",
        json={
            "source": "chatbot",
            "target": "prompt.chat.reply",
            "summary": "reduce hallucination",
            "diff": {"prompt_patch": "Add stricter citation requirements."},
        },
    )
    assert created.status_code == 201
    proposal_id = created.json()["proposal_id"]
    assert created.json()["status"] == "review_pending"

    approved = client.post(
        f"/api/v2/optimization/proposals/{proposal_id}/approve",
        json={"reviewer": "qrh", "note": "looks good"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["reviewer"] == "qrh"

    conflict = client.post(
        f"/api/v2/optimization/proposals/{proposal_id}/reject",
        json={"reviewer": "qrh", "reason": "conflict check"},
    )
    assert conflict.status_code == 409

    created_2 = client.post(
        "/api/v2/optimization/proposals",
        json={
            "source": "manual",
            "target": "workflow.stock.analysis",
            "summary": "change node order",
            "diff": {"flow_patch": "Swap macro and sentiment nodes."},
        },
    )
    proposal_id_2 = created_2.json()["proposal_id"]
    rejected = client.post(
        f"/api/v2/optimization/proposals/{proposal_id_2}/reject",
        json={"reviewer": "qrh", "reason": "insufficient evidence"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
