# 迭代开发记录

迭代编号：`迭代231`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为通知重试 runbook 一致性校验脚本补齐结构化错误合同（`--json-errors`）。
2. 将该校验脚本错误码并入统一 `validator-error-codes` 治理链路。

## 2. 计划范围（Plan）

1. 按 TDD 为 `validate-notification-retry-runbook.py` 新增 JSON 错误测试并先跑 RED。
2. 实现 `VALIDATOR_ERROR_CODES + typed error + --json-errors`。
3. 扩展 catalog/schema/overrides 与覆盖测试，完成文档和版本同步。

## 3. 实际完成（Done）

1. 脚本能力升级：
   - `refactor/backend/scripts/validate-notification-retry-runbook.py`
   - 新增：
     - `VALIDATOR_NAME`
     - `VALIDATOR_ERROR_CODES`
     - `NotificationRetryRunbookValidationError`
     - `--json-errors`
   - 覆盖错误码：
     - `notification_retry_runbook_file_not_found`
     - `notification_retry_runbook_baseline_parse_failed`
     - `notification_retry_runbook_baseline_mismatch`
     - `notification_retry_runbook_unexpected_error`
2. TDD 测试补齐：
   - `refactor/backend/tests/unit/test_notification_retry_runbook_validator.py`
   - 新增 JSON 错误测试：
     - mismatch 分支
     - missing file 分支
3. 统一治理接入：
   - `refactor/backend/scripts/sync-validator-error-codes.py` 新增
     `notification_retry_runbook` 分组注册。
   - `refactor/backend/config/schemas/validator-error-codes.schema.json`
     将 `notification_retry_runbook` 纳入 required。
   - `refactor/backend/config/validator-error-codes.json`
     同步生成 `notification_retry_runbook_*` 条目。
   - `refactor/backend/config/validator-error-code-metadata-overrides.json`
     增加该分组全量 metadata overrides。
4. 文档与版本：
   - `refactor/backend/README.md` 增加 runbook validator `--json-errors` 与分组说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.15` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为
     `0.4.15-m4-notification-runbook-json-error-catalog-sync`。

## 4. 未完成项（Not Done）

1. 暂未将 `validate-notification-retry-runbook.py` 的 argparse 参数错误（unknown args）纳入统一 JSON 错误合同。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-notification-retry-runbook.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/config/schemas/validator-error-codes.schema.json`
   - `refactor/backend/config/validator-error-codes.json`
   - `refactor/backend/config/validator-error-code-metadata-overrides.json`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_notification_retry_runbook_validator.py`
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代231-M4-notification-runbook-json-error-catalog-sync.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_retry_runbook_validator.py -k "json_errors"`
   - 结果：失败（预期，脚本未支持 `--json-errors`）。
2. GREEN：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_retry_runbook_validator.py`
   - 结果：通过。
3. catalog 接入 RED->GREEN：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "notification_retry_runbook or validator_scripts_expose_error_code_registries or validator_error_code_catalog_exists_and_has_prefix_groups or validator_error_code_catalog_schema_exists_and_has_required_fields or validator_error_code_catalog_covers_all_script_error_codes"`
   - 结果：先失败（缺分组），接入后通过。
4. 同步与校验：
   - `cd refactor/backend && python3 scripts/sync-validator-error-codes.py --strict-descriptions`
   - `cd refactor/backend && python3 scripts/sync-validator-error-codes.py --check --strict-descriptions`
   - `cd refactor/backend && python3 scripts/validate-validator-error-code-catalog.py`
   - `cd refactor/backend && python3 scripts/validate-validator-error-code-metadata-overrides.py`
   - `cd refactor/backend && python3 scripts/validate-summary-contract-changelog.py`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：若后续新增 runbook baseline 文本模板未同步 regex，可能触发 `baseline_parse_failed`。
2. 缓解措施：保持 runbook 模板与规则模板联动修改，并保留 CI 一致性校验门禁。

## 8. 关键决策

1. 决策内容：runbook validator 错误码优先接入统一 catalog，而不是单独维护错误字典文档。
2. 决策原因：降低治理分叉，保证所有 validator 的错误码在同一质量门禁下演进。
3. 影响模块：CI 校验链路、运维机器人错误处理、错误码目录治理。

## 9. 下迭代计划

1. 评估将 argparse 参数错误场景也统一输出 JSON 错误（`--json-errors` 模式）。
2. 继续推进 M4 剩余治理脚本与 error-code catalog 一致性收口。
