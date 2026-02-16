from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from app.api.deps import get_prompt_lock_audit_service
from app.services.prompt_lock_audit_service import PromptLockAuditService

router = APIRouter()


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
    lines.append(prompt_lock_audit_service.get_overview_metrics_prometheus().rstrip("\n"))
    return PlainTextResponse(
        content="\n".join(lines) + "\n",
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
