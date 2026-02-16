from fastapi.testclient import TestClient

from app.main import create_app


def test_submit_analysis_job_and_query_status_with_trace() -> None:
    client = TestClient(create_app())

    accepted = client.post(
        "/api/v2/analysis/jobs",
        json={"symbol": "600519", "report_type": "detailed"},
    )
    assert accepted.status_code == 202
    accepted_payload = accepted.json()
    assert "job_id" in accepted_payload
    assert accepted_payload["status"] in {"pending", "running", "succeeded"}

    job_id = accepted_payload["job_id"]
    queried = client.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["job_id"] == job_id
    assert payload["status"] == "succeeded"
    assert payload["result"]["report"]["meta"]["stock_code"] == "600519"
    assert payload["trace"]["flow_id"] == "stock_analysis_v1"
    assert len(payload["trace"]["nodes"]) >= 2
