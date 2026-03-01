# 迭代开发记录

迭代编号：`迭代182`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 sync `--json-errors` 在 placeholder marker 文件异常场景的细粒度错误码。
2. 覆盖 marker 文件缺失与 payload 非法两条核心异常路径。
3. 维持全量门禁稳定通过。

## 2. 计划范围（Plan）

1. 先补 RED 测试：missing marker file / invalid marker payload。
2. 修改 `_load_placeholder_markers`，统一抛出结构化 sync 异常。
3. 全量回归并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_missing_placeholder_markers_file`
     - `test_validator_error_code_sync_script_json_errors_for_invalid_placeholder_markers_payload`
   - Red 结果：两条均返回 `unexpected_error`（预期失败）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - `SYNC_ERROR_CODES` 新增：
       - `error_code_sync_validator_error_codes_placeholder_markers_file_not_found`
       - `error_code_sync_validator_error_codes_placeholder_markers_invalid`
     - `_load_placeholder_markers` 改为结构化异常：
       - 文件不存在
       - JSON 解析失败
       - markers 列表缺失/非法
       - marker 非字符串、空值、重复等
3. 文档与版本：
   - `refactor/backend/README.md` 增补 marker 异常 JSON 错误码说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.167-m3-sync-json-errors-placeholder-marker-exceptions`。
   - `refactor/backend/src/app/main.py` 版本升级到 `0.3.167-m3-sync-json-errors-placeholder-marker-exceptions`。

## 4. 未完成项（Not Done）

1. sync 仍有部分非核心路径使用通用 `unexpected_error`（后续继续细化）。
2. sync 与 validator 在 JSON context 字段完整度上仍可继续对齐。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代182-M3-sync-json-errors-placeholder-marker异常.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "missing_placeholder_markers_file or invalid_placeholder_markers_payload"`
   - 结果：失败（预期，error code 为 `unexpected_error`）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 全量回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：error code 细化后，调用方需同步处理新增码值。
2. 影响范围：消费 sync JSON 错误码的自动化脚本。
3. 缓解措施：通过 CHANGELOG + README 明确新增码，测试锁定契约。

## 8. 关键决策

1. 决策内容：优先覆盖 placeholder marker 异常，因为这是 strict 检查的关键前置依赖。
2. 决策原因：该路径失败会直接阻断 CI，结构化错误收益高。
3. 影响模块：sync placeholder marker loader、JSON 错误码契约、文档。

## 9. 下迭代计划

1. 继续补齐 sync 非核心异常路径的细粒度 error code。
2. 对齐 sync/validator 的 context 字段模型，形成统一错误契约。
3. 推进 profile 策略治理矩阵文档化。
