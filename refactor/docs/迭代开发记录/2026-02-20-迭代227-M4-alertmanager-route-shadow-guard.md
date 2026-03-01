# 迭代开发记录

迭代编号：`迭代227`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 Alertmanager 路由一致性校验新增“静态 shadow route”检测。
2. 在无实际告警命中的情况下，也提前识别后序路由被前序路由遮蔽的问题。

## 2. 计划范围（Plan）

1. 按 TDD 增加失败用例：后序 sibling route 被前序 non-continue route 覆盖。
2. 扩展 `validate-alertmanager-route-consistency.py` 路由树分析逻辑。
3. 同步 README、CHANGELOG、版本与迭代文档。

## 3. 实际完成（Done）

1. 新增测试：
   - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
   - 新增用例：
     - 注入 `scope=\"ghost\"` 与 `scope=\"ghost\", domain=\"ghost-domain\"` 两条 sibling 路由；
     - 即便当前无告警命中 `ghost`，也应触发 `shadowed route` 校验失败。
2. 脚本增强：
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - 新增能力：
     - 路由节点记录 `parent_path` 与 `continue`；
     - sibling 级别静态遮蔽检测：
       - 前序 route matcher 为后序 route matcher 子集，且前序 `continue=false`；
       - 后序 route 视为 shadowed 并失败。
3. 文档与版本：
   - `refactor/backend/README.md` 新增 shadow guard 说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.11` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为 `0.4.11-m4-alertmanager-route-shadow-guard`。

## 4. 未完成项（Not Done）

1. 尚未支持正则 matcher（`=~`, `!~`）的 shadow 检测。
2. 尚未支持“允许多路由广播”的显式白名单策略。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代227-M4-alertmanager-route-shadow-guard.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py`
   - 结果：失败（预期，新增 shadow 检测用例不通过）。
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

1. 风险描述：若后续业务确实需要“前序宽匹配 + 后序细分补充并 continue”，需显式设置 `continue=true` 才能通过。
2. 缓解措施：在 route 配置评审中明确 `continue` 使用规范，并补充示例模板。

## 8. 关键决策

1. 决策内容：shadow 检测在“无告警命中”场景也强制失败。
2. 决策原因：提前暴露潜在配置缺陷，避免后续新增告警时落入隐式路由陷阱。
3. 影响模块：Alertmanager 路由治理、CI 配置门禁。

## 9. 下迭代计划

1. 扩展 matcher 语法（`=~`, `!~`）解析与 shadow 检测。
2. 增加 route 顺序覆盖报告（warning）与 fail-fast 配置开关。
