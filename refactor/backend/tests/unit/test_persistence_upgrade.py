import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_analysis_job_persists_across_app_restarts(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "persist_across_restarts.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    client_1 = TestClient(create_app())
    created = client_1.post("/api/v2/analysis/jobs", json={"symbol": "600519", "report_type": "detailed"})
    assert created.status_code == 202
    job_id = created.json()["job_id"]

    client_2 = TestClient(create_app())
    queried = client_2.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["job_id"] == job_id
    assert payload["result"]["report"]["meta"]["stock_code"] == "600519"


def test_task_queue_records_are_persisted(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "queue_records.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    client = TestClient(create_app())
    created = client.post("/api/v2/analysis/jobs", json={"symbol": "000001", "report_type": "detailed"})
    assert created.status_code == 202

    connection = sqlite3.connect(db_file)
    try:
        cursor = connection.execute(
            "SELECT COUNT(*) FROM task_queue WHERE task_type IN ('analysis.run', 'workflow.run')"
        )
        row_count = cursor.fetchone()[0]
    finally:
        connection.close()

    assert row_count >= 1
