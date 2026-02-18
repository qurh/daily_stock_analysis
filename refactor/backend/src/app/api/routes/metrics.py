import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from app.api.deps import get_prompt_lock_audit_service
from app.services.prompt_lock_audit_service import PromptLockAuditService

router = APIRouter()

MULTI_WINDOW_ALERT_THRESHOLD_DIMENSIONS_TOTAL = 4


def _escape_prometheus_label_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace("\n", "\\n")
    return escaped.replace('"', '\\"')


def _load_status_counts(request: Request, table_name: str) -> dict[str, int]:
    query = f"SELECT status, COUNT(1) AS cnt FROM {table_name} GROUP BY status"
    with request.app.state.database.connection() as conn:
        rows = conn.execute(query).fetchall()
    return {str(row["status"]): int(row["cnt"]) for row in rows}


def _append_status_gauge_lines(lines: list[str], metric_name: str, help_text: str, counts: dict[str, int]) -> None:
    lines.append(f"# HELP {metric_name} {help_text}")
    lines.append(f"# TYPE {metric_name} gauge")
    for status in sorted(counts):
        escaped_status = _escape_prometheus_label_value(status)
        lines.append(f'{metric_name}{{status="{escaped_status}"}} {counts[status]}')


def _load_grouped_counts(request: Request, table_name: str, group_column: str) -> dict[str, int]:
    query = f"SELECT {group_column}, COUNT(1) AS cnt FROM {table_name} GROUP BY {group_column}"
    with request.app.state.database.connection() as conn:
        rows = conn.execute(query).fetchall()
    result: dict[str, int] = {}
    for row in rows:
        key = row[group_column] if row[group_column] is not None else "unknown"
        result[str(key)] = int(row["cnt"])
    return result


def _append_labeled_gauge_lines(
    lines: list[str], metric_name: str, help_text: str, label_name: str, counts: dict[str, int]
) -> None:
    lines.append(f"# HELP {metric_name} {help_text}")
    lines.append(f"# TYPE {metric_name} gauge")
    for label_value in sorted(counts):
        escaped_value = _escape_prometheus_label_value(label_value)
        lines.append(f'{metric_name}{{{label_name}="{escaped_value}"}} {counts[label_value]}')


def _append_labeled_gauge_lines_ordered(
    lines: list[str],
    metric_name: str,
    help_text: str,
    label_name: str,
    ordered_items: list[tuple[str, int]],
) -> None:
    lines.append(f"# HELP {metric_name} {help_text}")
    lines.append(f"# TYPE {metric_name} gauge")
    for label_value, metric_value in ordered_items:
        escaped_value = _escape_prometheus_label_value(label_value)
        lines.append(f'{metric_name}{{{label_name}="{escaped_value}"}} {metric_value}')


def _load_total_count(request: Request, table_name: str) -> int:
    query = f"SELECT COUNT(1) AS cnt FROM {table_name}"
    with request.app.state.database.connection() as conn:
        row = conn.execute(query).fetchone()
    if row is None:
        return 0
    return int(row["cnt"])


def _load_total_sum(request: Request, table_name: str, value_column: str) -> int:
    query = f"SELECT COALESCE(SUM({value_column}), 0) AS total FROM {table_name}"
    with request.app.state.database.connection() as conn:
        row = conn.execute(query).fetchone()
    if row is None:
        return 0
    return int(row["total"])


def _append_total_gauge_line(lines: list[str], metric_name: str, help_text: str, total: int) -> None:
    lines.append(f"# HELP {metric_name} {help_text}")
    lines.append(f"# TYPE {metric_name} gauge")
    lines.append(f"{metric_name} {int(total)}")


def _append_float_gauge_line(lines: list[str], metric_name: str, help_text: str, value: float) -> None:
    lines.append(f"# HELP {metric_name} {help_text}")
    lines.append(f"# TYPE {metric_name} gauge")
    lines.append(f"{metric_name} {value}")


