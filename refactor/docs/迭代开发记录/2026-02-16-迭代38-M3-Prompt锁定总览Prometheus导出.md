# 迭代开发记录

迭代编号：`迭代38`  
日期：`2026-02-16`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将 Prompt Lock overview 观测指标导出为 Prometheus 文本格式。
2. 提供可直接被监控系统抓取的标准化接口。
3. 维持无额外依赖的最小实现。

## 2. 计划范围（Plan）

1. 在 `PromptLockAuditService` 增加 Prometheus 文本导出方法。
2. 新增 `/api/v2/prompt-lock/overview/metrics/prometheus` 路由。
3. 增加服务层与路由层测试。
4. 同步 README、CHANGELOG 与迭代记录。

## 3. 实际完成（Done）

1. 服务层改造：
   - 新增 `get_overview_metrics_prometheus()` 方法
   - 输出 Prometheus 文本格式指标（counter/gauge）
2. 指标导出范围：
   - 全局：
     - request/degraded/cache-hit counters
     - degraded/cache-hit rates gauges
   - 模块（`summary/grouped/trends`）：
     - run/success/timeout/exception/degraded counters
     - timeout/error/degraded rates gauges
3. 新增路由：
   - `GET /api/v2/prompt-lock/overview/metrics/prometheus`
   - 返回 `text/plain; version=0.0.4; charset=utf-8`
4. 新增并通过测试：
   - `test_prompt_lock_overview_metrics_prometheus_text_contains_expected_series`
   - `test_prompt_lock_overview_metrics_prometheus_endpoint_returns_text`
5. 应用版本升级：
   - `0.3.23-m3-prompt-lock-overview-prometheus-export`

## 4. 未完成项（Not Done）

1. 暂未暴露全局 `/metrics` 聚合端点（当前聚焦 Prompt Lock 子域）。
2. 暂未接入 OpenTelemetry 指标 SDK。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/prompt_lock_audit_service.py`
   - `refactor/backend/src/app/api/routes/prompt_lock.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_prompt_lock_audit.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-16-迭代38-M3-Prompt锁定总览Prometheus导出.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest -q tests/unit/test_prompt_lock_audit.py -k "metrics_prometheus_text_contains_expected_series or metrics_prometheus_endpoint_returns_text"`
   - `cd refactor/backend && pytest tests/unit --maxfail=1`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - Prometheus 定向测试：通过
   - 全量单测：通过
   - CI：通过
3. 是否达到验收标准：
   - 达到（Prometheus 文本导出能力可用）

## 7. 风险与问题

1. 风险描述：当前导出是进程内计数，重启会清零。
2. 影响范围：长期监控需依赖外部抓取与存储系统。
3. 缓解措施：后续结合 Prometheus 持久化存储与告警规则。

## 8. 关键决策

1. 决策内容：先做子域级 Prometheus 导出，不引入新依赖包。
2. 决策原因：保持 MVP 节奏与实现简洁，快速提供可抓取指标。
3. 影响模块：Prompt Lock overview 治理与监控链路。

## 9. 下迭代计划

1. 评估统一 `/metrics` 聚合端点方案。
2. 增加关键指标阈值告警建议（降级率/超时率）。
3. 规划 OpenTelemetry 指标与 tracing 一体化接入。
