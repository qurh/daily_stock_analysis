from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_database_url() -> str:
    backend_root = Path(__file__).resolve().parents[3]
    default_db_file = backend_root / "var" / "refactor.sqlite3"
    return f"sqlite:///{default_db_file}"


def _default_chroma_path() -> str:
    backend_root = Path(__file__).resolve().parents[3]
    return str(backend_root / "var" / "chroma")


def _read_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _read_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid float value for {name}: {raw}") from exc


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid int value for {name}: {raw}") from exc


def _read_prompt_lock_mode_env(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized not in {"strict", "lenient"}:
        raise ValueError(f"Invalid prompt lock mode for {name}: {raw}")
    return normalized


@dataclass(frozen=True)
class AppSettings:
    database_url: str
    queue_auto_process: bool
    chroma_path: str
    chroma_collection: str
    memory_collection: str
    llm_provider: str
    llm_model: str
    llm_api_key: str | None
    llm_base_url: str
    llm_timeout_sec: float
    llm_max_retries: int
    llm_retry_backoff_ms: int
    llm_circuit_failure_threshold: int
    llm_circuit_reset_timeout_ms: int
    dashscope_api_key: str | None
    dashscope_base_http_api_url: str
    dashscope_enable_thinking: bool
    prompt_ref_lock_mode: str
    prompt_lock_overview_cache_ttl_sec: int
    prompt_lock_overview_cache_max_size: int
    prompt_lock_overview_module_timeout_sec: float
    prompt_lock_overview_timeout_summary_sec: float
    prompt_lock_overview_timeout_grouped_sec: float
    prompt_lock_overview_timeout_trends_sec: float
    backtest_return_sample_min_size: int
    backtest_return_sample_medium_coverage_pct: float
    backtest_multi_window_alert_warn_low_windows: int
    backtest_multi_window_alert_warn_threshold_unmet_windows: int
    backtest_multi_window_alert_critical_low_windows: int
    backtest_multi_window_alert_critical_threshold_unmet_windows: int


def load_settings() -> AppSettings:
    database_url = os.getenv("DATABASE_URL", _default_database_url())
    queue_auto_process = _read_bool_env("QUEUE_AUTO_PROCESS", True)
    chroma_path = os.getenv("CHROMA_PATH", _default_chroma_path())
    chroma_collection = os.getenv("CHROMA_COLLECTION", "knowledge_chunks")
    memory_collection = os.getenv("MEMORY_COLLECTION", "memory_entries")
    llm_provider = os.getenv("LLM_PROVIDER", "mock-llm")
    llm_model = os.getenv("LLM_MODEL", "mock-v1")
    llm_api_key = os.getenv("LLM_API_KEY")
    if llm_api_key is not None:
        llm_api_key = llm_api_key.strip() or None
    llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_timeout_sec = _read_float_env("LLM_TIMEOUT_SEC", 30.0)
    llm_max_retries = _read_int_env("LLM_MAX_RETRIES", 0)
    llm_retry_backoff_ms = _read_int_env("LLM_RETRY_BACKOFF_MS", 100)
    llm_circuit_failure_threshold = _read_int_env("LLM_CIRCUIT_FAILURE_THRESHOLD", 0)
    llm_circuit_reset_timeout_ms = _read_int_env("LLM_CIRCUIT_RESET_TIMEOUT_MS", 30000)
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    if dashscope_api_key is not None:
        dashscope_api_key = dashscope_api_key.strip() or None
    dashscope_base_http_api_url = os.getenv("DASHSCOPE_BASE_HTTP_API_URL", "https://dashscope.aliyuncs.com/api/v1")
    dashscope_enable_thinking = _read_bool_env("DASHSCOPE_ENABLE_THINKING", False)
    prompt_ref_lock_mode = _read_prompt_lock_mode_env("PROMPT_REF_LOCK_MODE", "lenient")
    prompt_lock_overview_cache_ttl_sec = _read_int_env("PROMPT_LOCK_OVERVIEW_CACHE_TTL_SEC", 30)
    prompt_lock_overview_cache_max_size = _read_int_env("PROMPT_LOCK_OVERVIEW_CACHE_MAX_SIZE", 128)
    prompt_lock_overview_module_timeout_sec = _read_float_env("PROMPT_LOCK_OVERVIEW_MODULE_TIMEOUT_SEC", 0.0)
    prompt_lock_overview_timeout_summary_sec = _read_float_env("PROMPT_LOCK_OVERVIEW_TIMEOUT_SUMMARY_SEC", 0.0)
    prompt_lock_overview_timeout_grouped_sec = _read_float_env("PROMPT_LOCK_OVERVIEW_TIMEOUT_GROUPED_SEC", 0.0)
    prompt_lock_overview_timeout_trends_sec = _read_float_env("PROMPT_LOCK_OVERVIEW_TIMEOUT_TRENDS_SEC", 0.0)
    backtest_return_sample_min_size = _read_int_env("BACKTEST_RETURN_SAMPLE_MIN_SIZE", 20)
    backtest_return_sample_medium_coverage_pct = _read_float_env("BACKTEST_RETURN_SAMPLE_MEDIUM_COVERAGE_PCT", 50.0)
    backtest_multi_window_alert_warn_low_windows = _read_int_env("BACKTEST_MULTI_WINDOW_ALERT_WARN_LOW_WINDOWS", 1)
    backtest_multi_window_alert_warn_threshold_unmet_windows = _read_int_env(
        "BACKTEST_MULTI_WINDOW_ALERT_WARN_THRESHOLD_UNMET_WINDOWS", 1
    )
    backtest_multi_window_alert_critical_low_windows = _read_int_env(
        "BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_LOW_WINDOWS", 2
    )
    backtest_multi_window_alert_critical_threshold_unmet_windows = _read_int_env(
        "BACKTEST_MULTI_WINDOW_ALERT_CRITICAL_THRESHOLD_UNMET_WINDOWS", 3
    )
    return AppSettings(
        database_url=database_url,
        queue_auto_process=queue_auto_process,
        chroma_path=chroma_path,
        chroma_collection=chroma_collection,
        memory_collection=memory_collection,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_timeout_sec=llm_timeout_sec,
        llm_max_retries=llm_max_retries,
        llm_retry_backoff_ms=llm_retry_backoff_ms,
        llm_circuit_failure_threshold=llm_circuit_failure_threshold,
        llm_circuit_reset_timeout_ms=llm_circuit_reset_timeout_ms,
        dashscope_api_key=dashscope_api_key,
        dashscope_base_http_api_url=dashscope_base_http_api_url,
        dashscope_enable_thinking=dashscope_enable_thinking,
        prompt_ref_lock_mode=prompt_ref_lock_mode,
        prompt_lock_overview_cache_ttl_sec=prompt_lock_overview_cache_ttl_sec,
        prompt_lock_overview_cache_max_size=prompt_lock_overview_cache_max_size,
        prompt_lock_overview_module_timeout_sec=prompt_lock_overview_module_timeout_sec,
        prompt_lock_overview_timeout_summary_sec=prompt_lock_overview_timeout_summary_sec,
        prompt_lock_overview_timeout_grouped_sec=prompt_lock_overview_timeout_grouped_sec,
        prompt_lock_overview_timeout_trends_sec=prompt_lock_overview_timeout_trends_sec,
        backtest_return_sample_min_size=backtest_return_sample_min_size,
        backtest_return_sample_medium_coverage_pct=backtest_return_sample_medium_coverage_pct,
        backtest_multi_window_alert_warn_low_windows=backtest_multi_window_alert_warn_low_windows,
        backtest_multi_window_alert_warn_threshold_unmet_windows=(
            backtest_multi_window_alert_warn_threshold_unmet_windows
        ),
        backtest_multi_window_alert_critical_low_windows=backtest_multi_window_alert_critical_low_windows,
        backtest_multi_window_alert_critical_threshold_unmet_windows=(
            backtest_multi_window_alert_critical_threshold_unmet_windows
        ),
    )
