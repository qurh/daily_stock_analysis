# 迭代开发记录

迭代编号：`迭代263`  
日期：`2026-03-04`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 在分析流程模板中支持并行因子采集子阶段（`+` 分组语法）。
2. 为分析节点执行增加可配置重试策略（重试次数与退避）。
3. 保持分析结果结构与 workflow trace 契约稳定。

## 2. 计划范围（Plan）

1. Red：新增并行模板与节点重试相关测试并观察失败。
2. Green：实现 stage 解析、并行执行、节点重试执行器。
3. 扩展 FactorService：按单因子采集接口支持模块化编排。
4. 配置接入：增加 `ANALYSIS_NODE_MAX_RETRIES`、`ANALYSIS_NODE_RETRY_BACKOFF_MS`。
5. 文档同步：`.env.example`、README、CHANGELOG、计划与迭代记录。

## 3. 实际完成（Done）

1. 测试层（Red -> Green）：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
     - 自定义 `+` 并行因子分组模板执行路径。
     - 节点瞬时失败后重试成功路径。
     - 重试预算耗尽失败路径（trace 保留失败节点）。
   - `refactor/backend/tests/unit/test_settings_env_names.py`
     - 新增重试配置项读取断言。
2. 业务实现：
   - `refactor/backend/src/app/services/analysis_service.py`
     - 模板解析升级为 stage 模型（支持 `+` 分组）。
     - 新增并行因子 stage 执行器。
     - 新增节点重试执行器（指数退避）。
     - 新增分因子节点：
       - `collect_technical_factor`
       - `collect_macro_factor`
       - `collect_credit_factor`
       - `collect_sentiment_factor`
     - 非 Prompt 异常失败时，落库 `result_json + execution_id`，确保 trace/result 可追溯。
   - `refactor/backend/src/app/services/factor_service.py`
     - 新增 `collect_factor(...)` 单因子采集 API。
     - 新增 `empty_factor_pack()`。
   - `refactor/backend/src/app/core/settings.py`
     - 新增 `analysis_node_max_retries`
     - 新增 `analysis_node_retry_backoff_ms`
   - `refactor/backend/src/app/main.py`
     - 注入新重试配置。
     - 版本升级：`0.4.47-m4-analysis-parallel-retry-orchestration`

## 4. 未完成项（Not Done）

1. 并行 stage 当前仅支持因子采集节点；尚未开放到任意节点类型。
2. 尚未接入 LangGraph 原生执行图（当前为本地 stage 执行器）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/analysis_service.py`
   - `refactor/backend/src/app/services/factor_service.py`
   - `refactor/backend/src/app/core/settings.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
   - `refactor/backend/tests/unit/test_settings_env_names.py`
3. 文档路径：
   - `refactor/backend/.env.example`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/plans/2026-03-04-m4-analysis-parallel-retry-orchestration.md`
   - `refactor/docs/迭代开发记录/2026-03-04-迭代263-M4-analysis-parallel-retry-orchestration.md`

## 6. 验证记录

1. Red 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`
   - 结果：失败（`+` 分组和重试配置未实现）。
2. Green 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`
   - 结果：通过。
3. 关联回归：
   - `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_notification_hub.py`
   - 结果：通过。
4. 语法与风格：
   - `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`
   - `flake8 refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`
   - 结果：通过。

## 7. 风险与问题

1. 并行 stage 中若外部因子源整体抖动，可能触发集中重试，需后续加全局并发限速策略。
2. 当前 trace 节点无 attempts 字段，难以直接观察重试次数，后续建议扩展 trace schema。

## 8. 关键决策

1. 决策内容：并行能力先限定在因子采集节点，避免共享上下文并发写的复杂度扩散。
2. 决策原因：先满足可编排与性能收益主路径，再逐步扩展到通用并行节点。

## 9. 下迭代计划

1. 引入 LangGraph adapter（节点依赖图 + 条件分支 + 并行扇出/汇聚）。
2. 补节点 trace 的重试次数、耗时、降级标记字段，完善治理观测。
