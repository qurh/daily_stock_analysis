# 迭代开发记录

迭代编号：`迭代154`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 metadata lint 配置增加 profile 支持（dev/staging/prod 可扩展）。
2. 让 lint 校验器与 overrides 校验器都支持按 profile 选择规则。
3. 在未知 profile 时输出结构化错误，避免静默回退。

## 2. 计划范围（Plan）

1. 先补失败测试：lint 校验器 profile 正/负路径、overrides 校验器 profile 正/负路径。
2. 扩展 lint schema 支持 profile 结构。
3. 改造两个校验脚本并补文档、版本、验证记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败约束：
     - lint 校验器支持 profiled lint 配置
     - lint 校验器未知 profile 返回结构化错误
     - overrides 校验器支持 `--lint-profile`
     - overrides 校验器未知 profile 返回结构化错误
2. TDD Green：
   - schema 扩展：
     - `refactor/backend/config/schemas/validator-error-code-metadata-lint.schema.json`
     - 新增 profile 模式字段：`default_profile`、`profiles`
   - lint 校验器改造：
     - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 新增参数：`--lint-profile`
     - 新增错误码：`error_code_metadata_lint_profile_not_found`
     - 在 profile 模式下解析目标 profile 并执行 action verb 语义校验
   - overrides 校验器改造：
     - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 新增参数：`--lint-profile`
     - 新增错误码：`error_code_metadata_overrides_lint_profile_not_found`
     - 复用 profile 规则解析结果用于 remediation 质量校验
3. 文档与版本：
   - `refactor/backend/README.md` 增加 profile 配置与参数说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.139-m3-error-code-lint-profile-support`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.139-m3-error-code-lint-profile-support`

## 4. 未完成项（Not Done）

1. profile 切换尚未接入环境变量默认值（当前以命令行参数为主）。
2. profile 选择操作尚未写入审计日志。

## 5. 代码与文档变更

1. schema：
   - `refactor/backend/config/schemas/validator-error-code-metadata-lint.schema.json`
2. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
3. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
4. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代154-M3-error-code-lint-profile支持.md`
5. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "profiled_lint_config or unknown_profile or supports_lint_profile or unknown_lint_profile" -q`
   - 结果：预期失败（脚本尚不支持 `--lint-profile`）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（lint profile 规则可被两个校验器一致消费，并具备明确错误反馈）。

## 7. 风险与问题

1. 风险描述：profile 名称拼写错误会直接阻断校验流程。
2. 影响范围：本地/CI lint 规则执行。
3. 缓解措施：保留 `available_profiles` 上下文，便于快速定位配置错误。

## 8. 关键决策

1. 决策内容：lint config 保持兼容 legacy 单 profile，同时新增 profile 模式。
2. 决策原因：减少历史配置迁移成本，支持渐进升级。
3. 影响模块：schema、lint 校验器、overrides 校验器、README 说明。

## 9. 下迭代计划

1. 支持 `LINT_PROFILE` 环境变量作为默认 profile 源。
2. 为 profile 相关失败输出自动修复建议（推荐 profile / 推荐动作动词）。
3. 增加 profile 级规则差异对比报告，便于策略审阅。
