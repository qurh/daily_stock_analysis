# 迭代开发记录

迭代编号：`迭代252`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为高频业务失败错误码建立 `context` 子 schema 约束。
2. 将子 schema 纳入自动化契约测试。
3. 同步文档与版本。

## 2. 计划范围（Plan）

1. 先补失败测试（schema 存在性 + 高频错误样本校验）。
2. 新增 `validator-error-context-high-frequency.schema.json`。
3. 回归测试并更新 README、CHANGELOG、版本号与迭代记录。

## 3. 实际完成（Done）

1. 新增 schema：
   - `refactor/backend/config/schemas/validator-error-context-high-frequency.schema.json`
   - 约束类型：
     - `pathContext`
     - `pathRoleContext`
     - `validationPathContext`
     - `groupContext`
     - `sourceKeyContext`
2. 测试增强：
   - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
   - 新增：
     - `test_validator_error_context_high_frequency_schema_exists_and_is_valid`
     - `test_validator_json_errors_high_frequency_context_contract`
   - 覆盖 18 条高频业务失败样本并做 schema 校验。
3. 文档与版本：
   - `refactor/backend/README.md` 补充 context 子 schema 说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.36` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为 `0.4.36-m4-validator-error-context-high-frequency-schema`。

## 4. 未完成项（Not Done）

1. 仅覆盖“高频业务失败”错误码，尚未覆盖全部错误码。
2. 暂未将该子 schema 接入独立 CLI 校验脚本（当前由单测驱动）。

## 5. 代码与文档变更

1. 配置路径：
   - `refactor/backend/config/schemas/validator-error-context-high-frequency.schema.json`
2. 测试路径：
   - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代252-M4-validator-error-context-high-frequency-schema.md`
4. 版本路径：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. 契约测试：
   - `pytest -q refactor/backend/tests/unit/test_validator_success_output_contract.py`
   - 结果：通过（12 tests）
2. 语法检查：
   - `python3 -m py_compile refactor/backend/tests/unit/test_validator_success_output_contract.py refactor/backend/src/app/main.py`
   - 结果：通过

## 7. 风险与问题

1. 风险描述：子 schema 当前聚焦高频码，低频码仍仅受基础 schema 约束。
2. 影响范围：低频异常分支的 `context` 稳定性约束仍偏弱。
3. 缓解措施：后续按优先级逐步扩展子 schema 覆盖范围。

## 8. 关键决策

1. 决策内容：优先做“高频错误码”细粒度 `context` 契约，而不是一次性覆盖所有错误码。
2. 决策原因：降低改动风险并快速提升自动化消费稳定性。
3. 影响模块：validator 错误输出契约测试、文档说明、版本迭代记录。

## 9. 下迭代计划

1. 扩展更多错误码的 `context` 子 schema（优先 CLI 失败与 schema 校验失败相关错误）。
2. 评估是否将子 schema 校验抽成可复用脚本并接入 CI。
