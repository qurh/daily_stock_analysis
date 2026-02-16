from fastapi.testclient import TestClient

from app.main import create_app


def test_prompt_publish_and_rollback() -> None:
    client = TestClient(create_app())

    created_template = client.post(
        "/api/v2/prompts/templates",
        json={"prompt_id": "prompt.analysis.merge", "name": "analysis merge", "module": "analysis"},
    )
    assert created_template.status_code == 201

    version_1 = client.post(
        "/api/v2/prompts/templates/prompt.analysis.merge/versions",
        json={"content": "v1", "variables": ["symbol"], "output_schema": "analysis_dashboard_v2"},
    )
    assert version_1.status_code == 201
    assert version_1.json()["version"] == 1

    version_2 = client.post(
        "/api/v2/prompts/templates/prompt.analysis.merge/versions",
        json={"content": "v2", "variables": ["symbol"], "output_schema": "analysis_dashboard_v2"},
    )
    assert version_2.status_code == 201
    assert version_2.json()["version"] == 2

    publish_1 = client.post("/api/v2/prompts/templates/prompt.analysis.merge/versions/1/publish")
    assert publish_1.status_code == 200
    assert publish_1.json()["active_version"] == 1

    publish_2 = client.post("/api/v2/prompts/templates/prompt.analysis.merge/versions/2/publish")
    assert publish_2.status_code == 200
    assert publish_2.json()["active_version"] == 2

    rollback = client.post("/api/v2/prompts/templates/prompt.analysis.merge/rollback")
    assert rollback.status_code == 200
    assert rollback.json()["active_version"] == 1

    queried = client.get("/api/v2/prompts/templates/prompt.analysis.merge")
    assert queried.status_code == 200
    queried_payload = queried.json()
    statuses = {v["version"]: v["status"] for v in queried_payload["versions"]}
    assert statuses[1] == "active"
    assert statuses[2] == "rolled_back"
