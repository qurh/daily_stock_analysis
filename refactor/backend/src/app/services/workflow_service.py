from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase
from app.services.task_queue_service import TaskQueueService


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowService:
    """Workflow execution service backed by persistent storage."""

    def __init__(
        self,
        database: SQLiteDatabase,
        task_queue: TaskQueueService,
        queue_auto_process: bool = True,
    ) -> None:
        self._database = database
        self._task_queue = task_queue
        self._queue_auto_process = queue_auto_process
        self._task_queue.register_handler("workflow.run", self._handle_workflow_task)

    def start_execution(
        self,
        flow_id: str,
        flow_input: dict[str, Any],
        enqueue: bool = True,
        defer_run: bool = False,
    ) -> dict[str, str]:
        execution_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO workflow_executions (
                    execution_id, flow_id, input_json, status, output_json, created_at, updated_at
                )
                VALUES (?, ?, ?, 'pending', NULL, ?, ?)
                """,
                (execution_id, flow_id, self._database.json_dump(flow_input), now, now),
            )

        if defer_run:
            pass
        elif enqueue:
            self._task_queue.enqueue("workflow.run", {"execution_id": execution_id})
            if self._queue_auto_process:
                self._task_queue.process_all()
        else:
            self._run_flow(execution_id)

        execution = self.get_execution(execution_id)
        return {"execution_id": execution_id, "status": execution["status"]}

    def complete_execution(
        self,
        execution_id: str,
        trace_nodes: list[dict[str, Any]],
        output: dict[str, Any] | None = None,
    ) -> None:
        now = _utc_now()
        with self._database.connection() as conn:
            row = conn.execute(
                "SELECT status FROM workflow_executions WHERE execution_id = ?",
                (execution_id,),
            ).fetchone()
            if row is None or row["status"] == "cancelled":
                return
            conn.execute(
                "UPDATE workflow_executions SET status = 'running', updated_at = ? WHERE execution_id = ?",
                (now, execution_id),
            )
            self._persist_trace_nodes(conn=conn, execution_id=execution_id, trace_nodes=trace_nodes)
            conn.execute(
                """
                UPDATE workflow_executions
                SET status = 'succeeded', output_json = ?, updated_at = ?
                WHERE execution_id = ?
                """,
                (self._database.json_dump(output or {}), now, execution_id),
            )

    def fail_execution(
        self,
        execution_id: str,
        trace_nodes: list[dict[str, Any]],
        output: dict[str, Any] | None = None,
    ) -> None:
        now = _utc_now()
        with self._database.connection() as conn:
            row = conn.execute(
                "SELECT status FROM workflow_executions WHERE execution_id = ?",
                (execution_id,),
            ).fetchone()
            if row is None or row["status"] == "cancelled":
                return
            self._persist_trace_nodes(conn=conn, execution_id=execution_id, trace_nodes=trace_nodes)
            conn.execute(
                """
                UPDATE workflow_executions
                SET status = 'failed', output_json = ?, updated_at = ?
                WHERE execution_id = ?
                """,
                (self._database.json_dump(output or {}), now, execution_id),
            )

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        with self._database.connection() as conn:
            row = conn.execute(
                """
                SELECT execution_id, flow_id, input_json, status, output_json, created_at, updated_at
                FROM workflow_executions
                WHERE execution_id = ?
                """,
                (execution_id,),
            ).fetchone()
            if row is None:
                return None

            node_rows = conn.execute(
                """
                SELECT
                    node_id,
                    status,
                    started_at,
                    ended_at,
                    attempts,
                    duration_ms,
                    degraded,
                    failure_code,
                    degrade_reason,
                    failure_context
                FROM workflow_trace_nodes
                WHERE execution_id = ?
                ORDER BY id ASC
                """,
                (execution_id,),
            ).fetchall()

        return {
            "execution_id": row["execution_id"],
            "flow_id": row["flow_id"],
            "input": self._database.json_load(row["input_json"], {}),
            "status": row["status"],
            "output": self._database.json_load(row["output_json"], {}),
            "trace": {
                "flow_id": row["flow_id"],
                "nodes": [
                    {
                        "node_id": item["node_id"],
                        "status": item["status"],
                        "started_at": item["started_at"],
                        "ended_at": item["ended_at"],
                        "attempts": int(item["attempts"]),
                        "duration_ms": int(item["duration_ms"]),
                        "degraded": bool(item["degraded"]),
                        "failure_code": item["failure_code"],
                        "degrade_reason": item["degrade_reason"],
                        "failure_context": item["failure_context"],
                    }
                    for item in node_rows
                ],
            },
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def cancel_execution(self, execution_id: str) -> dict[str, Any] | None:
        with self._database.connection() as conn:
            row = conn.execute(
                "SELECT status FROM workflow_executions WHERE execution_id = ?",
                (execution_id,),
            ).fetchone()
            if row is None:
                return None

            is_cancellable = row["status"] in {"pending", "running"}
            if is_cancellable:
                conn.execute(
                    "UPDATE workflow_executions SET status = 'cancelled', updated_at = ? WHERE execution_id = ?",
                    (_utc_now(), execution_id),
                )
            return {"execution_id": execution_id, "cancelled": is_cancellable}

    def _handle_workflow_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        execution_id = payload["execution_id"]
        self._run_flow(execution_id=execution_id)
        execution = self.get_execution(execution_id)
        if execution is None:
            return {"execution_id": execution_id, "status": "missing"}
        return {"execution_id": execution_id, "status": execution["status"]}

    def _run_flow(self, execution_id: str) -> None:
        with self._database.connection() as conn:
            row = conn.execute(
                "SELECT flow_id, status FROM workflow_executions WHERE execution_id = ?",
                (execution_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Execution not found: {execution_id}")
            if row["status"] in {"cancelled", "succeeded", "failed"}:
                return

            conn.execute(
                "UPDATE workflow_executions SET status = 'running', updated_at = ? WHERE execution_id = ?",
                (_utc_now(), execution_id),
            )

        with self._database.connection() as conn:
            row = conn.execute(
                "SELECT flow_id, status FROM workflow_executions WHERE execution_id = ?",
                (execution_id,),
            ).fetchone()
            if row is None or row["status"] == "cancelled":
                return

            flow_id = row["flow_id"]
            node_start = _utc_now()
            node_end = _utc_now()
            conn.execute("DELETE FROM workflow_trace_nodes WHERE execution_id = ?", (execution_id,))
            conn.executemany(
                """
                INSERT INTO workflow_trace_nodes (
                    execution_id, node_id, status, started_at, ended_at, attempts, duration_ms, degraded,
                    failure_code, degrade_reason, failure_context
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (execution_id, "collect_data", "succeeded", node_start, node_end, 1, 0, 0, None, None, None),
                    (
                        execution_id,
                        "generate_report",
                        "succeeded",
                        node_start,
                        node_end,
                        1,
                        0,
                        0,
                        None,
                        None,
                        None,
                    ),
                ],
            )
            output = {"summary": f"Flow {flow_id} completed"}
            conn.execute(
                """
                UPDATE workflow_executions
                SET status = 'succeeded', output_json = ?, updated_at = ?
                WHERE execution_id = ?
                """,
                (self._database.json_dump(output), _utc_now(), execution_id),
            )

    def _persist_trace_nodes(
        self,
        conn: Any,
        execution_id: str,
        trace_nodes: list[dict[str, Any]],
    ) -> None:
        now = _utc_now()
        conn.execute("DELETE FROM workflow_trace_nodes WHERE execution_id = ?", (execution_id,))
        rows = [
            (
                execution_id,
                item["node_id"],
                item.get("status", "succeeded"),
                now,
                now,
                int(item.get("attempts", 1)),
                int(item.get("duration_ms", 0)),
                1 if bool(item.get("degraded", False)) else 0,
                item.get("failure_code"),
                item.get("degrade_reason"),
                item.get("failure_context"),
            )
            for item in trace_nodes
        ]
        if rows:
            conn.executemany(
                """
                INSERT INTO workflow_trace_nodes (
                    execution_id, node_id, status, started_at, ended_at, attempts, duration_ms, degraded,
                    failure_code, degrade_reason, failure_context
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
