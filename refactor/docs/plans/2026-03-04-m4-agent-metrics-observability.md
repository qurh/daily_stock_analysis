# M4 Agent Metrics Observability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expose Agent runtime observability metrics from persisted chat `agent_trace` into `GET /api/v2/metrics`.

**Architecture:** Reuse existing global metrics route and add a dedicated snapshot loader over `conversation_messages.tool_trace_json`. Keep metrics low-cardinality by aggregating only `tool_name`, `status`, and `error_code`, plus 24h/7d/30d windows.

**Tech Stack:** Python 3.10, FastAPI, SQLite, pytest.

### Task 1: RED contract test for agent metrics

**Files:**
- Modify: `refactor/backend/tests/unit/test_metrics_route.py`

**Step 1: Add failing metrics assertions**

```python
assert "refactor_agent_tool_calls_total 4" in metrics_text
assert 'refactor_agent_tool_calls_by_tool_total{tool_name="backtest.performance"} 1' in metrics_text
```

**Step 2: Run test and verify failure**

Run: `pytest -q refactor/backend/tests/unit/test_metrics_route.py`  
Expected: FAIL because `/api/v2/metrics` does not export agent metrics yet.

### Task 2: GREEN implementation in metrics route

**Files:**
- Modify: `refactor/backend/src/app/api/routes/metrics.py`

**Step 1: Add agent trace snapshot loader**

- Parse `conversation_messages.tool_trace_json`.
- Extract `agent_trace.trace[]` call entries.
- Aggregate:
  - total/succeeded/degraded/failed/retry
  - avg latency and failed ratio
  - windows: 24h/7d/30d
  - labeled counts by `tool_name`, `status`, `error_code`

**Step 2: Append Prometheus series in `get_global_metrics(...)`**

### Task 3: Regression and docs sync

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Modify: `refactor/backend/src/app/main.py`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代270-M4-agent-metrics-observability.md`

**Step 1: Run focused regression**

Run:  
`pytest -q refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_chat_service.py refactor/backend/tests/unit/test_agent_service.py refactor/backend/tests/unit/test_agent_routes.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: PASS.

**Step 2: Run syntax/lint checks**

Run:
- `python3 -m py_compile refactor/backend/src/app/api/routes/metrics.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_metrics_route.py`
- `flake8 refactor/backend/src/app/api/routes/metrics.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_metrics_route.py --max-line-length=120`

Expected: PASS.
