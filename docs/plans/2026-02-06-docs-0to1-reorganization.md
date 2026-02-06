# Docs 0-1 Reorganization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a unified documentation system for 0-to-1 product requirement analysis and project planning, and integrate legacy docs into the new structure.

**Architecture:** Keep legacy docs in place as historical references, create a canonical baseline in the new `docs/00-05` hierarchy, and add explicit mapping/index files to bridge old and new content. Use incremental migration to avoid broken links and reduce coordination risk.

**Tech Stack:** Markdown, repository docs conventions, Git history traceability

---

### Task 1: Build 0-to-1 requirement baseline document

**Files:**
- Create: `docs/01-需求管理/2026-02-06-从0到1-需求分析.md`
- Modify: `docs/01-需求管理/README.md`

**Steps:**
1. Write requirement analysis from problem, users, scope, non-goals, constraints, success metrics.
2. Consolidate MVP scope based on current effective baseline.
3. Add acceptance checklist and requirement IDs for traceability.

### Task 2: Build 0-to-1 project planning baseline document

**Files:**
- Create: `docs/04-实施计划/2026-02-06-从0到1-项目规划.md`
- Modify: `docs/04-实施计划/README.md`

**Steps:**
1. Define phases, milestones, deliverables, owners, dependencies.
2. Add risk register and mitigation.
3. Add execution cadence and status update rules.

### Task 3: Integrate system design baseline and gap matrix

**Files:**
- Create: `docs/02-系统设计/2026-02-06-系统设计整合基线.md`
- Modify: `docs/02-系统设计/数据模型与API基线.md`

**Steps:**
1. Merge architecture/API/data model key points needed for MVP.
2. Add “design vs implementation” gap matrix.
3. Mark current, target, and planned completion phase.

### Task 4: Integrate legacy docs into new governance system

**Files:**
- Create: `docs/99-历史文档/历史文档映射表.md`
- Create: `docs/99-历史文档/迁移路线图.md`
- Modify: `docs/99-历史文档/README.md`

**Steps:**
1. Build one-to-one mapping from old docs to new canonical docs.
2. Tag each old doc with status: retained, merged, or to-archive.
3. Define migration order and completion criteria.

### Task 5: Update global entry and reading path

**Files:**
- Modify: `docs/README.md`

**Steps:**
1. Add “0-to-1 reading order”.
2. Add “single source of truth” list.
3. Add current progress snapshot and next action pointers.

### Task 6: Validate structure and consistency

**Files:**
- Verify all docs created and cross-links valid.

**Steps:**
1. Run file listing check under `docs/`.
2. Review key docs for link/path consistency.
3. Confirm git diff scope is docs-only.