def _percentile_linear(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * p
    lower_idx = int(rank)
    upper_idx = min(lower_idx + 1, len(sorted_values) - 1)
    weight = rank - lower_idx
    return sorted_values[lower_idx] + weight * (sorted_values[upper_idx] - sorted_values[lower_idx])


def _trimmed_mean(sorted_values: list[float], trim_ratio: float) -> float:
    if not sorted_values:
        return 0.0
    trim_count = int(len(sorted_values) * trim_ratio)
    if trim_count <= 0 or (len(sorted_values) - trim_count * 2) <= 0:
        return sum(sorted_values) / len(sorted_values)
    trimmed_values = sorted_values[trim_count : len(sorted_values) - trim_count]
    return sum(trimmed_values) / len(trimmed_values)


def _winsorized_mean(sorted_values: list[float], trim_ratio: float) -> float:
    if not sorted_values:
        return 0.0
    trim_count = int(len(sorted_values) * trim_ratio)
    if trim_count <= 0 or (len(sorted_values) - trim_count * 2) <= 0:
        return sum(sorted_values) / len(sorted_values)

    lower_bound = sorted_values[trim_count]
    upper_bound = sorted_values[len(sorted_values) - trim_count - 1]
    winsorized_values = [min(max(value, lower_bound), upper_bound) for value in sorted_values]
    return sum(winsorized_values) / len(winsorized_values)


def _compute_sample_adequacy(
    sample_size: int, min_sample_required: int, medium_coverage_threshold_pct: float
) -> dict[str, Any]:
    threshold_met = 1 if sample_size >= min_sample_required else 0
    coverage_ratio_pct = round(sample_size / min_sample_required * 100.0, 2)
    if threshold_met == 1:
        adequacy_level = "high"
    elif coverage_ratio_pct >= medium_coverage_threshold_pct:
        adequacy_level = "medium"
    else:
        adequacy_level = "low"
    adequacy_levels_onehot = {
        "low": 1 if adequacy_level == "low" else 0,
        "medium": 1 if adequacy_level == "medium" else 0,
        "high": 1 if adequacy_level == "high" else 0,
    }
    adequacy_score = {"low": 0.0, "medium": 0.5, "high": 1.0}[adequacy_level]
    return {
        "threshold_met": threshold_met,
        "coverage_ratio_pct": coverage_ratio_pct,
        "adequacy_levels_onehot": adequacy_levels_onehot,
        "adequacy_score": adequacy_score,
    }


def _compute_multi_window_alert_levels(
    threshold_unmet_windows_total: int,
    low_adequacy_windows_total: int,
    warn_low_windows_threshold: int,
    warn_threshold_unmet_windows_threshold: int,
    critical_low_windows_threshold: int,
    critical_threshold_unmet_windows_threshold: int,
) -> dict[str, int]:
    if (
        low_adequacy_windows_total >= critical_low_windows_threshold
        or threshold_unmet_windows_total >= critical_threshold_unmet_windows_threshold
    ):
        alert_level = "critical"
    elif (
        low_adequacy_windows_total >= warn_low_windows_threshold
        or threshold_unmet_windows_total >= warn_threshold_unmet_windows_threshold
    ):
        alert_level = "warn"
    else:
        alert_level = "none"
    return {
        "none": 1 if alert_level == "none" else 0,
        "warn": 1 if alert_level == "warn" else 0,
        "critical": 1 if alert_level == "critical" else 0,
    }


def _compute_multi_window_alert_level_score(alert_levels_onehot: dict[str, int]) -> float:
    if int(alert_levels_onehot.get("critical", 0)) == 1:
        return 1.0
    if int(alert_levels_onehot.get("warn", 0)) == 1:
        return 0.5
    return 0.0


def _load_backtest_quality_snapshot(request: Request) -> dict[str, Any]:
    query = "SELECT outcome, return_pct, direction_correct, created_at FROM backtest_records"
    with request.app.state.database.connection() as conn:
        rows = conn.execute(query).fetchall()

    outcome_counts: dict[str, int] = {}
    return_values: list[float] = []
    return_values_24h: list[float] = []
    return_values_7d: list[float] = []
    return_values_30d: list[float] = []
    direction_flags: list[int] = []
    now_utc = datetime.now(timezone.utc)
    cutoff_24h = now_utc - timedelta(hours=24)
    cutoff_7d = now_utc - timedelta(days=7)
    cutoff_30d = now_utc - timedelta(days=30)
    for row in rows:
        outcome = str(row["outcome"] if row["outcome"] is not None else "unknown")
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

        if row["return_pct"] is not None:
            return_value = float(row["return_pct"])
            return_values.append(return_value)
            created_at_raw = row["created_at"]
            if created_at_raw is not None:
                try:
                    created_at = datetime.fromisoformat(str(created_at_raw))
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    created_at_utc = created_at.astimezone(timezone.utc)
                    if created_at_utc >= cutoff_24h:
                        return_values_24h.append(return_value)
                    if created_at_utc >= cutoff_7d:
                        return_values_7d.append(return_value)
                    if created_at_utc >= cutoff_30d:
                        return_values_30d.append(return_value)
                except ValueError:
                    pass
        if row["direction_correct"] is not None:
            direction_flags.append(int(row["direction_correct"]))

    sorted_returns = sorted(return_values)
    trim_ratio_10pct = 0.1
    return_avg = round(sum(return_values) / len(return_values), 4) if return_values else 0.0
    return_trimmed_mean_10pct = round(_trimmed_mean(sorted_returns, trim_ratio_10pct), 4) if sorted_returns else 0.0
    return_winsorized_mean_10pct = (
        round(_winsorized_mean(sorted_returns, trim_ratio_10pct), 4) if sorted_returns else 0.0
    )
    return_p50 = round(_percentile_linear(sorted_returns, 0.5), 4) if sorted_returns else 0.0
    return_p90 = round(_percentile_linear(sorted_returns, 0.9), 4) if sorted_returns else 0.0
    return_p95 = round(_percentile_linear(sorted_returns, 0.95), 4) if sorted_returns else 0.0
    return_p99 = round(_percentile_linear(sorted_returns, 0.99), 4) if sorted_returns else 0.0
    if return_values:
        mean = sum(return_values) / len(return_values)
        variance = sum((value - mean) ** 2 for value in return_values) / len(return_values)
        return_stddev = round(variance**0.5, 4)
    else:
        return_stddev = 0.0
    direction_accuracy_pct = round(sum(direction_flags) / len(direction_flags) * 100.0, 2) if direction_flags else 0.0
    settings = getattr(request.app.state, "settings", None)
    min_sample_required = 20
    medium_coverage_threshold_pct = 50.0
    multi_window_alert_warn_low_windows_threshold = 1
    multi_window_alert_warn_threshold_unmet_windows_threshold = 1
    multi_window_alert_critical_low_windows_threshold = 2
    multi_window_alert_critical_threshold_unmet_windows_threshold = 3
    multi_window_alert_warn_low_windows_threshold_raw = 1
    multi_window_alert_warn_threshold_unmet_windows_threshold_raw = 1
    multi_window_alert_critical_low_windows_threshold_raw = 2
    multi_window_alert_critical_threshold_unmet_windows_threshold_raw = 3
    multi_window_alert_threshold_normalization_applied = False
    multi_window_alert_critical_low_windows_threshold_normalized = False
    multi_window_alert_critical_threshold_unmet_windows_threshold_normalized = False
    if settings is not None:
        min_sample_required = int(getattr(settings, "backtest_return_sample_min_size", 20))
        medium_coverage_threshold_pct = float(getattr(settings, "backtest_return_sample_medium_coverage_pct", 50.0))
        multi_window_alert_warn_low_windows_threshold = int(
            getattr(settings, "backtest_multi_window_alert_warn_low_windows", 1)
        )
        multi_window_alert_warn_threshold_unmet_windows_threshold = int(
            getattr(settings, "backtest_multi_window_alert_warn_threshold_unmet_windows", 1)
        )
        multi_window_alert_critical_low_windows_threshold = int(
            getattr(settings, "backtest_multi_window_alert_critical_low_windows", 2)
        )
        multi_window_alert_critical_threshold_unmet_windows_threshold = int(
            getattr(settings, "backtest_multi_window_alert_critical_threshold_unmet_windows", 3)
        )
        multi_window_alert_warn_low_windows_threshold_raw = int(
            getattr(settings, "backtest_multi_window_alert_warn_low_windows_raw", 1)
        )
        multi_window_alert_warn_threshold_unmet_windows_threshold_raw = int(
            getattr(settings, "backtest_multi_window_alert_warn_threshold_unmet_windows_raw", 1)
        )
        multi_window_alert_critical_low_windows_threshold_raw = int(
            getattr(settings, "backtest_multi_window_alert_critical_low_windows_raw", 2)
        )
        multi_window_alert_critical_threshold_unmet_windows_threshold_raw = int(
            getattr(settings, "backtest_multi_window_alert_critical_threshold_unmet_windows_raw", 3)
        )
        multi_window_alert_threshold_normalization_applied = bool(
            getattr(settings, "backtest_multi_window_alert_threshold_normalization_applied", False)
        )
        multi_window_alert_critical_low_windows_threshold_normalized = bool(
            getattr(settings, "backtest_multi_window_alert_critical_low_windows_threshold_normalized", False)
        )
        multi_window_alert_critical_threshold_unmet_windows_threshold_normalized = bool(
            getattr(
                settings,
                "backtest_multi_window_alert_critical_threshold_unmet_windows_threshold_normalized",
                False,
            )
        )
    min_sample_required = max(min_sample_required, 1)
    medium_coverage_threshold_pct = max(min(medium_coverage_threshold_pct, 100.0), 0.0)
    multi_window_alert_warn_low_windows_threshold = max(multi_window_alert_warn_low_windows_threshold, 0)
    multi_window_alert_warn_threshold_unmet_windows_threshold = max(
        multi_window_alert_warn_threshold_unmet_windows_threshold, 0
    )
    multi_window_alert_critical_low_windows_threshold = max(multi_window_alert_critical_low_windows_threshold, 0)
    multi_window_alert_critical_threshold_unmet_windows_threshold = max(
        multi_window_alert_critical_threshold_unmet_windows_threshold, 0
    )
    adequacy_all = _compute_sample_adequacy(
        sample_size=len(return_values),
        min_sample_required=min_sample_required,
        medium_coverage_threshold_pct=medium_coverage_threshold_pct,
    )
    adequacy_24h = _compute_sample_adequacy(
        sample_size=len(return_values_24h),
        min_sample_required=min_sample_required,
        medium_coverage_threshold_pct=medium_coverage_threshold_pct,
    )
    adequacy_7d = _compute_sample_adequacy(
        sample_size=len(return_values_7d),
        min_sample_required=min_sample_required,
        medium_coverage_threshold_pct=medium_coverage_threshold_pct,
    )
    adequacy_30d = _compute_sample_adequacy(
        sample_size=len(return_values_30d),
        min_sample_required=min_sample_required,
        medium_coverage_threshold_pct=medium_coverage_threshold_pct,
    )
    sample_threshold_met = int(adequacy_all["threshold_met"])
    sample_threshold_met_24h = int(adequacy_24h["threshold_met"])
    sample_threshold_met_7d = int(adequacy_7d["threshold_met"])
    sample_threshold_met_30d = int(adequacy_30d["threshold_met"])
    sample_size_gap = max(min_sample_required - len(return_values), 0)
    sample_coverage_ratio_pct = float(adequacy_all["coverage_ratio_pct"])
    sample_coverage_ratio_pct_24h = float(adequacy_24h["coverage_ratio_pct"])
    sample_coverage_ratio_pct_7d = float(adequacy_7d["coverage_ratio_pct"])
    sample_coverage_ratio_pct_30d = float(adequacy_30d["coverage_ratio_pct"])
    sample_adequacy_levels_onehot = dict(adequacy_all["adequacy_levels_onehot"])
    sample_adequacy_levels_onehot_24h = dict(adequacy_24h["adequacy_levels_onehot"])
    sample_adequacy_levels_onehot_7d = dict(adequacy_7d["adequacy_levels_onehot"])
    sample_adequacy_levels_onehot_30d = dict(adequacy_30d["adequacy_levels_onehot"])
    sample_adequacy_score = float(adequacy_all["adequacy_score"])
    sample_adequacy_score_24h = float(adequacy_24h["adequacy_score"])
    sample_adequacy_score_7d = float(adequacy_7d["adequacy_score"])
    sample_adequacy_score_30d = float(adequacy_30d["adequacy_score"])
    sample_threshold_unmet_windows_total = (
        int(not bool(adequacy_24h["threshold_met"]))
        + int(not bool(adequacy_7d["threshold_met"]))
        + int(not bool(adequacy_30d["threshold_met"]))
    )
    sample_low_adequacy_windows_total = (
        int(adequacy_24h["adequacy_levels_onehot"]["low"])
        + int(adequacy_7d["adequacy_levels_onehot"]["low"])
        + int(adequacy_30d["adequacy_levels_onehot"]["low"])
    )
    sample_multi_window_alert_levels_onehot = _compute_multi_window_alert_levels(
        threshold_unmet_windows_total=sample_threshold_unmet_windows_total,
        low_adequacy_windows_total=sample_low_adequacy_windows_total,
        warn_low_windows_threshold=multi_window_alert_warn_low_windows_threshold,
        warn_threshold_unmet_windows_threshold=multi_window_alert_warn_threshold_unmet_windows_threshold,
        critical_low_windows_threshold=multi_window_alert_critical_low_windows_threshold,
        critical_threshold_unmet_windows_threshold=multi_window_alert_critical_threshold_unmet_windows_threshold,
    )
    sample_multi_window_alert_level_score = _compute_multi_window_alert_level_score(
        alert_levels_onehot=sample_multi_window_alert_levels_onehot
    )
    sample_multi_window_alert_threshold_raw_normalized_mismatch_count = (
        int(multi_window_alert_warn_low_windows_threshold_raw != multi_window_alert_warn_low_windows_threshold)
        + int(
            multi_window_alert_warn_threshold_unmet_windows_threshold_raw
            != multi_window_alert_warn_threshold_unmet_windows_threshold
        )
        + int(
            multi_window_alert_critical_low_windows_threshold_raw != multi_window_alert_critical_low_windows_threshold
        )
        + int(
            multi_window_alert_critical_threshold_unmet_windows_threshold_raw
            != multi_window_alert_critical_threshold_unmet_windows_threshold
        )
    )
    sample_multi_window_alert_threshold_raw_normalized_dimensions_total = MULTI_WINDOW_ALERT_THRESHOLD_DIMENSIONS_TOTAL
    sample_multi_window_alert_threshold_raw_normalized_mismatch_ratio = round(
        (
            sample_multi_window_alert_threshold_raw_normalized_mismatch_count
            / sample_multi_window_alert_threshold_raw_normalized_dimensions_total
        ),
        4,
    )
    return {
        "outcome_counts": outcome_counts,
        "return_sample_size": len(return_values),
        "return_sample_size_24h": len(return_values_24h),
        "return_sample_size_7d": len(return_values_7d),
        "return_sample_size_30d": len(return_values_30d),
        "return_sample_min_size_required": min_sample_required,
        "return_sample_medium_coverage_threshold_pct": round(medium_coverage_threshold_pct, 2),
        "return_sample_threshold_met": sample_threshold_met,
        "return_sample_threshold_met_24h": sample_threshold_met_24h,
        "return_sample_threshold_met_7d": sample_threshold_met_7d,
        "return_sample_threshold_met_30d": sample_threshold_met_30d,
        "return_sample_size_gap": sample_size_gap,
        "return_sample_coverage_ratio_pct": sample_coverage_ratio_pct,
        "return_sample_coverage_ratio_pct_24h": sample_coverage_ratio_pct_24h,
        "return_sample_coverage_ratio_pct_7d": sample_coverage_ratio_pct_7d,
        "return_sample_coverage_ratio_pct_30d": sample_coverage_ratio_pct_30d,
        "return_sample_adequacy_levels_onehot": sample_adequacy_levels_onehot,
        "return_sample_adequacy_levels_onehot_24h": sample_adequacy_levels_onehot_24h,
        "return_sample_adequacy_levels_onehot_7d": sample_adequacy_levels_onehot_7d,
        "return_sample_adequacy_levels_onehot_30d": sample_adequacy_levels_onehot_30d,
        "return_sample_adequacy_score": sample_adequacy_score,
        "return_sample_adequacy_score_24h": sample_adequacy_score_24h,
        "return_sample_adequacy_score_7d": sample_adequacy_score_7d,
        "return_sample_adequacy_score_30d": sample_adequacy_score_30d,
        "return_sample_threshold_unmet_windows_total": sample_threshold_unmet_windows_total,
        "return_sample_low_adequacy_windows_total": sample_low_adequacy_windows_total,
        "return_sample_multi_window_alert_levels_onehot": sample_multi_window_alert_levels_onehot,
        "return_sample_multi_window_alert_level_score": sample_multi_window_alert_level_score,
        "return_sample_multi_window_alert_warn_low_windows_threshold": multi_window_alert_warn_low_windows_threshold,
        "return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold": (
            multi_window_alert_warn_threshold_unmet_windows_threshold
        ),
        "return_sample_multi_window_alert_critical_low_windows_threshold": (
            multi_window_alert_critical_low_windows_threshold
        ),
        "return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold": (
            multi_window_alert_critical_threshold_unmet_windows_threshold
        ),
        "return_sample_multi_window_alert_warn_low_windows_threshold_raw": (
            multi_window_alert_warn_low_windows_threshold_raw
        ),
        "return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold_raw": (
            multi_window_alert_warn_threshold_unmet_windows_threshold_raw
        ),
        "return_sample_multi_window_alert_critical_low_windows_threshold_raw": (
            multi_window_alert_critical_low_windows_threshold_raw
        ),
        "return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_raw": (
            multi_window_alert_critical_threshold_unmet_windows_threshold_raw
        ),
        "return_sample_multi_window_alert_threshold_raw_normalized_mismatch_count": (
            sample_multi_window_alert_threshold_raw_normalized_mismatch_count
        ),
        "return_sample_multi_window_alert_threshold_raw_normalized_mismatch_ratio": (
            sample_multi_window_alert_threshold_raw_normalized_mismatch_ratio
        ),
        "return_sample_multi_window_alert_threshold_dimensions_total": (
            sample_multi_window_alert_threshold_raw_normalized_dimensions_total
        ),
        "return_sample_multi_window_alert_threshold_normalization_applied": (
            int(multi_window_alert_threshold_normalization_applied)
        ),
        "return_sample_multi_window_alert_critical_low_windows_threshold_normalized": (
            int(multi_window_alert_critical_low_windows_threshold_normalized)
        ),
        "return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_normalized": (
            int(multi_window_alert_critical_threshold_unmet_windows_threshold_normalized)
        ),
        "return_avg": return_avg,
        "return_trimmed_mean_10pct": return_trimmed_mean_10pct,
        "return_winsorized_mean_10pct": return_winsorized_mean_10pct,
        "return_p50": return_p50,
        "return_p90": return_p90,
        "return_p95": return_p95,
        "return_p99": return_p99,
        "return_stddev": return_stddev,
        "direction_sample_size": len(direction_flags),
        "direction_accuracy_pct": direction_accuracy_pct,
    }


def _load_optimization_quality_snapshot(request: Request) -> dict[str, Any]:
    query = "SELECT result_json FROM optimization_jobs WHERE status = 'completed'"
    with request.app.state.database.connection() as conn:
        rows = conn.execute(query).fetchall()

    quality_scores: list[float] = []
    recommendation_counts: dict[str, int] = {}
    for row in rows:
        try:
            payload = json.loads(str(row["result_json"] or "{}"))
        except json.JSONDecodeError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}

        raw_score = payload.get("quality_score")
        if raw_score is not None:
            try:
                quality_scores.append(float(raw_score))
            except (TypeError, ValueError):
                pass

        recommendation = str(payload.get("recommendation") or "").strip()
        if recommendation:
            recommendation_counts[recommendation] = recommendation_counts.get(recommendation, 0) + 1

    quality_score_avg = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0
    return {
        "quality_sample_size": len(quality_scores),
        "quality_score_avg": quality_score_avg,
        "recommendation_counts": recommendation_counts,
    }


