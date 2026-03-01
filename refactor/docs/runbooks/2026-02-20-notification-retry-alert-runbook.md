# Notification Retry Alert Runbook

## 1. Scope

This runbook is for notification retry governance alerts.

Applicable alerts:
- `RefactorNotificationRetrySuccessRatioWarn`
- `RefactorNotificationRetrySuccessRatioCritical`
- `RefactorNotificationAutoRetryFinalFailureRatioWarn`
- `RefactorNotificationAutoRetryFinalFailureRatioCritical`

Related metrics:
- `refactor_notification_retry_attempts_total`
- `refactor_notification_retry_success_total`
- `refactor_notification_retry_failed_total`
- `refactor_notification_retry_success_ratio`
- `refactor_notification_auto_retry_deliveries_total`
- `refactor_notification_auto_retry_final_failed_total`
- `refactor_notification_auto_retry_final_failure_ratio`
- `refactor_notification_deliveries_total{status=...}`
- `refactor_notification_deliveries_by_channel_total{channel=...}`

## 2. Trigger Semantics

<!-- notification-retry-thresholds:start -->
Prod baseline:
- retry success ratio warn: attempts `>= 10` and success ratio `< 0.6` for `15m`
- retry success ratio critical: attempts `>= 10` and success ratio `< 0.4` for `5m`
- auto-retry final failure ratio warn: deliveries `>= 10` and final failure ratio `>= 0.3` for `15m`
- auto-retry final failure ratio critical: deliveries `>= 10` and final failure ratio `>= 0.5` for `5m`

Profile baseline matrix:

| profile | signal | sample gate | threshold | duration |
| --- | --- | --- | --- | --- |
| dev | retry success ratio warn | attempts >= 10 | success ratio < 0.7 | 5m |
| dev | retry success ratio critical | attempts >= 10 | success ratio < 0.5 | 2m |
| dev | auto-retry final failure ratio warn | deliveries >= 10 | final failure ratio >= 0.25 | 5m |
| dev | auto-retry final failure ratio critical | deliveries >= 10 | final failure ratio >= 0.4 | 2m |
| staging | retry success ratio warn | attempts >= 10 | success ratio < 0.65 | 10m |
| staging | retry success ratio critical | attempts >= 10 | success ratio < 0.45 | 5m |
| staging | auto-retry final failure ratio warn | deliveries >= 10 | final failure ratio >= 0.28 | 10m |
| staging | auto-retry final failure ratio critical | deliveries >= 10 | final failure ratio >= 0.45 | 5m |
| prod | retry success ratio warn | attempts >= 10 | success ratio < 0.6 | 15m |
| prod | retry success ratio critical | attempts >= 10 | success ratio < 0.4 | 5m |
| prod | auto-retry final failure ratio warn | deliveries >= 10 | final failure ratio >= 0.3 | 15m |
| prod | auto-retry final failure ratio critical | deliveries >= 10 | final failure ratio >= 0.5 | 5m |
<!-- notification-retry-thresholds:end -->

Interpretation:
- low retry success ratio means manual retry recovery is ineffective.
- high auto-retry final failure ratio means automatic retries cannot recover channel delivery.

## 3. First Response Checklist

1. Confirm alert level, active duration, and affected environment in Alertmanager.
2. Confirm if issue is channel-specific by checking `refactor_notification_deliveries_by_channel_total`.
3. Confirm release/rollout window and recent config changes:
   - `NOTIFICATION_SEND_MAX_RETRIES`
   - `NOTIFICATION_RETRY_BACKOFF_MS`
4. Confirm whether external provider incidents exist (Feishu/WeChat/Telegram/Email, etc).

## 4. Diagnosis Steps

### 4.1 PromQL quick checks

```promql
refactor_notification_retry_attempts_total
```

```promql
refactor_notification_retry_success_ratio
```

```promql
refactor_notification_auto_retry_final_failure_ratio
```

```promql
increase(refactor_notification_retry_failed_total[15m])
```

```promql
refactor_notification_deliveries_by_channel_total
```

### 4.2 API checks

List recent failed deliveries:

