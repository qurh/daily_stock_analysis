# 迭代开发记录

迭代编号：`迭代186`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 sync `--json-errors` 在 validator registry 缺失/非法场景的专用错误码。
2. 避免上述场景落到 `unexpected_error`。
3. 固化可复现测试与文档契约。

## 2. 计划范围（Plan）

1. 先新增 RED 用例覆盖 missing/invalid registry 两个分支。
2. 修改 `_load_validator_registry_codes` 为结构化异常输出。
3. 回归测试并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_missing_validator_registry`
     - `test_validator_error_code_sync_script_json_errors_for_invalid_validator_registry_item`
   - Red 结果：两条均返回 `error_code_sync_validator_error_codes_unexpected_error`（预期失败）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - `SYNC_ERROR_CODES` 新增：
       - `error_code_sync_validator_error_codes_validator_registry_missing`
       - `error_code_sync_validator_error_codes_validator_registry_invalid`
     - `_load_validator_registry_codes` 改为抛 `SyncValidatorErrorCodesError`，上下文包含：
       - `group`
       - `path`
       - `registry_key`（仅 invalid 场景）
3. 文档与版本：
   - `refactor/backend/README.md` 增补 registry 类 sync JSON 错误码说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.171-m3-sync-json-errors-validator-registry-codes`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.171-m3-sync-json-errors-validator-registry-codes`。

## 4. 未完成项（Not Done）

1. sync `--json-errors` 仍有零散分支可继续细化（后续迭代处理）。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代186-M3-sync-json-errors-validator-registry异常.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "missing_validator_registry or invalid_validator_registry_item"`
   - 结果：失败（预期，返回 `unexpected_error`）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "missing_validator_registry or invalid_validator_registry_item or missing_validator_script_file or missing_metadata_overrides_file"`
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：新增错误码可能要求下游 JSON 错误码消费端更新映射。
2. 影响范围：sync CI 自动化告警与分类逻辑。
3. 缓解措施：以测试 + README + CHANGELOG 固化契约。

## 8. 关键决策

1. 决策内容：采用隔离 backend 副本触发 registry 异常分支，不改动真实 validator 脚本文件。
2. 决策原因：提升测试稳定性，避免对工作区已有文件造成破坏式影响。
3. 影响模块：sync registry loader、JSON 错误契约、测试覆盖率。

## 9. 下迭代计划

1. 继续梳理 sync 分支中剩余 `unexpected_error` 路径并逐步专用化。
2. 推进 sync/validator 错误上下文字段 schema 的统一校验。
