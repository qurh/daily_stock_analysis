from pathlib import Path


def test_threshold_governance_alert_rule_template_exists_with_required_alerts() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    rule_file = backend_root / "monitoring" / "prometheus" / "rules" / "refactor-threshold-governance-alerts.yml"

    assert rule_file.exists()
    content = rule_file.read_text(encoding="utf-8")

    assert "name: refactor-threshold-governance-alerts" in content
    assert "alert: RefactorThresholdGovernanceWarn" in content
    assert "alert: RefactorThresholdGovernanceCritical" in content
    assert "alert: RefactorThresholdGovernanceNormalizationApplied" in content
    assert "alert: RefactorPromtoolSoftAuditMaxLinesExceeded" in content
    assert "alert: RefactorPromtoolSoftAuditMaxBytesExceeded" in content
    assert "alert: RefactorPromtoolSoftAuditRotationUnbounded" in content
    assert (
        'refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_level{level="warn"} == 1'
        in content
    )
    assert (
        'refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_level{level="critical"} == 1'
        in content
    )
    assert (
        "refactor_backtest_records_return_sample_multi_window_alert_threshold_governance_ratio_"
        "normalization_applied > 0" in content
    )
    assert "refactor_promtool_remote_soft_fallback_audit_config_max_lines > 0" in content
    assert (
        "refactor_promtool_remote_soft_fallback_audit_file_line_count > "
        "refactor_promtool_remote_soft_fallback_audit_config_max_lines" in content
    )
    assert "refactor_promtool_remote_soft_fallback_audit_config_max_bytes > 0" in content
    assert (
        "refactor_promtool_remote_soft_fallback_audit_file_size_bytes > "
        "refactor_promtool_remote_soft_fallback_audit_config_max_bytes" in content
    )
    assert (
        "refactor_promtool_remote_soft_fallback_audit_config_max_lines == 0 and "
        "refactor_promtool_remote_soft_fallback_audit_config_max_bytes == 0 and "
        "refactor_promtool_remote_soft_fallback_audit_config_retention_days == 0" in content
    )


def test_threshold_governance_alert_rule_profile_templates_exist() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    rules_dir = backend_root / "monitoring" / "prometheus" / "rules"

    dev_file = rules_dir / "refactor-threshold-governance-alerts.dev.yml"
    staging_file = rules_dir / "refactor-threshold-governance-alerts.staging.yml"
    prod_file = rules_dir / "refactor-threshold-governance-alerts.prod.yml"

    assert dev_file.exists()
    assert staging_file.exists()
    assert prod_file.exists()

    dev_content = dev_file.read_text(encoding="utf-8")
    staging_content = staging_file.read_text(encoding="utf-8")
    prod_content = prod_file.read_text(encoding="utf-8")

    assert "alert: RefactorThresholdGovernanceWarn" in dev_content
    assert "for: 5m" in dev_content
    assert "severity: info" in dev_content
    assert "alert: RefactorPromtoolSoftAuditMaxLinesExceeded" in dev_content
    assert "alert: RefactorPromtoolSoftAuditMaxBytesExceeded" in dev_content
    assert "alert: RefactorPromtoolSoftAuditRotationUnbounded" in dev_content
    assert 'description: "Soft audit file line count exceeded configured max lines for 3m."' in dev_content
    assert 'description: "All soft audit rotation guards are disabled (lines/bytes/retention) for 20m."' in dev_content

    assert "alert: RefactorThresholdGovernanceWarn" in staging_content
    assert "for: 10m" in staging_content
    assert "severity: warning" in staging_content
    assert "alert: RefactorPromtoolSoftAuditMaxLinesExceeded" in staging_content
    assert "alert: RefactorPromtoolSoftAuditMaxBytesExceeded" in staging_content
    assert "alert: RefactorPromtoolSoftAuditRotationUnbounded" in staging_content
    assert 'description: "Soft audit file line count exceeded configured max lines for 8m."' in staging_content
    assert (
        'description: "All soft audit rotation guards are disabled (lines/bytes/retention) for 30m."' in staging_content
    )

    assert "alert: RefactorThresholdGovernanceWarn" in prod_content
    assert "for: 15m" in prod_content
    assert "severity: warning" in prod_content
    assert "alert: RefactorPromtoolSoftAuditMaxLinesExceeded" in prod_content
    assert "alert: RefactorPromtoolSoftAuditMaxBytesExceeded" in prod_content
    assert "alert: RefactorPromtoolSoftAuditRotationUnbounded" in prod_content
    assert 'description: "Soft audit file line count exceeded configured max lines for 10m."' in prod_content
    assert 'description: "All soft audit rotation guards are disabled (lines/bytes/retention) for 45m."' in prod_content
