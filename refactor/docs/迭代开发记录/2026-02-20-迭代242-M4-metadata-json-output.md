# 迭代开发记录

迭代编号：`迭代242`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 metadata lint 与 metadata overrides validator 增加成功态 JSON 输出开关。
2. 在保持现有 `--json-errors` 失败态契约不变的前提下，提供机器可读成功态结果。

## 2. 计划范围（Plan）

1. 按 TDD 新增两条成功态 JSON 输出测试（lint/overrides）。
2. 为两个 validator 增加 `--json-output` 与成功 payload 输出。
3. 更新 README、CHANGELOG、版本并完成回归验证。

## 3. 实际完成（Done）

1. 测试先行（RED -> GREEN）：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增：
     - `test_validator_error_code_metadata_lint_validator_script_json_output_on_success`
     - `test_validator_error_code_metadata_overrides_validator_script_json_output_on_success`
2. 实现落地：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 新增 `--json-output`。
     - 成功 payload：
       - `validator`, `status`, `lint_config_file`, `schema_file`, `selected_profile`
       - `min_remediation_length`, `action_verbs_count`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 新增 `--json-output`。
     - 成功 payload：
       - `validator`, `status`, `overrides_file`, `schema_file`, `catalog_file`
       - `lint_config_file`, `placeholder_markers_file`
       - `requested_overrides_profile`, `requested_lint_profile`
       - `total_override_groups`, `total_override_codes`
   - 两脚本均保持现有 `--json-errors` 失败态契约不变。
3. 文档与版本：
   - `refactor/backend/README.md` 增加 lint/overrides 的 `--json-output` 使用与 payload 字段说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.26` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为
     `0.4.26-m4-metadata-json-output`。

## 4. 未完成项（Not Done）

1. placeholder/summary 系列 validator 成功态 `--json-output` 尚未统一。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代242-M4-metadata-json-output.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "metadata_lint_validator_script_json_output_on_success or metadata_overrides_validator_script_json_output_on_success"`
   - 结果：失败（预期，旧脚本不识别 `--json-output`）。
2. GREEN：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "metadata_lint_validator_script_json_output_on_success or metadata_overrides_validator_script_json_output_on_success or metadata_lint_validator_script_json_errors_for_unknown_args or metadata_overrides_validator_script_json_errors_for_unknown_args"`
   - 结果：通过。
3. 模块回归：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "metadata_lint or metadata_overrides"`
   - 结果：通过。
4. 全量回归：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py tests/unit/test_alertmanager_route_consistency.py tests/unit/test_notification_retry_runbook_validator.py`
   - `cd refactor/backend && python3 scripts/sync-validator-error-codes.py --check --strict-descriptions`
   - `cd refactor/backend && python3 scripts/validate-validator-error-code-catalog.py`
   - `cd refactor/backend && python3 scripts/validate-validator-error-code-metadata-overrides.py`
   - `cd refactor/backend && python3 scripts/validate-summary-contract-changelog.py`
   - 结果：全部通过。

## 7. 风险与问题

1. 风险描述：成功态 JSON 字段后续变更可能影响自动化消费端兼容性。
2. 缓解措施：保留成功态输出测试，新增字段应保持向后兼容（仅增不减）。

## 8. 关键决策

1. 决策内容：成功态 JSON 输出使用独立开关 `--json-output`，默认文本输出保持不变。
2. 决策原因：兼容人工 CLI 使用习惯，同时满足自动化链路机器可读需求。
3. 影响模块：metadata lint / overrides validator CLI、CI 自动化解析、文档契约。

## 9. 下迭代计划

1. 为 `validate-validator-placeholder-markers.py` 增加 `--json-output`。
2. 梳理统一 success payload 字段标准并补充总览文档。
