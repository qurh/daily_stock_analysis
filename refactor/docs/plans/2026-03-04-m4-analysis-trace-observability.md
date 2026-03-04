# M4 Analysis Trace Observability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add node-level observability fields (`attempts`, `duration_ms`, `degraded`) to analysis workflow traces and make them queryable from existing APIs.

**Architecture:** Keep current analysis flow executor unchanged in behavior, and only enrich node trace payloads emitted by `AnalysisService`. Persist optional observability columns in `workflow_trace_nodes` via backward-compatible SQLite schema evolution (`_ensure_column`) and expose them in `WorkflowService.get_execution`.

**Tech Stack:** Python 3.10, FastAPI, SQLite, pytest.

### Task 1: RED tests for trace observability payload

**Files:**
- Modify: `refactor/backend/tests/unit/test_analysis_jobs.py`
- Modify: `refactor/backend/tests/unit/test_workflow_executions.py`

**Step 1: Write failing test assertions**

```python
assert prompt_node["attempts"] == 2
assert isinstance(prompt_node["duration_ms"], int)
assert prompt_node["degraded"] is True
```

```python
node = queried_payload["trace"]["nodes"][0]
assert "attempts" in node
assert "duration_ms" in node
assert "degraded" in node
```

**Step 2: Run targeted tests to verify failure**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py`  
Expected: FAIL because trace nodes currently only contain `node_id/status/started_at/ended_at`.

### Task 2: GREEN implementation for trace metrics capture and persistence

**Files:**
- Modify: `refactor/backend/src/app/services/analysis_service.py`
- Modify: `refactor/backend/src/app/services/workflow_service.py`
- Modify: `refactor/backend/src/app/persistence/sqlite_db.py`

**Step 1: Capture node-level observability in analysis execution**

```python
trace_nodes.append({
    "node_id": node_id,
    "status": "succeeded",
    "attempts": attempts,
    "duration_ms": duration_ms,
    "degraded": attempts > 1,
})
```

**Step 2: Persist and read optional observability fields in workflow trace table**

```python
self._ensure_column(..., table_name="workflow_trace_nodes", column_name="attempts", column_ddl="INTEGER NOT NULL DEFAULT 1")
self._ensure_column(..., table_name="workflow_trace_nodes", column_name="duration_ms", column_ddl="INTEGER NOT NULL DEFAULT 0")
self._ensure_column(..., table_name="workflow_trace_nodes", column_name="degraded", column_ddl="INTEGER NOT NULL DEFAULT 0")
```

```python
"attempts": int(item["attempts"]),
"duration_ms": int(item["duration_ms"]),
"degraded": bool(item["degraded"]),
```

**Step 3: Re-run targeted tests to verify passing**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py`  
Expected: PASS.

### Task 3: Verification + docs + iteration records

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代264-M4-analysis-langgraph-adapter-fallback.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代265-M4-analysis-trace-observability.md`

**Step 1: Full verification**

Run: `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_notification_hub.py`  
Expected: PASS.

Run: `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: PASS.

Run: `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`  
Expected: PASS.
