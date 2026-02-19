from app.core.settings import load_settings


def test_settings_reads_non_prefixed_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:////tmp/non-prefixed.sqlite3")
    monkeypatch.setenv("QUEUE_AUTO_PROCESS", "false")
    monkeypatch.setenv("CHROMA_PATH", "/tmp/chroma-non-prefixed")
    monkeypatch.setenv("CHROMA_COLLECTION", "np_knowledge")
    monkeypatch.setenv("MEMORY_COLLECTION", "np_memory")
    monkeypatch.setenv("LLM_PROVIDER", "dashscope")
    monkeypatch.setenv("LLM_MODEL", "qwen-plus")
    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_TIMEOUT_SEC", "45")
    monkeypatch.setenv("LLM_MAX_RETRIES", "3")
    monkeypatch.setenv("LLM_RETRY_BACKOFF_MS", "250")
    monkeypatch.setenv("LLM_CIRCUIT_FAILURE_THRESHOLD", "5")
    monkeypatch.setenv("LLM_CIRCUIT_RESET_TIMEOUT_MS", "60000")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dash-key")
    monkeypatch.setenv("DASHSCOPE_BASE_HTTP_API_URL", "https://dashscope.aliyuncs.com/api/v1")
    monkeypatch.setenv("DASHSCOPE_ENABLE_THINKING", "true")
    monkeypatch.setenv("PROMPT_REF_LOCK_MODE", "strict")
    monkeypatch.setenv("PROMPT_LOCK_OVERVIEW_CACHE_TTL_SEC", "45")
    monkeypatch.setenv("PROMPT_LOCK_OVERVIEW_CACHE_MAX_SIZE", "256")
    monkeypatch.setenv("PROMPT_LOCK_OVERVIEW_MODULE_TIMEOUT_SEC", "1.5")
    monkeypatch.setenv("PROMPT_LOCK_OVERVIEW_TIMEOUT_SUMMARY_SEC", "0.3")
    monkeypatch.setenv("PROMPT_LOCK_OVERVIEW_TIMEOUT_GROUPED_SEC", "0.4")
    monkeypatch.setenv("PROMPT_LOCK_OVERVIEW_TIMEOUT_TRENDS_SEC", "0.5")
    monkeypatch.setenv("PROMTOOL_REMOTE_SOFT_AUDIT_FILE", "/tmp/promtool-soft-audit.log")
    monkeypatch.setenv("PROMTOOL_REMOTE_SOFT_AUDIT_MAX_LINES", "88")
    monkeypatch.setenv("PROMTOOL_REMOTE_SOFT_AUDIT_MAX_BYTES", "8192")
    monkeypatch.setenv("PROMTOOL_REMOTE_SOFT_AUDIT_RETENTION_DAYS", "14")
    monkeypatch.setenv("FEEDBACK_EVENT_OPTIMIZATION_ENABLED", "false")
    monkeypatch.setenv("FEEDBACK_EVENT_OPTIMIZATION_MIN_RECORDS", "5")
    monkeypatch.setenv("FEEDBACK_EVENT_OPTIMIZATION_COOLDOWN_SECONDS", "120")
    monkeypatch.setenv("STRATEGY_PUBLISH_REQUIRE_PROPOSAL_ID", "true")
    monkeypatch.setenv("BACKTEST_RETURN_SAMPLE_MIN_SIZE", "12")
    monkeypatch.setenv("BACKTEST_RETURN_SAMPLE_MEDIUM_COVERAGE_PCT", "65")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_WARN_LOW_WINDOWS", "1")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_WARN_THRESHOLD_UNMET_WINDOWS", "2")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_LOW_WINDOWS", "3")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_THRESHOLD_UNMET_WINDOWS", "4")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_WARN_RATIO", "0.3")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_CRITICAL_RATIO", "0.7")

    settings = load_settings()

    assert settings.database_url == "sqlite:////tmp/non-prefixed.sqlite3"
    assert settings.queue_auto_process is False
    assert settings.chroma_path == "/tmp/chroma-non-prefixed"
    assert settings.chroma_collection == "np_knowledge"
    assert settings.memory_collection == "np_memory"
    assert settings.llm_provider == "dashscope"
    assert settings.llm_model == "qwen-plus"
    assert settings.llm_api_key == "llm-key"
    assert settings.llm_base_url == "https://example.com/v1"
    assert settings.llm_timeout_sec == 45.0
    assert settings.llm_max_retries == 3
    assert settings.llm_retry_backoff_ms == 250
    assert settings.llm_circuit_failure_threshold == 5
    assert settings.llm_circuit_reset_timeout_ms == 60000
    assert settings.dashscope_api_key == "dash-key"
    assert settings.dashscope_base_http_api_url == "https://dashscope.aliyuncs.com/api/v1"
    assert settings.dashscope_enable_thinking is True
    assert settings.prompt_ref_lock_mode == "strict"
    assert settings.prompt_lock_overview_cache_ttl_sec == 45
    assert settings.prompt_lock_overview_cache_max_size == 256
    assert settings.prompt_lock_overview_module_timeout_sec == 1.5
    assert settings.prompt_lock_overview_timeout_summary_sec == 0.3
    assert settings.prompt_lock_overview_timeout_grouped_sec == 0.4
    assert settings.prompt_lock_overview_timeout_trends_sec == 0.5
    assert settings.promtool_remote_soft_audit_file == "/tmp/promtool-soft-audit.log"
    assert settings.promtool_remote_soft_audit_max_lines == 88
    assert settings.promtool_remote_soft_audit_max_bytes == 8192
    assert settings.promtool_remote_soft_audit_retention_days == 14
    assert settings.feedback_event_optimization_enabled is False
    assert settings.feedback_event_optimization_min_records == 5
    assert settings.feedback_event_optimization_cooldown_seconds == 120
    assert settings.strategy_publish_require_proposal_id is True
    assert settings.backtest_return_sample_min_size == 12
    assert settings.backtest_return_sample_medium_coverage_pct == 65.0
    assert settings.backtest_multi_window_alert_warn_low_windows == 1
    assert settings.backtest_multi_window_alert_warn_threshold_unmet_windows == 2
    assert settings.backtest_multi_window_alert_critical_low_windows == 3
    assert settings.backtest_multi_window_alert_critical_threshold_unmet_windows == 4
    assert settings.backtest_multi_window_alert_warn_low_windows_raw == 1
    assert settings.backtest_multi_window_alert_warn_threshold_unmet_windows_raw == 2
    assert settings.backtest_multi_window_alert_critical_low_windows_raw == 3
    assert settings.backtest_multi_window_alert_critical_threshold_unmet_windows_raw == 4
    assert settings.backtest_multi_window_alert_threshold_normalization_applied is False
    assert settings.backtest_multi_window_alert_critical_low_windows_threshold_normalized is False
    assert settings.backtest_multi_window_alert_critical_threshold_unmet_windows_threshold_normalized is False
    assert settings.backtest_multi_window_alert_threshold_governance_warn_ratio == 0.3
    assert settings.backtest_multi_window_alert_threshold_governance_critical_ratio == 0.7
    assert settings.backtest_multi_window_alert_threshold_governance_warn_ratio_normalized is False
    assert settings.backtest_multi_window_alert_threshold_governance_critical_ratio_normalized is False
    assert settings.backtest_multi_window_alert_threshold_governance_ratio_normalization_applied is False


