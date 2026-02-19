# 迭代开发记录

迭代编号：`迭代128`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 防止 summary schema 版本与同步脚本版本出现漂移。
2. 将版本一致性校验纳入现有 schema validator。

## 2. 计划范围（Plan）

1. 先补失败测试定义版本漂移场景。
2. 增强 schema validator，增加跨文件版本一致性校验。
3. 同步 README / CHANGELOG / 版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败场景：schema `schema_version.const` 与 sync 脚本版本不一致时必须失败。
2. TDD Green：
   - `refactor/backend/scripts/validate-strict-gate-summary-schema.py`
   - 新增校验逻辑：
     - 读取 schema 中 `properties.schema_version.const`
     - 解析 `sync-strict-gate-alert-thresholds.py` 中 `SUMMARY_SCHEMA_VERSION`
     - 两者不一致时报错 `schema_version mismatch`
   - 新增参数：
     - `--sync-script-file`（默认指向 `sync-strict-gate-alert-thresholds.py`）
3. 文档与版本：
   - `refactor/backend/README.md` 补充版本一致性校验说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.113-m3-summary-schema-version-drift-guard`。
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.113-m3-summary-schema-version-drift-guard`。

## 4. 未完成项（Not Done）

1. 暂未对 `schema_version` 升级流程做自动化迁移检查。
2. 暂未强制 changelog 条目与 schema_version 升级绑定。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-strict-gate-summary-schema.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代128-M3-summary-schema版本防漂移.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "schema_version_mismatch" -q`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - 漂移场景用例通过（不一致时正确失败）
   - 后端全量 CI 通过
3. 是否达到验收标准：
   - 达到（已具备跨文件版本一致性防护）

## 7. 风险与问题

1. 风险描述：版本解析依赖 sync 脚本常量命名约定。
2. 影响范围：若常量名重构，校验脚本会失败。
3. 缓解措施：保持常量命名稳定，重构时同步更新校验脚本与测试。

## 8. 关键决策

1. 决策内容：版本一致性在 schema validator 阶段强校验，而非运行时宽容处理。
2. 决策原因：尽早暴露契约漂移，降低后续兼容风险。
3. 影响模块：CI 稳定性与摘要契约演进流程。

## 9. 下迭代计划

1. 增加“schema_version 变更必须伴随 changelog 新条目”的自动检查。
2. 增加 summary payload golden sample 机制。
3. 评估将校验结果输出为 CI artifact。
