# 迭代开发记录

迭代编号：`迭代266`  
日期：`2026-03-04`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 在分析 trace 中新增结构化失败/降级原因字段：`failure_code`、`degrade_reason`。
2. 将上述字段持久化到 `workflow_trace_nodes` 并通过查询接口回读。
3. 在 `/api/v2/metrics` 输出 workflow trace 节点可观测聚合指标。

## 2. 计划范围（Plan）

1. Red：补充 analysis/workflow/metrics 合约测试并验证失败。
2. Green：扩展 `analysis_service` trace 节点结构与原因归一化逻辑。
3. Green：扩展 sqlite/workflow 持久化字段与回读。
4. Green：扩展 metrics 路由输出节点总量/比率/标签统计。
5. 文档同步：README、CHANGELOG、计划与迭代记录。

## 3. 实际完成（Done）

1. 测试层（Red -> Green）：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
     - 增加 `failure_code/degrade_reason` 断言。
     - 重试成功路径断言 `degrade_reason=retry_recovered`。
     - 重试耗尽失败路径断言 `failure_code=node_execution_error`。
   - `refactor/backend/tests/unit/test_workflow_executions.py`
     - 增加 workflow trace 默认原因字段断言（`None`）。
   - `refactor/backend/tests/unit/test_metrics_route.py`
     - 新增 `/api/v2/metrics` workflow trace 可观测指标合约测试。
2. 业务实现：
   - `refactor/backend/src/app/services/analysis_service.py`
     - trace 节点统一输出：`failure_code/degrade_reason`。
     - 新增失败码归一化与降级原因归一化方法。
   - `refactor/backend/src/app/persistence/sqlite_db.py`
     - `workflow_trace_nodes` 增加列：`failure_code`、`degrade_reason`。
     - `init_schema()` 增加兼容 `_ensure_column`。
   - `refactor/backend/src/app/services/workflow_service.py`
     - trace 写入与读取增加 `failure_code/degrade_reason`。
   - `refactor/backend/src/app/api/routes/metrics.py`
     - 新增 workflow trace 可观测快照加载逻辑。
     - 新增 workflow trace Prometheus 指标输出（总量/比率/标签计数）。
   - `refactor/backend/src/app/main.py`
     - 版本升级：`0.4.50-m4-analysis-trace-failure-metrics`。

## 4. 未完成项（Not Done）

1. 失败原因目前为低基数归一化码，尚未接入详细错误上下文（如节点异常摘要）。
2. 暂未新增 trace 时间窗口指标（24h/7d/30d）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/analysis_service.py`
   - `refactor/backend/src/app/services/workflow_service.py`
   - `refactor/backend/src/app/persistence/sqlite_db.py`
   - `refactor/backend/src/app/api/routes/metrics.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
   - `refactor/backend/tests/unit/test_workflow_executions.py`
   - `refactor/backend/tests/unit/test_metrics_route.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/plans/2026-03-04-m4-analysis-trace-failure-metrics.md`
   - `refactor/docs/迭代开发记录/2026-03-04-迭代266-M4-analysis-trace-failure-metrics.md`

## 6. 验证记录

1. Red 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py`
   - 结果：失败（缺少 `failure_code/degrade_reason` 字段与 metrics 合约未实现）。
2. Green 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py`
   - 结果：通过。
3. 关联回归：
   - `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_notification_hub.py`
   - 结果：通过。
4. 语法与风格：
   - `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/api/routes/metrics.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_settings_env_names.py`
   - `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/api/routes/metrics.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`
   - 结果：通过。

## 7. 风险与问题

1. 若未来将 `failure_code/degrade_reason` 扩展为高基数字段，Prometheus 标签可能膨胀。
2. 目前指标为全量快照，超大数据量下需要进一步优化为增量聚合。

## 8. 关键决策

1. 决策内容：原因字段先保持低基数枚举，避免标签爆炸。
2. 决策原因：优先确保线上可观测稳定，再逐步扩展失败上下文细节。

## 9. 下迭代计划

1. 在 trace 中补充 `failure_context`（截断且脱敏）并维持低基数标签策略。
2. 为 workflow trace 指标新增时间窗口视图（24h/7d/30d）。
