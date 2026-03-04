# 迭代开发记录

迭代编号：`迭代267`  
日期：`2026-03-04`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 workflow trace 节点增加失败上下文字段：`failure_context`。
2. 在 `/api/v2/metrics` 增加 workflow trace 的 24h/7d/30d 窗口指标。
3. 保持 trace 与 metrics 契约向后兼容。

## 2. 计划范围（Plan）

1. Red：新增 `failure_context` 与窗口指标测试并观察失败。
2. Green：扩展 sqlite/workflow/analysis 三层，写入并回读 `failure_context`。
3. Green：扩展 metrics route，输出窗口总量/失败比率/平均耗时。
4. 文档同步：README、CHANGELOG、计划与迭代记录。

## 3. 实际完成（Done）

1. 测试层（Red -> Green）：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
     - 失败节点新增 `failure_context` 断言。
     - 成功/降级节点断言 `failure_context is None`。
   - `refactor/backend/tests/unit/test_workflow_executions.py`
     - 默认 workflow trace 节点断言 `failure_context is None`。
   - `refactor/backend/tests/unit/test_metrics_route.py`
     - 新增 24h/7d/30d 窗口总量与失败比率、平均耗时断言。
2. 业务实现：
   - `refactor/backend/src/app/services/analysis_service.py`
     - trace 失败节点新增 `failure_context`。
     - 新增 `failure_context` 清洗/截断逻辑，避免原始异常文本失控。
   - `refactor/backend/src/app/persistence/sqlite_db.py`
     - `workflow_trace_nodes` 增加 `failure_context` 列并兼容历史库。
   - `refactor/backend/src/app/services/workflow_service.py`
     - trace 持久化与查询新增 `failure_context` 字段。
   - `refactor/backend/src/app/api/routes/metrics.py`
     - workflow trace 快照新增时间窗口计算：24h/7d/30d。
     - 新增窗口指标输出：总量、失败比率、平均耗时。
   - `refactor/backend/src/app/main.py`
     - 版本升级：`0.4.51-m4-analysis-trace-failure-context-window-metrics`。

## 4. 未完成项（Not Done）

1. `failure_context` 目前为文本摘要，未引入结构化错误上下文对象。
2. 窗口指标当前以全表扫描计算，后续可优化为增量汇总。

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
   - `refactor/docs/plans/2026-03-04-m4-analysis-trace-failure-context-window-metrics.md`
   - `refactor/docs/迭代开发记录/2026-03-04-迭代267-M4-analysis-trace-failure-context-window-metrics.md`

## 6. 验证记录

1. Red 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_metrics_route.py`
   - 结果：失败（缺少 `failure_context` 字段与窗口指标）。
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

1. `failure_context` 若直接用于标签会导致高基数；当前仅在 trace API 返回，不进入标签维度。
2. 窗口统计基于 `ended_at` 解析，若历史数据时间格式异常会被窗口过滤。

## 8. 关键决策

1. 决策内容：`failure_context` 保持文本字段，做长度限制与空白规范化。
2. 决策原因：先满足排障可读性，再评估结构化上下文字段设计。

## 9. 下迭代计划

1. `failure_context` 增加脱敏策略（如 URL/token/路径掩码）。
2. 为窗口指标增加 degraded/retry 比率窗口维度（24h/7d/30d）。
