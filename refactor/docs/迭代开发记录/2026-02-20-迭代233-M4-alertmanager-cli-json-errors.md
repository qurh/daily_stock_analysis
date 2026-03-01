# 迭代开发记录

迭代编号：`迭代233`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将 alertmanager route consistency validator 的 CLI 参数错误纳入 `--json-errors` 合同。
2. 将新增 CLI 错误码同步到统一 error-code catalog 与 metadata 治理。

## 2. 计划范围（Plan）

1. 按 TDD 新增两条失败测试：unknown args / missing arg value。
2. 实现自定义 parser 错误处理与 `alertmanager_route_consistency_cli_args_invalid`。
3. 同步 catalog、文档、版本并完成回归验证。

## 3. 实际完成（Done）

1. 测试先行（RED -> GREEN）：
   - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
   - 新增：
     - `test_alertmanager_route_consistency_validator_script_json_errors_for_unknown_args`
     - `test_alertmanager_route_consistency_validator_script_json_errors_for_missing_arg_value`
2. 解析层实现：
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - 新增：
     - `VALIDATOR_ERROR_CODES["CLI_ARGS_INVALID"]`
     - `_AlertmanagerArgumentParser.error()`，将 argparse 错误转 typed validation error
     - `_build_parser()` + `_parse_args()`，统一 unknown args / argparse error 路径
   - 在 `--json-errors` 模式下，CLI 参数错误统一输出：
     - `code=alertmanager_route_consistency_cli_args_invalid`
     - `context` 包含 `failure_mode` 与 `argv/unknown_args`。
3. 治理链路同步：
   - `refactor/backend/config/validator-error-code-metadata-overrides.json`
     新增 `alertmanager_route_consistency_cli_args_invalid` 元数据。
   - `refactor/backend/config/validator-error-codes.json`
     已同步纳入该错误码。
4. 文档与版本：
   - `refactor/backend/README.md` 增加 alertmanager validator JSON 错误命名空间说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.17` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为
     `0.4.17-m4-alertmanager-cli-json-errors`。

## 4. 未完成项（Not Done）

1. 尚未为 alertmanager validator 提供成功态 JSON 输出（当前仅失败态结构化）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - `refactor/backend/config/validator-error-code-metadata-overrides.json`
   - `refactor/backend/config/validator-error-codes.json`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代233-M4-alertmanager-cli-json-errors.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py -k "unknown_args or missing_arg_value"`
   - 结果：失败（预期，脚本先前输出 argparse 文本错误）。
2. GREEN：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py -k "unknown_args or missing_arg_value"`
   - 结果：通过。
3. catalog 联动 RED->GREEN：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "alertmanager_route_consistency or validator_error_code_catalog_covers_all_script_error_codes"`
   - 结果：先失败（缺 `cli_args_invalid`），同步后通过。
4. 同步与回归：
   - `cd refactor/backend && python3 scripts/sync-validator-error-codes.py --strict-descriptions`
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py tests/unit/test_ci_prometheus_rules_check.py -k "alertmanager_route_consistency or validator_error_code_catalog_covers_all_script_error_codes or validator_scripts_expose_error_code_registries"`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：后续参数扩展若未保持 `argv/unknown_args` 字段，会影响调用端契约。
2. 缓解措施：保留 CLI JSON 错误字段断言测试，防止回归。

## 8. 关键决策

1. 决策内容：采用自定义 `ArgumentParser.error`，而非消费 stderr 文本。
2. 决策原因：保证 CLI 参数错误走统一 typed error-code 合同，便于自动化消费。
3. 影响模块：alertmanager validator CLI、CI 错误处理、运维自动化治理。

## 9. 下迭代计划

1. 继续推进 M4 治理脚本 JSON 错误合同一致性（按 validator 逐个对齐）。
2. 评估是否需要为关键 validator 增加成功态 JSON 输出模式。
