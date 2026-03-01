# 迭代开发记录

迭代编号：`迭代168`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 提升 unknown profile 场景 `suggested_command` 的可执行安全性。
2. 避免 `--lint-config-file` 路径在命令模板中因 shell 字符处理不当而引发误执行风险。
3. 保持现有错误码、fallback 语义和建议字段结构不变。

## 2. 计划范围（Plan）

1. 先补失败测试：断言 `suggested_command` 使用 `shlex.quote` 风格的 lint config 参数。
2. 在 lint/overrides 两个脚本统一接入 shell-safe quoting helper。
3. 更新 README、CHANGELOG、后端版本并执行完整回归。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 两条近似 profile 建议测试新增断言：
     - `expected_lint_config_arg = --lint-config-file {shlex.quote(path)}`
     - `context.suggested_command` 必须包含该参数片段
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 新增 `_shell_quote(...)`
     - command template 改为 `--lint-config-file {_shell_quote(path)}`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步新增 `_shell_quote(...)`
     - command template 改为 `--lint-config-file {_shell_quote(path)}`
3. 文档与版本：
   - `refactor/backend/README.md` 更新 `suggested_command` 说明为 shell-safe quoting
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.153-m3-error-code-shell-safe-suggested-command`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.153-m3-error-code-shell-safe-suggested-command`

## 4. 未完成项（Not Done）

1. 目前只处理 lint config 路径的 shell-safe quoting，后续可评估对其它路径参数统一封装。
2. 尚未输出多平台 shell（如 PowerShell）差异化命令模板。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代168-M3-suggested-command-shell安全转义.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "suggests_nearby_profile or suggests_nearby_lint_profile"`
   - 结果：预期失败（command template 使用双引号拼接，未满足 shell-safe 断言）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 全量回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（`suggested_command` 对 lint config 路径使用 shell-safe quoting，回归通过）。

## 7. 风险与问题

1. 风险描述：`shlex.quote` 语义基于 POSIX shell，不同 shell 环境显示样式可能不同。
2. 影响范围：复制命令到非 POSIX shell（如 PowerShell）时可能需要人工调整。
3. 缓解措施：后续可按执行环境输出差异化命令模板，默认仍维持 POSIX 安全优先。

## 8. 关键决策

1. 决策内容：以 `shlex.quote` 作为命令模板路径参数的统一转义策略。
2. 决策原因：避免命令模板中的路径被 shell 展开或误解析，降低复制执行风险。
3. 影响模块：lint/overrides validator 的 unknown profile suggestion 输出。

## 9. 下迭代计划

1. 为 unknown profile context 增加 machine-readable 提示等级（`hint` / `warning` / `error`）。
2. 评估将 suggestion payload 构造成更细粒度的可渲染字段（命令片段数组而非整串命令）。
3. 补充前端错误展示契约文档，明确 message/context/suggestion 的优先渲染规则。
