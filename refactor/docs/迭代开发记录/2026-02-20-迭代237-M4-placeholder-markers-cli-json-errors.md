# 迭代开发记录

迭代编号：`迭代237`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将 placeholder markers validator 的 CLI 参数错误纳入 `--json-errors` 合同。
2. 将新增 CLI 错误码同步到统一 error-code catalog 与 metadata 治理。

## 2. 计划范围（Plan）

1. 按 TDD 覆盖 unknown args / missing arg value 的 JSON 错误测试。
2. 在 validator 中统一 argparse/unknown args 为 `placeholder_markers_cli_args_invalid`。
3. 同步 catalog、README、版本与变更记录并回归验证。

## 3. 实际完成（Done）

1. 测试覆盖与契约校验：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 覆盖：
     - `test_validator_placeholder_markers_validator_script_json_errors_for_unknown_args`
     - `test_validator_placeholder_markers_validator_script_json_errors_for_missing_arg_value`
2. 解析契约落地：
   - `refactor/backend/scripts/validate-validator-placeholder-markers.py`
   - CLI 参数错误统一产出：
     - `code=placeholder_markers_cli_args_invalid`
     - `context` 包含 `failure_mode` 与 `argv/unknown_args`。
3. 治理链路同步：
   - `refactor/backend/config/validator-error-code-metadata-overrides.json`
     新增 `placeholder_markers` 分组并覆盖 `placeholder_markers_cli_args_invalid`。
   - `refactor/backend/config/validator-error-codes.json`
     已同步纳入该错误码。
4. 文档与版本：
   - `refactor/backend/README.md` 增加 placeholder markers validator JSON 错误命名空间说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.21` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为
     `0.4.21-m4-placeholder-markers-cli-json-errors`。

## 4. 未完成项（Not Done）

1. 尚未将 validator 成功态也统一为结构化 JSON 输出（当前仅失败态结构化）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-validator-placeholder-markers.py`
   - `refactor/backend/config/validator-error-code-metadata-overrides.json`
   - `refactor/backend/config/validator-error-codes.json`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代237-M4-placeholder-markers-cli-json-errors.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "validator_placeholder_markers_validator_script_json_errors_for_unknown_args or validator_placeholder_markers_validator_script_json_errors_for_missing_arg_value or metadata_overrides_config_exists"`
   - 结果：失败（预期，`metadata-overrides` 缺失 `placeholder_markers` 分组）。
2. GREEN：
   - `cd refactor/backend && python3 scripts/sync-validator-error-codes.py --strict-descriptions`
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "placeholder_markers or validator_error_code_catalog_covers_all_script_error_codes or validator_error_code_catalog_has_specific_metadata_for_key_codes or metadata_overrides_config_exists"`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：后续新增 CLI 参数若未保持 `failure_mode/argv/unknown_args` 字段，可能导致 JSON 消费端兼容性回归。
2. 缓解措施：保留并扩展 CLI JSON 错误断言测试，防止契约漂移。

## 8. 关键决策

1. 决策内容：placeholder markers validator CLI 错误进入统一 typed error-code 合同。
2. 决策原因：保障 validator 错误可被 catalog/lint/自动化链路稳定消费。
3. 影响模块：placeholder markers validator CLI、错误码治理、CI 校验脚本。

## 9. 下迭代计划

1. 继续补齐剩余 validator 的 CLI JSON 错误合同一致性收尾与治理回归。
2. 评估是否引入统一成功态 JSON 输出开关，减少 stderr/stdout 解析分歧。
