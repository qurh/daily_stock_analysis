# 2026-03-04 迭代270 - M4 Agent Metrics Observability

迭代编号：`迭代270`  
日期：`2026-03-04`  
负责人：`Codex`

---

## 1. 本迭代目标

1. 将 Agent 运行 trace 的核心观测指标接入全局指标端点。
2. 为运维与回归提供可查询的成功率、失败率、重试与延迟数据。
3. 保持指标低基数，避免引入高成本监控维度。

## 2. 计划范围（Plan）

1. 在 `test_metrics_route.py` 新增 Agent 指标契约测试（先红后绿）。
2. 在 `metrics.py` 增加 `agent_trace` 聚合快照与 Prometheus 指标输出。
3. 更新 README、CHANGELOG 与版本号，并补迭代记录。

## 3. 实际完成（Done）

1. 测试先行：
   - 新增 `test_metrics_expose_agent_tool_trace_observability_snapshot`。
   - 先运行 `pytest`，确认缺失指标断言失败（RED）。
2. 指标实现：
   - 新增 `_load_agent_tool_trace_observability_snapshot(request)`，聚合来源：
     - `conversation_messages.tool_trace_json`
     - 路径：`tool_trace.agent_trace.trace[]`
   - 新增全量指标：
     - `refactor_agent_tool_calls_total`
     - `refactor_agent_tool_calls_succeeded_total`
     - `refactor_agent_tool_calls_degraded_total`
     - `refactor_agent_tool_calls_failed_total`
     - `refactor_agent_tool_calls_retry_total`
     - `refactor_agent_tool_calls_latency_ms_avg`
     - `refactor_agent_tool_calls_failed_ratio`
   - 新增窗口指标：
     - `refactor_agent_tool_calls_total_24h`
     - `refactor_agent_tool_calls_total_7d`
     - `refactor_agent_tool_calls_total_30d`
     - `refactor_agent_tool_calls_failed_ratio_24h`
     - `refactor_agent_tool_calls_failed_ratio_7d`
     - `refactor_agent_tool_calls_failed_ratio_30d`
   - 新增标签指标：
     - `refactor_agent_tool_calls_by_tool_total{tool_name="..."}`
     - `refactor_agent_tool_calls_by_status_total{status="..."}`
     - `refactor_agent_tool_calls_error_code_total{error_code="..."}`
3. 文档与版本同步：
   - `refactor/backend/README.md` 增补 Agent 指标列表。
   - `refactor/docs/CHANGELOG.md` 新增版本节。
   - 后端版本更新为 `0.4.54-m4-agent-metrics-observability`。

## 4. 未完成项（Not Done）

1. 尚未接入实时 counter/histogram（当前为 SQLite snapshot gauge）。
2. 尚未增加 Agent 指标的 Prometheus 告警规则模板。
3. 尚未补前端可视化页面（仅后端指标接口可用）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/api/routes/metrics.py`
   - `refactor/backend/src/app/main.py`
   - `refactor/backend/tests/unit/test_metrics_route.py`
2. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/plans/2026-03-04-m4-agent-metrics-observability.md`

## 6. 验证记录

1. 执行命令：
   - `pytest -q refactor/backend/tests/unit/test_metrics_route.py`
   - `pytest -q refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_chat_service.py refactor/backend/tests/unit/test_agent_service.py refactor/backend/tests/unit/test_agent_routes.py refactor/backend/tests/unit/test_settings_env_names.py`
2. 结果摘要：
   - RED 阶段符合预期失败，GREEN 阶段通过。
   - 受影响回归测试通过。
3. 是否达到验收标准：
   - 是（Agent 指标可通过 `/api/v2/metrics` 统一导出，且已有自动化测试保障）。

## 7. 风险与问题

1. 风险描述：当前指标来自数据库快照，非实时累积计数。
2. 影响范围：高并发下会有时间窗口内可见性延迟。
3. 缓解措施：后续补充进程内计数器与指标采样策略，并保持与快照交叉校验。

## 8. 关键决策

1. 决策内容：优先实现低侵入的快照聚合指标，不引入额外监控中间件。
2. 决策原因：在现阶段先保障功能可观测与回归验证，再做性能化扩展。
3. 影响模块：`metrics.py`、`test_metrics_route.py`、运维指标文档。

## 9. 下迭代计划

1. 为 Agent 指标增加告警阈值与规则文件（warn/critical）。
2. 将 planner 策略版本、命中率、退化率接入可观测指标。
3. 在前端监控页展示 Agent 指标时间窗口趋势。
