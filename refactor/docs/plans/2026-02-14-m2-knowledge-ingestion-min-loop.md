# M2 Knowledge Ingestion Min Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver M2 phase-1 minimum loop: markdown upload, chunk+summary, Chroma indexing, and retrieval API.

**Architecture:** Add a dedicated `KnowledgeService` backed by SQLite metadata tables and Chroma local vector index. Routes under `/api/v2/knowledge` keep ingestion and retrieval flow explicit (`upload -> ingest -> search`). Chunking and summarization are deterministic local algorithms for MVP baseline.

**Tech Stack:** Python 3.10+, FastAPI, sqlite3, chromadb, pytest.

### Task 1: RED tests for knowledge loop

**Files:**
- Modify: `refactor/backend/tests/unit/conftest.py`
- Create: `refactor/backend/tests/unit/test_knowledge_service.py`

**Step 1: Write failing tests**
- Upload markdown document should return `201` and `UPLOADED`.
- Ingest should return `202`, `COMPLETED`, and `chunk_count >= 1`.
- Search should return hit list with source metadata.
- Delete should remove retrievable hits.

**Step 2: Run failing tests**
Run: `PYTHONPATH=refactor/backend/src python3 -m pytest -q refactor/backend/tests/unit/test_knowledge_service.py`
Expected: FAIL with `404` because routes are not implemented yet.

### Task 2: Implement persistence + Chroma adapters

**Files:**
- Modify: `refactor/backend/src/app/core/settings.py`
- Modify: `refactor/backend/src/app/persistence/sqlite_db.py`
- Create: `refactor/backend/src/app/knowledge/vector_store.py`
- Create: `refactor/backend/src/app/knowledge/chunker.py`
- Create: `refactor/backend/src/app/knowledge/summarizer.py`
- Create: `refactor/backend/src/app/services/knowledge_service.py`

**Step 1: Extend settings/schema**
- Add `REF_CHROMA_PATH` and `REF_CHROMA_COLLECTION`.
- Add `knowledge_documents` and `knowledge_chunks` tables.

**Step 2: Implement vector/chunk/summarize**
- Implement deterministic chunking and summary generation.
- Implement Chroma upsert/query/delete with deterministic hash embedding.

### Task 3: Expose knowledge APIs

**Files:**
- Create: `refactor/backend/src/app/api/routes/knowledge.py`
- Modify: `refactor/backend/src/app/api/deps.py`
- Modify: `refactor/backend/src/app/api/router.py`
- Modify: `refactor/backend/src/app/main.py`

**Step 1: Wire service and routes**
- Add endpoints:
  - `POST /api/v2/knowledge/documents/upload`
  - `POST /api/v2/knowledge/documents/{doc_id}/ingest`
  - `GET /api/v2/knowledge/documents/{doc_id}`
  - `GET /api/v2/knowledge/chunks/search`
  - `DELETE /api/v2/knowledge/documents/{doc_id}`

### Task 4: Verify and sync docs

**Files:**
- Modify: `refactor/backend/requirements-dev.txt`
- Modify: `refactor/backend/pyproject.toml`
- Modify: `refactor/docs/07-OpenAPI-v2-接口草案.yaml`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-02-14-迭代4-M2知识导入检索最小闭环.md`

**Step 1: Verification**
- Run targeted tests + all unit tests + CI script.

**Step 2: Documentation**
- Update OpenAPI draft and iteration log with evidence and residual risks.
