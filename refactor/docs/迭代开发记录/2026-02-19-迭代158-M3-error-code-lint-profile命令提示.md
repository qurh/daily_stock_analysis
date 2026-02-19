# 迭代开发记录

迭代编号：`迭代158`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 在未知 profile 的 plain stderr 中提供可复制修复参数。
2. 保持现有错误码与 JSON 错误结构兼容。
3. 让 CLI 用户可直接按提示修复命令参数。

## 2. 计划范围（Plan）

1. 先补失败测试：两个校验器 plain stderr 必须包含 `--lint-profile <suggested>`。
2. 实现 message 增强：推荐 profile + 快速修复参数。
3. 更新 README、CHANGELOG、版本号与迭代记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 在既有 plain stderr 推荐测试中新增断言：
     - 包含 `--lint-profile prod`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 未知 profile 且有推荐时，message 追加：
       - `Try: --lint-profile <suggested_profile>`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步追加快速修复参数提示
3. 文档与版本：
   - `refactor/backend/README.md` 补充 quick-fix args 说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.143-m3-error-code-lint-profile-cli-hint`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.143-m3-error-code-lint-profile-cli-hint`

## 4. 未完成项（Not Done）

1. 目前仅输出参数片段，未输出完整命令示例（含脚本名与配置路径）。
2. 尚未把 quick-fix 参数写入 JSON context 的独立字段。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代158-M3-error-code-lint-profile命令提示.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "plain_errors_include_profile_suggestion or plain_errors_include_lint_profile_suggestion" -q`
   - 结果：预期失败（缺 `--lint-profile` 提示）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（stderr 推荐可直接转化为可执行修复参数）。

## 7. 风险与问题

1. 风险描述：只给参数片段可能仍需用户自行拼接完整命令。
2. 影响范围：CLI 使用体验。
3. 缓解措施：后续迭代输出完整命令模板。

## 8. 关键决策

1. 决策内容：先输出参数片段，不强耦合具体脚本绝对路径。
2. 决策原因：保持提示通用性，避免路径环境差异导致误导。
3. 影响模块：lint/overrides 校验器 stderr 文案与 README。

## 9. 下迭代计划

1. 在 JSON context 增加 `suggested_cli_args` 字段，便于上层自动处理。
2. 输出完整命令示例模板（含脚本名与 `--lint-config-file`）。
3. 评估统一提取推荐提示构建函数，减少重复逻辑。
