# M4 One-Click Positive Smoke Rehearsal Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provide a one-command rehearsal script that starts backend runtime and executes positive strategy flow smoke (`publish -> bind -> rollback`).

**Architecture:** Add a new bash script under `refactor/backend/scripts` that reuses existing env-loading conventions, spins up uvicorn with isolated temporary runtime (DB/Chroma), waits for health, runs `smoke-positive-strategy-flow.py`, and performs cleanup on exit.

**Tech Stack:** Bash, Python 3.10+, FastAPI/uvicorn.

### Task 1: RED verification

**Files:**
- N/A (pre-implementation check)

**Step 1: Run missing command and verify it fails**

Run: `cd refactor/backend && ./scripts/rehearse-m4-positive-flow.sh`  
Expected: fails because script does not exist yet.

### Task 2: Implement one-click rehearsal script

**Files:**
- Create: `refactor/backend/scripts/rehearse-m4-positive-flow.sh`

**Step 1: Add env whitelist loading and runtime defaults**

- reuse `.env` loader pattern from existing script family
- support overridable vars:
  - `API_HOST`
  - `API_PORT`
  - `MAX_SYMBOL_ATTEMPTS`
  - `SAMPLES_PER_SYMBOL`
  - `REPORT_TYPE`
  - `KEEP_RUNTIME_ARTIFACTS`

**Step 2: Start backend + wait for health**

- launch `uvicorn app.main:app --app-dir src`
- trap exit for process cleanup
- poll `GET /api/v2/health`

**Step 3: Run positive smoke script and print summary paths**

- call `./scripts/smoke-positive-strategy-flow.py --base-url ...`
- print log path and runtime artifact path

### Task 3: GREEN verification and docs

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Modify: `refactor/backend/src/app/main.py`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代274-M4-one-click-positive-smoke-rehearsal.md`

**Step 1: Run script end-to-end**

Run: `cd refactor/backend && ./scripts/rehearse-m4-positive-flow.sh`  
Expected: passes and prints JSON summary with `publish_status: 200`.

**Step 2: Run focused quality checks**

Run:
- `bash -n refactor/backend/scripts/rehearse-m4-positive-flow.sh`
- `python3 -m py_compile refactor/backend/scripts/smoke-positive-strategy-flow.py refactor/backend/src/app/main.py`
- `flake8 refactor/backend/scripts/smoke-positive-strategy-flow.py refactor/backend/src/app/main.py --max-line-length=120`

Expected: PASS.
