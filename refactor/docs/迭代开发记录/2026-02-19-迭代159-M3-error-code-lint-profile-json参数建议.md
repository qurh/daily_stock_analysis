# 迭代开发记录

迭代编号：`迭代159`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为未知 profile 的 JSON 错误增加可机读的修复参数建议。
2. 让上层服务可直接消费建议参数，无需解析自然语言 message。
3. 保持 plain stderr 与 JSON 提示一致。

## 2. 计划范围（Plan）

1. 先补失败测试：两个校验器 JSON `context` 必须包含 `suggested_cli_args`。
2. 在未知 profile 分支填充 `suggested_cli_args` 字段。
3. 更新 README、CHANGELOG、版本号和迭代记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 在建议 profile 测试中新增断言：
     - `context.suggested_cli_args == "--lint-profile prod"`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 未知 profile 时新增 `context.suggested_cli_args`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步新增 `context.suggested_cli_args`
3. 文档与版本：
   - `refactor/backend/README.md` 补充 `suggested_cli_args` 说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.144-m3-error-code-lint-profile-cli-args-context`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.144-m3-error-code-lint-profile-cli-args-context`

## 4. 未完成项（Not Done）

1. 当前只提供参数片段，未提供完整命令模板字段。
2. `suggested_cli_args` 尚未覆盖“无推荐候选”场景的明确值约束。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代159-M3-error-code-lint-profile-json参数建议.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "suggests_nearby_profile or suggests_nearby_lint_profile" -q`
   - 结果：预期失败（缺 `suggested_cli_args`）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（JSON context 已能直接提供修复参数建议）。

## 7. 风险与问题

1. 风险描述：上层若强依赖 `suggested_cli_args` 非空，在无近似候选时需要兜底。
2. 影响范围：自动修复提示链路。
3. 缓解措施：保留 `suggested_profiles` 与 `available_profiles` 作为兜底输入。

## 8. 关键决策

1. 决策内容：`suggested_cli_args` 作为 JSON context 字段落地，不增加新错误码。
2. 决策原因：兼容既有错误处理逻辑，低成本增强机器可读性。
3. 影响模块：校验器错误输出消费方（API/Agent/前端）。

## 9. 下迭代计划

1. 增加 `suggested_command` 字段，提供完整命令模板。
2. 抽取 profile 提示构建逻辑为共用 helper，减少重复代码。
3. 增加“无匹配候选”场景专门测试。
