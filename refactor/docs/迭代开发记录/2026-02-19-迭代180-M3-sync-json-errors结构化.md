# 迭代开发记录

迭代编号：`迭代180`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 `sync-validator-error-codes.py` 增加 `--json-errors` 能力。
2. 让 sync 路径的 unknown profile / unknown override code 能输出结构化错误。
3. 维持现有测试与 CI 门禁稳定。

## 2. 计划范围（Plan）

1. 先补 RED：sync `--json-errors` 失败路径测试。
2. 实现结构化错误对象与错误码映射。
3. 回归验证并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_unknown_metadata_overrides_profile`
     - `test_validator_error_code_sync_script_json_errors_for_unknown_override_code`
   - Red 结果：脚本不识别 `--json-errors`（预期失败）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - 新增 `--json-errors` 参数。
     - 新增结构化异常类型：`SyncValidatorErrorCodesError`。
     - 新增 sync 错误码注册表：`SYNC_ERROR_CODES`。
     - unknown metadata overrides profile / unknown override code 等路径改为抛出带 code/context 的结构化异常。
     - `main()` 中按 `--json-errors` 输出统一 JSON 错误 payload。
3. 文档与版本：
   - `refactor/backend/README.md` 新增 sync `--json-errors` 与关键错误码说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.165-m3-sync-json-errors`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.165-m3-sync-json-errors`。

## 4. 未完成项（Not Done）

1. sync 仍未覆盖所有失败分支的细粒度错误码（当前先覆盖核心路径）。
2. sync 的错误上下文与 validator 仍有字段丰富度差异，可后续对齐。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代180-M3-sync-json-errors结构化.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "sync_script_json_errors_for_unknown_metadata_overrides_profile or sync_script_json_errors_for_unknown_override_code"`
   - 结果：失败（预期，`--json-errors` 未实现）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 全量回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：新增错误码后，后续若补更多分支需保持错误码语义一致。
2. 影响范围：sync CLI 调用方的错误解析逻辑。
3. 缓解措施：通过新增 JSON 错误测试锁定关键路径契约。

## 8. 关键决策

1. 决策内容：优先以结构化异常 + 顶层统一序列化方式实现 `--json-errors`。
2. 决策原因：便于后续扩展更多 error code，且对 plain stderr 行为兼容。
3. 影响模块：sync script 主流程与 metadata overrides 校验路径。

## 9. 下迭代计划

1. 扩展 sync 其余失败分支错误码覆盖（check drift、placeholder strict failures 等）。
2. 评估 sync JSON 错误结构与 validator 结构字段完全对齐。
3. 继续推进 profile 策略治理文档矩阵。
