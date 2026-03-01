# 迭代开发记录

迭代编号：`迭代177`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 metadata overrides 的 profile-mode 能力，兼容 flat 配置。
2. 打通 validator 与 sync 两条链路的 profile 选择参数。
3. 保持现有门禁与回归测试稳定通过。

## 2. 计划范围（Plan）

1. 先执行 RED：运行现有 overrides profile 相关用例，确认失败原因是参数未支持。
2. 实现 `--overrides-profile` 与 `--metadata-overrides-profile`。
3. 扩展 overrides schema 支持 profile-mode 结构并回归验证。
4. 更新 README / CHANGELOG / 版本号。

## 3. 实际完成（Done）

1. RED 确认：
   - 运行：
     - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "supports_overrides_profile or unknown_overrides_profile or metadata_overrides_profile"`
   - 结果：3 个用例失败，均为 CLI 未识别 `--overrides-profile` 或 `--metadata-overrides-profile`。
2. GREEN 实现：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 新增 `OVERRIDES_PROFILE` 环境变量支持。
     - 新增 `--overrides-profile` 参数与 profile 解析流程。
     - 新增错误码：`error_code_metadata_overrides_overrides_profile_not_found`。
     - profile-mode 下先解析 profile，再做 target/lint/placeholder 校验。
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - 新增 `METADATA_OVERRIDES_PROFILE` 环境变量支持。
     - 新增 `--metadata-overrides-profile` 参数。
     - 新增 profile 解析逻辑，兼容 flat 配置。
   - `refactor/backend/config/schemas/validator-error-code-metadata-overrides.schema.json`
     - 支持两种 payload：
       - flat：`group -> code -> fields`
       - profile：`default_profile + profiles.<name>.(group -> code -> fields)`
3. 文档与版本：
   - `refactor/backend/README.md` 增加 overrides profile-mode 与 CLI/env 优先级说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.162-m3-metadata-overrides-profile-mode`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.162-m3-metadata-overrides-profile-mode`。

## 4. 未完成项（Not Done）

1. 尚未为 sync 脚本补充“未知 metadata overrides profile”的专用单测（当前通过运行链路与已有用例间接覆盖）。
2. 尚未在 docs 中输出 profile 策略治理矩阵（后续可并入 M3 文档）。

## 5. 代码与文档变更

1. 修改：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/config/schemas/validator-error-code-metadata-overrides.schema.json`
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/src/app/main.py`
2. 新增：
   - `refactor/docs/迭代开发记录/2026-02-19-迭代177-M3-metadata-overrides-profile-mode落地.md`

## 6. 验证记录

1. 目标用例回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py -k "supports_overrides_profile or unknown_overrides_profile or metadata_overrides_profile"`
   - 结果：通过。
2. 关键测试文件回归：
   - `pytest -q refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 结果：通过。
3. 编译与全门禁：
   - `cd refactor/backend && python3 -m compileall -q src scripts`
   - `cd refactor/backend && bash scripts/ci.sh`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：profile-mode 与 flat 双形态并存，后续手工维护配置时更易出现结构误用。
2. 影响范围：metadata overrides 配置与 sync/validator 行为一致性。
3. 缓解措施：通过 schema + validator + CI 约束，禁止无效结构进入主干。

## 8. 关键决策

1. 决策内容：保持 flat 向后兼容，不强制一次性迁移为 profile-mode。
2. 决策原因：降低迁移成本，允许先接入 profile 选择能力再逐步治理。
3. 影响模块：overrides schema、validator、sync、README 使用说明。

## 9. 下迭代计划

1. 为 sync 脚本补齐 unknown profile 的显式失败测试与错误文案断言。
2. 评估是否将 profile 提示建议（近似匹配）扩展到 overrides profile 路径。
3. 在 M3 文档中补齐“profile 策略治理矩阵”和操作规范。
