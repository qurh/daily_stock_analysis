# 迭代开发记录

迭代编号：`迭代218`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为通知重试闭环补齐可观测性，支持用指标直接观察重试质量。
2. 在 `/api/v2/metrics` 中输出通知投递状态、渠道分布、重试成功率和最终失败率。

## 2. 计划范围（Plan）

1. 按 TDD 新增全局 metrics 用例，先验证通知指标缺失（RED）。
2. 实现通知投递聚合快照与 Prometheus 指标输出（GREEN）。
3. 同步 README、CHANGELOG 与迭代记录。

## 3. 实际完成（Done）

1. 指标聚合实现：
   - 新增 `_load_notification_delivery_snapshot()`，从 `notification_deliveries` 聚合：
     - 状态分布
     - 渠道分布
     - 手动重试尝试数/成功数/失败数
     - 自动重试样本数/最终失败数
     - 手动重试成功率、自动重试最终失败率
2. 全局指标输出接入：
   - `refactor_notification_deliveries_total{status=...}`
   - `refactor_notification_deliveries_by_channel_total{channel=...}`
   - `refactor_notification_retry_attempts_total`
   - `refactor_notification_retry_success_total`
   - `refactor_notification_retry_failed_total`
   - `refactor_notification_retry_success_ratio`
   - `refactor_notification_auto_retry_deliveries_total`
   - `refactor_notification_auto_retry_final_failed_total`
   - `refactor_notification_auto_retry_final_failure_ratio`
3. 测试新增：
   - `test_global_metrics_endpoint_includes_notification_retry_metrics`
4. 版本升级：
   - 后端版本更新为 `0.4.3-m4-notification-retry-metrics`。

## 4. 未完成项（Not Done）

1. 指标告警规则（Prometheus alert rules）尚未新增。
2. 指标看板（Grafana）与前端治理页尚未联动。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/api/routes/metrics.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_prompt_lock_audit.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代218-M4-notification-retry-metrics治理.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_prompt_lock_audit.py -k "notification_retry_metrics"`
   - 结果：失败（预期，指标尚未接入）。
2. GREEN（定向）：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_prompt_lock_audit.py -k "notification_retry_metrics"`
   - 结果：通过。
3. 相关回归：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_prompt_lock_audit.py -k "global_metrics_endpoint_includes"`
   - 结果：通过。
4. 全量回归：
   - `cd refactor/backend && python3 scripts/validate-summary-contract-changelog.py`
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit`
   - `cd refactor/backend && python3 -m compileall -q src`

## 7. 风险与问题

1. 风险描述：指标目前基于 SQLite 在线聚合，数据规模增大后可能增加 `/api/v2/metrics` 查询负担。
2. 缓解措施：后续可引入周期性聚合表或缓存策略。

## 8. 关键决策

1. 决策内容：优先在现有 `/api/v2/metrics` 中补齐通知重试治理指标，不额外引入新采集端点。
2. 决策原因：保持接入成本最低，便于直接复用现有监控链路。
3. 影响模块：Metrics、Notification治理、运维观测。

## 9. 下迭代计划

1. 基于新指标补 Prometheus 告警规则（重试成功率过低、自动重试最终失败率升高）。
2. 将通知重试指标接入前端治理页面与运行手册（runbook）。
