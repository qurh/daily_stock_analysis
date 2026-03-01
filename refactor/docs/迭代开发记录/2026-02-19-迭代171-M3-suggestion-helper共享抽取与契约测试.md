# 迭代开发记录

迭代编号：`迭代171`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将 unknown profile 建议逻辑从 lint/overrides 两个脚本中抽取为共享 helper。
2. 降低重复代码，减少两脚本后续维护漂移风险。
3. 增加契约测试，锁定共享 helper 的 action/payload 结构。

## 2. 计划范围（Plan）

1. 先补失败测试：要求存在共享 helper 模块，且两个 validator 均从该模块导入。
2. 创建共享 helper 模块并改造两个脚本引用。
3. 回归测试 + 文档 + 版本同步。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增测试：
     - `test_profile_suggestion_helper_module_is_shared_and_contract_stable`
   - 覆盖点：
     - 共享 helper 模块存在
     - lint/overrides 两个脚本从共享模块导入
     - helper 输出 `fallback_reason`/`suggestion_level`/`suggested_actions` 契约稳定
2. TDD Green：
   - 新增 `refactor/backend/scripts/profile_suggestion_helpers.py`
   - 抽取并复用函数：
     - `build_profile_suggestion_payload`
     - `build_ordered_available_profiles`
     - `shell_quote`
     - `build_profile_mode_config_snippet`
     - `build_suggested_actions_for_profile_not_found`
   - 改造脚本：
     - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
   - 两脚本改为从共享模块导入（私有别名保持原调用点）
3. 文档与版本：
   - `refactor/backend/README.md` 增加共享 helper 模块路径说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.156-m3-error-code-shared-suggestion-helpers`
   - `refactor/backend/src/app/main.py` 版本升级为 `0.3.156-m3-error-code-shared-suggestion-helpers`

## 4. 未完成项（Not Done）

1. 尚未将两个 validator 的未知 profile context 组装完全合并为单一 helper（当前仍保留脚本内 context 封装）。
2. 尚未把 shared helper 纳入独立 schema 校验脚本（当前由单测保障）。

## 5. 代码与文档变更

1. 新增：
   - `refactor/backend/scripts/profile_suggestion_helpers.py`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代171-M3-suggestion-helper共享抽取与契约测试.md`
2. 修改：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "profile_suggestion_helper_module_is_shared_and_contract_stable"`
   - 结果：预期失败（helper 文件不存在）。
2. Green 阶段：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "profile_suggestion_helper_module_is_shared_and_contract_stable or suggests_nearby_profile or handles_no_nearby_profile_suggestion or reports_non_profile_config_when_profile_requested or suggests_nearby_lint_profile or handles_no_nearby_lint_profile_suggestion"`
   - 结果：通过。
3. 全量回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（共享 helper 抽取完成且契约测试通过）。

## 7. 风险与问题

1. 风险描述：helper 模块被多个脚本共享后，变更影响面扩大。
2. 影响范围：lint/overrides validator 的 unknown profile 建议输出。
3. 缓解措施：通过契约测试锁定关键输出结构，避免无意破坏。

## 8. 关键决策

1. 决策内容：保留脚本内私有函数名别名（`_build_*`），实际实现迁移到 shared helper。
2. 决策原因：兼容现有调用点与脚本可读性，同时消除逻辑重复。
3. 影响模块：两个 validator 脚本与单元测试。

## 9. 下迭代计划

1. 为 `suggested_actions` 补充轻量 schema 校验（如 action 字段枚举和必要参数校验）。
2. 评估进一步合并 unknown profile context 构建逻辑，减少脚本内重复字段拼装。
3. 逐步把 shared helper 的用例从集成单测下沉到更独立的 helper 单测文件。
