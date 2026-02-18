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
