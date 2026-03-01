# 迭代开发记录

迭代编号：`迭代194`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 sync `--json-errors` 在 metadata overrides 为非 UTF-8 内容场景的错误分类。
2. 避免该场景落到 `unexpected_error`。
3. 统一归类到 `json_parse_error`（`role=metadata_overrides`）。

## 2. 计划范围（Plan）

1. 新增 RED 用例：metadata overrides 文件写入非法 UTF-8 字节。
2. 修改 `_load_metadata_overrides` 捕获 `UnicodeDecodeError` 并映射为 parse error。
3. 回归并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_invalid_utf8_metadata_overrides`
   - Red 结果：返回 `error_code_sync_validator_error_codes_unexpected_error`（预期失败）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - `_load_metadata_overrides` 新增 `UnicodeDecodeError` 捕获并抛：
       - `error_code_sync_validator_error_codes_json_parse_error`
       - `context.role=metadata_overrides`
3. 文档与版本：
   - `refactor/backend/README.md` 增补 metadata overrides 非 UTF-8 场景说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.179-m3-sync-json-errors-metadata-overrides-utf8-parse`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.179-m3-sync-json-errors-metadata-overrides-utf8-parse`。

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
   - `refactor/docs/迭代开发记录/2026-02-19-迭代194-M3-sync-json-errors-metadata-overrides-utf8解析.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "invalid_utf8_metadata_overrides"`
   - 结果：失败（预期，返回 `unexpected_error`）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "invalid_utf8_metadata_overrides or unreadable_metadata_overrides_path or invalid_utf8_catalog"`
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：错误分类从 `unexpected_error` 收敛到 `json_parse_error` 后，下游统计口径可能变化。
2. 影响范围：sync JSON 错误消费端、告警报表。
3. 缓解措施：通过测试 + README + CHANGELOG 明确行为变更。

## 8. 关键决策

1. 决策内容：将 metadata overrides UTF-8 解码异常归入 parse error。
2. 决策原因：该问题本质是“内容编码/格式不可解析”，不应归类为 read failure。
3. 影响模块：sync metadata overrides loader、错误码分类策略。

## 9. 下迭代计划

1. 继续梳理 sync 剩余 `unexpected_error` 路径并细化。
2. 推进 sync/validator 错误上下文 schema 一致性校验。
