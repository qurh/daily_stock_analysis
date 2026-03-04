# 迭代开发记录

迭代编号：`迭代262`  
日期：`2026-03-04`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将因子采集与仪表盘聚合接入分析主链路的可编排节点执行。
2. 支持通过配置调整节点执行顺序，并将真实节点轨迹写入 workflow trace。
3. 保持分析、回测、策略上下文等既有能力不回归。

## 2. 计划范围（Plan）

1. 测试先行（Red）：分析 trace 断言必须包含 `collect_factors/build_dashboard/finalize_report`，并支持自定义模板顺序。
2. 最小实现（Green）：
   - Workflow 支持 defer run + 外部回填执行结果。
   - Analysis 按模板执行节点并回写轨迹。
3. 配置接入：`ANALYSIS_FLOW_TEMPLATE`。
4. 回归：分析、回测、workflow、设置、通知相关单测通过。
5. 文档：README、`.env.example`、CHANGELOG、迭代记录。

## 3. 实际完成（Done）

1. 测试层（Red -> Green）：
   - 更新 `refactor/backend/tests/unit/test_analysis_jobs.py`
     - 默认 trace 要求出现 `collect_factors/build_dashboard` 且 `finalize_report` 结尾。
     - 新增自定义模板顺序测试。
   - 更新 `refactor/backend/tests/unit/test_settings_env_names.py`
     - 新增 `ANALYSIS_FLOW_TEMPLATE` 配置读取断言。
2. 业务实现：
   - 更新 `refactor/backend/src/app/services/workflow_service.py`
     - `start_execution(..., defer_run=True)` 支持延迟执行。
     - 新增 `complete_execution(...)` / `fail_execution(...)`。
   - 更新 `refactor/backend/src/app/services/analysis_service.py`
     - 引入节点处理器映射与模板执行：
       - `resolve_strategy_context`
       - `resolve_prompt`
       - `collect_factors`
       - `build_dashboard`
       - `finalize_report`
     - 节点执行结果写回 workflow trace。
   - 更新 `refactor/backend/src/app/core/settings.py`
     - 新增 `analysis_flow_template`。
   - 更新 `refactor/backend/src/app/main.py`
     - 注入 `analysis_flow_template` 到 `AnalysisService`。
3. 文档与版本：
   - 更新 `refactor/backend/.env.example`
   - 更新 `refactor/backend/README.md`
   - 更新 `refactor/docs/CHANGELOG.md`
   - 版本升级：`0.4.46-m4-analysis-flow-template-orchestration`

## 4. 未完成项（Not Done）

1. 当前仍为“线性模板编排”，未提供并行分支/条件分支执行（LangGraph 深度能力后续接入）。
2. 尚未实现节点级 prompt 独立模板管理 UI（后续与 Prompt Center 联动）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/workflow_service.py`
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
   - `refactor/docs/迭代开发记录/2026-03-04-迭代262-M4-analysis-flow-template-orchestration.md`

## 6. 验证记录

1. Red 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`
   - 结果：失败（旧 trace 节点不满足断言，settings 缺字段）
2. Green 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_notification_hub.py`
   - 结果：通过
3. 关联回归：
   - `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_workflow_executions.py refactor/backend/tests/unit/test_settings_env_names.py`
   - 结果：通过
4. 语法与风格：
   - `python3 -m py_compile refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py`
   - `flake8 refactor/backend/src/app/services/workflow_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_settings_env_names.py --max-line-length=120`
   - 结果：通过

## 7. 风险与问题

1. 模板配置错误会在服务启动阶段直接失败（快速失败），需在部署前校验。
2. defer-run 模式增强了灵活性，但要求调用方在异常路径显式调用 `fail_execution(...)`，否则可能遗留 pending/running 记录。

## 8. 关键决策

1. 决策内容：先落地“模板化线性节点 + trace 回写”最小编排闭环，再引入 LangGraph 的并行/分支。
2. 决策原因：以最低风险满足 FR-ORC-001 的节点化和可编排要求，同时保证现有链路稳定。

## 9. 下迭代计划

1. 接入 LangGraph adapter，补串并混编、条件分支和节点级重试降级（FR-ORC-002、FR-AGT-004）。
2. 将节点级 prompt 参数化配置与 Prompt Center 版本发布机制绑定（FR-ORC-003、FR-ORC-004）。
