# M4 Analysis Flow Template Orchestration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move analysis execution into configurable node-template orchestration and persist real node trace in workflow executions.

**Architecture:** Keep `WorkflowService` as execution record store, but allow deferred execution and external trace/result completion. `AnalysisService` executes modular node handlers according to a flow template and writes node-by-node status back to workflow storage.

**Tech Stack:** Python 3.10, FastAPI service layer, SQLite persistence, pytest.

### Task 1: Red tests for analysis trace contract

**Files:**
- Modify: `refactor/backend/tests/unit/test_analysis_jobs.py`
- Modify: `refactor/backend/tests/unit/test_settings_env_names.py`

**Step 1: Write the failing tests**

```python
assert "collect_factors" in node_ids
assert node_ids[-1] == "finalize_report"
```

```python
monkeypatch.setenv("ANALYSIS_FLOW_TEMPLATE", "resolve_prompt,collect_factors,build_dashboard,finalize_report")
```

**Step 2: Run test to verify it fails**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: fail due to old static workflow nodes and missing settings field.

### Task 2: Minimal orchestration implementation

**Files:**
- Modify: `refactor/backend/src/app/services/workflow_service.py`
- Modify: `refactor/backend/src/app/services/analysis_service.py`
- Modify: `refactor/backend/src/app/core/settings.py`
- Modify: `refactor/backend/src/app/main.py`

**Step 1: Add deferred execution completion APIs to workflow service**

```python
start_execution(..., defer_run=True)
complete_execution(...)
fail_execution(...)
```

**Step 2: Implement template-driven node execution in analysis service**

```python
self._analysis_node_handlers = {...}
self._analysis_flow_template = ...
```

**Step 3: Add env-driven flow template wiring**

```python
analysis_flow_template = _read_csv_env("ANALYSIS_FLOW_TEMPLATE")
```

### Task 3: Green verification and regression

**Step 1: Run core tests**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_workflow_executions.py`  
Expected: pass.

**Step 2: Run related regression**

Run: `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py`  
Expected: pass.

**Step 3: Run syntax + lint**

Run: `python3 -m py_compile refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: pass.

Run: `flake8 refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`  
Expected: pass.

### Task 4: Documentation sync

**Files:**
- Modify: `refactor/backend/.env.example`
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代262-M4-analysis-flow-template-orchestration.md`

**Step 1: Document new flow-template config and node list**

```markdown
ANALYSIS_FLOW_TEMPLATE=resolve_strategy_context,resolve_prompt,collect_factors,build_dashboard,finalize_report
```

**Step 2: Write changelog and iteration record**

```markdown
## [0.4.46-m4-analysis-flow-template-orchestration] - 2026-03-04
```
