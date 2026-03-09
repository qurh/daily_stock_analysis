# Upstream 更新融合清单

更新时间：2026-03-05  
适用分支：`refactor`  
分析基线：`upstream/main` 最新提交 `c87c8ff`（与 `origin/main` 对齐）

---

## 1. 目标与结论

目标：评估父仓库 `ZhuLinsen/daily_stock_analysis` 的近期更新，判断哪些能力可融合进 `refactor` 重构工程。

结论：

1. 可以融合，但应采用“能力迁移”而不是 `cherry-pick` 旧架构提交。
2. 高价值可融合项主要集中在：
   - 市场策略蓝图（CN/US）；
   - Agent 上下文保真（股票名/标的识别）；
   - 多 Key LLM 容灾能力（以 `refactor` 现有 Provider 架构实现）。
3. 与旧工程形态强绑定的能力（Electron/DMG/PyInstaller、老 WebUI 自动构建）不建议融合到 `refactor` 主线。

---

## 2. 融合原则

1. 只迁移“能力”，不迁移“实现细节”。
2. 以 `refactor/backend/src/app/*` 的模块边界为准，不回退到旧工程 `src/*` 架构。
3. 新能力优先挂载到既有主链路：
   - 分析链路：`analysis_service.py` + `factor_service.py` + `prompt_service.py`
   - 对话链路：`chat_service.py` + `agent_service.py`
   - 通知链路：`notification_service.py`
4. 每个融合项必须有对应单测。
5. 保持配置隔离：仅使用 `refactor/backend/.env`，不混用根目录 `.env`。

---

## 3. 上游更新评估矩阵

| 上游提交 | 能力点 | 与 refactor 关系 | 融合结论 | 优先级 |
|---|---|---|---|---|
| `17f7bac` | CN/US 市场策略蓝图系统 | `refactor` 已有分析编排与 Prompt 绑定，但缺少 region/blueprint 维度 | 融合（按能力重做） | P0 |
| `1fe967d` | Agent 流程中保留已解析股票名 | `refactor` Agent 将扩展行情/新闻工具，存在同类风险 | 融合（提前加固） | P0 |
| `0154992` | LiteLLM + 多 API Key 轮询 | `refactor` 已有 Provider 抽象（OpenAI-Compatible/DashScope），但缺少多 Key 池化 | 融合（不直接引 LiteLLM） | P1 |
| `46a8af4` | 通知发送器解耦重构 | `refactor` 已完成插件化 `NotificationHub` | 已覆盖，仅做差异补齐 | P1 |
| `115811e` | history API 精确查询修复 | `refactor` 当前无历史报告 API 模块，后续能力建设可参考 | 暂缓（待 history 模块立项） | P2 |
| `f3715b4` | 交易日检查开关 + `--force-run` | `refactor` 目前无调度执行器模块 | 暂缓（调度模块阶段引入） | P2 |
| `2349ac9` `b77519f` `69752b6` | 老 WebUI 启动构建与 UI 修复 | `refactor` 为独立前后端工程，不复用旧 WebUI | 不融合 | N/A |
| `175c1ad` `bc5b682` `bd0716a` | Electron/打包/发布 CI 修复 | 与 `refactor` 当前交付边界不匹配 | 不融合 | N/A |

---

## 4. 推荐实施批次

## 4.1 批次 A（P0，优先执行）

### A1. 分析链路引入市场策略蓝图（CN/US）

目标：

1. 分析任务可显式携带 `market_region`（`cn/us`）。
2. Prompt 渲染变量中注入策略蓝图文本，支撑区域化分析。

建议改动点：

- `refactor/backend/src/app/api/routes/analysis.py`
- `refactor/backend/src/app/services/analysis_service.py`
- `refactor/backend/src/app/core/settings.py`
- `refactor/backend/tests/unit/test_analysis_jobs.py`

验收标准：

1. `POST /api/v2/analysis/jobs` 支持 `market_region`；
2. `meta` 中可见 region 与 blueprint 标识；
3. 单测覆盖 `cn/us` 两种路径。

### A2. Agent 标的上下文保真（symbol/name canonical context）

目标：

1. Agent 调用链传递统一标的上下文（`symbol`, `resolved_name`, `aliases`）；
2. 避免工具调用后回复阶段丢失解析后的股票名称。

建议改动点：

