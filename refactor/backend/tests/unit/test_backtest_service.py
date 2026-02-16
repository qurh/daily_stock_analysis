from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app


def _create_analysis_job(client: TestClient, symbol: str) -> str:
    created = client.post(
        "/api/v2/analysis/jobs",
        json={"symbol": symbol, "report_type": "detailed"},
    )
    assert created.status_code == 202
    return created.json()["job_id"]


def test_backtest_job_lifecycle_and_query_endpoints() -> None:
    client = TestClient(create_app())
    _create_analysis_job(client, "600519")
    _create_analysis_job(client, "000001")

    accepted = client.post(
        "/api/v2/backtest/jobs",
        json={"scope": "market", "eval_window_days": 10},
    )
    assert accepted.status_code == 202
    accepted_payload = accepted.json()
    assert "job_id" in accepted_payload

    job_id = accepted_payload["job_id"]
    queried = client.get(f"/api/v2/backtest/jobs/{job_id}")
    assert queried.status_code == 200
    job_payload = queried.json()
    assert job_payload["job_id"] == job_id
    assert job_payload["scope"] == "market"
    assert job_payload["status"] in {"completed", "partial_completed"}
    assert job_payload["metrics"]["sample_size"] >= 2

    results = client.get("/api/v2/backtest/results", params={"job_id": job_id, "limit": 50})
    assert results.status_code == 200
    result_payload = results.json()
    items = result_payload["items"]
    assert len(items) >= 2
    assert {item["job_id"] for item in items} == {job_id}

    performance = client.get("/api/v2/backtest/performance", params={"job_id": job_id})
    assert performance.status_code == 200
    performance_payload = performance.json()
    assert performance_payload["scope"] == "market"
    assert performance_payload["metrics"]["sample_size"] == len(items)

    by_symbol = client.get("/api/v2/backtest/performance/600519")
    assert by_symbol.status_code == 200
    by_symbol_payload = by_symbol.json()
    assert by_symbol_payload["scope"] == "symbol"
    assert by_symbol_payload["symbol"] == "600519"
    assert by_symbol_payload["metrics"]["sample_size"] >= 1


def test_backtest_symbol_scope_only_outputs_target_symbol() -> None:
    client = TestClient(create_app())
    _create_analysis_job(client, "600519")
    _create_analysis_job(client, "000001")

    accepted = client.post(
        "/api/v2/backtest/jobs",
        json={"scope": "symbol", "symbol": "600519", "eval_window_days": 7},
    )
    assert accepted.status_code == 202
    job_id = accepted.json()["job_id"]

    results = client.get("/api/v2/backtest/results", params={"job_id": job_id})
    assert results.status_code == 200
    symbols = {item["symbol"] for item in results.json()["items"]}
    assert symbols == {"600519"}


def test_backtest_marks_incompatible_report_as_insufficient_data() -> None:
    client = TestClient(create_app())
    broken_job_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO analysis_jobs (
                job_id, symbol, report_type, status, result_json, execution_id, created_at, updated_at
            )
            VALUES (?, ?, ?, 'succeeded', ?, NULL, ?, ?)
            """,
            (broken_job_id, "300999", "detailed", "null", now, now),
        )

    accepted = client.post(
        "/api/v2/backtest/jobs",
        json={"scope": "symbol", "symbol": "300999", "eval_window_days": 5},
    )
    assert accepted.status_code == 202
    job_id = accepted.json()["job_id"]

    queried = client.get(f"/api/v2/backtest/jobs/{job_id}")
    assert queried.status_code == 200
    assert queried.json()["status"] == "partial_completed"

    results = client.get("/api/v2/backtest/results", params={"job_id": job_id})
    assert results.status_code == 200
    item = results.json()["items"][0]
    assert item["outcome"] == "insufficient_data"
    assert "insufficient_data" in item["flags"]
