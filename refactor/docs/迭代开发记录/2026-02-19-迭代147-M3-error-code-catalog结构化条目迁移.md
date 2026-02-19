# 迭代开发记录

迭代编号：`迭代147`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将 validator error code catalog 从字符串描述升级为结构化条目。
2. 保持 sync 脚本兼容旧格式输入并自动迁移为新格式输出。
3. 扩展 strict 占位词门禁到 `description` 与 `remediation` 字段。

## 2. 计划范围（Plan）

1. 先补失败测试，约束条目结构、legacy 迁移、strict 新字段校验。
2. 改造 schema 与 sync 脚本，落地结构化条目生成逻辑。
3. 更新 catalog、README、CHANGELOG、版本并完成验证。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增/调整失败约束：
     - catalog 每个 error code 条目必须是 `{description,severity,remediation}` 对象
     - sync 脚本需将 legacy 字符串条目迁移为结构化条目
     - strict 模式需拦截 `remediation` 字段中的占位词
2. TDD Green：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
     - 支持读取 legacy 字符串条目与结构化条目
     - 输出统一结构化条目
     - strict 占位词扫描范围扩展至 `description/remediation`
   - `refactor/backend/config/schemas/validator-error-codes.schema.json`
     - 条目 schema 升级为对象结构
     - `severity` 枚举：`info|warning|error|critical`
   - `refactor/backend/config/validator-error-codes.json`
     - 全量迁移为结构化条目
3. 文档与版本：
   - `refactor/backend/README.md` 增补结构化条目与 strict 字段范围说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.132-m3-error-code-catalog-structured-entries`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.132-m3-error-code-catalog-structured-entries`

## 4. 未完成项（Not Done）

1. catalog 的 `severity/remediation` 仍使用统一默认值，尚未做按错误码细分策略。
2. catalog 结构化字段尚未下发到独立对外文档页。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/scripts/validate-validator-error-code-catalog.py`
2. 配置：
   - `refactor/backend/config/schemas/validator-error-codes.schema.json`
   - `refactor/backend/config/validator-error-codes.json`
3. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
4. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代147-M3-error-code-catalog结构化条目迁移.md`
5. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "catalog_exists_and_has_prefix_groups or migrates_legacy_string_catalog_entries or strict_descriptions_fail_on_todo or strict_error_includes_group_and_remediation or supports_custom_placeholder_marker_file or strict_descriptions_fail_on_tbd_fixme" -q`
   - 结果：预期失败（条目仍为旧字符串结构）。
2. Green 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "catalog_exists_and_has_prefix_groups or migrates_legacy_string_catalog_entries or strict_descriptions_fail_on_todo or strict_error_includes_group_and_remediation or strict_descriptions_fail_on_remediation_placeholder or supports_custom_placeholder_marker_file or strict_descriptions_fail_on_tbd_fixme" -q`
   - 结果：通过。
3. 全量验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（结构化条目迁移、legacy 兼容、strict 门禁扩展均可验证）。

## 7. 风险与问题

1. 风险描述：全量默认 `severity=error` 可能无法反映不同错误级别的实际差异。
2. 影响范围：告警分级、运维优先级判定。
3. 缓解措施：后续按错误码分域补齐 severity/remediation 精细化映射。

## 8. 关键决策

1. 决策内容：先做“结构升级 + 兼容迁移 + 默认值”最小闭环，不一次性引入复杂分级模型。
2. 决策原因：降低迁移风险，优先确保 schema 和 CI 门禁稳定落地。
3. 影响模块：catalog 配置、sync 脚本、strict 质量门禁、文档说明。

## 9. 下迭代计划

1. 按错误码维度细化 `severity` 与 `remediation` 映射表。
2. 为结构化条目增加 lint（例如 remediation 质量词典、长度阈值）。
3. 将结构化 catalog 输出接入对外 API/治理看板。
