# 迭代开发记录

迭代编号：`迭代170`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 unknown profile 场景提供结构化 UI action 提示，减少前端从 message 文本推断行为。
2. 将建议动作与 fallback 原因绑定，支持统一编排与渲染。
3. 保持已有字段（`fallback_reason`、`suggestion_level`、`suggested_*`）兼容。

## 2. 计划范围（Plan）

1. 先补失败测试：close/no-close/no-profiles 三类路径都断言 `suggested_actions`。
2. 在 lint/overrides 两个脚本实现统一的 action 组装 helper。
3. 更新 README、CHANGELOG、版本号，完成全量回归。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 6 条 unknown profile 用例新增断言：
     - close-match:
       - `copy_command`
       - `use_profile`
     - no-close-match:
       - `show_profiles`
     - no-profiles-config:
       - `migrate_profile_mode`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 新增 `_build_suggested_actions_for_profile_not_found(...)`
     - close/no-close/no-profiles 三类 context 注入 `suggested_actions`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步新增 `_build_suggested_actions_for_profile_not_found(...)`
     - 同步注入 `suggested_actions`
3. 文档与版本：
   - `refactor/backend/README.md` 补充 `suggested_actions` 契约
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.155-m3-error-code-suggested-actions`
   - `refactor/backend/src/app/main.py` 升级至 `0.3.155-m3-error-code-suggested-actions`

## 4. 未完成项（Not Done）

1. action 目前仍为通用 JSON 结构，尚未定义前端专属 schema 文件。
2. 尚未引入 action i18n 文案（目前只返回动作与参数，不带展示文案）。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代170-M3-unknown-profile结构化action提示.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "suggests_nearby_profile or handles_no_nearby_profile_suggestion or reports_non_profile_config_when_profile_requested or suggests_nearby_lint_profile or handles_no_nearby_lint_profile_suggestion"`
   - 结果：预期失败（缺少 `suggested_actions`）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 全量回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（unknown profile 场景可输出可编排的结构化动作建议）。

## 7. 风险与问题

1. 风险描述：若上游 UI 对 action 结构做严格 schema 校验，后续扩展 action 字段需同步升级。
2. 影响范围：消费 `suggested_actions` 的前端与自动化工作流。
3. 缓解措施：以 `action` 作为稳定键，参数字段向后兼容扩展。

## 8. 关键决策

1. 决策内容：采用 `suggested_actions: list[dict]` 作为 machine-readable 交互建议载体。
2. 决策原因：保持 JSON 简单、扩展成本低，便于前端按 action 类型渲染。
3. 影响模块：lint/overrides validator 的 unknown profile 错误上下文。

## 9. 下迭代计划

1. 抽出 shared helper（避免 lint/overrides 两脚本重复组装建议 payload）。
2. 为 `suggested_actions` 增加 schema 校验与契约测试，防止字段漂移。
3. 将该结构接入 API 层统一错误响应适配器，减少客户端兼容成本。
