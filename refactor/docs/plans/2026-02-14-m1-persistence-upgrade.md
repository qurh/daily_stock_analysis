# M1 Persistence Upgrade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace M1 in-memory runtime with durable database storage and persistent task queue while keeping existing API contracts.

**Architecture:** Keep FastAPI routes unchanged and swap service internals to SQLite-backed repositories plus DB task queue. Queue handlers execute workflow/analysis tasks and write status/trace/results back to relational tables. Prompt center state moves from process memory to persistent tables with version lifecycle operations.

**Tech Stack:** Python 3.10+, FastAPI, built-in `sqlite3`, pytest.

### Task 1: Add RED tests for persistence and queue durability

**Files:**
- Create: `refactor/backend/tests/unit/conftest.py`
- Create: `refactor/backend/tests/unit/test_persistence_upgrade.py`
- Test: `refactor/backend/tests/unit/test_persistence_upgrade.py`

**Step 1: Write failing tests**

- Add an autouse fixture setting `REF_DATABASE_URL` per-test temp SQLite file.
- Add test for cross-app persistence (`create_app()` -> write -> recreate app -> read exists).
- Add test proving queue records are persisted in `task_queue` table.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=refactor/backend/src python3 -m pytest -q refactor/backend/tests/unit/test_persistence_upgrade.py`
Expected: FAIL because current services keep state only in memory and no queue table exists.

### Task 2: Implement SQLite persistence infrastructure

**Files:**
- Create: `refactor/backend/src/app/core/settings.py`
- Create: `refactor/backend/src/app/persistence/sqlite_db.py`
- Create: `refactor/backend/src/app/persistence/__init__.py`

**Step 1: Implement configuration loading**

- Read `REF_DATABASE_URL` and `REF_QUEUE_AUTO_PROCESS` from env.
- Define default local SQLite path under backend runtime dir.

**Step 2: Implement schema bootstrap**

- Create tables for `analysis_jobs`, `workflow_executions`, `workflow_trace_nodes`, `prompt_templates`, `prompt_versions`, `task_queue`.
- Add helper methods for JSON encode/decode and atomic execute/query operations.

### Task 3: Replace services with persistent implementations

**Files:**
- Create: `refactor/backend/src/app/services/task_queue_service.py`
- Modify: `refactor/backend/src/app/services/workflow_service.py`
- Modify: `refactor/backend/src/app/services/analysis_service.py`
- Modify: `refactor/backend/src/app/services/prompt_service.py`
- Modify: `refactor/backend/src/app/main.py`

**Step 1: Implement DB task queue service**

- Support `register_handler`, `enqueue`, `process_next`, `process_all`.
- Persist queue task status transitions (`pending/running/succeeded/failed`).

**Step 2: Refactor workflow/analysis/prompt services**

- Store state in SQLite tables instead of in-memory dicts.
- Wire analysis handler to run workflow and persist trace.
- Keep response shape identical to existing tests.

**Step 3: Wire app bootstrap**

- Initialize settings + SQLite schema at startup.
- Register queue handlers and inject persistent services into `app.state`.

### Task 4: Verify GREEN and update docs

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-02-14-迭代3-M1持久化升级.md`

**Step 1: Run all tests and CI**

- `PYTHONPATH=refactor/backend/src python3 -m pytest -q refactor/backend/tests/unit`
- `cd refactor/backend && ./scripts/ci.sh`

**Step 2: Update docs**

- Document SQLite + DB queue runtime behavior.
- Record completed scope, validations, and residual risks.