@router.get("/metrics")
def get_global_metrics(
    request: Request,
    prompt_lock_audit_service: PromptLockAuditService = Depends(get_prompt_lock_audit_service),
) -> PlainTextResponse:
    app_version = _escape_prometheus_label_value(str(request.app.version))
    backtest_status_counts = _load_status_counts(request=request, table_name="backtest_jobs")
    optimization_status_counts = _load_status_counts(request=request, table_name="optimization_jobs")
    analysis_status_counts = _load_status_counts(request=request, table_name="analysis_jobs")
    workflow_status_counts = _load_status_counts(request=request, table_name="workflow_executions")
    knowledge_doc_status_counts = _load_status_counts(request=request, table_name="knowledge_documents")
    conversation_session_status_counts = _load_status_counts(request=request, table_name="conversation_sessions")
    conversation_message_role_counts = _load_grouped_counts(
        request=request, table_name="conversation_messages", group_column="role"
    )
    memory_summaries_total = _load_total_count(request=request, table_name="memory_summaries")
    long_term_memory_total = _load_total_count(request=request, table_name="long_term_memory_entries")
    conversation_messages_total = _load_total_count(request=request, table_name="conversation_messages")
    knowledge_chunks_total = _load_total_count(request=request, table_name="knowledge_chunks")
    knowledge_chunks_token_total = _load_total_sum(
        request=request, table_name="knowledge_chunks", value_column="token_count"
    )
    backtest_quality = _load_backtest_quality_snapshot(request=request)
    optimization_quality = _load_optimization_quality_snapshot(request=request)
    lines = [
        "# HELP refactor_backend_build_info Backend build info.",
        "# TYPE refactor_backend_build_info gauge",
        f'refactor_backend_build_info{{version="{app_version}"}} 1',
    ]
    _append_status_gauge_lines(
        lines=lines,
        metric_name="refactor_backtest_jobs_total",
        help_text="Current backtest job count grouped by status.",
        counts=backtest_status_counts,
    )
    _append_status_gauge_lines(
        lines=lines,
        metric_name="refactor_optimization_jobs_total",
        help_text="Current optimization job count grouped by status.",
        counts=optimization_status_counts,
    )
    _append_status_gauge_lines(
        lines=lines,
        metric_name="refactor_analysis_jobs_total",
        help_text="Current analysis job count grouped by status.",
        counts=analysis_status_counts,
    )
    _append_status_gauge_lines(
        lines=lines,
        metric_name="refactor_workflow_executions_total",
        help_text="Current workflow execution count grouped by status.",
        counts=workflow_status_counts,
    )
    _append_status_gauge_lines(
        lines=lines,
        metric_name="refactor_knowledge_documents_total",
        help_text="Current knowledge document count grouped by status.",
        counts=knowledge_doc_status_counts,
    )
    _append_status_gauge_lines(
        lines=lines,
        metric_name="refactor_conversation_sessions_total",
        help_text="Current conversation session count grouped by status.",
        counts=conversation_session_status_counts,
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_memory_summaries_total",
        help_text="Current memory summary record count.",
        total=memory_summaries_total,
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_long_term_memory_entries_total",
        help_text="Current long-term memory entry count.",
        total=long_term_memory_total,
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_conversation_messages_total",
        help_text="Current conversation message count.",
        total=conversation_messages_total,
    )
    _append_labeled_gauge_lines(
        lines=lines,
        metric_name="refactor_conversation_messages_by_role_total",
        help_text="Current conversation message count grouped by role.",
        label_name="role",
        counts=conversation_message_role_counts,
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_knowledge_chunks_total",
        help_text="Current knowledge chunk count.",
        total=knowledge_chunks_total,
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_knowledge_chunks_token_count_total",
        help_text="Current summed token count across all knowledge chunks.",
        total=knowledge_chunks_token_total,
    )
    _append_labeled_gauge_lines(
        lines=lines,
        metric_name="refactor_backtest_records_total",
        help_text="Current backtest record count grouped by outcome.",
        label_name="outcome",
        counts=backtest_quality["outcome_counts"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size",
        help_text="Current number of backtest records with return_pct value.",
        total=backtest_quality["return_sample_size"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size_24h",
        help_text="Current number of backtest records with return_pct value in last 24h.",
        total=backtest_quality["return_sample_size_24h"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size_7d",
        help_text="Current number of backtest records with return_pct value in last 7 days.",
        total=backtest_quality["return_sample_size_7d"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size_30d",
        help_text="Current number of backtest records with return_pct value in last 30 days.",
        total=backtest_quality["return_sample_size_30d"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_min_size_required",
        help_text="Minimum sample size required for stable return statistics.",
        total=backtest_quality["return_sample_min_size_required"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_medium_coverage_threshold_pct",
        help_text="Coverage ratio threshold used to classify medium sample adequacy level.",
        value=backtest_quality["return_sample_medium_coverage_threshold_pct"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size_threshold_met",
        help_text="Whether return sample size meets minimum required threshold (1 met, 0 unmet).",
        total=backtest_quality["return_sample_threshold_met"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size_threshold_met_24h",
        help_text="Whether last-24h return sample size meets minimum required threshold (1 met, 0 unmet).",
        total=backtest_quality["return_sample_threshold_met_24h"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size_threshold_met_7d",
        help_text="Whether last-7d return sample size meets minimum required threshold (1 met, 0 unmet).",
        total=backtest_quality["return_sample_threshold_met_7d"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size_threshold_met_30d",
        help_text="Whether last-30d return sample size meets minimum required threshold (1 met, 0 unmet).",
        total=backtest_quality["return_sample_threshold_met_30d"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_threshold_unmet_windows_total",
        help_text="Current number of recent windows (24h/7d/30d) with unmet minimum return sample threshold.",
        total=backtest_quality["return_sample_threshold_unmet_windows_total"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_low_adequacy_windows_total",
        help_text="Current number of recent windows (24h/7d/30d) classified as low return sample adequacy.",
        total=backtest_quality["return_sample_low_adequacy_windows_total"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_multi_window_alert_warn_low_windows_threshold",
        help_text="Configured warn threshold for low adequacy windows (24h/7d/30d), normalized.",
        total=backtest_quality["return_sample_multi_window_alert_warn_low_windows_threshold"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold",
        help_text="Configured warn threshold for threshold-unmet windows (24h/7d/30d), normalized.",
        total=backtest_quality["return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold",
        help_text="Configured critical threshold for low adequacy windows (24h/7d/30d), normalized.",
        total=backtest_quality["return_sample_multi_window_alert_critical_low_windows_threshold"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name=(
            "refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold"
        ),
        help_text="Configured critical threshold for threshold-unmet windows (24h/7d/30d), normalized.",
        total=backtest_quality["return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_multi_window_alert_warn_low_windows_threshold_raw",
        help_text="Configured warn threshold for low adequacy windows (24h/7d/30d), raw before normalization.",
        total=backtest_quality["return_sample_multi_window_alert_warn_low_windows_threshold_raw"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name=(
            "refactor_backtest_records_return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold_raw"
        ),
        help_text="Configured warn threshold for threshold-unmet windows (24h/7d/30d), raw before normalization.",
        total=backtest_quality["return_sample_multi_window_alert_warn_threshold_unmet_windows_threshold_raw"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name=("refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold_raw"),
        help_text="Configured critical threshold for low adequacy windows (24h/7d/30d), raw before normalization.",
        total=backtest_quality["return_sample_multi_window_alert_critical_low_windows_threshold_raw"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name=(
            "refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_raw"
        ),
        help_text=("Configured critical threshold for threshold-unmet windows (24h/7d/30d), raw before normalization."),
        total=backtest_quality["return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_raw"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name=(
            "refactor_backtest_records_return_sample_multi_window_alert_threshold_raw_normalized_mismatch_count"
        ),
        help_text="Current number of threshold dimensions where raw and normalized values differ.",
        total=backtest_quality["return_sample_multi_window_alert_threshold_raw_normalized_mismatch_count"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name=(
            "refactor_backtest_records_return_sample_multi_window_alert_threshold_raw_normalized_mismatch_ratio"
        ),
        help_text="Current ratio of threshold dimensions where raw and normalized values differ (0.0-1.0).",
        value=backtest_quality["return_sample_multi_window_alert_threshold_raw_normalized_mismatch_ratio"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_multi_window_alert_threshold_dimensions_total",
        help_text="Current number of threshold dimensions included in raw-normalized mismatch governance.",
        total=backtest_quality["return_sample_multi_window_alert_threshold_dimensions_total"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_multi_window_alert_threshold_normalization_applied",
        help_text="Whether multi-window alert thresholds were normalized from configured values (1 yes, 0 no).",
        total=backtest_quality["return_sample_multi_window_alert_threshold_normalization_applied"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name=(
            "refactor_backtest_records_return_sample_multi_window_alert_critical_low_windows_threshold_normalized"
        ),
        help_text="Whether critical low-windows threshold was normalized to satisfy critical>=warn (1 yes, 0 no).",
        total=backtest_quality["return_sample_multi_window_alert_critical_low_windows_threshold_normalized"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name=(
            "refactor_backtest_records_return_sample_multi_window_alert_critical_threshold_unmet_windows_"
            "threshold_normalized"
        ),
        help_text=(
            "Whether critical threshold-unmet-windows threshold was normalized to satisfy critical>=warn (1 yes, 0 no)."
        ),
        total=backtest_quality[
            "return_sample_multi_window_alert_critical_threshold_unmet_windows_threshold_normalized"
        ],
    )
    _append_labeled_gauge_lines_ordered(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_multi_window_alert_level",
        help_text="Current multi-window sample alert level one-hot gauge (none/warn/critical).",
        label_name="level",
        ordered_items=[
            ("none", int(backtest_quality["return_sample_multi_window_alert_levels_onehot"]["none"])),
            ("warn", int(backtest_quality["return_sample_multi_window_alert_levels_onehot"]["warn"])),
            ("critical", int(backtest_quality["return_sample_multi_window_alert_levels_onehot"]["critical"])),
        ],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_multi_window_alert_level_score",
        help_text="Current multi-window sample alert level score (none=0.0, warn=0.5, critical=1.0).",
        value=backtest_quality["return_sample_multi_window_alert_level_score"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_size_gap",
        help_text="Remaining sample count needed to meet minimum required threshold.",
        total=backtest_quality["return_sample_size_gap"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_coverage_ratio_pct",
        help_text="Current return sample coverage ratio against required minimum (percentage).",
        value=backtest_quality["return_sample_coverage_ratio_pct"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_coverage_ratio_pct_24h",
        help_text="Last-24h return sample coverage ratio against required minimum (percentage).",
        value=backtest_quality["return_sample_coverage_ratio_pct_24h"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_coverage_ratio_pct_7d",
        help_text="Last-7d return sample coverage ratio against required minimum (percentage).",
        value=backtest_quality["return_sample_coverage_ratio_pct_7d"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_coverage_ratio_pct_30d",
        help_text="Last-30d return sample coverage ratio against required minimum (percentage).",
        value=backtest_quality["return_sample_coverage_ratio_pct_30d"],
    )
    _append_labeled_gauge_lines_ordered(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_adequacy_level",
        help_text="Current return sample adequacy level one-hot gauge (low/medium/high).",
        label_name="level",
        ordered_items=[
            ("low", int(backtest_quality["return_sample_adequacy_levels_onehot"]["low"])),
            ("medium", int(backtest_quality["return_sample_adequacy_levels_onehot"]["medium"])),
            ("high", int(backtest_quality["return_sample_adequacy_levels_onehot"]["high"])),
        ],
    )
    _append_labeled_gauge_lines_ordered(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_adequacy_level_24h",
        help_text="Last-24h return sample adequacy level one-hot gauge (low/medium/high).",
        label_name="level",
        ordered_items=[
            ("low", int(backtest_quality["return_sample_adequacy_levels_onehot_24h"]["low"])),
            ("medium", int(backtest_quality["return_sample_adequacy_levels_onehot_24h"]["medium"])),
            ("high", int(backtest_quality["return_sample_adequacy_levels_onehot_24h"]["high"])),
        ],
    )
    _append_labeled_gauge_lines_ordered(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_adequacy_level_7d",
        help_text="Last-7d return sample adequacy level one-hot gauge (low/medium/high).",
        label_name="level",
        ordered_items=[
            ("low", int(backtest_quality["return_sample_adequacy_levels_onehot_7d"]["low"])),
            ("medium", int(backtest_quality["return_sample_adequacy_levels_onehot_7d"]["medium"])),
            ("high", int(backtest_quality["return_sample_adequacy_levels_onehot_7d"]["high"])),
        ],
    )
    _append_labeled_gauge_lines_ordered(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_adequacy_level_30d",
        help_text="Last-30d return sample adequacy level one-hot gauge (low/medium/high).",
        label_name="level",
        ordered_items=[
            ("low", int(backtest_quality["return_sample_adequacy_levels_onehot_30d"]["low"])),
            ("medium", int(backtest_quality["return_sample_adequacy_levels_onehot_30d"]["medium"])),
            ("high", int(backtest_quality["return_sample_adequacy_levels_onehot_30d"]["high"])),
        ],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_adequacy_score",
        help_text="Current return sample adequacy score (low=0.0, medium=0.5, high=1.0).",
        value=backtest_quality["return_sample_adequacy_score"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_adequacy_score_24h",
        help_text="Last-24h return sample adequacy score (low=0.0, medium=0.5, high=1.0).",
        value=backtest_quality["return_sample_adequacy_score_24h"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_adequacy_score_7d",
        help_text="Last-7d return sample adequacy score (low=0.0, medium=0.5, high=1.0).",
        value=backtest_quality["return_sample_adequacy_score_7d"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_sample_adequacy_score_30d",
        help_text="Last-30d return sample adequacy score (low=0.0, medium=0.5, high=1.0).",
        value=backtest_quality["return_sample_adequacy_score_30d"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_pct_avg",
        help_text="Current average return_pct across backtest records with return value.",
        value=backtest_quality["return_avg"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_pct_trimmed_mean_10pct",
        help_text="Current 10pct trimmed mean return_pct across backtest records with return value.",
        value=backtest_quality["return_trimmed_mean_10pct"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_pct_winsorized_mean_10pct",
        help_text="Current 10pct winsorized mean return_pct across backtest records with return value.",
        value=backtest_quality["return_winsorized_mean_10pct"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_pct_p50",
        help_text="Current p50 return_pct across backtest records with return value.",
        value=backtest_quality["return_p50"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_pct_p90",
        help_text="Current p90 return_pct across backtest records with return value.",
        value=backtest_quality["return_p90"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_pct_p95",
        help_text="Current p95 return_pct across backtest records with return value.",
        value=backtest_quality["return_p95"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_pct_p99",
        help_text="Current p99 return_pct across backtest records with return value.",
        value=backtest_quality["return_p99"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_return_pct_stddev",
        help_text="Current standard deviation of return_pct across backtest records with return value.",
        value=backtest_quality["return_stddev"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_direction_sample_size",
        help_text="Current number of backtest records with direction_correct value.",
        total=backtest_quality["direction_sample_size"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_backtest_records_direction_accuracy_pct",
        help_text="Current direction accuracy percentage across backtest records with direction label.",
        value=backtest_quality["direction_accuracy_pct"],
    )
    _append_total_gauge_line(
        lines=lines,
        metric_name="refactor_optimization_quality_score_sample_size",
        help_text="Current number of completed optimization jobs with quality score.",
        total=optimization_quality["quality_sample_size"],
    )
    _append_float_gauge_line(
        lines=lines,
        metric_name="refactor_optimization_quality_score_avg",
        help_text="Current average quality score across completed optimization jobs.",
        value=optimization_quality["quality_score_avg"],
    )
    _append_labeled_gauge_lines(
        lines=lines,
        metric_name="refactor_optimization_recommendations_total",
        help_text="Current completed optimization recommendation count grouped by recommendation.",
        label_name="recommendation",
        counts=optimization_quality["recommendation_counts"],
    )
    lines.append(prompt_lock_audit_service.get_overview_metrics_prometheus().rstrip("\n"))
    return PlainTextResponse(
        content="\n".join(lines) + "\n",
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
