# 迭代开发记录

迭代编号：`迭代125`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为阈值同步 JSON 摘要补充 schema 版本字段。
2. 固化下游解析契约，降低字段演进带来的兼容风险。

## 2. 计划范围（Plan）

1. 先补失败测试，定义 schema 版本字段要求。
2. 在摘要 payload 中添加版本字段。
3. 同步 README / CHANGELOG / 版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_strict_gate_alert_threshold_sync.py`
   - 新增失败场景：JSON 摘要必须包含 `schema_version`。
2. TDD Green：
   - `refactor/backend/scripts/sync-strict-gate-alert-thresholds.py`
   - 新增常量：`SUMMARY_SCHEMA_VERSION = "1"`
   - JSON 摘要新增字段：`schema_version`
3. 文档与版本：
   - `refactor/backend/README.md` 增加 schema 版本说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.110-m3-threshold-summary-schema-version`。
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.110-m3-threshold-summary-schema-version`。

## 4. 未完成项（Not Done）

1. 暂未引入正式 JSON Schema 文件（如 draft-07）。
2. 暂未覆盖 schema 版本升级兼容策略（v1->v2）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/sync-strict-gate-alert-thresholds.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_strict_gate_alert_threshold_sync.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代125-M3-summary-schema版本.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_strict_gate_alert_threshold_sync.py -k "summary_json_includes_schema_version" -q`
   - `cd refactor/backend && pytest tests/unit/test_strict_gate_alert_threshold_sync.py -q`
2. 结果摘要：
   - schema 版本契约测试通过
   - 阈值同步单测集全部通过
3. 是否达到验收标准：
   - 达到（摘要契约具备显式版本标识）

## 7. 风险与问题

1. 风险描述：后续字段升级若未同步提升版本号，仍可能造成静默兼容问题。
2. 影响范围：CI 解析器、告警归因脚本。
3. 缓解措施：后续在 CI 增加 schema_version 与字段集合一致性校验。

## 8. 关键决策

1. 决策内容：当前 schema 版本固定为字符串 `"1"`。
2. 决策原因：先建立版本化机制，再按需演进。
3. 影响模块：阈值同步摘要消费者与契约管理流程。

## 9. 下迭代计划

1. 增加正式 JSON Schema 文档并做自动校验。
2. 为 schema_version 升级设计兼容策略与迁移脚本。
3. 将 schema 契约检查纳入 CI 门禁。
