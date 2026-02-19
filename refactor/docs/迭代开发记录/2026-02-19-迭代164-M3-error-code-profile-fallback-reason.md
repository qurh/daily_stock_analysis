# 迭代开发记录

迭代编号：`迭代164`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 unknown profile 提示补充结构化原因字段，便于上层决策。
2. 区分“有近似建议”和“无近似建议”两类失败路径。
3. 保持现有提示文案与上下文字段兼容。

## 2. 计划范围（Plan）

1. 先补失败测试：`fallback_reason` 在 close/no-close 场景必须可用。
2. 改造 profile suggestion helper，返回并写入 `fallback_reason`。
3. 更新 README、CHANGELOG、版本号、迭代记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增断言：
     - close-match 场景：`fallback_reason == "close_match"`
     - no-close-match 场景：`fallback_reason == "no_close_match"`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - `_build_profile_suggestion_payload` 返回 `fallback_reason`
     - unknown profile 上下文新增 `fallback_reason`
     - no-profiles-config 场景返回 `fallback_reason=no_profiles_config`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步返回并写入 `fallback_reason`
3. 文档与版本：
   - `refactor/backend/README.md` 新增 `fallback_reason` 枚举说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.149-m3-error-code-profile-fallback-reason`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.149-m3-error-code-profile-fallback-reason`

## 4. 未完成项（Not Done）

1. `fallback_reason=no_profiles_available` 分支当前未新增专项测试。
2. 尚未将 fallback reason 写入可观测性指标。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代164-M3-error-code-profile-fallback-reason.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "suggests_nearby_profile or handles_no_nearby_profile_suggestion or suggests_nearby_lint_profile or handles_no_nearby_lint_profile_suggestion" -q`
   - 结果：预期失败（缺 `fallback_reason`）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（unknown profile 场景具备结构化失败原因标签）。

## 7. 风险与问题

1. 风险描述：新增 reason 枚举后，消费方若写死旧字段处理逻辑，可能忽略新信息。
2. 影响范围：上层提示编排与自动修复分支。
3. 缓解措施：README 明确枚举语义，保持原字段不变。

## 8. 关键决策

1. 决策内容：使用短枚举字符串表达 fallback reason。
2. 决策原因：便于日志检索、规则匹配与前端展示映射。
3. 影响模块：lint/overrides validator 错误上下文消费者。

## 9. 下迭代计划

1. 为 `no_profiles_available` 分支增加专项测试。
2. 将 `fallback_reason` 接入策略优化审计维度。
3. 评估将 reason 枚举集中维护在共享常量中。
