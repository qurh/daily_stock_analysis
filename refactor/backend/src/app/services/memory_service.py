from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.memory.vector_store import MemoryVectorStore
from app.persistence.sqlite_db import SQLiteDatabase


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryService:
    """Session memory service backed by SQLite and Chroma."""

    def __init__(self, database: SQLiteDatabase, vector_store: MemoryVectorStore) -> None:
        self._database = database
        self._vector_store = vector_store

    def create_session(self, user_id: str, memory_policy: str = "summary_v1") -> dict[str, Any]:
        session_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO conversation_sessions (session_id, user_id, memory_policy, status, created_at, updated_at)
                VALUES (?, ?, ?, 'ACTIVE', ?, ?)
                """,
                (session_id, user_id, memory_policy, now, now),
            )
        return {
            "session_id": session_id,
            "user_id": user_id,
            "memory_policy": memory_policy,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        }

    def get_session(self, session_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = self._require_session(conn=conn, session_id=session_id)
            summary_rows = conn.execute(
                """
                SELECT summary_id, covered_range, summary_text, embedding_ref, created_at
                FROM memory_summaries
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
            message_count_row = conn.execute(
                "SELECT COUNT(*) AS count FROM conversation_messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return {
            "session_id": row["session_id"],
            "user_id": row["user_id"],
            "memory_policy": row["memory_policy"],
            "status": row["status"],
            "message_count": int(message_count_row["count"]),
            "summaries": [
                {
                    "summary_id": item["summary_id"],
                    "covered_range": item["covered_range"],
                    "summary_text": item["summary_text"],
                    "embedding_ref": item["embedding_ref"],
                    "created_at": item["created_at"],
                }
                for item in summary_rows
            ],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        tool_trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        citations_payload = citations or []
        trace_payload = tool_trace or {}
        message_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            self._require_session(conn=conn, session_id=session_id)
            conn.execute(
                """
                INSERT INTO conversation_messages
                (message_id, session_id, role, content, citations_json, tool_trace_json, token_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    self._database.json_dump(citations_payload),
                    self._database.json_dump(trace_payload),
                    len(content),
                    now,
                ),
            )
            conn.execute(
                "UPDATE conversation_sessions SET status = 'ACTIVE', updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
        return {
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "citations": citations_payload,
            "tool_trace": trace_payload,
            "created_at": now,
        }

    def list_messages(self, session_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            self._require_session(conn=conn, session_id=session_id)
            rows = conn.execute(
                """
                SELECT message_id, session_id, role, content, citations_json, tool_trace_json, created_at
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return {
            "session_id": session_id,
            "messages": [
                {
                    "message_id": row["message_id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "citations": self._database.json_load(row["citations_json"], []),
                    "tool_trace": self._database.json_load(row["tool_trace_json"], {}),
                    "created_at": row["created_at"],
                }
                for row in rows
            ],
        }

    def summarize_session(self, session_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            self._require_session(conn=conn, session_id=session_id)
            rows = conn.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()

        summary_lines = [f"{row['role']}: {row['content']}" for row in rows[-6:]]
        if summary_lines:
            summary_text = " | ".join(summary_lines)
        else:
            summary_text = "No conversation messages found."
        if len(summary_text) > 400:
            summary_text = f"{summary_text[:397]}..."

        summary_id = str(uuid4())
        entry_id = str(uuid4())
        covered_range = f"1-{max(len(rows), 0)}"
        topic = _extract_topic(summary_text)
        now = _utc_now()
        with self._database.connection() as conn:
            self._require_session(conn=conn, session_id=session_id)
            conn.execute(
                """
                INSERT INTO memory_summaries
                (summary_id, session_id, covered_range, summary_text, embedding_ref, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (summary_id, session_id, covered_range, summary_text, summary_id, now),
            )
            conn.execute(
                """
                INSERT INTO long_term_memory_entries
                (entry_id, topic, content, score, source_session_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (entry_id, topic, summary_text, 1.0, session_id, now),
            )

        self._vector_store.upsert_entries(
            [
                {
                    "entry_id": entry_id,
                    "topic": topic,
                    "content": summary_text,
                    "score": 1.0,
                    "source_session_id": session_id,
                }
            ]
        )
        return {
            "session_id": session_id,
            "summary_id": summary_id,
            "summary_text": summary_text,
            "long_term_entry_id": entry_id,
        }

    def search_long_term(self, query: str, top_k: int = 5) -> dict[str, Any]:
        hits = self._vector_store.search(query=query, top_k=top_k)
        return {"hits": hits}

    def delete_session(self, session_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            self._require_session(conn=conn, session_id=session_id)
            conn.execute(
                "DELETE FROM long_term_memory_entries WHERE source_session_id = ?",
                (session_id,),
            )
            conn.execute("DELETE FROM memory_summaries WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM conversation_messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM conversation_sessions WHERE session_id = ?", (session_id,))
        self._vector_store.delete_session(session_id=session_id)
        return {"session_id": session_id, "deleted": True}

    @staticmethod
    def _require_session(conn: Any, session_id: str) -> Any:
        row = conn.execute(
            """
            SELECT session_id, user_id, memory_policy, status, created_at, updated_at
            FROM conversation_sessions
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Session not found: {session_id}")
        return row


def _extract_topic(text: str, max_words: int = 8) -> str:
    tokens = [token for token in text.replace("|", " ").split(" ") if token]
    if not tokens:
        return "general"
    return " ".join(tokens[:max_words])
