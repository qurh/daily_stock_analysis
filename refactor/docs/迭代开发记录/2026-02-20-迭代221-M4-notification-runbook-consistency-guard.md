# 迭代开发记录

迭代编号：`迭代221`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为通知重试告警 runbook 增加自动一致性校验，防止规则与文档漂移。
2. 将该校验接入后端 CI 脚本形成默认门禁。

## 2. 计划范围（Plan）

1. 先按 TDD 增加校验脚本测试并跑 RED。
2. 实现 `validate-notification-retry-runbook.py`。
3. 在 `scripts/ci.sh` 接入校验脚本并补测试覆盖。
4. 同步 README、CHANGELOG 与迭代文档。

## 3. 实际完成（Done）

1. 新增校验脚本：
   - `refactor/backend/scripts/validate-notification-retry-runbook.py`
   - 功能：对比以下两者的 prod 基线阈值与持续时间是否一致：
     - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.yml`
     - `refactor/docs/runbooks/2026-02-20-notification-retry-alert-runbook.md`
2. 新增单测：
   - `refactor/backend/tests/unit/test_notification_retry_runbook_validator.py`
   - 覆盖：
     - 默认文件校验通过
     - runbook 阈值漂移触发失败
     - CI 脚本包含该校验调用
3. CI 接入：
   - `refactor/backend/scripts/ci.sh` 新增 `validate-notification-retry-runbook.py` 调用。
4. 文档同步：
   - `refactor/backend/README.md` 增加 runbook/rule consistency guard 使用说明。
5. 版本升级：
   - `refactor/backend/src/app/main.py` -> `0.4.5-m4-notification-runbook-consistency-guard`。

## 4. 未完成项（Not Done）

1. 目前只校验 default（prod baseline），尚未覆盖 dev/staging/prod 全 profile 逐项比对。
2. 尚未统一到现有“阈值同步脚本”框架。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-notification-retry-runbook.py`
   - `refactor/backend/scripts/ci.sh`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_notification_retry_runbook_validator.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代221-M4-notification-runbook-consistency-guard.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_retry_runbook_validator.py`
   - 结果：失败（预期，脚本不存在）。
2. GREEN（校验脚本）：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_retry_runbook_validator.py`
   - 结果：通过。
3. 全量回归：
   - `cd refactor/backend && python3 scripts/validate-summary-contract-changelog.py`
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：runbook 文案格式若后续调整，可能导致解析规则失效。
2. 缓解措施：保持 runbook “Prod baseline”段落模板稳定；必要时更新解析规则与测试。

## 8. 关键决策

1. 决策内容：先做 lightweight 文本解析校验，优先解决漂移问题。
2. 决策原因：实现成本低、可快速上线并纳入 CI。
3. 影响模块：通知告警治理、runbook 维护流程、CI 质量门禁。

## 9. 下迭代计划

1. 扩展为多 profile（dev/staging/prod）一致性校验。
2. 评估统一迁移到阈值配置中心与同步脚本。
