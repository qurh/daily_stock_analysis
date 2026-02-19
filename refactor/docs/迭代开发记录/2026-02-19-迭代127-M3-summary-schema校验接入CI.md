# 迭代开发记录

迭代编号：`迭代127`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将 strict gate 摘要 schema 校验正式接入 CI。
2. 避免 schema 文件损坏或契约字段缺失时进入后续阶段。

## 2. 计划范围（Plan）

1. 先补失败测试定义 CI 和校验脚本行为。
2. 新增 schema 校验脚本并接入 `scripts/ci.sh`。
3. 同步 README / CHANGELOG / 版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败场景：
     - CI 必须包含 `validate-strict-gate-summary-schema.py`
     - 校验脚本可通过默认 schema
     - 校验脚本遇到非法 JSON 需失败
2. TDD Green：
   - 新增脚本：
     - `refactor/backend/scripts/validate-strict-gate-summary-schema.py`
   - 校验能力：
     - schema 文件存在性
     - JSON 解析
     - `Draft202012Validator.check_schema` 检查 schema 合法性
     - 契约字段存在性（`schema_version/changed_files_count/total_added_lines/total_removed_lines/files/modules`）
   - CI 接入：
     - `refactor/backend/scripts/ci.sh` 增加执行 `python3 ./scripts/validate-strict-gate-summary-schema.py`
3. 文档与版本：
   - `refactor/backend/README.md` 增加 schema 校验命令。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.112-m3-summary-schema-validator-ci`。
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.112-m3-summary-schema-validator-ci`。

## 4. 未完成项（Not Done）

1. 暂未将 schema 校验失败细分为稳定错误码。
2. 暂未增加 schema 版本变更策略自动检查。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-strict-gate-summary-schema.py`
   - `refactor/backend/scripts/ci.sh`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代127-M3-summary-schema校验接入CI.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "summary_schema_validator_script or ci_script_invokes_prometheus_rules_check" -q`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - 新增 schema validator 用例通过
   - 后端全量 CI 通过（promtool 缺失按策略 skip）
3. 是否达到验收标准：
   - 达到（schema 校验已成为 CI 固定步骤）

## 7. 风险与问题

1. 风险描述：脚本默认依赖 `jsonschema`，环境缺失时会失败。
2. 影响范围：本地与 CI 执行稳定性。
3. 缓解措施：已在 dev 依赖中显式声明 `jsonschema`。

## 8. 关键决策

1. 决策内容：schema 校验脚本独立于业务脚本，作为 CI 预检步骤执行。
2. 决策原因：解耦运行时路径和契约治理职责。
3. 影响模块：CI 流程与 schema 契约可维护性。

## 9. 下迭代计划

1. 增加 schema 版本变更与 changelog 同步约束检查。
2. 提供 `--strict-contract` 模式校验更多字段约束。
3. 评估把 summary payload 示例文件加入仓库用于回归对比。
