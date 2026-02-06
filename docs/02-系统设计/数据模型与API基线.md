# 数据模型与 API 基线

## 1. 已实现 API（2026-02-06）

- `GET /stocks`
- `POST /stocks/sync`
- `GET /watchlists`
- `POST /watchlists`
- `PUT /watchlists/{watchlist_id}`
- `DELETE /watchlists/{watchlist_id}`
- `POST /watchlists/{watchlist_id}/stocks`
- `DELETE /watchlists/{watchlist_id}/stocks/{code}`
- `GET /stock/{code}/reports`
- `GET /reports`
- `GET /reports/{report_id}`

## 2. 待实现 API

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /market/list`
- `GET /stock/{code}/detail`
- `POST /stock/{code}/analyze`

## 3. 已实现数据模型

- `stocks`
- `watchlists`
- `watchlist_stocks`
- `analysis_reports`

## 4. 待补齐数据模型

- `users`
- `refresh_tokens`
- `stock_quotes`（分钟级）
- `stock_daily` 在新 API 数据层中的复用策略

## 5. 差距矩阵（设计 vs 实现）

| 项目 | 设计要求 | 当前状态 | 优先级 |
|---|---|---|---|
| 鉴权 | JWT + 刷新轮换 | 未实现 | P0 |
| 用户隔离 | 资源需按用户归属校验 | 部分固定 user_id=1 | P0 |
| 报告访问安全 | 路径受控 + 权限校验 | 待加固 | P0 |
| 行情与详情 | `/market/list`、`/stock/{code}/detail` | 未实现 | P0 |
| 分析生成 | `/stock/{code}/analyze` | 未实现 | P0 |

## 6. 安全基线提醒

当前报告读取尚未完成用户归属校验，属于必须补齐项。
