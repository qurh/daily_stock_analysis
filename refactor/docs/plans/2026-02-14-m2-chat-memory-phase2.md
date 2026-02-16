# M2 Chat Memory Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver M2 phase-2 minimum loop: multi-turn chat with RAG citations plus memory summarize/search/delete APIs.

**Architecture:** Add persistent `ChatService` and `MemoryService` on top of SQLite, with dedicated Chroma collection for long-term memory retrieval. Chat message handling writes user/assistant turns, retrieves knowledge and memory hits, and returns citations in assistant messages. Memory summarize API compacts recent conversation into summary and stores long-term memory entry for cross-session retrieval.

**Tech Stack:** Python 3.10+, FastAPI, sqlite3, chromadb, pytest.

### Task 1: RED tests for chat + memory contracts

**Files:**
- Create: `refactor/backend/tests/unit/test_chat_service.py`
- Create: `refactor/backend/tests/unit/test_memory_service.py`

**Step 1: Write failing tests**
- Create session and post message should produce assistant response with citations.
- Query session messages should include user+assistant turns in order.
- Summarize session should generate summary and long-term memory entry.
- Memory search should return hit entries.
- Delete session memory should clean chat retrieval and related memory entries.

**Step 2: Run tests and verify fail**
- `PYTHONPATH=refactor/backend/src python3 -m pytest -q refactor/backend/tests/unit/test_chat_service.py refactor/backend/tests/unit/test_memory_service.py`

### Task 2: Implement persistence schema and services

**Files:**
- Modify: `refactor/backend/src/app/core/settings.py`
- Modify: `refactor/backend/src/app/persistence/sqlite_db.py`
- Create: `refactor/backend/src/app/memory/vector_store.py`
- Create: `refactor/backend/src/app/services/memory_service.py`
- Create: `refactor/backend/src/app/services/chat_service.py`

**Step 1: Extend settings/schema**
- Add `REF_MEMORY_COLLECTION`.
- Add tables for conversation session/message and memory summary/long-term entries.

**Step 2: Implement services**
- `MemoryService`: get session, summarize, search long-term memory, delete session data.
- `ChatService`: create session, append user message, retrieve knowledge/memory hits, generate assistant turn with citations.

### Task 3: Expose APIs and wire dependencies

**Files:**
- Create: `refactor/backend/src/app/api/routes/chat.py`
- Create: `refactor/backend/src/app/api/routes/memory.py`
- Modify: `refactor/backend/src/app/api/deps.py`
- Modify: `refactor/backend/src/app/api/router.py`
- Modify: `refactor/backend/src/app/main.py`
- Modify: `refactor/backend/src/app/shared/error_codes.py`

**Step 1: Add routes**
- Chat:
  - `POST /api/v2/chat/sessions`
  - `POST /api/v2/chat/sessions/{session_id}/messages`
  - `GET /api/v2/chat/sessions/{session_id}/messages`
- Memory:
  - `GET /api/v2/memory/sessions/{session_id}`
  - `POST /api/v2/memory/sessions/{session_id}/summarize`
  - `POST /api/v2/memory/search`
  - `DELETE /api/v2/memory/sessions/{session_id}`

### Task 4: Verify and document

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/07-OpenAPI-v2-接口草案.yaml`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-02-14-迭代5-M2聊天记忆检索闭环.md`

**Step 1: Run verifications**
- `PYTHONPATH=refactor/backend/src python3 -m pytest -q refactor/backend/tests/unit`
- `cd refactor/backend && ./scripts/ci.sh`

**Step 2: Sync docs**
- Update API draft and iteration record with evidence and residual risks.
