# M4 Analysis Trace Failure Context And Window Metrics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add sanitized `failure_context` to workflow trace nodes and extend workflow trace observability metrics with 24h/7d/30d windows.

**Architecture:** Keep trace contract additive-only. Persist optional `failure_context` field in `workflow_trace_nodes`, emit it only for failure nodes through `AnalysisService`, and compute windowed observability snapshots in metrics route from `workflow_trace_nodes.ended_at` with low-cardinality outputs.

**Tech Stack:** Python 3.10, FastAPI, SQLite, pytest.

### Task 1: RED tests for failure context and window metrics

**Files:**
- Modify: `refactor/backend/tests/unit/test_analysis_jobs.py`
- Modify: `refactor/backend/tests/unit/test_workflow_executions.py`
- Modify: `refactor/backend/tests/unit/test_metrics_route.py`

**Step 1: Add failing trace assertions**

```python
assert prompt_node["failure_context"] is not None
assert "prompt resolver hard failure" in prompt_node["failure_context"]
```

```python
assert first_node["failure_context"] is None
```

**Step 2: Add failing window metrics assertions**

```python
assert "refactor_workflow_trace_nodes_total_24h 1" in metrics_text
assert "refactor_workflow_trace_nodes_total_7d 2" in metrics_text
assert "refactor_workflow_trace_nodes_total_30d 3" in metrics_text
```

**Step 3: Run targeted tests and verify failure**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py`  
Expected: FAIL because `failure_context` and window metrics are not implemented.

### Task 2: GREEN implementation for trace failure context

**Files:**
- Modify: `refactor/backend/src/app/services/analysis_service.py`
- Modify: `refactor/backend/src/app/services/workflow_service.py`
- Modify: `refactor/backend/src/app/persistence/sqlite_db.py`

**Step 1: Emit sanitized `failure_context` from analysis node failures**

```python
failure_context=self._sanitize_failure_context(exc)
```

**Step 2: Persist and return `failure_context` in workflow trace nodes**

```python
failure_context TEXT
```

Use `_ensure_column(...)` for backward compatibility.

### Task 3: GREEN implementation for metrics windows

**Files:**
- Modify: `refactor/backend/src/app/api/routes/metrics.py`

**Step 1: Extend workflow trace observability snapshot with windows**

- all time (existing)
- 24h / 7d / 30d window totals and ratios
- 24h / 7d / 30d average duration

**Step 2: Export Prometheus gauges**

- `refactor_workflow_trace_nodes_total_24h`
- `refactor_workflow_trace_nodes_total_7d`
- `refactor_workflow_trace_nodes_total_30d`
- `refactor_workflow_trace_nodes_failed_ratio_24h`
- `refactor_workflow_trace_nodes_failed_ratio_7d`
- `refactor_workflow_trace_nodes_failed_ratio_30d`
- `refactor_workflow_trace_nodes_duration_ms_avg_24h`
- `refactor_workflow_trace_nodes_duration_ms_avg_7d`
- `refactor_workflow_trace_nodes_duration_ms_avg_30d`

### Task 4: Regression and docs sync

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代267-M4-analysis-trace-failure-context-window-metrics.md`

**Step 1: Full verification**

Run: `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_notification_hub.py`  
Expected: PASS.

Run: `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/api/routes/metrics.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: PASS.

Run: `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/api/routes/metrics.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`  
Expected: PASS.
