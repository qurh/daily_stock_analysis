# 迭代开发记录

迭代编号：`迭代169`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 unknown profile 错误上下文新增 machine-readable 建议等级字段。
2. 让调用方无需解析 message 文本即可判断建议强度。
3. 保持已有 `fallback_reason` 与建议字段兼容。

## 2. 计划范围（Plan）

1. 先补失败测试：close/no-close/no-profiles 三类 fallback 都要断言 `suggestion_level`。
2. 在 lint/overrides 两个脚本中写入统一等级映射。
3. 更新 README、CHANGELOG、版本号，并完成全量回归。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 在 6 条 unknown profile 场景测试新增断言：
     - close-match -> `suggestion_level == "hint"`
     - no-close-match -> `suggestion_level == "warning"`
     - no-profiles-config -> `suggestion_level == "error"`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - `_build_profile_suggestion_payload(...)` 增加 `suggestion_level` 返回
     - no-profile-config 分支 context 增加 `suggestion_level: "error"`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步增加 `suggestion_level` 输出
3. 文档与版本：
   - `refactor/backend/README.md` 增补 `suggestion_level` 语义（lint/overrides 两处）
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.154-m3-error-code-suggestion-level`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.154-m3-error-code-suggestion-level`

## 4. 未完成项（Not Done）

1. 目前只提供等级字符串，尚未输出结构化 UI 建议模板（例如按钮文案与动作）。
2. 尚未将该等级字段接入前端展示逻辑。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代169-M3-unknown-profile建议等级.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "suggests_nearby_profile or handles_no_nearby_profile_suggestion or reports_non_profile_config_when_profile_requested or suggests_nearby_lint_profile or handles_no_nearby_lint_profile_suggestion"`
   - 结果：预期失败（缺少 `suggestion_level` 字段）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 全量回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（unknown profile 场景可提供 machine-readable 建议等级）。

## 7. 风险与问题

1. 风险描述：外部调用方若将 `suggestion_level` 误用为告警级别，可能与业务严重性混淆。
2. 影响范围：消费错误 context 的 UI 和自动化流程。
3. 缓解措施：文档明确该字段表示“建议强度”，非系统故障严重度。

## 8. 关键决策

1. 决策内容：使用 `hint/warning/error` 三档建议等级并与 `fallback_reason` 一一映射。
2. 决策原因：简单稳定、可扩展，前端可直接映射颜色和交互动作。
3. 影响模块：lint/overrides validator 的 unknown profile JSON context。

## 9. 下迭代计划

1. 为 unknown profile 增加结构化 UI action 提示（如 `copy_command` / `show_profiles` / `migrate_profile_mode`）。
2. 评估将 suggestion payload 抽成统一 helper，减少 lint/overrides 双脚本重复字段构造。
3. 为 message/context 在 API 层补充契约测试，防止字段漂移。
