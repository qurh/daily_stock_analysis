# 迭代开发记录

迭代编号：`迭代185`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 sync `--json-errors` 在 validator registry 脚本缺失场景的专用错误码。
2. 避免该场景落到通用 `unexpected_error`。
3. 固化测试与文档契约。

## 2. 计划范围（Plan）

1. 先加 RED 用例，复现隔离副本下脚本缺失场景。
2. 修改 `_build_catalog` 缺失脚本分支为结构化异常。
3. 回归测试并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_missing_validator_script_file`
   - Red 结果：返回 `error_code_sync_validator_error_codes_unexpected_error`（预期失败）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - `SYNC_ERROR_CODES` 新增：
       - `error_code_sync_validator_error_codes_validator_script_file_not_found`
     - `_build_catalog` 中 validator 脚本缺失时改为抛 `SyncValidatorErrorCodesError`，并补充：
       - `context.group`
       - `context.path`
3. 文档与版本：
   - `refactor/backend/README.md` 补充该错误码说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.170-m3-sync-json-errors-missing-validator-script-file`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.170-m3-sync-json-errors-missing-validator-script-file`。

## 4. 未完成项（Not Done）

1. sync `--json-errors` 仍有少量分支可能走 `unexpected_error`，后续继续细化。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代185-M3-sync-json-errors-validator-script缺失.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "missing_validator_script_file"`
   - 结果：失败（预期，返回 `unexpected_error`）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "missing_validator_script_file or missing_metadata_overrides_file or sync_script_json_errors_for_unknown_metadata_overrides_profile or non_profile_overrides_config_when_profile_requested"`
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：新增错误码需要下游消费端同步 allowlist。
2. 影响范围：消费 sync JSON 错误码的 CI 自动化流程。
3. 缓解措施：通过测试与 README/CHANGELOG 固化契约。

## 8. 关键决策

1. 决策内容：使用“隔离 backend 副本”测试方式稳定复现脚本缺失分支，不污染仓库真实脚本文件。
2. 决策原因：保证测试稳定且不依赖运行时破坏式操作。
3. 影响模块：sync catalog builder、JSON 错误契约、测试策略。

## 9. 下迭代计划

1. 继续细化 sync JSON 错误码覆盖，进一步收敛 `unexpected_error` 使用范围。
2. 推进 sync/validator 错误上下文字段 schema 对齐。
