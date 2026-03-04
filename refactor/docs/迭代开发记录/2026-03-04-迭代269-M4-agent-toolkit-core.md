# 2026-03-04 迭代269 - M4 Agent Toolkit Core

迭代编号：`迭代269`  
日期：`2026-03-04`  
负责人：`Codex`

---

## 1. 本迭代目标

1. 补齐 FR-AGT-001~004 的最小可用实现。
2. 提供 Agent 工具注册/调用接口，支持调试与后续扩展。
3. 将 Agent 运行链路接入 Chat，并返回工具调用 trace。

## 2. 计划范围（Plan）

1. 新增 `AgentService`（协议、注册、计划、执行、重试、降级）。
2. 新增 `/api/v2/agent/*` 路由。
3. Chat 自动触发 Agent，并在 `tool_trace` 中输出 `agent_trace`。

## 3. 实际完成（Done）

1. 新增 `refactor/backend/src/app/services/agent_service.py`：
   - `ToolSpec` + `ToolNotFoundError`
   - `register_tool` / `register_static_tool` / `list_tools`
   - `plan` / `invoke` / `invoke_with_intent`
   - 重试 + 降级 + trace bundle
2. 新增 `refactor/backend/src/app/api/routes/agent.py`：
   - `POST /api/v2/agent/tools/register`
   - `GET /api/v2/agent/tools`
   - `POST /api/v2/agent/invoke`
3. 接入依赖注入与路由树：
   - `api/deps.py`、`api/router.py`
4. Chat 联动完成：
   - `ChatService` 自动执行 Agent intent invoke
   - assistant `tool_trace` 增加 `agent_trace`
5. 新增配置项：
   - `AGENT_TOOL_MAX_RETRIES`
   - `AGENT_TOOL_RETRY_BACKOFF_MS`
6. 测试补齐：
   - `test_agent_service.py`
   - `test_agent_routes.py`
   - `test_chat_service.py`（agent_trace 断言）
   - `test_settings_env_names.py`（新增 env 断言）

## 4. 未完成项（Not Done）

1. 未接入 LangChain/LlamaIndex 真实 Agent 框架（当前为自研最小执行内核）。
2. 未实现工具级熔断器与并行调用调度（当前串行 + 重试 + 降级）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/agent_service.py`
   - `refactor/backend/src/app/api/routes/agent.py`
   - `refactor/backend/src/app/services/chat_service.py`
   - `refactor/backend/src/app/main.py`
   - `refactor/backend/src/app/core/settings.py`
   - `refactor/backend/src/app/api/deps.py`
   - `refactor/backend/src/app/api/router.py`
   - `refactor/backend/tests/unit/test_agent_service.py`
   - `refactor/backend/tests/unit/test_agent_routes.py`
2. 文档路径：
   - `refactor/backend/.env.example`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
3. 接口/配置变更：
   - 新增 Agent API 与 Agent runtime env 配置。

## 6. 验证记录

1. 执行命令：
   - `pytest -q refactor/backend/tests/unit/test_agent_service.py refactor/backend/tests/unit/test_agent_routes.py refactor/backend/tests/unit/test_chat_service.py refactor/backend/tests/unit/test_settings_env_names.py`
   - `pytest -q refactor/backend/tests/unit/test_knowledge_service.py refactor/backend/tests/unit/test_memory_service.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_chat_prompt_binding.py`
   - `python3 -m py_compile refactor/backend/src/app/services/agent_service.py refactor/backend/src/app/api/routes/agent.py refactor/backend/src/app/services/chat_service.py refactor/backend/src/app/main.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/api/deps.py refactor/backend/src/app/api/router.py`
2. 结果摘要：
   - 目标测试通过，回归测试通过，语法检查通过。
3. 是否达到验收标准：
   - 是（FR-AGT 最小闭环可用，且未破坏现有主链路测试）。

## 7. 风险与问题

1. 风险描述：当前意图规划基于关键词匹配，准确率依赖表达风格。
2. 影响范围：复杂问题下工具组合可能不足或冗余。
3. 缓解措施：下一步引入策略驱动规划与 LLM-based planner，可灰度替换。

## 8. 关键决策

1. 决策内容：先实现可测试的自研 Agent 运行内核，再接框架适配层。
2. 决策原因：优先满足 MVP 功能闭环与可控可测。
3. 影响模块：`agent_service`、`chat_service`、`api/routes/agent.py`。

## 9. 下迭代计划

1. 引入工具并行调用与超时中断策略。
2. 增加 Agent 运行指标到 `/api/v2/metrics`。
3. 前端补 Agent 调试入口（工具注册/调用与 trace 可视化）。
