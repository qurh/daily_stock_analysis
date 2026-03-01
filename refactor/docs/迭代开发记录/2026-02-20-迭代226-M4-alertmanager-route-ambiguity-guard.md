# 迭代开发记录

迭代编号：`迭代226`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 Alertmanager 路由一致性校验补充“路由歧义”防护。
2. 防止单个告警命中多条显式路由导致接收链路不确定。

## 2. 计划范围（Plan）

1. TDD 先新增“多路由命中失败”测试并跑 RED。
2. 扩展 `validate-alertmanager-route-consistency.py`，在多路由命中时失败。
3. 同步 README、CHANGELOG、版本号。

## 3. 实际完成（Done）

1. 新增测试覆盖：
   - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
   - 新增用例：构造 `scope="notification"` 宽匹配路由，验证同一告警命中多条显式路由时失败。
2. 脚本能力增强：
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - 新增校验：
     - 告警未命中显式路由 -> 失败；
     - 告警命中多条显式路由 -> 失败（报错包含路由路径与 receiver）。
3. 文档与版本同步：
   - `refactor/backend/README.md` 增加 route ambiguity guardrails 说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.10` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为 `0.4.10-m4-alertmanager-route-ambiguity-guard`。

## 4. 未完成项（Not Done）

1. 尚未实现路由优先级冲突（顺序覆盖）静态分析报告。
2. 尚未支持 `=~` / `!~` 等正则 matcher 语法解析。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_alertmanager_route_consistency.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代226-M4-alertmanager-route-ambiguity-guard.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py`
   - 结果：失败（预期，原脚本允许多路由命中）。
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

1. 风险描述：告警路由策略若后续有意“多路由广播”，当前规则会将其判定为失败。
2. 缓解措施：未来可增加白名单或策略开关支持有意多路由场景。

## 8. 关键决策

1. 决策内容：当前阶段采用“每个告警仅命中一条显式路由”的严格约束。
2. 决策原因：保证告警投递路径单一可追踪，降低运维排障复杂度。
3. 影响模块：Alertmanager 路由治理、CI 配置门禁。

## 9. 下迭代计划

1. 增加 route 顺序覆盖与优先级冲突检测。
2. 扩展 matcher 语法支持（`=~`/`!~`）并补充测试矩阵。
