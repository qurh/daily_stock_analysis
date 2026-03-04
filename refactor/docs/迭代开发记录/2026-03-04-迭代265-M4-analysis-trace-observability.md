# 迭代开发记录

迭代编号：`迭代265`  
日期：`2026-03-04`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为分析流程 trace 节点补齐可观测字段：`attempts`、`duration_ms`、`degraded`。
2. 保证新增字段可持久化并可通过现有查询接口回读。
3. 与现有流程编排和回测链路保持兼容。

## 2. 计划范围（Plan）

1. Red：先在分析/工作流测试中断言新增字段并验证失败。
2. Green：在分析执行器计算节点指标并写入 trace。
3. 持久化：扩展 `workflow_trace_nodes` schema 与读写逻辑。
4. 文档同步：README、CHANGELOG、计划与迭代记录。

## 3. 实际完成（Done）

1. 测试层（Red -> Green）：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
     - 默认分析 trace 断言 `attempts/duration_ms/degraded`。
     - 瞬时失败重试成功路径断言 `attempts=2`、`degraded=true`。
     - 重试预算耗尽失败路径断言 `attempts=1`、`degraded=false`。
   - `refactor/backend/tests/unit/test_workflow_executions.py`
     - 工作流 trace 节点断言新增字段存在且类型正确。
2. 业务实现：
   - `refactor/backend/src/app/services/analysis_service.py`
     - 顺序节点执行新增耗时统计（`duration_ms`）与尝试次数（`attempts`）。
     - 并行因子采集节点新增尝试次数、耗时与降级标记计算。
     - 新增统一 trace 节点构造逻辑，输出契约稳定。
   - `refactor/backend/src/app/persistence/sqlite_db.py`
     - `workflow_trace_nodes` 增加兼容列：`attempts`、`duration_ms`、`degraded`。
     - `init_schema()` 加入 `_ensure_column`，兼容既有数据库。
   - `refactor/backend/src/app/services/workflow_service.py`
     - trace 持久化写入新增字段。
     - 查询接口回读并返回新增字段。
   - `refactor/backend/src/app/main.py`
     - 版本升级：`0.4.49-m4-analysis-trace-observability`。

## 4. 未完成项（Not Done）

1. 尚未为 trace 增加更细粒度错误码/降级原因字段（当前只提供布尔降级标记）。
2. 尚未将 trace 指标直接对接监控指标输出（当前仅 API 可查）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/analysis_service.py`
   - `refactor/backend/src/app/services/workflow_service.py`
   - `refactor/backend/src/app/persistence/sqlite_db.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
   - `refactor/backend/tests/unit/test_workflow_executions.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/plans/2026-03-04-m4-analysis-trace-observability.md`
   - `refactor/docs/迭代开发记录/2026-03-04-迭代265-M4-analysis-trace-observability.md`

## 6. 验证记录

1. Red 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py`
   - 结果：失败（缺少 `attempts/duration_ms/degraded`）。
2. Green 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py`
   - 结果：通过。
3. 关联回归：
   - `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_notification_hub.py`
   - 结果：通过。
4. 语法与风格：
   - `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_settings_env_names.py`
   - `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/persistence/sqlite_db.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`
   - 结果：通过。

## 7. 风险与问题

1. 并行阶段失败场景下暂未输出结构化失败原因，只保留失败状态与降级标记。
2. `duration_ms` 为进程内测量值，跨实例对比需统一时钟与采样策略。

## 8. 关键决策

1. 决策内容：trace 先落最小观测字段（三元组），保持数据库与接口轻量兼容。
2. 决策原因：优先满足可观测闭环与调试需求，后续再逐步加详细失败上下文。

## 9. 下迭代计划

1. trace 增加失败原因码与降级原因（细粒度）。
2. 将节点级 trace 指标汇聚到 `/api/v2/metrics`，形成时序观测。
