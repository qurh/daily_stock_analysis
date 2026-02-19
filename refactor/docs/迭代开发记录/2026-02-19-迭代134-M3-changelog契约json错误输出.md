# 迭代开发记录

迭代编号：`迭代134`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 changelog 契约校验脚本增加结构化错误输出。
2. 统一两类契约校验脚本的机器可解析错误能力。

## 2. 计划范围（Plan）

1. 先补失败测试定义 `--json-errors` 行为。
2. 在 `validate-summary-contract-changelog.py` 增加结构化错误输出和稳定错误码。
3. 同步 README / CHANGELOG / 版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败场景：
     - 缺失 schema note 时 `--json-errors` 输出 JSON 错误
     - changelog/app 版本不一致时 `--json-errors` 输出 JSON 错误
2. TDD Green：
   - `refactor/backend/scripts/validate-summary-contract-changelog.py`
   - 新增参数：`--json-errors`
   - 新增错误类型：`SummaryContractValidationError`
   - 新增稳定错误码（示例）：
     - `missing_summary_schema_version_note`
     - `changelog_app_version_mismatch`
     - `required_file_not_found`
   - 在 `--json-errors` 下输出 `validator/code/message/context`
3. 文档与版本：
   - `refactor/backend/README.md` 增加 `--json-errors` 用法说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.119-m3-contract-validator-json-errors`。
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.119-m3-contract-validator-json-errors`。

## 4. 未完成项（Not Done）

1. 暂未统一所有 validator 的错误码清单文档。
2. 暂未支持多错误聚合输出。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-summary-contract-changelog.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代134-M3-changelog契约json错误输出.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "summary_contract_changelog_validator_script_json_errors" -q`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - json-errors 相关新增用例通过
   - 后端全量 CI 通过
3. 是否达到验收标准：
   - 达到（契约校验脚本支持结构化错误输出）

## 7. 风险与问题

1. 风险描述：错误码后续变更会影响依赖脚本。
2. 影响范围：CI 后处理和外部集成。
3. 缓解措施：后续补充错误码稳定性文档并纳入测试约束。

## 8. 关键决策

1. 决策内容：默认仍使用人类可读错误输出，`--json-errors` 显式启用结构化输出。
2. 决策原因：兼容现有开发习惯并逐步推进自动化集成。
3. 影响模块：契约校验脚本可维护性与可集成性。

## 9. 下迭代计划

1. 增加错误码文档并放入 README/Runbook。
2. 为两类 validator 增加统一错误码前缀约定。
3. 评估将结构化错误自动上传为 CI artifact。
