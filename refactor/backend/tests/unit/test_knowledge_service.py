from fastapi.testclient import TestClient

from app.main import create_app


def test_upload_ingest_and_search_markdown_document() -> None:
    client = TestClient(create_app())

    uploaded = client.post(
        "/api/v2/knowledge/documents/upload",
        json={
            "title": "trend note",
            "markdown": "# Trend\nMA bullish alignment with volume expansion.\n\n## Risk\nWatch drawdown.",
            "tags": ["strategy", "ma"],
        },
    )
    assert uploaded.status_code == 201
    uploaded_payload = uploaded.json()
    doc_id = uploaded_payload["doc_id"]
    assert uploaded_payload["status"] == "UPLOADED"

    ingested = client.post(f"/api/v2/knowledge/documents/{doc_id}/ingest")
    assert ingested.status_code == 202
    ingest_payload = ingested.json()
    assert ingest_payload["doc_id"] == doc_id
    assert ingest_payload["status"] == "COMPLETED"
    assert ingest_payload["chunk_count"] >= 1

    queried_doc = client.get(f"/api/v2/knowledge/documents/{doc_id}")
    assert queried_doc.status_code == 200
    queried_payload = queried_doc.json()
    assert queried_payload["doc_id"] == doc_id
    assert queried_payload["status"] == "COMPLETED"
    assert queried_payload["chunk_count"] >= 1

    searched = client.get(
        "/api/v2/knowledge/chunks/search",
        params={"query": "volume expansion", "top_k": 3},
    )
    assert searched.status_code == 200
    search_payload = searched.json()
    assert len(search_payload["hits"]) >= 1
    assert search_payload["hits"][0]["doc_id"] == doc_id
    assert search_payload["hits"][0]["section_path"] != ""


def test_delete_document_removes_search_hits() -> None:
    client = TestClient(create_app())

    uploaded = client.post(
        "/api/v2/knowledge/documents/upload",
        json={"title": "macro memo", "markdown": "# Macro\nGDP and employment trends.", "tags": ["macro"]},
    )
    assert uploaded.status_code == 201
    doc_id = uploaded.json()["doc_id"]

    ingested = client.post(f"/api/v2/knowledge/documents/{doc_id}/ingest")
    assert ingested.status_code == 202

    deleted = client.delete(f"/api/v2/knowledge/documents/{doc_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    searched = client.get(
        "/api/v2/knowledge/chunks/search",
        params={"query": "GDP", "top_k": 3, "doc_id": doc_id},
    )
    assert searched.status_code == 200
    assert searched.json()["hits"] == []
