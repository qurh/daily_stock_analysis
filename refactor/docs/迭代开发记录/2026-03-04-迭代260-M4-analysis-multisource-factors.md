# 迭代开发记录

迭代编号：`迭代260`  
日期：`2026-03-04`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐未完成需求中“分析多源因子融合”最小闭环。
2. 在不破坏既有分析/回测链路前提下，将宏观、信用、舆情因子进入结构化仪表盘。
3. 保持实现可扩展，为后续真实数据源接入留出 provider 插槽。

## 2. 计划范围（Plan）

1. 测试先行（Red）：增强分析任务测试，要求结果包含多源因子与决策字段。
2. 最小实现（Green）：新增 `FactorService` 与 4 类默认 provider，并接入 `AnalysisService`。
3. 回归验证：分析、回测、策略上下文相关测试必须全部通过。
4. 文档与版本：同步 README、CHANGELOG、版本号。

## 3. 实际完成（Done）

1. 测试层（Red->Green）：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
   - 新增断言：
     - `dashboard.factors` 包含 `technical/macro/credit/sentiment`
     - `dashboard.decision.direction/confidence`
     - `report.meta.factor_quality_flags`
2. 业务实现：
   - 新增：
     - `refactor/backend/src/app/services/factor_service.py`
   - 接入：
     - `refactor/backend/src/app/services/analysis_service.py`
       - 采集因子包并生成决策仪表盘
     - `refactor/backend/src/app/main.py`
       - 应用启动时注入 `FactorService`
3. 文档与版本：
   - `refactor/backend/README.md` 新增分析仪表盘结构说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.44` 条目
   - `refactor/backend/src/app/main.py` 版本升级：
     - `0.4.44-m4-analysis-multisource-factors`

## 4. 未完成项（Not Done）

1. 多源因子目前为可复现 mock/规则型 provider，尚未接入真实宏观/信用/舆情外部数据源。
2. 还未引入 LangGraph/LangChain 工具编排到分析主链路。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/factor_service.py`
   - `refactor/backend/src/app/services/analysis_service.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_analysis_jobs.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-03-04-迭代260-M4-analysis-multisource-factors.md`

## 6. 验证记录

1. Red 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py -k trace`
   - 结果：失败（`dashboard.factors` 缺失，符合预期）
2. Green 验证：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py -k trace`
   - 结果：通过
3. 关联回归：
   - `pytest -q refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_analysis_jobs.py`
   - 结果：通过
4. 语法检查：
   - `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/services/analysis_service.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_analysis_jobs.py`
   - 结果：通过

## 7. 风险与问题

1. 当前因子 provider 为确定性模拟逻辑，风险在于“功能契约可用，但数据真实性不足”。
2. 方向决策逻辑仍为规则融合，后续需引入可配置权重与策略版本绑定。

## 8. 关键决策

1. 决策内容：优先固化“报告结构契约 + 扩展点”，暂不直接接外部高波动数据源。
2. 决策原因：先保证分析、回测、治理链路稳定，再逐步替换数据 provider。

## 9. 下迭代计划

1. 引入真实宏观/信用/舆情 provider 适配器（保留当前 provider 作为降级）。
2. 将因子采集节点接入可编排流程模板（向 FR-ORC-001~003 靠齐）。

