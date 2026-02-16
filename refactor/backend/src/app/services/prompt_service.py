from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.persistence.sqlite_db import SQLiteDatabase


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PromptService:
    """Prompt center service backed by persistent storage."""

    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def create_template(self, prompt_id: str, name: str, module: str) -> dict[str, Any]:
        try:
            with self._database.connection() as conn:
                conn.execute(
                    """
                    INSERT INTO prompt_templates
                    (prompt_id, name, module, active_version, previous_active_version, created_at)
                    VALUES (?, ?, ?, NULL, NULL, ?)
                    """,
                    (prompt_id, name, module, _utc_now()),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Template already exists: {prompt_id}") from exc

        return {
            "prompt_id": prompt_id,
            "name": name,
            "module": module,
            "active_version": None,
            "previous_active_version": None,
            "versions": [],
        }

    def add_version(
        self,
        prompt_id: str,
        content: str,
        variables: list[str],
        output_schema: str,
    ) -> dict[str, Any]:
        with self._database.connection() as conn:
            self._require_template(conn=conn, prompt_id=prompt_id)
            row = conn.execute(
                "SELECT COALESCE(MAX(version), 0) AS max_version FROM prompt_versions WHERE prompt_id = ?",
                (prompt_id,),
            ).fetchone()
            version = int(row["max_version"]) + 1
            created_at = _utc_now()
            conn.execute(
                """
                INSERT INTO prompt_versions
                (prompt_id, version, content, variables_json, output_schema, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'draft', ?)
                """,
                (prompt_id, version, content, self._database.json_dump(variables), output_schema, created_at),
            )

        return {
            "version": version,
            "content": content,
            "variables": variables,
            "output_schema": output_schema,
            "status": "draft",
            "created_at": created_at,
        }

    def publish_version(self, prompt_id: str, version: int) -> dict[str, Any]:
        with self._database.connection() as conn:
            template = self._require_template(conn=conn, prompt_id=prompt_id)
            self._require_version(conn=conn, prompt_id=prompt_id, version=version)
            active_version = template["active_version"]
            if active_version is not None and active_version != version:
                conn.execute(
                    "UPDATE prompt_versions SET status = 'inactive' WHERE prompt_id = ? AND version = ?",
                    (prompt_id, active_version),
                )
            conn.execute(
                "UPDATE prompt_versions SET status = 'active' WHERE prompt_id = ? AND version = ?",
                (prompt_id, version),
            )
            conn.execute(
                """
                UPDATE prompt_templates
                SET active_version = ?, previous_active_version = ?
                WHERE prompt_id = ?
                """,
                (version, active_version, prompt_id),
            )
        return {"prompt_id": prompt_id, "active_version": version}

    def rollback(self, prompt_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            template = self._require_template(conn=conn, prompt_id=prompt_id)
            active_version = template["active_version"]
            previous_active_version = template["previous_active_version"]
            if previous_active_version is None:
                return {"prompt_id": prompt_id, "active_version": active_version}

            if active_version is not None and active_version != previous_active_version:
                conn.execute(
                    "UPDATE prompt_versions SET status = 'rolled_back' WHERE prompt_id = ? AND version = ?",
                    (prompt_id, active_version),
                )

            conn.execute(
                "UPDATE prompt_versions SET status = 'active' WHERE prompt_id = ? AND version = ?",
                (prompt_id, previous_active_version),
            )
            conn.execute(
                """
                UPDATE prompt_templates
                SET active_version = ?, previous_active_version = NULL
                WHERE prompt_id = ?
                """,
                (previous_active_version, prompt_id),
            )

        return {"prompt_id": prompt_id, "active_version": previous_active_version}

    def get_template(self, prompt_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            template = self._require_template(conn=conn, prompt_id=prompt_id)
            versions = conn.execute(
                """
                SELECT version, content, variables_json, output_schema, status, created_at
                FROM prompt_versions
                WHERE prompt_id = ?
                ORDER BY version ASC
                """,
                (prompt_id,),
            ).fetchall()

        return {
            "prompt_id": template["prompt_id"],
            "name": template["name"],
            "module": template["module"],
            "active_version": template["active_version"],
            "versions": [
                {
                    "version": item["version"],
                    "content": item["content"],
                    "variables": self._database.json_load(item["variables_json"], []),
                    "output_schema": item["output_schema"],
                    "status": item["status"],
                    "created_at": item["created_at"],
                }
                for item in versions
            ],
        }

    def render_active_prompt(self, prompt_id: str, variables: dict[str, str]) -> dict[str, Any]:
        with self._database.connection() as conn:
            template = self._require_template(conn=conn, prompt_id=prompt_id)
            active_version = template["active_version"]
            if active_version is None:
                raise KeyError(f"No active version for prompt: {prompt_id}")
            version_row = conn.execute(
                """
                SELECT content, variables_json
                FROM prompt_versions
                WHERE prompt_id = ? AND version = ?
                """,
                (prompt_id, active_version),
            ).fetchone()
            if version_row is None:
                raise KeyError(f"Version not found: {active_version}")

        rendered = self._render_prompt_row(version_row=version_row, variables=variables)
        return {
            "prompt_ref": f"{prompt_id}@{active_version}",
            "rendered_prompt": rendered,
            "version": active_version,
        }

    def render_prompt_version(self, prompt_id: str, version: int, variables: dict[str, str]) -> dict[str, Any]:
        with self._database.connection() as conn:
            self._require_template(conn=conn, prompt_id=prompt_id)
            version_row = conn.execute(
                """
                SELECT content, variables_json
                FROM prompt_versions
                WHERE prompt_id = ? AND version = ?
                """,
                (prompt_id, version),
            ).fetchone()
            if version_row is None:
                raise KeyError(f"Version not found: {version}")

        rendered = self._render_prompt_row(version_row=version_row, variables=variables)
        return {
            "prompt_ref": f"{prompt_id}@{version}",
            "rendered_prompt": rendered,
            "version": version,
        }

    def _render_prompt_row(self, version_row: Any, variables: dict[str, str]) -> str:
        required_variables = self._database.json_load(version_row["variables_json"], [])
        missing_variables = [name for name in required_variables if name not in variables]
        if missing_variables:
            raise ValueError(f"Missing variables: {', '.join(missing_variables)}")
        return _render_template(version_row["content"], variables)

    @staticmethod
    def _require_template(conn: sqlite3.Connection, prompt_id: str) -> sqlite3.Row:
        row = conn.execute(
            """
            SELECT prompt_id, name, module, active_version, previous_active_version, created_at
            FROM prompt_templates
            WHERE prompt_id = ?
            """,
            (prompt_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Template not found: {prompt_id}")
        return row

    @staticmethod
    def _require_version(conn: sqlite3.Connection, prompt_id: str, version: int) -> sqlite3.Row:
        row = conn.execute(
            "SELECT version FROM prompt_versions WHERE prompt_id = ? AND version = ?",
            (prompt_id, version),
        ).fetchone()
        if row is None:
            raise KeyError(f"Version not found: {version}")
        return row


def _render_template(template: str, variables: dict[str, str]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered
