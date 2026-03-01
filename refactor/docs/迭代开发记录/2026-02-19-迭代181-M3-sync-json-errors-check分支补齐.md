# 迭代开发记录

迭代编号：`迭代181`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 sync `--json-errors` 在 `--check` 失败分支的结构化错误输出。
2. 覆盖 check drift 与 strict placeholder 两条核心失败路径。
3. 保持门禁稳定通过。

## 2. 计划范围（Plan）

1. 先补 RED 测试：`--check --json-errors` 的 drift 与 strict placeholder。
2. 修改 sync 脚本，新增对应错误码与 context。
3. 全量回归并同步文档与版本。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_check_drift`
     - `test_validator_error_code_sync_script_json_errors_for_strict_placeholder_descriptions`
   - Red 结果：stderr 仍是 plain 文本，非 JSON（预期失败）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - `SYNC_ERROR_CODES` 新增：
       - `error_code_sync_validator_error_codes_catalog_file_not_found`
       - `error_code_sync_validator_error_codes_catalog_not_in_sync`
       - `error_code_sync_validator_error_codes_placeholder_text_detected`
     - `--check` 模式下对 catalog missing / drift / strict placeholder 违规在 `--json-errors` 时输出结构化 payload。
     - strict placeholder context 新增 `violations` 结构化列表（group/code/field/marker/value）。
3. 文档与版本：
   - `refactor/backend/README.md` 增加 sync check/strict 路径 JSON 错误码说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.166-m3-sync-json-errors-check-coverage`。
   - `refactor/backend/src/app/main.py` 版本升级为 `0.3.166-m3-sync-json-errors-check-coverage`。

## 4. 未完成项（Not Done）

1. sync 仍有部分异常路径暂未细分 error code（例如部分 placeholder marker 文件异常仍走通用路径）。
2. sync JSON context 与 validator JSON context 还有细节差异可继续统一。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代181-M3-sync-json-errors-check分支补齐.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "json_errors_for_check_drift or json_errors_for_strict_placeholder_descriptions"`
   - 结果：失败（预期，stderr 不是 JSON）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 全量回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：error code 数量增长后，需要保持命名与语义一致。
2. 影响范围：依赖 sync JSON 输出的自动化流程。
3. 缓解措施：通过新增测试锁定 JSON code/context 契约。

## 8. 关键决策

1. 决策内容：优先覆盖 `--check` 的 drift/placeholder 高价值失败分支。
2. 决策原因：这两条是 CI 门禁最常见失败路径，优先结构化收益最高。
3. 影响模块：sync check 分支、JSON 错误输出契约、README 说明。

## 9. 下迭代计划

1. 补齐 sync 其余异常路径的细粒度 error code（placeholder marker 文件类异常等）。
2. 对齐 sync 与 validator JSON context 字段模型。
3. 继续推进 profile 策略治理矩阵文档化。
