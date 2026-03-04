# M4 Strategy Gate Precheck And Positive Smoke Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce Strategy publish trial-and-error by showing gate hints in frontend and provide a reusable positive integration smoke script.

**Architecture:** Add lightweight client-side error-code hint mapping in `StrategyPage` without backend API changes. Add one backend script that runs against a live API and validates `publish -> bind -> rollback` by iterating symbols until backtest gate passes.

**Tech Stack:** React + Vitest, Python 3.10+ script, FastAPI API contract.

### Task 1: RED test for Strategy publish gate hint

**Files:**
- Create: `refactor/frontend/src/pages/StrategyPage.test.tsx`

**Step 1: Add failing test**

```tsx
expect(screen.getByText(/Publish gate hint:/i)).toBeInTheDocument();
```

**Step 2: Run and verify failure**

Run: `cd refactor/frontend && npm run test -- --run src/pages/StrategyPage.test.tsx`  
Expected: FAIL because page currently only shows raw error.

### Task 2: GREEN implementation in StrategyPage

**Files:**
- Modify: `refactor/frontend/src/pages/StrategyPage.tsx`

**Step 1: Add gate hint resolver**

- Map common gate codes:
  - `STR-GATE-005`
  - `STR-GATE-009`
  - `STR-GATE-007/008`

**Step 2: Render hint on publish errors**

- Parse error text in publish catch block.
- Set and render `publishGateHint`.

**Step 3: Re-run test**

Run: `cd refactor/frontend && npm run test -- --run src/pages/StrategyPage.test.tsx`  
Expected: PASS.

### Task 3: Add reusable positive smoke script

**Files:**
- Create: `refactor/backend/scripts/smoke-positive-strategy-flow.py`

**Step 1: Implement end-to-end script against running backend**

- chat session + memo distill/review + strategy extract
- loop symbols to generate analysis/backtest samples
- publish when gate passes
- bind + list bindings + rollback

**Step 2: Execute script against local backend**

Expected: outputs JSON summary with `publish_status=200`.

### Task 4: Docs and verification

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/frontend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Modify: `refactor/backend/src/app/main.py`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代273-M4-strategy-gate-precheck-and-positive-smoke.md`

**Step 1: Run focused checks**

- `cd refactor/frontend && npm run test -- --run src/pages/StrategyPage.test.tsx`
- `cd refactor/frontend && npm run test -- --run`
- `cd refactor/frontend && npm run build`
- `python3 -m py_compile refactor/backend/scripts/smoke-positive-strategy-flow.py`
- `flake8 refactor/backend/scripts/smoke-positive-strategy-flow.py --max-line-length=120`

Expected: PASS.
