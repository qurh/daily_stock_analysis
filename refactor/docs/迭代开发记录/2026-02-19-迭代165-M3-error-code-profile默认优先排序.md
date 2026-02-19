# 迭代开发记录

迭代编号：`迭代165`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 优化 unknown profile 响应中的 `available_profiles` 排序。
2. 让 `default_profile` 优先显示，提升修复引导效率。
3. 保持现有字段结构兼容。

## 2. 计划范围（Plan）

1. 先补失败测试：no-match 场景下 `available_profiles[0] == default_profile`。
2. 在两个校验脚本增加排序 helper。
3. 更新 README、CHANGELOG、版本号和迭代记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 在 no-match 用例中新增断言：
     - lint validator：`available_profiles[0] == "prod"`
     - overrides validator：`available_profiles[0] == "prod"`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 新增 `_build_ordered_available_profiles(...)`
     - unknown profile 分支改为 default-first 排序
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 新增 `_build_ordered_available_profiles(...)`
     - unknown profile 分支改为 default-first 排序
3. 文档与版本：
   - `refactor/backend/README.md` 补充排序语义说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.150-m3-error-code-profile-default-first-order`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.150-m3-error-code-profile-default-first-order`

## 4. 未完成项（Not Done）

1. 当前排序策略未引入“最近使用 profile”维度。
2. 尚未把排序逻辑抽成跨脚本共享模块。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代165-M3-error-code-profile默认优先排序.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "handles_no_nearby_profile_suggestion or handles_no_nearby_lint_profile_suggestion" -q`
   - 结果：预期失败（排序为字母序，default 未置顶）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（`available_profiles` 默认优先排序生效）。

## 7. 风险与问题

1. 风险描述：在无 `default_profile` 时仍退回字母序，可能不符合部分团队偏好。
2. 影响范围：提示展示层。
3. 缓解措施：后续可支持配置化排序策略。

## 8. 关键决策

1. 决策内容：采用“default-first + alphabetical”混合排序。
2. 决策原因：兼顾快速引导与稳定可预测顺序。
3. 影响模块：unknown profile suggestion context 生成逻辑。

## 9. 下迭代计划

1. 为 `no_profiles_config` 场景补专门测试，验证 fallback 一致性。
2. 评估将排序 helper 抽至共享 util。
3. 增加 profile 排序策略配置入口（可选）。
