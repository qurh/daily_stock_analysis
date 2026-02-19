# 迭代开发记录

迭代编号：`迭代149`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 validator error code metadata 增加手工 override 能力。
2. 允许按 `group.code` 定向覆写 `description/severity/remediation`。
3. 对 override 输入做严格校验，避免 silent typo 漏洞。

## 2. 计划范围（Plan）

1. 先补失败测试：配置文件存在、override 生效、非法 override 拦截。
2. 增加默认 override 配置文件并实现脚本参数与应用逻辑。
3. 更新 README/CHANGELOG/版本并完成门禁验证。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败约束：
     - metadata override 配置文件必须存在
     - 指定 override 文件可生效覆写 metadata
     - unknown override code 必须失败
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - 新增参数：`--metadata-overrides-file`
     - 新增默认路径：`config/validator-error-code-metadata-overrides.json`
     - override 输入校验：
       - payload 必须为 object
       - 仅允许字段 `description|severity|remediation`
       - `severity` 必须在 `info|warning|error|critical`
       - unknown group/code 直接失败
     - 生成 catalog 时应用 override
   - 新增配置：
     - `refactor/backend/config/validator-error-code-metadata-overrides.json`
3. 文档与版本：
   - `refactor/backend/README.md` 补充 override 配置与规则说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.134-m3-error-code-metadata-overrides`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.134-m3-error-code-metadata-overrides`

## 4. 未完成项（Not Done）

1. override 文件当前为空模板，尚未提供真实业务覆写样例。
2. override 文件尚未引入独立 schema 校验脚本。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
2. 配置：
   - `refactor/backend/config/validator-error-code-metadata-overrides.json`
3. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
4. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代149-M3-error-code元数据override机制.md`
5. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "metadata_overrides_config_exists or applies_custom_metadata_overrides or fails_on_unknown_override_code" -q`
   - 结果：预期失败（缺默认配置和参数逻辑）。
2. Green 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "metadata_overrides_config_exists or applies_custom_metadata_overrides or fails_on_unknown_override_code" -q`
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（override 能力可用且具备校验护栏）。

## 7. 风险与问题

1. 风险描述：override 字段手工维护可能造成策略分散与冲突。
2. 影响范围：error metadata 一致性与治理可读性。
3. 缓解措施：通过严格校验阻断未知 group/code，并在后续引入 schema 与 lint。

## 8. 关键决策

1. 决策内容：采用单独 override 文件，而非直接编辑 sync 脚本内硬编码映射。
2. 决策原因：降低改动成本，便于运营/治理层低成本覆写。
3. 影响模块：sync 脚本、catalog 配置治理、文档使用方式。

## 9. 下迭代计划

1. 为 metadata override 引入 schema 文件与独立校验脚本，并接入 CI。
2. 增加 override 冲突检测（同 code 多来源覆写审计）。
3. 提供一份最小可用 override 示例集用于 runbook。
