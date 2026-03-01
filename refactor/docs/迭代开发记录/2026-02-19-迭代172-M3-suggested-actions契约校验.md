# 迭代开发记录

迭代编号：`迭代172`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 `suggested_actions` 提供严格契约校验，防止 action 结构漂移。
2. 在 shared helper 层统一兜底，避免脚本调用方返回非法 action payload。
3. 增加失败用例，确保非法 action 能被明确拒绝。

## 2. 计划范围（Plan）

1. 先补失败测试：unknown action、缺失必填字段两类错误路径。
2. 在 `profile_suggestion_helpers.py` 实现 `validate_suggested_actions_contract(...)`。
3. 在 action 构造函数返回前强制执行契约校验。
4. 同步 README、CHANGELOG、版本号与回归验证。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增测试：
     - `test_profile_suggestion_helper_rejects_unknown_action_contract`
     - `test_profile_suggestion_helper_rejects_missing_required_action_field`
2. TDD Green：
   - `refactor/backend/scripts/profile_suggestion_helpers.py`
   - 新增：
     - `SUPPORTED_SUGGESTED_ACTIONS`（action 枚举与必填字段声明）
     - `validate_suggested_actions_contract(...)`
   - 变更：
     - `build_suggested_actions_for_profile_not_found(...)` 返回前执行契约校验
3. 文档与版本：
   - `refactor/backend/README.md` 增补 strict contract validation 说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.157-m3-error-code-suggested-actions-contract-validation`
   - `refactor/backend/src/app/main.py` 升级为 `0.3.157-m3-error-code-suggested-actions-contract-validation`

## 4. 未完成项（Not Done）

1. 当前校验聚焦 action 枚举与关键字段类型，尚未扩展到更细粒度字段语义（例如 command 可执行性）。
2. 尚未单独拆分 helper unit test 文件（仍与现有测试文件共存）。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/scripts/profile_suggestion_helpers.py`
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代172-M3-suggested-actions契约校验.md`

## 6. 验证记录

1. Red 阶段：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "profile_suggestion_helper_module_is_shared_and_contract_stable or profile_suggestion_helper_rejects_unknown_action_contract or profile_suggestion_helper_rejects_missing_required_action_field"`
   - 结果：预期失败（`validate_suggested_actions_contract` 尚不存在）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 兼容回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "suggests_nearby_profile or handles_no_nearby_profile_suggestion or reports_non_profile_config_when_profile_requested or suggests_nearby_lint_profile or handles_no_nearby_lint_profile_suggestion"`
   - 结果：通过。
4. 全量回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
5. 是否达到验收标准：
   - 达到（`suggested_actions` 已具备 shared helper 级别契约校验）。

## 7. 风险与问题

1. 风险描述：契约校验更严格后，后续扩展 action 字段可能触发旧调用路径异常。
2. 影响范围：所有通过 shared helper 生成或验证 action 的脚本路径。
3. 缓解措施：新增 action 时先扩展 `SUPPORTED_SUGGESTED_ACTIONS` 并补测试。

## 8. 关键决策

1. 决策内容：在 shared helper 层强制执行 `suggested_actions` 合规校验。
2. 决策原因：统一防线，避免不同脚本各自放宽校验导致契约漂移。
3. 影响模块：unknown profile suggestion 相关 helper 与调用点。

## 9. 下迭代计划

1. 为 `suggested_actions` 增补独立 schema 文件与 schema 校验脚本（可选门禁）。
2. 将 helper 合同测试下沉到独立测试文件，减小巨型测试文件耦合。
3. 评估在 API 层把 invalid action 转换为结构化错误码，方便上游快速定位。
