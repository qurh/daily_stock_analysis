from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS task_queue (
    task_id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    result_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_task_queue_status_created_at
ON task_queue (status, created_at);

CREATE TABLE IF NOT EXISTS workflow_executions (
    execution_id TEXT PRIMARY KEY,
    flow_id TEXT NOT NULL,
    input_json TEXT NOT NULL,
    status TEXT NOT NULL,
    output_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_trace_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_trace_execution_id
ON workflow_trace_nodes (execution_id, id);

CREATE TABLE IF NOT EXISTS analysis_jobs (
    job_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    report_type TEXT NOT NULL,
    status TEXT NOT NULL,
    result_json TEXT,
    execution_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id)
);

CREATE TABLE IF NOT EXISTS backtest_jobs (
    job_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    symbol TEXT,
    eval_window_days INTEGER NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL,
    metrics_json TEXT,
    engine_version TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_backtest_jobs_status_created_at
ON backtest_jobs (status, created_at);

CREATE TABLE IF NOT EXISTS backtest_records (
    record_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    analysis_job_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    outcome TEXT NOT NULL,
    return_pct REAL,
    direction_correct INTEGER,
    flags_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES backtest_jobs(job_id),
    FOREIGN KEY (analysis_job_id) REFERENCES analysis_jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_backtest_records_job_id
ON backtest_records (job_id, created_at);

CREATE INDEX IF NOT EXISTS idx_backtest_records_symbol
ON backtest_records (symbol, created_at);

CREATE TABLE IF NOT EXISTS feedback_records (
    feedback_id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    score REAL NOT NULL,
    tags_json TEXT NOT NULL,
    comment TEXT,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_records_target
ON feedback_records (target_type, target_id, created_at);

CREATE TABLE IF NOT EXISTS optimization_jobs (
    job_id TEXT PRIMARY KEY,
    trigger_source TEXT NOT NULL,
    reason TEXT,
    backtest_job_id TEXT,
    status TEXT NOT NULL,
    feature_set_json TEXT,
    result_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (backtest_job_id) REFERENCES backtest_jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_optimization_jobs_status_created_at
ON optimization_jobs (status, created_at);

CREATE TABLE IF NOT EXISTS change_proposals (
    proposal_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    summary TEXT,
    diff_json TEXT NOT NULL,
    status TEXT NOT NULL,
    gate_result_json TEXT,
    reviewer TEXT,
    review_note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_change_proposals_status_created_at
ON change_proposals (status, created_at);

CREATE TABLE IF NOT EXISTS cognition_memos (
    memo_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    markdown TEXT NOT NULL,
    source_sessions_json TEXT NOT NULL,
    source_message_ids_json TEXT NOT NULL,
    status TEXT NOT NULL,
    reviewer TEXT,
    review_notes TEXT,
    knowledge_doc_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (knowledge_doc_id) REFERENCES knowledge_documents(doc_id)
);

CREATE INDEX IF NOT EXISTS idx_cognition_memos_status_created_at
ON cognition_memos (status, created_at);

CREATE TABLE IF NOT EXISTS strategy_artifacts (
    strategy_id TEXT PRIMARY KEY,
    strategy_type TEXT NOT NULL,
    version INTEGER NOT NULL,
    rules_json TEXT NOT NULL,
    thresholds_json TEXT NOT NULL,
    conditions_json TEXT NOT NULL,
    source_memo_ids_json TEXT NOT NULL,
    status TEXT NOT NULL,
    gate_result_json TEXT,
    backtest_job_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(strategy_type, version),
    FOREIGN KEY (backtest_job_id) REFERENCES backtest_jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_strategy_artifacts_type_status
ON strategy_artifacts (strategy_type, status, created_at);

CREATE TABLE IF NOT EXISTS strategy_bindings (
    binding_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    flow_id TEXT NOT NULL,
    prompt_refs_json TEXT NOT NULL,
    effective_scope_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (strategy_id) REFERENCES strategy_artifacts(strategy_id)
);

CREATE INDEX IF NOT EXISTS idx_strategy_bindings_flow_status
ON strategy_bindings (flow_id, status, created_at);

CREATE TABLE IF NOT EXISTS strategy_publish_gate_events (
    event_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    gate_code TEXT NOT NULL,
    require_proposal_id INTEGER NOT NULL,
    blocked INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (strategy_id) REFERENCES strategy_artifacts(strategy_id)
);

CREATE INDEX IF NOT EXISTS idx_strategy_publish_gate_events_created_at
ON strategy_publish_gate_events (created_at);

CREATE INDEX IF NOT EXISTS idx_strategy_publish_gate_events_gate_code
ON strategy_publish_gate_events (gate_code, require_proposal_id, blocked, created_at);

CREATE TABLE IF NOT EXISTS prompt_lock_events (
    event_id TEXT PRIMARY KEY,
    flow_id TEXT NOT NULL,
    lock_mode TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT,
    requested_prompt_refs_json TEXT NOT NULL,
    failures_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_prompt_lock_events_flow_created_at
ON prompt_lock_events (flow_id, created_at);

CREATE INDEX IF NOT EXISTS idx_prompt_lock_events_source_created_at
ON prompt_lock_events (source_type, created_at);

CREATE TABLE IF NOT EXISTS prompt_templates (
    prompt_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    module TEXT NOT NULL,
    active_version INTEGER,
    previous_active_version INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    variables_json TEXT NOT NULL,
    output_schema TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(prompt_id, version),
    FOREIGN KEY (prompt_id) REFERENCES prompt_templates(prompt_id)
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    raw_markdown TEXT NOT NULL,
    optimized_markdown TEXT NOT NULL,
    status TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    section_path TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding_ref TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES knowledge_documents(doc_id)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_doc_id
ON knowledge_chunks (doc_id);

CREATE TABLE IF NOT EXISTS conversation_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    memory_policy TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    citations_json TEXT NOT NULL,
    tool_trace_json TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_id
ON conversation_messages (session_id, created_at);

CREATE TABLE IF NOT EXISTS memory_summaries (
    summary_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    covered_range TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    embedding_ref TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_memory_summaries_session_id
ON memory_summaries (session_id, created_at);

CREATE TABLE IF NOT EXISTS long_term_memory_entries (
    entry_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    score REAL NOT NULL,
    source_session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_session_id) REFERENCES conversation_sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_long_term_memory_session_id
ON long_term_memory_entries (source_session_id, created_at);

CREATE TABLE IF NOT EXISTS notification_deliveries (
    delivery_id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    provider_message_id TEXT,
    payload_preview TEXT,
    created_at TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    retry_of_delivery_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_notification_deliveries_created_at
ON notification_deliveries (created_at);

CREATE INDEX IF NOT EXISTS idx_notification_deliveries_source
ON notification_deliveries (source_type, source_id, created_at);
"""


class SQLiteDatabase:
    """SQLite database helper with schema bootstrap."""

    def __init__(self, database_url: str) -> None:
        self._database_path = self._parse_sqlite_path(database_url)
        self._ensure_parent_directory()

    @property
    def database_path(self) -> str:
        return self._database_path

    def init_schema(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA_SQL)
            self._ensure_column(
                conn=conn,
                table_name="notification_deliveries",
                column_name="attempt_count",
                column_ddl="INTEGER NOT NULL DEFAULT 1",
            )
            self._ensure_column(
                conn=conn,
                table_name="notification_deliveries",
                column_name="retry_of_delivery_id",
                column_ddl="TEXT",
            )

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def json_dump(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def json_load(raw: str | None, default: Any) -> Any:
        if raw is None:
            return default
        return json.loads(raw)

    @staticmethod
    def _parse_sqlite_path(database_url: str) -> str:
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            raise ValueError("Only sqlite database URLs are supported. Expected sqlite:///path/to/file.sqlite3")
        path_str = database_url[len(prefix) :]
        if path_str == ":memory:":
            return ":memory:"
        raw_path = Path(path_str).expanduser()
        if raw_path.is_absolute():
            return str(raw_path)
        return str((Path.cwd() / raw_path).resolve())

    def _ensure_parent_directory(self) -> None:
        if self._database_path == ":memory:":
            return
        Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _ensure_column(
        conn: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_ddl: str,
    ) -> None:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        existing = {str(row["name"]) for row in rows}
        if column_name in existing:
            return
        try:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_ddl}")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise
