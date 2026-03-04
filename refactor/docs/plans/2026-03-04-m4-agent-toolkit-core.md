# M4 Agent Toolkit Core Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver FR-AGT minimum loop with tool protocol, registry/invoke APIs, chat intent-based auto tool execution, and retry/degrade trace.

**Architecture:** Introduce a dedicated `AgentService` as the single entry for tool registration, planning, and runtime execution. Wire it into both API routes (`/api/v2/agent/*`) and `ChatService` so chatbot responses can auto-trigger tools and return call traces.

**Tech Stack:** Python 3.10, FastAPI, SQLite-backed services, pytest.

### Task 1: Red tests for Agent Toolkit contract

**Files:**
- Create: `refactor/backend/tests/unit/test_agent_service.py`
- Create: `refactor/backend/tests/unit/test_agent_routes.py`
- Modify: `refactor/backend/tests/unit/test_chat_service.py`
- Modify: `refactor/backend/tests/unit/test_settings_env_names.py`

**Step 1: Write failing tests for service-level tool registration/invoke**

```python
assert payload["degraded"] is True
assert payload["trace"][0]["status"] in {"succeeded", "degraded"}
```

**Step 2: Write failing tests for route-level register/list/invoke**

```python
assert client.get("/api/v2/agent/tools").status_code == 200
assert client.post("/api/v2/agent/invoke", ...).json()["trace"]
```

**Step 3: Write failing chat integration test**

```python
assert "agent_trace" in assistant["tool_trace"]
assert assistant["tool_trace"]["agent_trace"]["trace"]
```

**Step 4: Run test to verify RED**

Run: `pytest -q refactor/backend/tests/unit/test_agent_service.py refactor/backend/tests/unit/test_agent_routes.py refactor/backend/tests/unit/test_chat_service.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: fail due missing Agent service/routes/settings wiring.

### Task 2: Minimal Agent service and route wiring

**Files:**
- Create: `refactor/backend/src/app/services/agent_service.py`
- Create: `refactor/backend/src/app/api/routes/agent.py`
- Modify: `refactor/backend/src/app/api/deps.py`
- Modify: `refactor/backend/src/app/api/router.py`
- Modify: `refactor/backend/src/app/main.py`
- Modify: `refactor/backend/src/app/services/chat_service.py`
- Modify: `refactor/backend/src/app/core/settings.py`

**Step 1: Implement tool protocol + runtime contract**

```python
class AgentService:
    def register_tool(...)
    def list_tools(...)
    def invoke(...)
    def invoke_with_intent(...)
```

**Step 2: Add built-in tools and planning**

```python
intent -> tool_names
["knowledge.search", "memory.search", ...]
```

**Step 3: Add retry + degrade trace**

```python
max_retries / backoff_ms
status: succeeded | failed | degraded
```

**Step 4: Wire into ChatService**

```python
agent_result = self._agent_service.invoke_with_intent(...)
tool_trace["agent_trace"] = agent_result
```

### Task 3: Green verification and regression

**Step 1: Run focused tests**

Run: `pytest -q refactor/backend/tests/unit/test_agent_service.py refactor/backend/tests/unit/test_agent_routes.py refactor/backend/tests/unit/test_chat_service.py refactor/backend/tests/unit/test_settings_env_names.py`  
Expected: pass.

**Step 2: Run impacted regression tests**

Run: `pytest -q refactor/backend/tests/unit/test_knowledge_service.py refactor/backend/tests/unit/test_memory_service.py refactor/backend/tests/unit/test_workflow_executions.py`  
Expected: pass.

**Step 3: Run syntax check**

Run: `python3 -m py_compile refactor/backend/src/app/services/agent_service.py refactor/backend/src/app/api/routes/agent.py refactor/backend/src/app/services/chat_service.py refactor/backend/src/app/main.py refactor/backend/src/app/core/settings.py`  
Expected: pass.

### Task 4: Docs sync

**Files:**
- Modify: `refactor/backend/.env.example`
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代269-M4-agent-toolkit-core.md`

**Step 1: Document AGT env and APIs**

```markdown
AGENT_TOOL_MAX_RETRIES
AGENT_TOOL_RETRY_BACKOFF_MS
/api/v2/agent/tools/*
```

**Step 2: Record changelog + iteration evidence**

```markdown
## [0.4.53-m4-agent-toolkit-core] - 2026-03-04
```
