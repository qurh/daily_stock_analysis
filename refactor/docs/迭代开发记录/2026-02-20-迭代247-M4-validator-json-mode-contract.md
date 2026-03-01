# 迭代开发记录

迭代编号：`迭代247`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 明确并固化 validator 在 `--json-output` 与 `--json-errors` 同时开启时的行为契约。
2. 通过通用测试覆盖 9 个 validator，避免后续脚本改动引入输出通道回归。
3. 同步文档与版本记录。

## 2. 计划范围（Plan）

1. 在统一契约测试文件中新增并存模式 success/failure 两类用例。
2. 运行测试，若存在不一致则修脚本；一致则仅保留契约测试。
3. 更新 README、CHANGELOG、版本号。

## 3. 实际完成（Done）

1. 测试增强：
   - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
   - 新增：
     - `test_validator_scripts_both_json_flags_success_mode_contract`
     - `test_validator_scripts_both_json_flags_unknown_args_emit_structured_error`
2. 契约结果：
   - 当前 9 个 validator 已满足并存模式契约，无需修改脚本实现：
     - success：`stdout` JSON、`stderr` 为空、`exit_code=0`
     - failure（unknown args）：`stderr` JSON、`stdout` 为空、`exit_code!=0`
3. 文档与版本：
   - `refactor/backend/README.md` 增加并存模式行为说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.31` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为 `0.4.31-m4-validator-json-mode-contract`。

## 4. 未完成项（Not Done）

1. 暂未为“业务校验失败场景（非 CLI 参数错误）”增加并存模式矩阵测试（当前只覆盖 unknown args）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_validator_success_output_contract.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代247-M4-validator-json-mode-contract.md`

## 6. 验证记录

1. 契约测试：
   - `pytest -q refactor/backend/tests/unit/test_validator_success_output_contract.py`
   - 结果：通过（4 tests）。
2. 语法检查：
   - `python3 -m py_compile refactor/backend/tests/unit/test_validator_success_output_contract.py refactor/backend/src/app/main.py`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：并存模式当前 failure 分支仅覆盖 unknown args，业务失败分支仍可能出现差异。
2. 影响范围：自动化调用方对 stderr/stdout 的路由假设。
3. 缓解措施：下迭代增加非 CLI 失败分支矩阵测试。

## 8. 关键决策

1. 决策内容：先以测试固化既有实现行为，不强制改为互斥参数。
2. 决策原因：保持向后兼容，减少脚本行为突变风险。
3. 影响模块：validator CLI contract、自动化消费端、回归测试基线。

## 9. 下迭代计划

1. 为每个 validator 增加一条“业务失败 + 并存模式”测试样例。
2. 评估是否需要在 long term 将 `--json-output` / `--json-errors` 设计为互斥参数并提供迁移方案。
