# 迭代开发记录

迭代编号：`迭代192`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 sync `--json-errors` 在 placeholder marker 路径可见但不可读（目录路径）场景的专用错误码。
2. 避免该场景落到 `unexpected_error`。
3. 固化 `path/exception_type` 上下文字段。

## 2. 计划范围（Plan）

1. 新增 RED 用例：`--placeholder-markers-file` 指向目录。
2. 修改 `_load_placeholder_markers` 增加读文件异常处理。
3. 回归并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_unreadable_placeholder_markers_path`
   - Red 结果：返回 `error_code_sync_validator_error_codes_unexpected_error`（预期失败）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - `SYNC_ERROR_CODES` 新增：
       - `error_code_sync_validator_error_codes_placeholder_markers_read_failed`
     - `_load_placeholder_markers` 新增读取异常捕获：
       - `context.path`
       - `context.exception_type`
3. 文档与版本：
   - `refactor/backend/README.md` 增补 placeholder marker read failed 错误码说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.177-m3-sync-json-errors-placeholder-markers-read-failed`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.177-m3-sync-json-errors-placeholder-markers-read-failed`。

## 4. 未完成项（Not Done）

1. sync 仍有少量 `unexpected_error` 兜底路径，后续继续细化。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代192-M3-sync-json-errors-placeholder-marker读取失败.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "unreadable_placeholder_markers_path"`
   - 结果：失败（预期，返回 `unexpected_error`）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "unreadable_placeholder_markers_path or non_object_placeholder_markers_payload or missing_placeholder_markers_file"`
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：新增错误码需要下游消费方同步映射。
2. 影响范围：sync JSON 错误消费方（CI/告警分类）。
3. 缓解措施：通过测试 + README + CHANGELOG 固化契约。

## 8. 关键决策

1. 决策内容：将 placeholder marker 文件读取失败与 payload 非法错误分离建模。
2. 决策原因：提升问题定位速度，明确是 IO 层问题而非 JSON 内容问题。
3. 影响模块：sync marker loader、JSON 错误码契约。

## 9. 下迭代计划

1. 继续梳理 sync 剩余 `unexpected_error` 路径并细化专用错误码。
2. 推进 sync/validator 错误上下文 schema 一致性校验。
