from pathlib import Path


def test_notification_retry_alert_rule_template_exists_with_required_alerts() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    rule_file = backend_root / "monitoring" / "prometheus" / "rules" / "refactor-notification-retry-alerts.yml"

    assert rule_file.exists()
    content = rule_file.read_text(encoding="utf-8")

    assert "name: refactor-notification-retry-alerts" in content
    assert "alert: RefactorNotificationRetrySuccessRatioWarn" in content
    assert "alert: RefactorNotificationRetrySuccessRatioCritical" in content
    assert "alert: RefactorNotificationAutoRetryFinalFailureRatioWarn" in content
    assert "alert: RefactorNotificationAutoRetryFinalFailureRatioCritical" in content
    assert "refactor_notification_retry_attempts_total >= 10" in content
    assert "refactor_notification_retry_success_ratio < 0.6" in content
    assert "refactor_notification_retry_success_ratio < 0.4" in content
    assert "refactor_notification_auto_retry_deliveries_total >= 10" in content
    assert "refactor_notification_auto_retry_final_failure_ratio >= 0.3" in content
    assert "refactor_notification_auto_retry_final_failure_ratio >= 0.5" in content


def test_notification_retry_alert_rule_profile_templates_exist() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    rules_dir = backend_root / "monitoring" / "prometheus" / "rules"

    dev_file = rules_dir / "refactor-notification-retry-alerts.dev.yml"
    staging_file = rules_dir / "refactor-notification-retry-alerts.staging.yml"
    prod_file = rules_dir / "refactor-notification-retry-alerts.prod.yml"

    assert dev_file.exists()
    assert staging_file.exists()
    assert prod_file.exists()

    dev_content = dev_file.read_text(encoding="utf-8")
    staging_content = staging_file.read_text(encoding="utf-8")
    prod_content = prod_file.read_text(encoding="utf-8")

    assert "name: refactor-notification-retry-alerts-dev" in dev_content
    assert "severity: info" in dev_content
    assert "for: 5m" in dev_content
    assert "for: 2m" in dev_content
    assert "refactor_notification_retry_success_ratio < 0.7" in dev_content
    assert "refactor_notification_retry_success_ratio < 0.5" in dev_content
    assert "refactor_notification_auto_retry_final_failure_ratio >= 0.25" in dev_content
    assert "refactor_notification_auto_retry_final_failure_ratio >= 0.4" in dev_content

    assert "name: refactor-notification-retry-alerts-staging" in staging_content
    assert "severity: warning" in staging_content
    assert "for: 10m" in staging_content
    assert "for: 5m" in staging_content
    assert "refactor_notification_retry_success_ratio < 0.65" in staging_content
    assert "refactor_notification_retry_success_ratio < 0.45" in staging_content
    assert "refactor_notification_auto_retry_final_failure_ratio >= 0.28" in staging_content
    assert "refactor_notification_auto_retry_final_failure_ratio >= 0.45" in staging_content

    assert "name: refactor-notification-retry-alerts-prod" in prod_content
    assert "severity: warning" in prod_content
    assert "severity: critical" in prod_content
    assert "for: 15m" in prod_content
    assert "for: 5m" in prod_content
    assert "refactor_notification_retry_success_ratio < 0.6" in prod_content
    assert "refactor_notification_retry_success_ratio < 0.4" in prod_content
    assert "refactor_notification_auto_retry_final_failure_ratio >= 0.3" in prod_content
    assert "refactor_notification_auto_retry_final_failure_ratio >= 0.5" in prod_content
