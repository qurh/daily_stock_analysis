# Strict Gate Alert Runbook

## 1. Scope

This runbook is for strict publish gate alerts related to `STR-GATE-009`.

Applicable alerts:
- `RefactorStrategyPublishStrictGateBlockRatioWarn`
- `RefactorStrategyPublishStrictGateBlockRatioCritical`

Related metrics:
- `refactor_strategy_publish_strict_gate_hits_total`
- `refactor_strategy_publish_strict_gate_blocked_total`
- `refactor_strategy_publish_strict_gate_block_ratio`

## 2. Trigger Semantics

Prod baseline:
- warn: `hits_total >= 10` and `block_ratio >= 0.2` for `15m`
- critical: `hits_total >= 10` and `block_ratio >= 0.5` for `5m`

Interpretation:
- High `hits_total` means strict mode gate is actively evaluated.
- High `block_ratio` means many publish requests are missing `proposal_id`.

## 3. First Response Checklist

1. Confirm alert level and active duration in Alertmanager.
2. Confirm deployment environment and recent release/rollout window.
3. Confirm strict mode switch value:
   - `STRATEGY_PUBLISH_REQUIRE_PROPOSAL_ID`
4. Confirm whether impacted users are concentrated in a specific client version.

## 4. Diagnosis Steps

### 4.1 PromQL quick checks

```promql
refactor_strategy_publish_strict_gate_hits_total
```

```promql
refactor_strategy_publish_strict_gate_blocked_total
```

```promql
refactor_strategy_publish_strict_gate_block_ratio
```

```promql
increase(refactor_strategy_publish_strict_gate_blocked_total[15m])
```

### 4.2 API behavior checks

Use failed publish responses to verify error code:
- expected gate error: `409` + `STR-GATE-009`

### 4.3 Database checks (SQLite)

Default DB path when `DATABASE_URL` is not set:
- `refactor/backend/var/refactor.sqlite3`

Recent strict gate events:

```bash
sqlite3 refactor/backend/var/refactor.sqlite3 "
SELECT created_at, strategy_id, gate_code, require_proposal_id, blocked
FROM strategy_publish_gate_events
WHERE gate_code='STR-GATE-009'
ORDER BY created_at DESC
LIMIT 100;
"
```

15-minute block ratio from audit table:

```bash
sqlite3 refactor/backend/var/refactor.sqlite3 "
SELECT
  COUNT(1) AS hits_total,
  SUM(CASE WHEN blocked=1 THEN 1 ELSE 0 END) AS blocked_total,
  ROUND(
    CAST(SUM(CASE WHEN blocked=1 THEN 1 ELSE 0 END) AS REAL)
    / NULLIF(COUNT(1), 0),
    4
  ) AS blocked_ratio
FROM strategy_publish_gate_events
WHERE gate_code='STR-GATE-009'
  AND require_proposal_id=1
  AND created_at >= datetime('now', '-15 minutes');
"
```

## 5. Common Root Causes

1. Client publish request did not include `proposal_id`.
2. Strict mode was enabled before all clients completed contract upgrade.
3. Chatbot proposal flow exists but publish API call path did not forward `proposal_id`.
4. Internal SDK/request wrapper dropped `proposal_id` during serialization.

## 6. Mitigation Actions

### 6.1 Fast mitigation (service stability first)

1. Temporarily set `STRATEGY_PUBLISH_REQUIRE_PROPOSAL_ID=false` in backend env.
2. Restart backend service using your deployment method.
3. Verify alert recovery:
   - `block_ratio` decreases.
   - `STR-GATE-009` responses drop significantly.

### 6.2 Permanent fix

1. Ensure all publish callers send explicit `proposal_id`.
2. Add contract tests in caller services/clients for publish payload.
3. Block outdated client versions from strict mode environments until upgraded.
4. Re-enable strict mode after verification window.

## 7. Recovery Validation

1. `refactor_strategy_publish_strict_gate_block_ratio < 0.2` for at least 30 minutes.
2. `increase(refactor_strategy_publish_strict_gate_blocked_total[30m])` remains low and stable.
3. No new burst of `409 STR-GATE-009` in backend logs.
4. Strategy publish success rate returns to expected baseline.

## 8. Rollback Plan

1. Keep strict mode disabled (`STRATEGY_PUBLISH_REQUIRE_PROPOSAL_ID=false`).
2. Roll back to previous stable backend deployment if API behavior remains abnormal.
3. Keep alert muted only during approved maintenance window.
4. Record rollback timestamp, operator, and observed impact.

## 9. Postmortem Template

1. Incident window (start/end UTC).
2. Affected environment and user scope.
3. Primary root cause.
4. Why pre-release checks did not catch it.
5. Immediate mitigation done.
6. Permanent fixes and owners.
7. Follow-up tasks with due dates.

## 10. References

1. Metrics endpoint: `GET /api/v2/metrics`
2. Rule templates:
   - `refactor/backend/monitoring/prometheus/rules/refactor-threshold-governance-alerts.yml`
   - `refactor/backend/monitoring/prometheus/rules/refactor-threshold-governance-alerts.dev.yml`
   - `refactor/backend/monitoring/prometheus/rules/refactor-threshold-governance-alerts.staging.yml`
   - `refactor/backend/monitoring/prometheus/rules/refactor-threshold-governance-alerts.prod.yml`
3. Strategy strict gate implementation:
   - `refactor/backend/src/app/services/strategy_service.py`
   - `refactor/backend/src/app/api/routes/metrics.py`
