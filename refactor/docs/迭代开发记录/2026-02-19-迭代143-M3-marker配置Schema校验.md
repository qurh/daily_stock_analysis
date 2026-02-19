# 迭代开发记录

迭代编号：`迭代143`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 placeholder marker 配置引入独立 JSON Schema 契约。
2. 让 marker 校验脚本同时校验“schema 自身合法性 + payload 符合 schema”。

## 2. 计划范围（Plan）

1. 先新增失败测试，定义 schema 文件存在与脚本 schema 校验行为。
2. 新增 schema 文件并改造 marker 校验脚本支持 `--schema-file`。
3. 同步文档与版本，完成全量验证。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败约束：
     - marker schema 文件必须存在并包含核心契约字段
     - marker 校验脚本在 payload schema 违例时失败
     - marker 校验脚本在 schema 文件非法时失败
2. TDD Green：
   - 新增 schema：
     - `refactor/backend/config/schemas/validator-placeholder-markers.schema.json`
   - 改造脚本：
     - `refactor/backend/scripts/validate-validator-placeholder-markers.py`
     - 新增 `--schema-file`
     - 使用 `Draft202012Validator.check_schema` 校验 schema
     - 使用 `Draft202012Validator(schema).validate(payload)` 校验配置
3. 文档与版本：
   - `refactor/backend/README.md` 增加 marker schema 路径与自定义 schema 参数说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.128-m3-marker-schema-validation`。
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.128-m3-marker-schema-validation`。

## 4. 未完成项（Not Done）

1. schema 目前只覆盖基础结构约束，未表达“大小写归一后唯一”等语义规则。
2. marker 校验脚本暂未支持结构化 `--json-errors` 输出。

## 5. 代码与文档变更

1. 配置/Schema：
   - `refactor/backend/config/schemas/validator-placeholder-markers.schema.json`
2. 脚本：
   - `refactor/backend/scripts/validate-validator-placeholder-markers.py`
3. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
4. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代143-M3-marker配置Schema校验.md`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "markers_schema_exists or schema_violation or invalid_schema_file" -q`
   - 结果：预期失败（schema 文件和 schema 校验能力未实现）。
2. Green 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "markers_schema_exists or schema_violation or invalid_schema_file" -q`
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "placeholder_markers_validator_script or strict_descriptions" -q`
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
   - 结果：全部通过。
3. 是否达到验收标准：
   - 达到（marker 配置具备 schema 契约与自动校验能力）。

## 7. 风险与问题

1. 风险描述：schema 与脚本校验规则可能出现重复维护。
2. 影响范围：marker 治理逻辑的一致性。
3. 缓解措施：后续将脚本规则尽量下沉为 schema 规则并在 CI 增加 drift 检查。

## 8. 关键决策

1. 决策内容：引入独立 schema 文件并通过脚本内统一执行校验。
2. 决策原因：契约可读性更高，便于后续扩展和外部复用。
3. 影响模块：marker 配置治理、CI 质量门禁。

## 9. 下迭代计划

1. 为 marker 校验脚本增加 `--json-errors` 结构化错误输出。
2. 将 marker 语义规则（如大小写归一唯一）逐步迁移到 schema + 自定义关键字方案。
3. 推进错误码目录结构化字段（severity/remediation）的 schema 化校验。
