# M4 CI Optional Positive Rehearsal Stage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable optional execution of one-click positive M4 integration rehearsal from `scripts/ci.sh` without changing default CI runtime.

**Architecture:** Add an env-flag gated stage in `ci.sh` that invokes `./scripts/rehearse-m4-positive-flow.sh` only when explicitly enabled. Keep default behavior unchanged.

**Tech Stack:** Bash script orchestration.

### Task 1: RED check

**Step 1: Verify flag hook is absent**

Run: `rg -n "CI_RUN_M4_POSITIVE_REHEARSAL|rehearse-m4-positive-flow.sh" refactor/backend/scripts/ci.sh`  
Expected: no match (exit non-zero).

### Task 2: Implement optional stage

**Files:**
- Modify: `refactor/backend/scripts/ci.sh`

**Step 1: Add env-gated invocation**

```bash
if [[ "${CI_RUN_M4_POSITIVE_REHEARSAL:-0}" == "1" ]]; then
  ./scripts/rehearse-m4-positive-flow.sh
fi
```

### Task 3: GREEN verification + docs

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Modify: `refactor/backend/src/app/main.py`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代275-M4-ci-optional-positive-rehearsal-stage.md`

**Step 1: Verify hook exists**

Run: `rg -n "CI_RUN_M4_POSITIVE_REHEARSAL|rehearse-m4-positive-flow.sh" refactor/backend/scripts/ci.sh`  
Expected: match lines found.

**Step 2: Focused checks**

Run:
- `bash -n refactor/backend/scripts/ci.sh`
- `bash -n refactor/backend/scripts/rehearse-m4-positive-flow.sh`
- `python3 -m py_compile refactor/backend/src/app/main.py`

Expected: PASS.
