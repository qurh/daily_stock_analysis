# 迭代开发记录

迭代编号：`迭代107`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 降低 chatbot 策略提案与策略实体关联歧义。
2. 为提案输入增加 schema 级别硬约束。
3. 保持现有审批与发布闸门流程兼容。

## 2. 计划范围（Plan）

1. 先补失败测试，定义 `diff.strategy_id` 必填约束。
2. 在 `OptimizationService.create_proposal` 增加校验与归一化。
3. 同步版本、文档、CHANGELOG 并回归验证。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_feedback_optimization_service.py`
   - 新增用例 `test_chatbot_strategy_proposal_requires_strategy_id_in_diff`。
2. TDD Green：
   - `refactor/backend/src/app/services/optimization_service.py`
   - 新增 schema gate：
     - 当 `source=chatbot` 且 `target` 以 `strategy.` 开头时，
       要求 `diff.strategy_id`（支持直接字段和 `diff.strategy.strategy_id`）。
     - 缺失时返回 `ValueError("FDB-INPUT-002: ...")`，API 层映射为 `400`。
   - 入库前对 `strategy_id` 做归一化并写回 `diff`，提升后续闸门稳定性。
3. 文档与版本：
   - `refactor/backend/README.md` 新增 Optimization Proposal Schema Gate 说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.92-m3-chatbot-proposal-schema-gate`。
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.92-m3-chatbot-proposal-schema-gate`。

## 4. 未完成项（Not Done）

1. 暂未对 `target` 的领域枚举做更细粒度白名单（当前以前缀 `strategy.` 判定）。
2. 暂未引入 JSON Schema 校验器（当前为服务层逻辑校验）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/optimization_service.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_feedback_optimization_service.py`
   - `refactor/backend/tests/unit/test_strategy_service.py`（回归通过）
   - `refactor/backend/tests/integration/test_m3_acceptance_loop.py`（回归通过）
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代107-M3-chatbot提案schema校验.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_feedback_optimization_service.py -q`
   - `cd refactor/backend && pytest tests/unit/test_strategy_service.py -q`
   - `cd refactor/backend && pytest tests/integration/test_m3_acceptance_loop.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - 新增 schema 校验用例：通过
   - 策略与 M3 集成回归：通过
   - CI 脚本：通过
3. 是否达到验收标准：
   - 达到（chatbot 策略提案关联字段具备强校验）

## 7. 风险与问题

1. 风险描述：对旧客户端若未提供 `strategy_id` 会触发新增 400。
2. 影响范围：chatbot 策略提案请求兼容性。
3. 缓解措施：README 与接口约束已同步，后续前端/机器人侧补默认字段。

## 8. 关键决策

1. 决策内容：优先在服务层加轻量 schema gate，而非一次性引入全量 JSON Schema 框架。
2. 决策原因：实现成本低、收益立即生效、便于后续平滑演进。
3. 影响模块：优化提案创建链路与策略发布关联稳定性。

## 9. 下迭代计划

1. 将 `target` 标准化为枚举并做分目标 schema 校验。
2. 考虑在发布接口显式传入 `proposal_id`，减少隐式匹配。
3. 将 `FDB-INPUT-002` 纳入指标/告警，跟踪请求兼容性问题。
