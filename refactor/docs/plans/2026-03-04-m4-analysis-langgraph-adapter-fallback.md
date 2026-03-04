# M4 Analysis LangGraph Adapter Fallback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Introduce orchestrator engine selection (`local/langgraph`) and provide safe local fallback when langgraph import is unavailable.

**Architecture:** Keep local stage executor as default engine. Add langgraph adapter entrypoint in `AnalysisService`; engine routing occurs before flow execution. If langgraph import fails, execute with local engine and persist structured fallback metadata into analysis report meta.

**Tech Stack:** Python 3.10, FastAPI, optional langgraph import path, pytest.

### Task 1: Red tests for orchestrator metadata and langgraph fallback

**Files:**
- Modify: `refactor/backend/tests/unit/test_analysis_jobs.py`
- Modify: `refactor/backend/tests/unit/test_settings_env_names.py`

**Step 1: Write failing tests**

```python
assert meta["orchestrator"]["requested"] == "local"
```

```python
monkeypatch.setenv("ANALYSIS_ORCHESTRATOR_ENGINE", "langgraph")
```

**Step 2: Run tests to verify failure**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: fail due to missing orchestrator meta/settings and missing langgraph adapter method.

### Task 2: Implement orchestrator engine selection

**Files:**
- Modify: `refactor/backend/src/app/services/analysis_service.py`
- Modify: `refactor/backend/src/app/core/settings.py`
- Modify: `refactor/backend/src/app/main.py`

**Step 1: Add engine setting parsing and validation**

```python
analysis_orchestrator_engine = local|langgraph
```

**Step 2: Add engine router in AnalysisService**

```python
_execute_flow(...)
_execute_flow_local(...)
_execute_flow_with_langgraph(...)
```

**Step 3: Add fallback metadata**

```python
meta["orchestrator"] = {"requested": ..., "effective": ..., ...}
```

### Task 3: Verification and documentation sync

**Files:**
- Modify: `refactor/backend/.env.example`
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代264-M4-analysis-langgraph-adapter-fallback.md`

**Step 1: Run verification**

Run: `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_notification_hub.py`  
Expected: pass.

Run: `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: pass.

Run: `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`  
Expected: pass.
