# M4 Analysis Trace Failure Reason And Metrics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend analysis workflow trace with structured failure/degradation reasons and expose node-level observability aggregates in `/api/v2/metrics`.

**Architecture:** Keep existing trace contract backward-compatible by adding optional fields (`failure_code`, `degrade_reason`) to each trace node. Persist them in `workflow_trace_nodes` using additive schema evolution, then aggregate observability counters/ratios in metrics route with low-cardinality labels.

**Tech Stack:** Python 3.10, FastAPI, SQLite, pytest.

### Task 1: RED tests for failure/degradation semantics and metrics exposure

**Files:**
- Modify: `refactor/backend/tests/unit/test_analysis_jobs.py`
- Modify: `refactor/backend/tests/unit/test_workflow_executions.py`
- Create: `refactor/backend/tests/unit/test_metrics_route.py`

**Step 1: Add failing assertions in analysis/workflow tests**

```python
assert prompt_node["failure_code"] is None
assert prompt_node["degrade_reason"] == "retry_recovered"
```

```python
assert first_node["failure_code"] is None
assert first_node["degrade_reason"] is None
```

**Step 2: Add failing metrics contract test**

```python
assert "refactor_workflow_trace_nodes_total 3" in metrics_text
assert 'refactor_workflow_trace_nodes_failure_code_total{failure_code="node_execution_error"} 1' in metrics_text
assert 'refactor_workflow_trace_nodes_degrade_reason_total{degrade_reason="retry_recovered"} 1' in metrics_text
```

**Step 3: Run targeted tests and verify failure**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py`  
Expected: FAIL because trace nodes/metrics do not yet expose these fields.

### Task 2: GREEN implementation for trace schema + persistence + emission

**Files:**
- Modify: `refactor/backend/src/app/services/analysis_service.py`
- Modify: `refactor/backend/src/app/services/workflow_service.py`
- Modify: `refactor/backend/src/app/persistence/sqlite_db.py`

**Step 1: Emit structured trace reasons in analysis service**

```python
self._build_trace_node(..., failure_code="node_execution_error", degrade_reason="retry_exhausted")
```

Rules:
- retry recovered success -> `degrade_reason=retry_recovered`, `failure_code=None`
- quality degraded success -> `degrade_reason=factor_quality_degraded`
- failed node -> `failure_code` normalized (`prompt_lock_error` / `node_execution_error` / `factor_collection_error`)

**Step 2: Persist/read new fields in workflow trace storage**

```python
failure_code TEXT

degrade_reason TEXT
```

Use `_ensure_column(...)` for backward compatibility.

**Step 3: Run targeted tests and verify pass**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py`  
Expected: PASS.

### Task 3: GREEN implementation for `/metrics` workflow trace observability

**Files:**
- Modify: `refactor/backend/src/app/api/routes/metrics.py`

**Step 1: Add workflow trace observability snapshot loader**

Expose aggregates:
- total/degraded/failed/retry node counts
- degraded/failed/retry ratios
- avg duration ms
- by `failure_code`
- by `degrade_reason`

**Step 2: Append Prometheus lines in `get_global_metrics(...)`**

Metric names:
- `refactor_workflow_trace_nodes_total`
- `refactor_workflow_trace_nodes_degraded_total`
- `refactor_workflow_trace_nodes_failed_total`
- `refactor_workflow_trace_nodes_retry_total`
- `refactor_workflow_trace_nodes_degraded_ratio`
- `refactor_workflow_trace_nodes_failed_ratio`
- `refactor_workflow_trace_nodes_retry_ratio`
- `refactor_workflow_trace_nodes_duration_ms_avg`
- `refactor_workflow_trace_nodes_failure_code_total{failure_code=...}`
- `refactor_workflow_trace_nodes_degrade_reason_total{degrade_reason=...}`

### Task 4: Regression + docs sync

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代266-M4-analysis-trace-failure-metrics.md`

**Step 1: Full verification**

Run: `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_notification_hub.py`  
Expected: PASS.

Run: `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/api/routes/metrics.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: PASS.

Run: `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/api/routes/metrics.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`  
Expected: PASS.
