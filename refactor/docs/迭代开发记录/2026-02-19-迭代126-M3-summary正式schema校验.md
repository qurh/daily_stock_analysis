# 迭代开发记录

迭代编号：`迭代126`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 strict gate 摘要 JSON 建立正式 schema 文件。
2. 将 schema 校验纳入自动化测试，避免摘要字段无声漂移。

## 2. 计划范围（Plan）

1. 先补失败测试，要求摘要输出满足 schema。
2. 新增 schema 文件并声明测试依赖。
3. 同步 README / CHANGELOG / 版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_strict_gate_alert_threshold_sync.py`
   - 新增失败场景：`--summary-format json` 输出必须通过 schema 校验。
2. TDD Green：
   - 新增 schema 文件：
     - `refactor/backend/config/schemas/strict-gate-summary.schema.json`
   - 覆盖字段：
     - `schema_version`
     - 汇总行计数
     - `files[]` 每文件摘要
     - `modules` 模块计数（strict/governance/soft_audit）
   - 新增依赖声明：
     - `refactor/backend/pyproject.toml`（dev）
     - `refactor/backend/requirements-dev.txt`
     - 增加 `jsonschema>=4.21.0`
3. 文档与版本：
   - `refactor/backend/README.md` 增加 schema 路径说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.111-m3-summary-json-schema-validation`。
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.111-m3-summary-json-schema-validation`。

## 4. 未完成项（Not Done）

1. 暂未把 schema 校验提升到脚本运行时（目前在测试层校验）。
2. 暂未对 schema 文件做独立 lint/format 规则。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/config/schemas/strict-gate-summary.schema.json`
   - `refactor/backend/src/app/main.py`
   - `refactor/backend/pyproject.toml`
   - `refactor/backend/requirements-dev.txt`
2. 测试路径：
   - `refactor/backend/tests/unit/test_strict_gate_alert_threshold_sync.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代126-M3-summary正式schema校验.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_strict_gate_alert_threshold_sync.py -k "summary_json_matches_schema" -q`
   - `cd refactor/backend && pytest tests/unit/test_strict_gate_alert_threshold_sync.py -q`
2. 结果摘要：
   - schema 校验新增用例通过
   - 阈值同步单测集全部通过
3. 是否达到验收标准：
   - 达到（摘要输出具备正式 schema 契约并有自动化校验）

## 7. 风险与问题

1. 风险描述：schema 变更若未同步版本升级，可能导致下游解析歧义。
2. 影响范围：CI 产物消费者、告警审计脚本。
3. 缓解措施：后续将 schema 版本策略固化到发布流程检查项。

## 8. 关键决策

1. 决策内容：先在测试层执行 schema 校验，不在脚本运行时强制。
2. 决策原因：避免在线路径额外依赖和性能开销。
3. 影响模块：测试稳定性提升，运行时行为保持不变。

## 9. 下迭代计划

1. 在 CI 中增加 schema 文件完整性与 `$schema` 规范性检查。
2. 增加“schema 版本变更必须同步 changelog”的自动检查。
3. 评估提供 `--summary-schema-check` 可选运行时校验开关。
