# 迭代开发记录

迭代编号：`迭代155`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 支持通过环境变量设置 lint profile，减少命令行参数重复配置。
2. 统一 lint 校验器与 overrides 校验器的 profile 选择优先级。
3. 保持与现有 `--lint-profile` 兼容，不破坏已有调用方式。

## 2. 计划范围（Plan）

1. 先补失败测试：两个校验器在未传 `--lint-profile` 时可读取 `LINT_PROFILE`。
2. 实现环境变量读取逻辑并定义优先级。
3. 更新 README、CHANGELOG、版本号并完成验证。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败约束：
     - lint 校验器可通过 `LINT_PROFILE` 选择 profile
     - overrides 校验器可通过 `LINT_PROFILE` 选择 profile
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 新增环境变量读取：`LINT_PROFILE`
     - 解析优先级：`--lint-profile` > `LINT_PROFILE` > `default_profile`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 新增环境变量读取：`LINT_PROFILE`
     - 同步优先级策略
3. 文档与版本：
   - `refactor/backend/README.md` 增加 env 配置与优先级说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.140-m3-error-code-lint-profile-env`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.140-m3-error-code-lint-profile-env`

## 4. 未完成项（Not Done）

1. `LINT_PROFILE` 当前为通用变量，尚未细分为校验器级别变量（如需更强隔离后续再做）。
2. 尚未增加 profile 来源（CLI/ENV/default）观测字段到审计日志。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代155-M3-error-code-lint-profile环境变量.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "uses_env_profile" -q`
   - 结果：预期失败（脚本尚未读取 `LINT_PROFILE`）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（两类校验器均支持 env 方式切换 profile，且优先级清晰）。

## 7. 风险与问题

1. 风险描述：全局 `LINT_PROFILE` 可能被外部运行环境误设，导致非预期 profile 生效。
2. 影响范围：lint 校验行为与门禁结果。
3. 缓解措施：文档明确优先级，且 CLI 参数可覆盖环境变量。

## 8. 关键决策

1. 决策内容：采用单一环境变量 `LINT_PROFILE`，先覆盖两个校验器。
2. 决策原因：接入成本低，便于 CI 与本地一致配置。
3. 影响模块：lint/overrides 校验脚本、README 使用方式。

## 9. 下迭代计划

1. 增加 profile 来源审计（记录 CLI/ENV/default 命中路径）。
2. 为未知 profile 错误增加推荐 profile 提示。
3. 评估将 profile 选择能力扩展到 `sync-validator-error-codes.py`。
