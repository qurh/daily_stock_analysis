from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase

TaskHandler = Callable[[dict[str, Any]], dict[str, Any] | None]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskQueueService:
    """Persistent task queue backed by SQLite."""

    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database
        self._handlers: dict[str, TaskHandler] = {}
        self._lock = Lock()

    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        self._handlers[task_type] = handler

    def enqueue(self, task_type: str, payload: dict[str, Any]) -> str:
        task_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO task_queue (task_id, task_type, payload_json, status, result_json, created_at, updated_at)
                VALUES (?, ?, ?, 'pending', NULL, ?, ?)
                """,
                (task_id, task_type, self._database.json_dump(payload), now, now),
            )
        return task_id

    def process_next(self) -> bool:
        with self._lock:
            task = self._claim_next_task()
            if task is None:
                return False
            task_id = task["task_id"]
            task_type = task["task_type"]
            payload = task["payload"]
            handler = self._handlers.get(task_type)
            if handler is None:
                self._finalize_task(task_id=task_id, status="failed", result={"error": f"No handler: {task_type}"})
                return True

            try:
                result = handler(payload) or {}
                self._finalize_task(task_id=task_id, status="succeeded", result=result)
            except Exception as exc:
                self._finalize_task(task_id=task_id, status="failed", result={"error": str(exc)})
                raise
            return True

    def process_all(self, limit: int = 100) -> int:
        processed_count = 0
        while processed_count < limit:
            has_processed = self.process_next()
            if not has_processed:
                break
            processed_count += 1
        return processed_count

    def _claim_next_task(self) -> dict[str, Any] | None:
        with self._database.connection() as conn:
            row = conn.execute("""
                SELECT task_id, task_type, payload_json
                FROM task_queue
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
                """).fetchone()
            if row is None:
                return None
            now = _utc_now()
            conn.execute(
                "UPDATE task_queue SET status = 'running', updated_at = ? WHERE task_id = ?",
                (now, row["task_id"]),
            )
            return {
                "task_id": row["task_id"],
                "task_type": row["task_type"],
                "payload": self._database.json_load(row["payload_json"], {}),
            }

    def _finalize_task(self, task_id: str, status: str, result: dict[str, Any]) -> None:
        with self._database.connection() as conn:
            conn.execute(
                "UPDATE task_queue SET status = ?, result_json = ?, updated_at = ? WHERE task_id = ?",
                (status, self._database.json_dump(result), _utc_now(), task_id),
            )
