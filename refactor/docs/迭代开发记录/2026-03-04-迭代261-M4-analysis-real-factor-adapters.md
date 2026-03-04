# 迭代开发记录

迭代编号：`迭代261`  
日期：`2026-03-04`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐未完成需求中“真实宏观/信用/舆情 provider 适配器”最小闭环。
2. 保持分析链路稳定，在外部数据源失败时自动降级到内置因子逻辑。
3. 将适配器配置项统一纳入 `refactor/backend/.env` 体系。

## 2. 计划范围（Plan）

1. 测试先行（Red）：新增测试覆盖外部因子源成功路径与失败降级路径。
2. 最小实现（Green）：为宏观/信用/舆情 provider 增加 HTTP JSON 适配能力与 fallback。
3. 配置接入：`settings` + `main` 注入配置化 provider。
4. 回归验证：分析、回测、策略上下文、workflow 基础测试保持通过。
5. 文档同步：README、CHANGELOG、`.env.example`。

## 3. 实际完成（Done）

1. 测试层（Red -> Green）：
   - 新增 `refactor/backend/tests/unit/test_factor_service.py`
   - 扩展 `refactor/backend/tests/unit/test_settings_env_names.py`
   - 覆盖点：
     - 外部因子源配置成功读取并返回外部数据
     - 外部数据源失败时自动回退 deterministic fallback
     - `quality_flags` 记录降级原因
2. 业务实现：
   - 改造 `refactor/backend/src/app/services/factor_service.py`
     - 宏观/信用/舆情 provider 支持 `source_url + auth_token + timeout`
     - 外部失败自动 fallback 并写入 `_quality_flag`
   - 改造 `refactor/backend/src/app/core/settings.py`
     - 新增 analysis factor adapter 配置项
   - 改造 `refactor/backend/src/app/main.py`
     - 启动时根据 settings 组装 provider
3. 文档与配置模板：
   - 更新 `refactor/backend/.env.example`
   - 更新 `refactor/backend/README.md`
   - 更新 `refactor/docs/CHANGELOG.md`
   - 版本升级：`0.4.45-m4-analysis-real-factor-adapters`

## 4. 未完成项（Not Done）

1. 真实外部数据源的“官方 API 适配器”仍未逐一落地（当前为通用 HTTP JSON 适配层）。
2. 因子采集节点尚未并入 LangGraph 主编排执行链路（下一迭代处理）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/factor_service.py`
   - `refactor/backend/src/app/core/settings.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_factor_service.py`
   - `refactor/backend/tests/unit/test_settings_env_names.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/backend/.env.example`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-03-04-迭代261-M4-analysis-real-factor-adapters.md`

## 6. 验证记录

1. Red 验证：
   - `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_settings_env_names.py`
   - 结果：失败（符合预期，缺少 provider 参数和 settings 字段）
2. Green 验证：
   - `pytest -q refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_settings_env_names.py`
   - 结果：通过
3. 关联回归：
   - `pytest -q refactor/backend/tests/unit/test_analysis_jobs.py refactor/backend/tests/unit/test_backtest_service.py refactor/backend/tests/unit/test_strategy_context_injection.py refactor/backend/tests/unit/test_workflow_executions.py`
   - 结果：通过
4. 语法检查：
   - `python3 -m py_compile refactor/backend/src/app/services/factor_service.py refactor/backend/src/app/core/settings.py refactor/backend/src/app/main.py refactor/backend/tests/unit/test_factor_service.py refactor/backend/tests/unit/test_settings_env_names.py`
   - 结果：通过

## 7. 风险与问题

1. 外部接口返回 schema 不稳定时，当前策略为 fallback + quality flag，不会中断分析任务。
2. 统一 `auth_token` 方案可快速接入，但不同供应商的签名机制（HMAC、query key）需后续按供应商细化。

## 8. 关键决策

1. 决策内容：先交付“通用 HTTP JSON 适配 + fallback”，不在本轮绑定单一供应商 SDK。
2. 决策原因：优先满足可扩展与可降级，避免供应商耦合影响主链路稳定性。

## 9. 下迭代计划

1. 将因子采集与决策聚合拆为可编排节点并接入 workflow 主链路（FR-ORC-001~003）。
2. 增加供应商级 adapter（宏观/信用/舆情）和契约校验样例。
