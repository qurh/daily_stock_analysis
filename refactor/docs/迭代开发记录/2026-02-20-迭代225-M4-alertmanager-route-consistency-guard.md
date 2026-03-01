# 迭代开发记录

迭代编号：`迭代225`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 增加 Prometheus 告警规则与 Alertmanager 路由/receiver 的一致性自动校验。
2. 将一致性校验接入后端 CI，避免“有告警无路由/无接收器”。

## 2. 计划范围（Plan）

1. 先按 TDD 增加校验脚本测试并跑 RED。
2. 新增 Alertmanager 路由配置模板。
3. 实现 `validate-alertmanager-route-consistency.py`。
4. 接入 `scripts/ci.sh` 并同步 README/CHANGELOG/版本号。

## 3. 实际完成（Done）

1. 新增 Alertmanager 路由配置：
   - `refactor/backend/monitoring/alertmanager/refactor-alertmanager-routing.yml`
   - 覆盖当前告警域路由：
     - `scope=notification, domain=retry-governance`
     - `scope=backtest, domain=threshold-governance`
     - `scope=strategy, domain=publish-gate`
     - `scope=promtool, domain=soft-audit`
2. 新增一致性校验脚本：
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - 校验内容：
     - 遍历 `monitoring/prometheus/rules` 所有规则文件；
     - 提取每个告警的 `scope/domain/severity` 标签；
     - 确认至少命中一条显式 Alertmanager 路由；
     - 确认每条路由引用的 receiver 在 `receivers` 列表中存在。
3. 新增单测：
   - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
   - 覆盖：
     - 默认配置校验通过；
     - 删除通知路由匹配条件后校验失败；
     - CI 脚本包含该校验调用。
4. CI 接入：
   - `refactor/backend/scripts/ci.sh` 新增：
     - `python3 scripts/validate-alertmanager-route-consistency.py`
5. 文档与版本：
   - `refactor/backend/README.md` 增加 alertmanager 路由一致性说明；
   - `refactor/docs/runbooks/2026-02-20-notification-retry-alert-runbook.md` 增加路由配置与校验脚本引用；
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.9` 条目；
   - `refactor/backend/src/app/main.py` 版本升级为 `0.4.9-m4-alertmanager-route-consistency-guard`。

## 4. 未完成项（Not Done）

1. 当前仅校验路由可匹配与 receiver 存在，尚未校验按环境 profile 的路由差异策略。
2. 尚未校验 Alertmanager 通知分组、抑制规则与业务优先级一致性。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/monitoring/alertmanager/refactor-alertmanager-routing.yml`
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - `refactor/backend/scripts/ci.sh`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/runbooks/2026-02-20-notification-retry-alert-runbook.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代225-M4-alertmanager-route-consistency-guard.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py`
   - 结果：失败（预期，脚本与配置未实现）。
2. GREEN：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py`
   - 结果：通过。
3. 回归：
   - `cd refactor/backend && python3 -m flake8 scripts/validate-alertmanager-route-consistency.py tests/unit/test_alertmanager_route_consistency.py --max-line-length=120`
   - `cd refactor/backend && python3 -m py_compile scripts/validate-alertmanager-route-consistency.py`
   - `cd refactor/backend && python3 scripts/validate-alertmanager-route-consistency.py`
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py tests/unit/test_notification_retry_alert_threshold_sync.py tests/unit/test_notification_retry_runbook_validator.py tests/unit/test_notification_retry_alert_rules_template.py`
   - `cd refactor/backend && python3 scripts/validate-summary-contract-changelog.py`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：校验脚本目前仅支持 `match` 与 `matchers` 的精确匹配语法（`key=\"value\"`）。
2. 缓解措施：若后续引入正则 matcher（`=~`），同步扩展解析器并补单测。

## 8. 关键决策

1. 决策内容：先用轻量静态校验保证“路由存在 + receiver 存在”两条最关键链路。
2. 决策原因：实现成本低，能快速纳入 CI 门禁并显著降低漏配风险。
3. 影响模块：Prometheus 告警治理、Alertmanager 配置管理、CI 质量门禁。

## 9. 下迭代计划

1. 扩展为 profile 级路由模板与一致性校验。
2. 增加路由优先级冲突与覆盖范围冲突检测。
