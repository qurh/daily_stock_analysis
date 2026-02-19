# 迭代开发记录

迭代编号：`迭代108`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 对优化提案 `target` 建立明确命名空间约束。
2. 按 `target` 类型增加 `diff` 字段级校验，防止提案语义不完整。
3. 保持现有审批、发布闸门和 M3 演练链路兼容。

## 2. 计划范围（Plan）

1. 先补失败测试：不支持 target、workflow 缺少 `flow_patch`、prompt 缺少 `prompt_patch`。
2. 在 `OptimizationService.create_proposal` 增加 target 分类与分目标校验。
3. 同步版本、README、CHANGELOG，并执行回归与 CI。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_feedback_optimization_service.py`
   - 新增用例：
     - `test_optimization_proposal_rejects_unsupported_target_namespace`
     - `test_workflow_proposal_requires_flow_patch_in_diff`
     - `test_prompt_proposal_requires_prompt_patch_in_diff`
2. TDD Green：
   - `refactor/backend/src/app/services/optimization_service.py`
   - 新增逻辑：
     - target 命名空间分类（`prompt.* / workflow.* / strategy.*`）
     - 不支持命名空间返回 `FDB-INPUT-003`
     - `prompt.*` 强制 `diff.prompt_patch`（`FDB-INPUT-005`）
     - `workflow.*` 强制 `diff.flow_patch`（`FDB-INPUT-004`）
     - `strategy.*` 强制 `diff.strategy_id`（`FDB-INPUT-002`）
   - `strategy.*` 支持 `diff.strategy.strategy_id`，并归一化写入 `diff.strategy_id`。
3. 文档与版本：
   - `refactor/backend/README.md` 增补 target/diff 约束清单。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.93-m3-proposal-target-schema`。
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.93-m3-proposal-target-schema`。

## 4. 未完成项（Not Done）

1. 暂未将 `target` 改为接口层枚举（当前在服务层做强校验）。
2. 暂未接入统一 JSON Schema 校验引擎（当前为代码逻辑校验）。

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
   - `refactor/docs/迭代开发记录/2026-02-19-迭代108-M3-提案target分目标schema校验.md`

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
   - 达到（target 命名空间与分目标 diff 约束已生效）

## 7. 风险与问题

1. 风险描述：历史客户端若发送不合规 target/diff 会新增 400。
2. 影响范围：优化提案创建接口兼容性。
3. 缓解措施：README 已同步约束，后续前端/机器人请求体同步适配。

## 8. 关键决策

1. 决策内容：优先服务层分类校验，不在本轮引入 API 层枚举破坏性变更。
2. 决策原因：兼容性更平滑，便于后续逐步迁移到显式枚举。
3. 影响模块：Optimization 提案入口与发布前治理质量。

## 9. 下迭代计划

1. 在 API 请求模型上增加 `target` 枚举/受限模式，并给出迁移窗口。
2. 将 proposal schema 与 `target` 枚举对齐到文档规范（`04-详细逻辑设计文档.md`）。
3. 增加 `FDB-INPUT-00x` 指标统计，观测客户端兼容性风险。
