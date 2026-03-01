# 迭代开发记录

迭代编号：`迭代217`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 在通知中心落地渠道级重试能力，补齐失败投递恢复闭环。
2. 提供失败投递的手动重试 API，支持从投递记录直接恢复发送。
3. 为投递审计补齐重试相关字段，并保持旧 SQLite 文件可平滑升级。

## 2. 计划范围（Plan）

1. 按 TDD 新增“自动重试成功”和“手动重试 API”失败测试。
2. 扩展 `NotificationHub` 重试策略与持久化字段。
3. 新增 `POST /api/v2/notifications/deliveries/{delivery_id}/retry`。
4. 同步 README / OpenAPI / CHANGELOG / `.env.example`。

## 3. 实际完成（Done）

1. 通知发送重试能力：
   - `NotificationHub` 新增 `max_retries`、`retry_backoff_ms` 配置。
   - 对单渠道发送增加重试循环与可选线性退避。
   - 发送结果增加 `attempt_count`、`retry_count`，汇总增加 `retried`。
2. 手动重试 API：
   - 新增路由 `POST /api/v2/notifications/deliveries/{delivery_id}/retry`。
   - 支持基于历史 `delivery_id` 重试并建立重试关联。
3. 投递记录持久化增强：
   - `notification_deliveries` 增加字段：
     - `attempt_count`
     - `retry_of_delivery_id`
   - `GET /api/v2/notifications/deliveries` 返回新增字段，并补充 `display_name`。
4. 向后兼容与并发幂等：
   - `SQLiteDatabase.init_schema()` 增加列存在性补齐。
   - 对并发 `ALTER TABLE` 竞争导致的重复列错误做幂等兜底。
5. 配置与接线：
   - 新增配置项：
     - `NOTIFICATION_SEND_MAX_RETRIES`
     - `NOTIFICATION_RETRY_BACKOFF_MS`
   - 应用启动注入到 `NotificationHub`。
6. 版本升级：
   - `refactor/backend/src/app/main.py` -> `0.4.2-m4-notification-retry-loop`。

## 4. 未完成项（Not Done）

1. 渠道级“错误分类重试策略”（按错误码决定是否重试）尚未细化。
2. 重试链路的专用监控指标（例如重试成功率）尚未接入 `/api/v2/metrics`。
3. 通知中心前端治理页面仍待联调（M4 后续）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/notification_service.py`
   - `refactor/backend/src/app/api/routes/notifications.py`
   - `refactor/backend/src/app/persistence/sqlite_db.py`
   - `refactor/backend/src/app/core/settings.py`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_notification_hub.py`
   - `refactor/backend/tests/unit/test_settings_env_names.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/backend/.env.example`
   - `refactor/docs/07-OpenAPI-v2-接口草案.yaml`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代217-M4-notification-retry-loop与手动重试.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_hub.py -k "retries_before_success or retry_delivery_endpoint"`
   - 结果：失败（预期，`NotificationHub` 尚不支持 `max_retries`）。
2. GREEN（定向）：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_hub.py -k "retries_before_success or retry_delivery_endpoint"`
   - 结果：通过。
3. 相关回归：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_hub.py tests/unit/test_settings_env_names.py`
   - 结果：通过。
4. 全量单测：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：当前重试判定策略基于“非 delivered 即重试”，未做渠道细粒度错误语义识别。
2. 影响范围：部分不可重试错误仍可能发生重复尝试，增加外部接口调用成本。
3. 缓解措施：后续在插件返回中标准化 `retryable` 标记，并引入错误类型映射。

## 8. 关键决策

1. 决策内容：优先落地统一重试机制与审计字段，再逐渠道细化错误分类策略。
2. 决策原因：先保证闭环可用和可追踪，降低 M4 联调阻塞。
3. 影响模块：NotificationHub、Persistence、API 契约、配置中心。

## 9. 下迭代计划

1. 为重试链路增加指标与告警（重试成功率、最终失败率）。
2. 增加按渠道/错误类型的重试策略配置。
3. 评估将通知失败事件接入优化任务触发，形成更完整的治理闭环。
