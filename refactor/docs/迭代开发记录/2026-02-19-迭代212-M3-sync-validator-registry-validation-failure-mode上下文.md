# 迭代开发记录

迭代编号：`迭代212`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 细化 validator registry 校验阶段错误语义。
2. 为 `validator_registry_missing` 与 `validator_registry_invalid` 补齐 `context.failure_mode`。
3. 不改变错误码，仅增强结构化错误路由能力。

## 2. 计划范围（Plan）

1. 对 missing/invalid 用例增加 `failure_mode` 断言（RED）。
2. 在脚本对应上下文补 `failure_mode`（GREEN）。
3. 回归并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - 修改测试：
     - `test_validator_error_code_sync_script_json_errors_for_missing_validator_registry`
     - `test_validator_error_code_sync_script_json_errors_for_invalid_validator_registry_item`
   - Red 结果：两条用例均因缺失 `context.failure_mode` 失败（预期）。
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - `VALIDATOR_REGISTRY_MISSING` 上下文新增：
       - `failure_mode: "missing_registry"`
     - `VALIDATOR_REGISTRY_INVALID` 上下文新增：
       - `failure_mode: "invalid_registry_item"`
3. 文档与版本：
   - `refactor/backend/README.md` 增加 missing/invalid 的 `failure_mode` 说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.197-m3-sync-json-errors-validator-registry-validation-failure-mode-context`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.197-m3-sync-json-errors-validator-registry-validation-failure-mode-context`。

## 4. 未完成项（Not Done）

1. registry validation 阶段尚未补充统一的 `exception_type`（该阶段多为语义校验，不一定由异常驱动）。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代212-M3-sync-validator-registry-validation-failure-mode上下文.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "missing_validator_registry or invalid_validator_registry_item"`
   - 结果：失败（预期，缺失 `context.failure_mode`）。
2. GREEN（目标回归）：
   - 同命令回归通过。
3. 回归：
   - `cd refactor/backend && pytest -q tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：新增 context 字段可能影响严格 JSON 字段白名单校验逻辑。
2. 影响范围：消费 missing/invalid 错误 JSON 的自动化脚本。
3. 缓解措施：测试锁定 + README/CHANGELOG 契约同步。

## 8. 关键决策

1. 决策内容：在 registry validation 错误场景引入 `failure_mode`：
   - `missing_registry`
   - `invalid_registry_item`
2. 决策原因：便于上游系统直接按语义分支，不必依赖 message 文本。
3. 影响模块：sync validator registry validation 错误上下文。

## 9. 下迭代计划

1. 继续收敛结构化错误字段一致性（例如是否补 `argv`）。
2. 评估是否需要为更多校验型错误引入 `failure_mode` 统一分类。
