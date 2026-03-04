# M4 Analysis Parallel Retry Orchestration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add staged parallel factor collection and node-level retry to analysis flow-template orchestration.

**Architecture:** Keep current analysis flow-template model, but parse each template entry as a stage. Support `+` grouped parallel stages for factor collection nodes and execute each node with retry policy. Keep workflow trace and result contracts stable.

**Tech Stack:** Python 3.10, FastAPI service layer, SQLite, ThreadPoolExecutor, pytest.

### Task 1: Red tests for parallel stage and retry behavior

**Files:**
- Modify: `refactor/backend/tests/unit/test_analysis_jobs.py`
- Modify: `refactor/backend/tests/unit/test_settings_env_names.py`

**Step 1: Write failing tests**

```python
ANALYSIS_FLOW_TEMPLATE="resolve_prompt,collect_macro_factor+collect_credit_factor+...,build_dashboard,finalize_report"
```

```python
ANALYSIS_NODE_MAX_RETRIES=1
```

**Step 2: Run tests to verify failure**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: fail due to unsupported `+` stage and missing retry settings fields.

### Task 2: Implement staged parser + retry executor

**Files:**
- Modify: `refactor/backend/src/app/services/analysis_service.py`

**Step 1: Stage parser and validation**

```python
_normalize_analysis_flow_template(...) -> list[list[str]]
```

**Step 2: Add node retry wrapper**

```python
_execute_node_with_retry(...)
```

**Step 3: Add parallel factor stage execution**

```python
_execute_parallel_stage(...)
```

### Task 3: Factor service modular collection APIs

**Files:**
- Modify: `refactor/backend/src/app/services/factor_service.py`

**Step 1: Add single-factor collection API**

```python
collect_factor(symbol, report_type, factor_key)
```

**Step 2: Add empty factor pack helper**

```python
empty_factor_pack()
```

### Task 4: Settings/bootstrap wiring

**Files:**
- Modify: `refactor/backend/src/app/core/settings.py`
- Modify: `refactor/backend/src/app/main.py`

**Step 1: Add retry env settings**

```python
analysis_node_max_retries
analysis_node_retry_backoff_ms
```

**Step 2: Pass settings into analysis service**

```python
AnalysisService(... analysis_node_max_retries=..., analysis_node_retry_backoff_ms=...)
```

### Task 5: Verification and docs sync

**Files:**
- Modify: `refactor/backend/.env.example`
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代263-M4-analysis-parallel-retry-orchestration.md`

**Step 1: Run verification**

Run: `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_notification_hub.py`  
Expected: pass.

Run: `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: pass.

Run: `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`  
Expected: pass.