def test_settings_normalizes_multi_window_alert_threshold_relationship(monkeypatch) -> None:
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_WARN_LOW_WINDOWS", "3")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_WARN_THRESHOLD_UNMET_WINDOWS", "4")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_LOW_WINDOWS", "1")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_THRESHOLD_UNMET_WINDOWS", "2")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_WARN_RATIO", "0.8")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_CRITICAL_RATIO", "0.2")

    settings = load_settings()

    assert settings.backtest_multi_window_alert_warn_low_windows == 3
    assert settings.backtest_multi_window_alert_warn_threshold_unmet_windows == 4
    assert settings.backtest_multi_window_alert_critical_low_windows == 3
    assert settings.backtest_multi_window_alert_critical_threshold_unmet_windows == 4
    assert settings.backtest_multi_window_alert_warn_low_windows_raw == 3
    assert settings.backtest_multi_window_alert_warn_threshold_unmet_windows_raw == 4
    assert settings.backtest_multi_window_alert_critical_low_windows_raw == 1
    assert settings.backtest_multi_window_alert_critical_threshold_unmet_windows_raw == 2
    assert settings.backtest_multi_window_alert_threshold_normalization_applied is True
    assert settings.backtest_multi_window_alert_critical_low_windows_threshold_normalized is True
    assert settings.backtest_multi_window_alert_critical_threshold_unmet_windows_threshold_normalized is True
    assert settings.backtest_multi_window_alert_threshold_governance_warn_ratio == 0.8
    assert settings.backtest_multi_window_alert_threshold_governance_critical_ratio == 0.8
    assert settings.backtest_multi_window_alert_threshold_governance_warn_ratio_normalized is False
    assert settings.backtest_multi_window_alert_threshold_governance_critical_ratio_normalized is True
    assert settings.backtest_multi_window_alert_threshold_governance_ratio_normalization_applied is True


def test_settings_clamps_governance_ratio_range(monkeypatch) -> None:
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_WARN_RATIO", "1.2")
    monkeypatch.setenv("BACKTEST_MULTI_WINDOW_ALERT_THRESHOLD_GOVERNANCE_CRITICAL_RATIO", "-0.4")

    settings = load_settings()

    assert settings.backtest_multi_window_alert_threshold_governance_warn_ratio == 1.0
    assert settings.backtest_multi_window_alert_threshold_governance_critical_ratio == 1.0
    assert settings.backtest_multi_window_alert_threshold_governance_warn_ratio_normalized is True
    assert settings.backtest_multi_window_alert_threshold_governance_critical_ratio_normalized is True
    assert settings.backtest_multi_window_alert_threshold_governance_ratio_normalization_applied is True
