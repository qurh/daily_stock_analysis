# 迭代开发记录

迭代编号：`迭代150`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 metadata overrides 文件补齐 schema 契约。
2. 新增独立校验脚本，提前拦截 overrides 配置错误。
3. 将 overrides 校验接入 CI 门禁链路。

## 2. 计划范围（Plan）

1. 先补失败测试：schema 文件、校验脚本、CI 调用。
2. 实现 schema 与校验脚本（含 `--json-errors`）。
3. 更新文档、版本、迭代记录并完成验证。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败约束：
     - CI 必须调用 `validate-validator-error-code-metadata-overrides.py`
     - overrides schema 文件必须存在且为 Draft 2020-12
     - overrides 校验脚本默认配置通过
     - unknown override code 时 `--json-errors` 返回结构化错误
2. TDD Green：
   - 新增 schema：
     - `refactor/backend/config/schemas/validator-error-code-metadata-overrides.schema.json`
   - 新增脚本：
     - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 校验项：
       - overrides/schema/catalog 文件存在性
       - overrides schema 合法性与实例校验
       - override 目标 `group.code` 必须存在于 catalog
     - 支持 `--json-errors`（`error_code_metadata_overrides_*`）
   - CI 接入：
     - `refactor/backend/scripts/ci.sh` 增加 overrides 校验步骤
3. 文档与版本：
   - `refactor/backend/README.md` 补充 overrides schema 与校验脚本说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.135-m3-error-code-metadata-overrides-validator`
   - `refactor/backend/src/app/main.py` 版本升级到 `0.3.135-m3-error-code-metadata-overrides-validator`

## 4. 未完成项（Not Done）

1. overrides schema 尚未覆盖更细粒度语义规则（如 remediation 文案长度/关键词）。
2. overrides 校验脚本目前未输出建议修复模板（仅错误定位）。

## 5. 代码与文档变更

1. 配置：
   - `refactor/backend/config/schemas/validator-error-code-metadata-overrides.schema.json`
2. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
   - `refactor/backend/scripts/ci.sh`
3. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
4. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代150-M3-error-code-overrides校验器与schema.md`
5. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "ci_script_invokes_prometheus_rules_check or metadata_overrides_schema_exists or overrides_validator_script_passes_default_config or overrides_validator_script_json_errors_for_unknown_code" -q`
   - 结果：预期失败（缺 schema、缺脚本、CI 未接入）。
2. Green 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "ci_script_invokes_prometheus_rules_check or metadata_overrides_schema_exists or overrides_validator_script_passes_default_config or overrides_validator_script_json_errors_for_unknown_code" -q`
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（overrides 配置已具备 schema + 脚本 + CI 的完整门禁）。

## 7. 风险与问题

1. 风险描述：schema 仅覆盖结构与类型，无法判断 remediation 是否足够可操作。
2. 影响范围：metadata 可读性与治理质量。
3. 缓解措施：后续增加 remediation 质量 lint 规则。

## 8. 关键决策

1. 决策内容：先把 overrides 校验做成独立脚本，而不耦合进 sync 主脚本流程。
2. 决策原因：职责分离清晰，便于 CI 独立失败定位与后续扩展。
3. 影响模块：CI 门禁、配置治理脚本、测试套件。

## 9. 下迭代计划

1. 为 overrides 增加语义 lint（remediation 可操作性、禁用占位词）。
2. 输出 overrides 校验失败的修复建议模板（含示例片段）。
3. 评估将 overrides 校验结果纳入全局治理指标。