```bash
curl -s "http://127.0.0.1:18000/api/v2/notifications/deliveries?status=failed&limit=50"
```

Check retry records:

```bash
curl -s "http://127.0.0.1:18000/api/v2/notifications/deliveries?source_type=delivery_retry&limit=50"
```

Try a targeted manual retry:

```bash
curl -s -X POST \
  "http://127.0.0.1:18000/api/v2/notifications/deliveries/<delivery_id>/retry"
```

### 4.3 Database checks (SQLite)

Default DB path when `DATABASE_URL` is not set:
- `refactor/backend/var/refactor.sqlite3`

Recent failed deliveries:

```bash
sqlite3 refactor/backend/var/refactor.sqlite3 "
SELECT created_at, delivery_id, channel, source_type, status, attempt_count, error_code, error_message
FROM notification_deliveries
WHERE status='failed'
ORDER BY created_at DESC
LIMIT 100;
"
```

Recent retry effectiveness:

```bash
sqlite3 refactor/backend/var/refactor.sqlite3 "
SELECT
  COUNT(1) AS retry_attempts_total,
  SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) AS retry_success_total,
  SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS retry_failed_total,
  ROUND(
    CAST(SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) AS REAL)
    / NULLIF(COUNT(1), 0),
    4
  ) AS retry_success_ratio
FROM notification_deliveries
WHERE source_type='delivery_retry';
"
```

## 5. Common Root Causes

1. External provider outage or unstable network path.
2. Channel credentials/webhook expired or rotated without config refresh.
3. Payload rejected by provider side constraints (length/content format).
4. Retry settings are too weak (`max_retries` too low / backoff too short).
5. Channel plugin behavior changed and now returns persistent failure.

## 6. Mitigation Actions

### 6.1 Fast mitigation (stability first)

1. Route critical notifications to healthy channels temporarily (for example `wechat -> feishu` fallback in ops policy).
2. Increase retry capability temporarily:
   - `NOTIFICATION_SEND_MAX_RETRIES`
   - `NOTIFICATION_RETRY_BACKOFF_MS`
3. Trigger manual retries for high-priority failed records.

### 6.2 Permanent fix

1. Fix invalid channel configuration (webhook/token/receiver).
2. Improve channel payload adapter for provider constraints.
3. Add provider-side error classification and `retryable` strategy.
4. Add synthetic channel health probes for early detection.

## 7. Recovery Validation

1. `refactor_notification_retry_success_ratio >= 0.6` and stable for 30 minutes.
2. `refactor_notification_auto_retry_final_failure_ratio < 0.3` and trending down.
3. `increase(refactor_notification_retry_failed_total[30m])` returns to baseline.
4. New failed delivery records stop growing abnormally.

## 8. Rollback Plan

1. Revert recent notification plugin/config rollout.
2. Restore previous known-good channel credentials.
3. Reduce automated retry pressure if provider rate limits are hit.
4. Keep alerts muted only during approved maintenance window.

## 9. Postmortem Template

1. Incident window (start/end UTC).
2. Affected channels and user impact scope.
3. Primary root cause and contributing factors.
4. Why existing retry strategy did not absorb failures.
5. Immediate mitigation and permanent fix items.
6. Follow-up actions with owner and due date.

## 10. References

1. Metrics endpoint: `GET /api/v2/metrics`
2. Notification APIs:
   - `GET /api/v2/notifications/deliveries`
   - `POST /api/v2/notifications/deliveries/{delivery_id}/retry`
3. Rule templates:
   - `refactor/backend/config/notification-retry-alert-thresholds.json`
   - `refactor/backend/scripts/sync-notification-retry-alert-thresholds.py`
   - `refactor/backend/monitoring/alertmanager/refactor-alertmanager-routing.yml`
   - `refactor/backend/scripts/validate-alertmanager-route-consistency.py`
   - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.yml`
   - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.dev.yml`
   - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.staging.yml`
   - `refactor/backend/monitoring/prometheus/rules/refactor-notification-retry-alerts.prod.yml`
4. Notification implementation:
   - `refactor/backend/src/app/services/notification_service.py`
   - `refactor/backend/src/app/api/routes/metrics.py`
