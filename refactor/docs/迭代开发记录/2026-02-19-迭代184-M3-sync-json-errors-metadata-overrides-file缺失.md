# 迭代开发记录

迭代编号：`迭代184`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 sync `--json-errors` 在 metadata overrides 文件缺失场景的专用错误码。
2. 避免该场景退化为通用 `unexpected_error`。
3. 固化测试与文档契约。

## 2. 计划范围（Plan）

1. 先加 RED 用例，锁定缺失文件场景的目标 code。
2. 最小修改 sync 脚本文件不存在分支为结构化异常。
3. 回归测试并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_missing_metadata_overrides_file`
   - Red 结果：返回 `error_code_sync_validator_error_codes_unexpected_error`（预期失败）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - `SYNC_ERROR_CODES` 新增：
       - `error_code_sync_validator_error_codes_metadata_overrides_file_not_found`
     - `_load_metadata_overrides` 文件缺失分支改为抛出 `SyncValidatorErrorCodesError` 并携带 `context.path`。
3. 文档与版本：
   - `refactor/backend/README.md` 补充该错误码说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.169-m3-sync-json-errors-missing-metadata-overrides-file`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.169-m3-sync-json-errors-missing-metadata-overrides-file`。

## 4. 未完成项（Not Done）

1. sync `--json-errors` 仍有部分异常路径可继续从通用错误细化为专用错误码（后续迭代处理）。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代184-M3-sync-json-errors-metadata-overrides-file缺失.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "missing_metadata_overrides_file"`
   - 结果：失败（预期，返回 `unexpected_error`）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "sync_script_json_errors_for_unknown_metadata_overrides_profile or non_profile_overrides_config_when_profile_requested or missing_metadata_overrides_file"`
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：新增错误码可能要求下游调用方更新 allowlist。
2. 影响范围：消费 sync JSON 错误码的自动化脚本与告警策略。
3. 缓解措施：通过测试和 README/CHANGELOG 固化输出契约。

## 8. 关键决策

1. 决策内容：优先细化“文件缺失”这类高频、可定位问题为专用码。
2. 决策原因：比 `unexpected_error` 更利于自动化修复与问题归类。
3. 影响模块：sync metadata overrides loader、JSON 错误契约、文档。

## 9. 下迭代计划

1. 继续提升 sync JSON 错误覆盖率，减少通用错误码兜底比例。
2. 对齐 sync/validator 的错误上下文字段 schema 一致性。
