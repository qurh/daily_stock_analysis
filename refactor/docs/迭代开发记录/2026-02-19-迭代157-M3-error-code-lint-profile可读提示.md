# 迭代开发记录

迭代编号：`迭代157`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 在非 JSON 输出场景下，未知 profile 错误也给出可读推荐提示。
2. 保持 JSON 错误上下文字段与现有实现兼容。
3. 降低 CLI 用户在 profile 拼写错误时的排障成本。

## 2. 计划范围（Plan）

1. 先补失败测试：两个校验器的 plain stderr 必须包含 `Did you mean`。
2. 在未知 profile 分支拼接推荐文案，不改错误码。
3. 更新 README、CHANGELOG、版本与迭代记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败约束：
     - lint 校验器 plain stderr 包含推荐 profile 文案
     - overrides 校验器 plain stderr 包含推荐 profile 文案
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 未知 profile 时如果存在推荐项，message 追加：
       - `Did you mean: <profile>?`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步追加可读推荐文案
3. 文档与版本：
   - `refactor/backend/README.md` 补充 plain stderr 推荐行为说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.142-m3-error-code-lint-profile-message-hint`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.142-m3-error-code-lint-profile-message-hint`

## 4. 未完成项（Not Done）

1. 推荐文案目前为英文固定模板，尚未支持本地化。
2. 尚未支持在 CLI 输出中直接给出可复制的修复命令。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代157-M3-error-code-lint-profile可读提示.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "plain_errors_include_profile_suggestion or plain_errors_include_lint_profile_suggestion" -q`
   - 结果：预期失败（stderr 无推荐文案）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（plain stderr 与 JSON 错误在推荐信息上保持一致）。

## 7. 风险与问题

1. 风险描述：模糊匹配在极端命名场景可能给出不够准确的推荐。
2. 影响范围：错误提示体验，不影响校验结果正确性。
3. 缓解措施：同时输出 `available_profiles` 便于人工确认。

## 8. 关键决策

1. 决策内容：不新增参数，直接增强现有错误 message。
2. 决策原因：最小变更，兼容现有调用脚本和 CI 解析逻辑。
3. 影响模块：lint/overrides 校验器 stderr 消费方。

## 9. 下迭代计划

1. 在未知 profile 场景输出一条可复制命令示例。
2. 抽取 profile 推荐逻辑为共用 helper，减少脚本重复。
3. 评估把相同提示能力扩展到其他 validator。
