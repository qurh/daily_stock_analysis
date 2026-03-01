# 迭代开发记录

迭代编号：`迭代248`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将并存 JSON 模式契约从“CLI 参数失败”扩展到“业务失败”场景。
2. 对 9 个 validator 统一验证失败输出路由（stdout/stderr）行为。
3. 同步文档与版本记录。

## 2. 计划范围（Plan）

1. 在通用契约测试中新增业务失败矩阵用例。
2. 运行测试并检查是否需修改脚本实现。
3. 更新 README、CHANGELOG、版本号并记录迭代。

## 3. 实际完成（Done）

1. 测试增强：
   - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
   - 新增：
     - `test_validator_scripts_both_json_flags_business_failure_emit_structured_error`
2. 覆盖范围：
   - 9 个 validator 的并存模式业务失败场景（通过合法参数注入缺失文件/目录路径触发）
3. 契约结果：
   - 现有实现已满足契约，无需脚本改动：
     - 业务失败时：`exit_code != 0`
     - `stdout` 为空
     - `stderr` 为结构化 JSON 错误
4. 文档与版本：
   - `refactor/backend/README.md` 明确并存模式覆盖 CLI 失败与业务失败。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.32` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为 `0.4.32-m4-validator-json-mode-business-failure-contract`。

## 4. 未完成项（Not Done）

1. 暂未覆盖“同一脚本多个业务失败类型”的细分断言（当前每脚本 1 条代表性失败样例）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代248-M4-validator-json-mode-business-failure-contract.md`

## 6. 验证记录

1. 契约测试：
   - `pytest -q refactor/backend/tests/unit/test_validator_success_output_contract.py`
   - 结果：通过（5 tests）。
2. 语法检查：
   - `python3 -m py_compile refactor/backend/tests/unit/test_validator_success_output_contract.py refactor/backend/src/app/main.py`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：当前业务失败样例为代表性输入，未穷举每类失败分支。
2. 影响范围：自动化调用方对某些稀有失败分支的兼容预期。
3. 缓解措施：后续按脚本逐步补齐更多业务失败类型测试。

## 8. 关键决策

1. 决策内容：优先做“每脚本一条代表性业务失败样例”的统一契约覆盖。
2. 决策原因：在成本可控前提下快速提升并存模式失败路由稳定性。
3. 影响模块：validator CLI 契约测试、文档说明、版本迭代记录。

## 9. 下迭代计划

1. 为重点脚本（summary schema/contract、metadata overrides/lint）补充多业务失败类型矩阵。
2. 评估是否增加统一错误输出 schema（validator/code/message/context）的独立校验脚本。
