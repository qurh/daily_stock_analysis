from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FeedbackService:
    """Feedback domain service for collection and lightweight aggregation."""

    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def record(
        self,
        target_type: str,
        target_id: str,
        score: float,
        tags: list[str] | None = None,
        comment: str | None = None,
        source: str = "user",
    ) -> dict[str, Any]:
        normalized_target_type = (target_type or "").strip().lower()
        normalized_target_id = (target_id or "").strip()
        normalized_source = (source or "user").strip().lower()
        if not normalized_target_type:
            raise ValueError("target_type is required")
        if not normalized_target_id:
            raise ValueError("target_id is required")
        if normalized_source not in {"user", "chatbot", "system", "manual"}:
            raise ValueError(f"Unsupported feedback source: {source}")

        normalized_score = float(score)
        if normalized_score < 0 or normalized_score > 5:
            raise ValueError("score must be in range [0, 5]")

        feedback_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO feedback_records (
                    feedback_id, target_type, target_id, score, tags_json, comment, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    normalized_target_type,
                    normalized_target_id,
                    normalized_score,
                    self._database.json_dump(tags or []),
                    comment,
                    normalized_source,
                    now,
                ),
            )
        return {
            "feedback_id": feedback_id,
            "target_type": normalized_target_type,
            "target_id": normalized_target_id,
            "score": normalized_score,
            "tags": tags or [],
            "comment": comment,
            "source": normalized_source,
            "created_at": now,
        }

    def list_records(
        self,
        target_type: str | None = None,
        target_id: str | None = None,
        source: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        safe_limit = max(min(int(limit), 500), 1)
        query = """
            SELECT
                feedback_id, target_type, target_id, score, tags_json, comment, source, created_at
            FROM feedback_records
            WHERE 1 = 1
        """
        params: list[Any] = []
        if target_type:
            query += " AND target_type = ?"
            params.append(target_type)
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)
        if source:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(safe_limit)
        with self._database.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        items = [
            {
                "feedback_id": row["feedback_id"],
                "target_type": row["target_type"],
                "target_id": row["target_id"],
                "score": row["score"],
                "tags": self._database.json_load(row["tags_json"], []),
                "comment": row["comment"],
                "source": row["source"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
        return {"items": items, "count": len(items)}

    def build_feature_snapshot(self, limit: int = 200) -> dict[str, Any]:
        safe_limit = max(min(int(limit), 1000), 1)
        with self._database.connection() as conn:
            rows = conn.execute(
                """
                SELECT score, source, created_at
                FROM feedback_records
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

        if not rows:
            return {
                "count": 0,
                "avg_score": None,
                "min_score": None,
                "max_score": None,
                "by_source": {},
                "latest_at": None,
            }

        scores = [float(row["score"]) for row in rows]
        by_source: dict[str, int] = {}
        for row in rows:
            source = row["source"]
            by_source[source] = by_source.get(source, 0) + 1
        return {
            "count": len(rows),
            "avg_score": round(sum(scores) / len(scores), 4),
            "min_score": min(scores),
            "max_score": max(scores),
            "by_source": by_source,
            "latest_at": rows[0]["created_at"],
        }
