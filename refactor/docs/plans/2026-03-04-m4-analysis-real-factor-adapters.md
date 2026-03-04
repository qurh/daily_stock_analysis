# M4 Analysis Real Factor Adapters Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add configurable external adapters for macro/credit/sentiment factors with deterministic fallback and degradation traceability.

**Architecture:** Keep `FactorService` as the contract entrypoint. Extend each factor provider with optional HTTP JSON source configuration and fallback path. Wire settings into app bootstrap so runtime behavior is controlled by `refactor/backend/.env`.

**Tech Stack:** Python 3.10, FastAPI app bootstrap, stdlib HTTP (`urllib`), pytest.

### Task 1: Red tests for factor adapter behavior

**Files:**
- Create: `refactor/backend/tests/unit/test_factor_service.py`
- Modify: `refactor/backend/tests/unit/test_settings_env_names.py`

**Step 1: Write the failing tests**

```python
def test_factor_service_uses_external_sources_when_configured():
    ...

def test_factor_service_falls_back_when_external_source_fails():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: fail due to missing provider ctor args and missing settings fields.

### Task 2: Minimal implementation for adapter + fallback

**Files:**
- Modify: `refactor/backend/src/app/services/factor_service.py`
- Modify: `refactor/backend/src/app/core/settings.py`
- Modify: `refactor/backend/src/app/main.py`

**Step 1: Implement external adapter support in factor providers**

```python
@dataclass
class MacroFactorProvider:
    source_url: str | None = None
    ...
```

**Step 2: Implement fallback + quality flag behavior**

```python
fallback["_quality_flag"] = {"factor": "...", "status": "degraded", ...}
```

**Step 3: Add settings fields and bootstrap wiring**

```python
analysis_macro_source_url = os.getenv("ANALYSIS_MACRO_SOURCE_URL")
...
```

### Task 3: Green verification + regression

**Files:**
- Verify: `refactor/backend/tests/unit/test_factor_service.py`
- Verify: `refactor/backend/tests/unit/test_analysis_jobs.py`

**Step 1: Run Green tests**

Run: `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: pass.

**Step 2: Run regression tests**

Run: `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_workflow_executions.py`  
Expected: pass.

**Step 3: Run syntax and lint checks**

Run: `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: pass.

Run: `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`  
Expected: pass.

### Task 4: Docs and changelog sync

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/backend/.env.example`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代261-M4-analysis-real-factor-adapters.md`

**Step 1: Document new env config and fallback behavior**

```markdown
ANALYSIS_MACRO_SOURCE_URL / ANALYSIS_CREDIT_SOURCE_URL / ANALYSIS_SENTIMENT_SOURCE_URL
```

**Step 2: Add changelog entry and iteration record**

```markdown
## [0.4.45-m4-analysis-real-factor-adapters] - 2026-03-04
```
