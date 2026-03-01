# 迭代开发记录

迭代编号：`迭代199`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 收敛 sync registry 加载时 `SystemExit` 的非结构化失败路径。
2. 保证 `--json-errors` 在该场景仍返回可消费 JSON。
3. 保持错误码体系不变，仅补齐异常映射。

## 2. 计划范围（Plan）

1. 新增 `SystemExit` 场景失败测试（RED）。
2. 在 registry loader 中补充最小捕获映射（GREEN）。
3. 回归并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 新增测试：
     - `test_validator_error_code_sync_script_json_errors_for_validator_registry_load_failed_system_exit`
   - Red 结果：
     - 原行为 `stderr` 为空，无法解析 JSON（预期暴露问题）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - 在 `_load_validator_registry_codes` 中新增 `except SystemExit`，
     - 映射为 `error_code_sync_validator_error_codes_validator_registry_load_failed`，
     - 并写入 `context.exception_type=SystemExit`。
3. 文档与版本：
   - `refactor/backend/README.md` 补充 registry load failed 覆盖 `SystemExit` 场景。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.184-m3-sync-json-errors-validator-registry-system-exit`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.184-m3-sync-json-errors-validator-registry-system-exit`。

## 4. 未完成项（Not Done）

1. sync 仍保留最终 `unexpected_error` 兜底分支，后续继续细分映射。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代199-M3-sync-validator-registry-system-exit结构化错误.md`

## 6. 验证记录

1. RED：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "validator_registry_load_failed_system_exit"`
   - 结果：失败（预期，`stderr` 空导致 JSON 解析失败）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：若下游依赖进程退出码细分（例如固定读取 `7`），行为会转为统一 sync 错误返回码路径。
2. 影响范围：消费 sync 子进程退出语义的自动化脚本。
3. 缓解措施：保留错误码稳定，补充 `exception_type` 供下游做细粒度识别。

## 8. 关键决策

1. 决策内容：仅针对 `SystemExit` 增加显式映射，不扩大到 `BaseException` 全量捕获。
2. 决策原因：避免吞掉中断类异常（如 `KeyboardInterrupt`）并控制改动面。
3. 影响模块：validator registry loader。

## 9. 下迭代计划

1. 继续收敛 sync 脚本剩余兜底路径，优先选择可稳定复现的非结构化失败场景。
2. 统一 `--json-errors` 各错误码的 context 字段基线。
