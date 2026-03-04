# 迭代开发记录

迭代编号：`迭代264`  
日期：`2026-03-04`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为分析编排增加执行引擎选择：`local` / `langgraph`。
2. 在 `langgraph` 不可导入时自动回退到 `local`，保证任务可用性。
3. 在分析结果 `meta` 中沉淀编排引擎请求值、生效值与回退告警信息。

## 2. 计划范围（Plan）

1. Red：新增编排元数据与导入失败回退测试并确认失败。
2. Green：实现引擎路由、LangGraph 适配执行入口与导入失败回退逻辑。
3. 配置接入：新增 `ANALYSIS_ORCHESTRATOR_ENGINE`。
4. 文档同步：`.env.example`、README、CHANGELOG、计划与迭代记录。

## 3. 实际完成（Done）

1. 测试层（Red -> Green）：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
     - 默认编排元数据断言（`requested/effective=local`）。
     - `langgraph` 导入失败回退到 `local` 路径断言。
   - `refactor/backend/tests/unit/test_settings_env_names.py`
     - 新增 `ANALYSIS_ORCHESTRATOR_ENGINE` 配置读取断言。
2. 业务实现：
   - `refactor/backend/src/app/services/analysis_service.py`
     - 新增引擎路由：`_execute_flow(...)`。
     - 新增本地执行器入口：`_execute_flow_local(...)`。
     - 新增 LangGraph 执行入口：`_execute_flow_with_langgraph(...)`。
     - 导入失败自动回退并输出：`warning_code/langgraph_import_error`。
   - `refactor/backend/src/app/core/settings.py`
     - 新增并校验 `analysis_orchestrator_engine`（`local|langgraph`）。
   - `refactor/backend/src/app/main.py`
     - 注入 `analysis_orchestrator_engine`。
     - 版本升级：`0.4.48-m4-analysis-langgraph-adapter-fallback`。

## 4. 未完成项（Not Done）

1. 尚未接入 LangGraph 条件分支与扇出/汇聚高级能力（当前仅 stage 串接执行）。
2. 节点 trace 尚未记录 attempts/duration/degraded（下一迭代补齐）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/analysis_service.py`
   - `refactor/backend/src/app/core/settings.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
   - `refactor/backend/tests/unit/test_settings_env_names.py`
3. 文档路径：
   - `refactor/backend/.env.example`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/plans/2026-03-04-m4-analysis-langgraph-adapter-fallback.md`
   - `refactor/docs/迭代开发记录/2026-03-04-迭代264-M4-analysis-langgraph-adapter-fallback.md`

## 6. 验证记录

1. Red 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`
   - 结果：失败（缺少引擎配置、编排元数据与 LangGraph 入口）。
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

1. `langgraph` 依赖缺失时虽可回退，但功能等价性仍依赖本地执行器实现，需持续对齐。
2. 当前回退信息仅在结果 meta 中记录，尚未接入全局告警。

## 8. 关键决策

1. 决策内容：默认引擎保持 `local`，`langgraph` 作为可选增强，失败自动回退。
2. 决策原因：优先保证分析任务稳定可用，再逐步增强编排能力。

## 9. 下迭代计划

1. 补齐节点 trace 可观测字段：`attempts`、`duration_ms`、`degraded`。
2. 将新增字段持久化到 workflow trace 并在查询接口返回。
