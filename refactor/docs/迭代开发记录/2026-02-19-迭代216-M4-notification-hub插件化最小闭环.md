# 迭代开发记录

迭代编号：`迭代216`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 进入 M4，落地通知中心插件化最小闭环。
2. 提供通知能力的统一 API（渠道列表、预览、发送、渠道测试）。
3. 保持与现有 `.env` 通知配置项兼容，为后续扩展保留接口边界。

## 2. 计划范围（Plan）

1. 按 TDD 补通知中心与通知 API 的失败测试。
2. 实现 `NotificationHub + ChannelPlugin` 插件化服务。
3. 接入 FastAPI 路由、依赖注入、应用启动注入。
4. 同步 README/OpenAPI/CHANGELOG 与迭代文档。

## 3. 实际完成（Done）

1. 新增通知服务模块：
   - `refactor/backend/src/app/services/notification_service.py`
   - 核心能力：
     - `ChannelPlugin` 插件接口
     - `NotificationMessage` 消息模型
     - `NotificationFormatter` 渲染与字节截断
     - `NotificationHub`（`list_channels/preview/send/test_channel`）
2. 内置渠道插件（配置驱动）：
   - `wechat`、`feishu`、`telegram`、`email`、`pushover`、`pushplus`、`serverchan3`、`custom`、`discord`、`astrbot`
3. 新增通知 API：
   - `GET /api/v2/notifications/channels`
   - `POST /api/v2/notifications/preview`
   - `POST /api/v2/notifications/send`
   - `POST /api/v2/notifications/channels/test`
4. 应用接线完成：
   - `deps/router/main` 注入与路由挂载完成
5. 错误码扩展：
   - `NTF-CHANNEL-001`
   - `NTF-FORMAT-002`
   - `NTF-SEND-003`
   - `NTF-RETRY-004`
6. 契约与文档同步：
   - `refactor/backend/README.md`
   - `refactor/docs/07-OpenAPI-v2-接口草案.yaml`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/backend/.env.example`
7. 版本升级：
   - `refactor/backend/src/app/main.py` -> `0.4.0-m4-notification-hub-min-loop`

## 4. 未完成项（Not Done）

1. 尚未将通知中心接入“分析任务完成后自动推送”的主业务触发链路。
2. 尚未实现通知投递记录持久化与审计查询接口。
3. 尚未实现渠道级重试策略与退避参数配置化（当前为最小可用实现）。
4. 尚未完成前端通知治理页面联调（M4 后续迭代）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/services/notification_service.py`
   - `refactor/backend/src/app/api/routes/notifications.py`
   - `refactor/backend/src/app/api/deps.py`
   - `refactor/backend/src/app/api/router.py`
   - `refactor/backend/src/app/main.py`
   - `refactor/backend/src/app/shared/error_codes.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_notification_hub.py`
   - `refactor/backend/tests/unit/test_error_codes.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/backend/.env.example`
   - `refactor/docs/07-OpenAPI-v2-接口草案.yaml`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/plans/2026-02-19-m4-notification-hub-pluginization.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代216-M4-notification-hub插件化最小闭环.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_hub.py tests/unit/test_error_codes.py`
   - 结果：失败（预期，缺少 `app.services.notification_service`）。
2. GREEN（定向）：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_notification_hub.py tests/unit/test_error_codes.py`
   - 结果：通过。
3. 相关回归：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_feedback_optimization_service.py tests/unit/test_strategy_service.py tests/unit/test_settings_env_names.py tests/unit/test_health.py`
   - 结果：通过。
4. 全量单测与语法：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit`
   - `cd refactor/backend && python3 -m compileall -q src`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：部分第三方通知渠道接口未做深度参数适配（当前按最小 payload 统一发送）。
2. 影响范围：渠道特定高级特性（格式方言、富媒体、线程回复）可能与旧实现存在差异。
3. 缓解措施：在 M4 后续迭代按渠道补齐格式策略与回归用例。

## 8. 关键决策

1. 决策内容：M4 第一批采用“插件接口 + 配置启停 + 聚合结果”最小闭环，先打通平台能力。
2. 决策原因：优先满足可扩展与可联调能力，再补高阶治理能力。
3. 影响模块：Notification、API Gateway、文档契约。

## 9. 下迭代计划

1. 将通知中心接入分析/回测/策略关键事件触发链路。
2. 增加 `DeliveryRecord` 持久化、查询和审计字段。
3. 增加渠道级重试与降级策略，并补监控指标导出。
4. 与前端页面进行通知配置与联调验证。