- `refactor/backend/src/app/services/agent_service.py`
- `refactor/backend/src/app/services/chat_service.py`
- `refactor/backend/tests/unit/test_chat_service.py`（或新增 agent/chat 交互测试）

验收标准：

1. `tool_trace.agent_trace` 中包含标准化标的上下文；
2. 多轮消息后上下文不丢失；
3. 无标的请求时不污染上下文。

### A3. 通知能力差异补齐（以 PushPlus Topic 为代表）

目标：

1. 保持插件化架构不变，补齐上游常用配置能力；
2. 优先补足 `PUSHPLUS_TOPIC` 等低侵入、高收益能力。

建议改动点：

- `refactor/backend/src/app/services/notification_service.py`
- `refactor/backend/.env.example`
- `refactor/backend/README.md`
- `refactor/backend/tests/unit/test_notification_service.py`（如已有则补案例）

验收标准：

1. 配置 `PUSHPLUS_TOKEN + PUSHPLUS_TOPIC` 可正确发送；
2. 未配置 topic 不影响已有行为；
3. 对应单测通过。

## 4.2 批次 B（P1）

### B1. LLM Provider 多 Key 池化与故障切换

目标：

1. 在现有 Provider 架构中支持 `API_KEYS` 列表；
2. 失败计数、重试、熔断后自动切换 key。

建议改动点：

- `refactor/backend/src/app/llm/provider.py`
- `refactor/backend/src/app/core/settings.py`
- `refactor/backend/.env.example`
- `refactor/backend/tests/unit/test_llm_provider.py`

说明：不直接引入 LiteLLM，保持 `refactor` 的 Provider 抽象一致性。

### B2. Agent 工具能力补齐（行情/新闻/宏观）

目标：

1. 在 `AgentService` 中增量注册新工具；
2. 与现有 `knowledge/memory/backtest/workflow` 工具并存。

建议改动点：

- `refactor/backend/src/app/services/agent_service.py`
- `refactor/backend/src/app/services/factor_service.py`（复用或封装数据查询）
- `refactor/backend/tests/unit/test_agent_service.py`

---

## 5. 暂缓与不融合项说明

### 暂缓（后续阶段再处理）

1. history API 的精细修复：等待 `refactor` history/report 模块正式立项。
2. 交易日检查/`force-run`：等待调度器模块（cron/job runner）进入实现阶段。

### 不融合（架构不匹配）

1. 旧 WebUI 启动自动构建相关提交。
2. Electron/DMG/PyInstaller 打包链路相关提交。

---

## 6. 实施顺序建议（可直接执行）

1. 执行批次 A1（市场策略蓝图）。
2. 执行批次 A2（Agent 上下文保真）。
3. 执行批次 A3（通知差异补齐）。
4. 再进入批次 B1（多 Key Provider）。

说明：上述顺序与 `refactor/docs/05-项目重构实施方案.md` 的“先核心功能、后工程化补齐”原则一致。

---

## 7. 执行状态（2026-03-05）

- `A1` 分析链路市场策略蓝图（CN/US）：已完成
  - 产出：`market_region` 入参与 blueprint 注入，单测覆盖 `cn/us`
- `A2` Agent 标的上下文保真：已完成
  - 产出：`entity_context` 标准化透传与 `tool_trace.symbol_context` 保留
- `A3` 通知差异补齐（PushPlus Topic）：已完成
  - 产出：`PUSHPLUS_TOPIC` 配置支持与单测
- `B1` LLM Provider 多 Key 池化与故障切换：已完成
  - 产出：`LLM_API_KEYS` / `DASHSCOPE_API_KEYS`，retryable 错误自动切 key
- `B2` Agent 工具能力补齐（行情/新闻/宏观）：已完成（当前阶段）
  - 产出：`market.quote` / `macro.snapshot` / `credit.snapshot` / `sentiment.snapshot` / `news.search`
  - 补充：`agent routes` 合同测试覆盖新工具列表与 `news.search` 调用结果
  - 补充：`news.search` 已支持 `ANALYSIS_NEWS_SOURCE_URL` 外部新闻源适配，失败自动降级到 deterministic fallback

后续建议（非阻塞）：

1. 在前端 Agent/Chat 页面增加工具结果结构化展示（headlines/risk/sentiment 标签）。
2. 补充 `news.search` 与 UI 的联动筛选参数（query/top_k）可视化配置入口。
