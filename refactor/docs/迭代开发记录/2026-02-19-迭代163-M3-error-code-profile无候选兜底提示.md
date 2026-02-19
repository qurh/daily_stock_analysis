# 迭代开发记录

迭代编号：`迭代163`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 覆盖“无近似候选 profile”场景的错误提示。
2. 在无建议可用时，给出 `Available profiles` 兜底信息。
3. 保持 `suggested_profiles/suggested_cli_args/suggested_command` 的空值语义一致。

## 2. 计划范围（Plan）

1. 先补失败测试：无候选时 message 包含 `Available profiles`。
2. 实现 helper 的无候选分支提示逻辑。
3. 更新 README、CHANGELOG、版本与迭代记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增两条无候选用例：
     - lint validator no-match case
     - overrides validator no-match case
   - 约束：
     - `suggested_profiles == []`
     - `suggested_cli_args is None`
     - `suggested_command is None`
     - `message` 包含 `available profiles`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - `_build_profile_suggestion_payload` 无候选分支追加：
       - `Available profiles: ...`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步无候选分支追加：
       - `Available profiles: ...`
3. 文档与版本：
   - `refactor/backend/README.md` 补充无候选兜底提示说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.148-m3-error-code-profile-no-match-fallback`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.148-m3-error-code-profile-no-match-fallback`

## 4. 未完成项（Not Done）

1. 无候选提示目前仅显示 profile 列表，未输出修复优先级建议。
2. 尚未将 no-match 场景打点到审计指标。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代163-M3-error-code-profile无候选兜底提示.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "handles_no_nearby_profile_suggestion or handles_no_nearby_lint_profile_suggestion" -q`
   - 结果：预期失败（message 未包含 `available profiles`）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（无候选场景错误信息可指导用户人工选择 profile）。

## 7. 风险与问题

1. 风险描述：可用 profile 列表较长时 message 可能偏长。
2. 影响范围：CLI 可读性。
3. 缓解措施：后续可引入长度截断或 top-N 展示策略。

## 8. 关键决策

1. 决策内容：无候选场景下优先保证信息完整，直接展示全部可用 profile。
2. 决策原因：不遗漏任何可选项，便于快速人工判断。
3. 影响模块：unknown profile 提示链路。

## 9. 下迭代计划

1. 为 no-match 场景增加结构化字段（如 `fallback_reason: no_close_match`）。
2. 评估 `available_profiles` 的排序策略（按常用优先）。
3. 将 profile 建议逻辑抽取到共享 util 模块。
