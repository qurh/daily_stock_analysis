# M4 Notification Hub Pluginization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a pluggable Notification Hub in `refactor/backend` with MVP APIs (`preview/send/channels/test`) and regression tests.

**Architecture:** Introduce a `notification` domain service layer with a plugin protocol (`ChannelPlugin`) and a hub orchestrator (`NotificationHub`). The API route delegates all channel discovery, formatting, and dispatch logic to the hub. Existing environment variables from `refactor/backend/.env.example` are reused for compatibility.

**Tech Stack:** FastAPI, Pydantic, SQLite-backed app wiring, `httpx`, pytest.

### Task 1: Add failing tests for notification routes and pluginized dispatch

**Files:**
- Create: `refactor/backend/tests/unit/test_notification_hub.py`
- Modify: `refactor/backend/tests/unit/test_error_codes.py`

**Step 1: Write failing tests**

- Add tests for:
  - `GET /api/v2/notifications/channels` returns all supported channels with `enabled` state.
  - `POST /api/v2/notifications/preview` returns per-channel rendered payload.
  - `POST /api/v2/notifications/send` dispatches to enabled plugins and aggregates per-channel results.
  - `POST /api/v2/notifications/channels/test` sends a test message to target channel.
  - One channel failure does not block other channels.
- Extend error code contract assertions for notification errors.

**Step 2: Run tests to verify RED**

Run:

```bash
cd refactor/backend
PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_hub.py tests/unit/test_error_codes.py
```

Expected: fail due to missing notification route/service and missing error codes.

### Task 2: Implement notification domain and API with minimal plugin architecture

**Files:**
- Create: `refactor/backend/src/app/services/notification_service.py`
- Create: `refactor/backend/src/app/api/routes/notifications.py`
- Modify: `refactor/backend/src/app/api/deps.py`
- Modify: `refactor/backend/src/app/api/router.py`
- Modify: `refactor/backend/src/app/main.py`
- Modify: `refactor/backend/src/app/core/settings.py`
- Modify: `refactor/backend/src/app/shared/error_codes.py`

**Step 1: Implement minimal production code**

- Add notification models and plugin protocol:
  - `NotificationMessage`
  - `DeliveryResult`
  - `DeliveryReport`
  - `ChannelDescriptor`
  - `ChannelPlugin` interface
- Add built-in plugins (MVP minimal):
  - `wechat`, `feishu`, `telegram`, `email`, `pushover`, `pushplus`, `serverchan3`, `custom`, `discord`, `astrbot`
  - Use existing env keys to detect availability.
  - Network-based plugins via `httpx` (best-effort contracts), SMTP for email.
- Add `NotificationHub` operations:
  - `list_channels()`
  - `preview(message, channels?)`
  - `send(message, channels?)`
  - `test_channel(channel, message?)`
- Add FastAPI routes under `/api/v2/notifications/*`.
- Wire service into app state and dependency injection.
- Add notification timeout setting with sane default.
- Add notification error codes.

**Step 2: Run tests to verify GREEN**

Run:

```bash
cd refactor/backend
PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_hub.py tests/unit/test_error_codes.py
```

Expected: all pass.

### Task 3: Regression checks and documentation sync

**Files:**
- Modify: `refactor/backend/README.md`
- Modify: `refactor/docs/07-OpenAPI-v2-接口草案.yaml`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-02-19-迭代216-M4-notification-hub插件化最小闭环.md`

**Step 1: Update docs**

- README: add notification APIs and env notes.
- OpenAPI draft: add notification paths and key schemas.
- CHANGELOG: add M4 notification hub entry.
- Iteration record: objective, done/not done, tests, risks, next step.

**Step 2: Run regression**

Run:

```bash
cd refactor/backend
PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_hub.py tests/unit/test_feedback_optimization_service.py tests/unit/test_strategy_service.py
PYTHONPATH=src python3 -m pytest -q tests/unit
python3 -m compileall -q src
```

Expected: pass with no syntax errors.

