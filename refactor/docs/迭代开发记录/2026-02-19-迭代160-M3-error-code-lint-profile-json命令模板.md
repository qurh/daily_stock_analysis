# 迭代开发记录

迭代编号：`迭代160`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 在未知 profile 的 JSON 错误中提供完整命令模板。
2. 让上层可以直接展示或执行建议命令，减少拼接逻辑。
3. 与既有 `suggested_profiles/suggested_cli_args` 保持一致。

## 2. 计划范围（Plan）

1. 先补失败测试：两个校验器 `context` 必须包含 `suggested_command`。
2. 实现 `suggested_command` 字段生成逻辑。
3. 更新 README、CHANGELOG、版本号与迭代记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 在建议 profile 测试中新增断言：
     - `context.suggested_command` 包含对应校验脚本名
     - `context.suggested_command` 包含 `--lint-profile prod`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 未知 profile 场景新增：
       - `suggested_command = "python3 scripts/validate-validator-error-code-metadata-lint.py --lint-profile <profile>"`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 未知 profile 场景新增：
       - `suggested_command = "python3 scripts/validate-validator-error-code-metadata-overrides.py --lint-profile <profile>"`
3. 文档与版本：
   - `refactor/backend/README.md` 增加 `suggested_command` 字段说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.145-m3-error-code-lint-profile-command-context`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.145-m3-error-code-lint-profile-command-context`

## 4. 未完成项（Not Done）

1. `suggested_command` 当前为模板命令，尚未携带实际 `--lint-config-file` 路径。
2. 尚未区分不同 Python 解释器（如 `python`/`python3`/venv）。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代160-M3-error-code-lint-profile-json命令模板.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "suggests_nearby_profile or suggests_nearby_lint_profile" -q`
   - 结果：预期失败（缺 `suggested_command`）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（JSON 上下文可直接提供完整建议命令模板）。

## 7. 风险与问题

1. 风险描述：模板命令未包含用户自定义 lint 配置路径时，可能需要人工补参数。
2. 影响范围：自动修复体验。
3. 缓解措施：保留 `suggested_cli_args` 作为最小稳定建议，后续补路径感知。

## 8. 关键决策

1. 决策内容：先提供稳定模板命令，不耦合调用时的上下文路径。
2. 决策原因：降低实现复杂度，避免脚本内部对外部调用上下文强依赖。
3. 影响模块：profile 错误 JSON 消费方。

## 9. 下迭代计划

1. 基于参数上下文生成带 `--lint-config-file` 的完整修复命令。
2. 抽取 profile 建议构建逻辑为共用 helper。
3. 增加无推荐候选时 `suggested_command = null` 的测试覆盖。
