import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_metrics_expose_workflow_trace_observability_snapshot(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "metrics-route.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    client = TestClient(create_app())
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    within_24h = (now_dt - timedelta(hours=6)).isoformat()
    within_7d = (now_dt - timedelta(days=2)).isoformat()
    within_30d = (now_dt - timedelta(days=15)).isoformat()
    older_than_30d = (now_dt - timedelta(days=40)).isoformat()

    with client.app.state.database.connection() as conn:
        conn.executemany(
            """
            INSERT INTO workflow_executions (
                execution_id, flow_id, input_json, status, output_json, created_at, updated_at
            )
            VALUES (?, 'stock_analysis_v1', '{}', 'succeeded', '{}', ?, ?)
            """,
            [
                ("metrics-trace-exec-1", now, now),
                ("metrics-trace-exec-2", now, now),
                ("metrics-trace-exec-3", now, now),
                ("metrics-trace-exec-4", now, now),
            ],
        )
        conn.executemany(
            """
            INSERT INTO workflow_trace_nodes (
                execution_id, node_id, status, started_at, ended_at, attempts, duration_ms, degraded,
                failure_code, degrade_reason, failure_context
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "metrics-trace-exec-1",
                    "resolve_prompt",
                    "succeeded",
                    within_24h,
                    within_24h,
                    1,
                    12,
                    0,
                    None,
                    None,
                    None,
                ),
                (
                    "metrics-trace-exec-2",
                    "resolve_prompt",
                    "succeeded",
                    within_7d,
                    within_7d,
                    2,
                    33,
                    1,
                    None,
                    "retry_recovered",
                    None,
                ),
                (
                    "metrics-trace-exec-3",
                    "resolve_prompt",
                    "failed",
                    within_30d,
                    within_30d,
                    1,
                    8,
                    0,
                    "node_execution_error",
                    None,
                    "prompt resolver hard failure",
                ),
                (
                    "metrics-trace-exec-4",
                    "resolve_prompt",
                    "succeeded",
                    older_than_30d,
                    older_than_30d,
                    1,
                    5,
                    0,
                    None,
                    None,
                    None,
                ),
            ],
        )

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    metrics_text = response.text

    assert "refactor_workflow_trace_nodes_total 4" in metrics_text
    assert "refactor_workflow_trace_nodes_degraded_total 1" in metrics_text
    assert "refactor_workflow_trace_nodes_failed_total 1" in metrics_text
    assert "refactor_workflow_trace_nodes_retry_total 1" in metrics_text
    assert "refactor_workflow_trace_nodes_total_24h 1" in metrics_text
    assert "refactor_workflow_trace_nodes_total_7d 2" in metrics_text
    assert "refactor_workflow_trace_nodes_total_30d 3" in metrics_text
    assert "refactor_workflow_trace_nodes_failed_ratio_30d 0.3333" in metrics_text
    assert "refactor_workflow_trace_nodes_duration_ms_avg_24h 12.0" in metrics_text
    assert 'refactor_workflow_trace_nodes_failure_code_total{failure_code="node_execution_error"} 1' in metrics_text
    assert 'refactor_workflow_trace_nodes_degrade_reason_total{degrade_reason="retry_recovered"} 1' in metrics_text


def test_metrics_expose_agent_tool_trace_observability_snapshot(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "metrics-route-agent.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    client = TestClient(create_app())
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    within_24h = (now_dt - timedelta(hours=2)).isoformat()
    within_7d = (now_dt - timedelta(days=3)).isoformat()
    within_30d = (now_dt - timedelta(days=20)).isoformat()
    older_than_30d = (now_dt - timedelta(days=45)).isoformat()

    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO conversation_sessions (session_id, user_id, memory_policy, status, created_at, updated_at)
            VALUES ('metrics-agent-session', 'u-agent-metrics', 'summary_v1', 'active', ?, ?)
            """,
            (now, now),
        )
        conn.executemany(
            """
            INSERT INTO conversation_messages (
                message_id, session_id, role, content, citations_json, tool_trace_json, token_count, created_at
            )
            VALUES (?, 'metrics-agent-session', 'assistant', 'reply', '[]', ?, 16, ?)
            """,
            [
                (
                    "metrics-agent-msg-1",
                    json.dumps(
                        {
                            "agent_trace": {
                                "trace": [
                                    {
                                        "tool_name": "knowledge.search",
                                        "status": "succeeded",
                                        "latency_ms": 10,
                                        "attempts": 1,
                                        "error_code": None,
                                    }
                                ]
                            }
                        },
                        ensure_ascii=False,
                    ),
                    within_24h,
                ),
                (
                    "metrics-agent-msg-2",
                    json.dumps(
                        {
                            "agent_trace": {
                                "trace": [
                                    {
                                        "tool_name": "backtest.performance",
                                        "status": "degraded",
                                        "latency_ms": 30,
                                        "attempts": 2,
                                        "error_code": "AGT-CALL-003",
                                    }
                                ]
                            }
                        },
                        ensure_ascii=False,
                    ),
                    within_7d,
                ),
                (
                    "metrics-agent-msg-3",
                    json.dumps(
                        {
                            "agent_trace": {
                                "trace": [
                                    {
                                        "tool_name": "workflow.execution.get",
                                        "status": "failed",
                                        "latency_ms": 20,
                                        "attempts": 1,
                                        "error_code": "AGT-FALLBACK-004",
                                    }
                                ]
                            }
                        },
                        ensure_ascii=False,
                    ),
                    within_30d,
                ),
                (
                    "metrics-agent-msg-4",
                    json.dumps(
                        {
                            "agent_trace": {
                                "trace": [
                                    {
                                        "tool_name": "memory.search",
                                        "status": "succeeded",
                                        "latency_ms": 40,
                                        "attempts": 1,
                                        "error_code": None,
                                    }
                                ]
                            }
                        },
                        ensure_ascii=False,
                    ),
                    older_than_30d,
                ),
            ],
        )

    response = client.get("/api/v2/metrics")
    assert response.status_code == 200
    metrics_text = response.text

    assert "refactor_agent_tool_calls_total 4" in metrics_text
    assert "refactor_agent_tool_calls_succeeded_total 2" in metrics_text
    assert "refactor_agent_tool_calls_degraded_total 1" in metrics_text
    assert "refactor_agent_tool_calls_failed_total 1" in metrics_text
    assert "refactor_agent_tool_calls_retry_total 1" in metrics_text
    assert "refactor_agent_tool_calls_latency_ms_avg 25.0" in metrics_text
    assert "refactor_agent_tool_calls_total_24h 1" in metrics_text
    assert "refactor_agent_tool_calls_total_7d 2" in metrics_text
    assert "refactor_agent_tool_calls_total_30d 3" in metrics_text
    assert "refactor_agent_tool_calls_failed_ratio_30d 0.3333" in metrics_text
    assert 'refactor_agent_tool_calls_by_tool_total{tool_name="backtest.performance"} 1' in metrics_text
    assert 'refactor_agent_tool_calls_by_status_total{status="degraded"} 1' in metrics_text
    assert 'refactor_agent_tool_calls_error_code_total{error_code="AGT-CALL-003"} 1' in metrics_text
