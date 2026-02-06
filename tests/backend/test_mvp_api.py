from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Config


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test_api.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("STOCK_LIST", "600519,000001")

    Config.reset_instance()

    from backend.app.db.api_database import reset_database
    from backend.app.main import create_app

    reset_database()
    app = create_app()

    with TestClient(app) as test_client:
        yield test_client

    reset_database()
    Config.reset_instance()


def test_stocks_sync_and_query(client: TestClient):
    sync_payload = {
        "stocks": [
            {"code": "600519", "name": "贵州茅台", "industry": "白酒", "market": "SH"},
            {"code": "000001", "name": "平安银行", "industry": "银行", "market": "SZ"},
        ]
    }
    sync_resp = client.post("/stocks/sync", json=sync_payload)
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["code"] == 0
    assert sync_data["data"]["synced"] == 2

    list_resp = client.get("/stocks", params={"q": "茅台"})
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["code"] == "600519"


def test_watchlist_crud_and_stocks(client: TestClient):
    create_resp = client.post("/watchlists", json={"name": "观察", "sort_order": 1})
    assert create_resp.status_code == 200
    created = create_resp.json()["data"]
    watchlist_id = created["id"]

    add_resp = client.post(f"/watchlists/{watchlist_id}/stocks", json={"code": "600519", "sort_order": 10})
    assert add_resp.status_code == 200
    assert add_resp.json()["code"] == 0

    list_resp = client.get("/watchlists")
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "观察"
    assert items[0]["stock_count"] == 1

    remove_resp = client.delete(f"/watchlists/{watchlist_id}/stocks/600519")
    assert remove_resp.status_code == 200

    delete_resp = client.delete(f"/watchlists/{watchlist_id}")
    assert delete_resp.status_code == 200


def test_reports_history_and_content(client: TestClient, tmp_path: Path):
    report_file = tmp_path / "reports" / "2026-02-05" / "600519" / "120000.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("# 600519\n\n测试报告正文", encoding="utf-8")

    from backend.app.db.api_database import SessionLocal
    from backend.app.models.api_models import AnalysisReport

    with SessionLocal() as session:
        report = AnalysisReport(
            user_id=1,
            code="600519",
            report_type="stock",
            report_date=date(2026, 2, 5),
            markdown_path=str(report_file),
            status="ready",
            source="template",
        )
        session.add(report)
        session.commit()
        report_id = report.id

    stock_reports_resp = client.get("/stock/600519/reports")
    assert stock_reports_resp.status_code == 200
    stock_reports_data = stock_reports_resp.json()["data"]
    assert stock_reports_data["total"] == 1

    all_reports_resp = client.get("/reports", params={"code": "600519"})
    assert all_reports_resp.status_code == 200
    assert all_reports_resp.json()["data"]["total"] == 1

    detail_resp = client.get(f"/reports/{report_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()["data"]
    assert "测试报告正文" in detail_data["markdown"]
    assert detail_data["metadata"]["code"] == "600519"
