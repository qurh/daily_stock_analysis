from fastapi.testclient import TestClient

from app.services.analysis_service import AnalysisService
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
    orchestrator = payload["result"]["report"]["meta"]["orchestrator"]
    assert orchestrator["requested"] == "local"
    assert orchestrator["effective"] == "local"
    dashboard = payload["result"]["report"]["dashboard"]
    assert "factors" in dashboard
    assert set(dashboard["factors"].keys()) == {"technical", "macro", "credit", "sentiment"}
    assert "decision" in dashboard
    assert dashboard["decision"]["direction"] in {"long", "hold", "short"}
    assert "confidence" in dashboard["decision"]
    assert isinstance(dashboard["risk_flags"], list)
    assert isinstance(dashboard["signals"], list)
    assert isinstance(payload["result"]["report"]["meta"]["factor_quality_flags"], list)
    assert payload["trace"]["flow_id"] == "stock_analysis_v1"
    for trace_node in payload["trace"]["nodes"]:
        assert trace_node["attempts"] == 1
        assert isinstance(trace_node["duration_ms"], int)
        assert trace_node["duration_ms"] >= 0
        assert trace_node["degraded"] is False
        assert trace_node["failure_code"] is None
        assert trace_node["degrade_reason"] is None
        assert trace_node["failure_context"] is None
    node_ids = [item["node_id"] for item in payload["trace"]["nodes"]]
    assert "collect_factors" in node_ids
    assert "build_dashboard" in node_ids
    assert node_ids[-1] == "finalize_report"


def test_submit_analysis_job_uses_custom_flow_template(monkeypatch) -> None:
    monkeypatch.setenv(
        "ANALYSIS_FLOW_TEMPLATE",
        "resolve_prompt,collect_macro_factor+collect_credit_factor+collect_sentiment_factor+collect_technical_factor,build_dashboard,finalize_report",
    )
    client = TestClient(create_app())

    accepted = client.post(
        "/api/v2/analysis/jobs",
        json={"symbol": "000001", "report_type": "summary"},
    )
    assert accepted.status_code == 202
    job_id = accepted.json()["job_id"]

    queried = client.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    payload = queried.json()
    node_ids = [item["node_id"] for item in payload["trace"]["nodes"]]
    assert node_ids == [
        "resolve_prompt",
        "collect_macro_factor",
        "collect_credit_factor",
        "collect_sentiment_factor",
        "collect_technical_factor",
        "build_dashboard",
        "finalize_report",
    ]


def test_submit_analysis_job_retries_transient_node_failure(monkeypatch) -> None:
    monkeypatch.setenv("ANALYSIS_NODE_MAX_RETRIES", "1")
    attempts = {"count": 0}
    original = AnalysisService._resolve_prompt

    def flaky_resolve_prompt(
        self: AnalysisService,
        symbol: str,
        report_type: str,
        strategy_context: dict | None = None,
    ) -> dict[str, str]:
        if attempts["count"] == 0:
            attempts["count"] += 1
            raise RuntimeError("transient prompt failure")
        return original(self, symbol=symbol, report_type=report_type, strategy_context=strategy_context)

    monkeypatch.setattr(AnalysisService, "_resolve_prompt", flaky_resolve_prompt)
    client = TestClient(create_app())

    accepted = client.post(
        "/api/v2/analysis/jobs",
        json={"symbol": "000333", "report_type": "summary"},
    )
    assert accepted.status_code == 202
    job_id = accepted.json()["job_id"]
    queried = client.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["status"] == "succeeded"
    assert attempts["count"] == 1
    prompt_node = next(item for item in payload["trace"]["nodes"] if item["node_id"] == "resolve_prompt")
    assert prompt_node["status"] == "succeeded"
    assert prompt_node["attempts"] == 2
    assert isinstance(prompt_node["duration_ms"], int)
    assert prompt_node["duration_ms"] >= 0
    assert prompt_node["degraded"] is True
    assert prompt_node["failure_code"] is None
    assert prompt_node["degrade_reason"] == "retry_recovered"
    assert prompt_node["failure_context"] is None


def test_submit_analysis_job_fails_when_retry_budget_exhausted(monkeypatch) -> None:
    monkeypatch.setenv("ANALYSIS_NODE_MAX_RETRIES", "0")

    def always_fail_resolve_prompt(
        self: AnalysisService,
        symbol: str,
        report_type: str,
        strategy_context: dict | None = None,
    ) -> dict[str, str]:
        raise RuntimeError("prompt resolver hard failure")

    monkeypatch.setattr(AnalysisService, "_resolve_prompt", always_fail_resolve_prompt)
    client = TestClient(create_app())

    accepted = client.post(
        "/api/v2/analysis/jobs",
        json={"symbol": "000651", "report_type": "summary"},
    )
    assert accepted.status_code == 202
    job_id = accepted.json()["job_id"]
    queried = client.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["status"] == "failed"
    prompt_node = next(item for item in payload["trace"]["nodes"] if item["node_id"] == "resolve_prompt")
    assert prompt_node["status"] == "failed"
    assert prompt_node["attempts"] == 1
    assert isinstance(prompt_node["duration_ms"], int)
    assert prompt_node["duration_ms"] >= 0
    assert prompt_node["degraded"] is False
    assert prompt_node["failure_code"] == "node_execution_error"
    assert prompt_node["degrade_reason"] is None
    assert prompt_node["failure_context"] is not None
    assert "prompt resolver hard failure" in prompt_node["failure_context"]


def test_submit_analysis_job_langgraph_import_error_falls_back_to_local(monkeypatch) -> None:
    monkeypatch.setenv("ANALYSIS_ORCHESTRATOR_ENGINE", "langgraph")

    def raise_langgraph_import_error(
        self: AnalysisService,
        context: dict,
        trace_nodes: list,
    ) -> None:
        raise ImportError("langgraph not installed")

    monkeypatch.setattr(AnalysisService, "_execute_flow_with_langgraph", raise_langgraph_import_error)
    client = TestClient(create_app())

    accepted = client.post(
        "/api/v2/analysis/jobs",
        json={"symbol": "600000", "report_type": "summary"},
    )
    assert accepted.status_code == 202
    job_id = accepted.json()["job_id"]
    queried = client.get(f"/api/v2/jobs/{job_id}")
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["status"] == "succeeded"
    orchestrator = payload["result"]["report"]["meta"]["orchestrator"]
    assert orchestrator["requested"] == "langgraph"
    assert orchestrator["effective"] == "local"
    assert orchestrator["warning_code"] == "langgraph_import_error"
