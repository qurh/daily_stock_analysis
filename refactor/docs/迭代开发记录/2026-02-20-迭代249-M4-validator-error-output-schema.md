# 迭代开发记录

迭代编号：`迭代249`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 validator 的结构化错误输出建立统一 schema 契约。
2. 在 9 个 validator 上验证 `--json-errors` 输出与 schema 一致。
3. 同步文档与版本记录。

## 2. 计划范围（Plan）

1. 先补失败测试（schema 存在性 + CLI 失败 + 业务失败 payload 校验）。
2. 落地 `validator-error-output.schema.json`。
3. 回归测试并更新 README、CHANGELOG、版本号。

## 3. 实际完成（Done）

1. 新增错误输出 schema：
   - `refactor/backend/config/schemas/validator-error-output.schema.json`
   - 必填字段：
     - `validator`
     - `code`
     - `message`
     - `context`
2. 测试增强：
   - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
   - 新增：
     - `test_validator_error_output_schema_exists_and_is_valid`
     - `test_validator_scripts_json_errors_conform_base_contract_cli_failures`
     - `test_validator_scripts_json_errors_conform_base_contract_business_failures`
3. 覆盖范围：
   - 9 个 validator 在 `--json-errors` 下的：
     - CLI 参数失败
     - 代表性业务失败
4. 文档与版本：
   - `refactor/backend/README.md` 新增 error-output base contract 说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.33` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为 `0.4.33-m4-validator-error-output-schema`。

## 4. 未完成项（Not Done）

1. 未对每个 validator 的所有业务失败分支做穷举校验（当前每脚本 1 条代表性业务失败样例）。

## 5. 代码与文档变更

1. 配置路径：
   - `refactor/backend/config/schemas/validator-error-output.schema.json`
2. 测试路径：
   - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代249-M4-validator-error-output-schema.md`
4. 版本路径：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. 契约测试：
   - `pytest -q refactor/backend/tests/unit/test_validator_success_output_contract.py`
2. 语法检查：
   - `python3 -m py_compile refactor/backend/tests/unit/test_validator_success_output_contract.py refactor/backend/src/app/main.py`

## 7. 风险与问题

1. 风险描述：schema 当前仅校验基础字段，不限制特定错误码的 `context` 结构。
2. 影响范围：调用方可依赖基础契约，但不能依赖所有错误码上下文字段恒定。
3. 缓解措施：后续可按高价值错误码增量补充细粒度 `context` 子 schema。

## 8. 关键决策

1. 决策内容：先落地“基础错误输出契约”并覆盖全 validator，再迭代细化到错误码级 context。
2. 决策原因：在成本可控下，先保证跨脚本结构一致性与自动化可消费性。
3. 影响模块：validator CLI 契约测试、文档说明、版本迭代记录。

## 9. 下迭代计划

1. 为重点脚本补“多业务失败类型矩阵”。
2. 评估将常见错误码（文件缺失、JSON 解析失败、schema 失败）升级为可选细粒度 schema 约束。
