from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.knowledge.chunker import chunk_markdown, normalize_markdown
from app.knowledge.summarizer import summarize_chunk
from app.knowledge.vector_store import ChromaVectorStore
from app.persistence.sqlite_db import SQLiteDatabase


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeService:
    """Knowledge ingestion and retrieval service."""

    def __init__(self, database: SQLiteDatabase, vector_store: ChromaVectorStore) -> None:
        self._database = database
        self._vector_store = vector_store

    def upload_document(self, title: str, markdown: str, tags: list[str]) -> dict[str, Any]:
        doc_id = str(uuid4())
        now = _utc_now()
        optimized_markdown = normalize_markdown(markdown)
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO knowledge_documents
                (
                    doc_id,
                    title,
                    source_type,
                    raw_markdown,
                    optimized_markdown,
                    status,
                    tags_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    title,
                    "manual_upload",
                    markdown,
                    optimized_markdown,
                    "UPLOADED",
                    self._database.json_dump(tags),
                    now,
                    now,
                ),
            )
        return {
            "doc_id": doc_id,
            "title": title,
            "status": "UPLOADED",
            "tags": tags,
        }

    def optimize_document(self, doc_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = conn.execute(
                "SELECT raw_markdown FROM knowledge_documents WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Document not found: {doc_id}")
            optimized_markdown = normalize_markdown(row["raw_markdown"])
            conn.execute(
                """
                UPDATE knowledge_documents
                SET optimized_markdown = ?, status = 'CLEANED', updated_at = ?
                WHERE doc_id = ?
                """,
                (optimized_markdown, _utc_now(), doc_id),
            )
        return {"doc_id": doc_id, "status": "CLEANED", "optimized_markdown": optimized_markdown}

    def ingest_document(self, doc_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = conn.execute(
                """
                SELECT title, optimized_markdown, tags_json
                FROM knowledge_documents
                WHERE doc_id = ?
                """,
                (doc_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Document not found: {doc_id}")
            optimized_markdown = normalize_markdown(row["optimized_markdown"])
            conn.execute(
                """
                UPDATE knowledge_documents
                SET optimized_markdown = ?, status = 'CHUNKED', updated_at = ?
                WHERE doc_id = ?
                """,
                (optimized_markdown, _utc_now(), doc_id),
            )

        chunk_items = chunk_markdown(optimized_markdown)
        chunk_records: list[dict[str, Any]] = []
        now = _utc_now()
        for item in chunk_items:
            chunk_id = str(uuid4())
            chunk_records.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "section_path": item.section_path,
                    "content": item.content,
                    "summary": summarize_chunk(item.content),
                    "token_count": item.token_count,
                    "embedding_ref": chunk_id,
                    "created_at": now,
                }
            )

        with self._database.connection() as conn:
            conn.execute("DELETE FROM knowledge_chunks WHERE doc_id = ?", (doc_id,))
            if chunk_records:
                conn.executemany(
                    """
                    INSERT INTO knowledge_chunks
                    (chunk_id, doc_id, section_path, content, summary, token_count, embedding_ref, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            record["chunk_id"],
                            record["doc_id"],
                            record["section_path"],
                            record["content"],
                            record["summary"],
                            record["token_count"],
                            record["embedding_ref"],
                            record["created_at"],
                        )
                        for record in chunk_records
                    ],
                )
            conn.execute(
                "UPDATE knowledge_documents SET status = 'COMPLETED', updated_at = ? WHERE doc_id = ?",
                (_utc_now(), doc_id),
            )

        self._vector_store.delete_document(doc_id)
        self._vector_store.upsert_chunks(chunk_records)
        return {"doc_id": doc_id, "status": "COMPLETED", "chunk_count": len(chunk_records)}

    def get_document(self, doc_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = conn.execute(
                """
                SELECT doc_id, title, source_type, status, tags_json, created_at, updated_at
                FROM knowledge_documents
                WHERE doc_id = ?
                """,
                (doc_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Document not found: {doc_id}")
            chunk_count_row = conn.execute(
                "SELECT COUNT(*) AS count FROM knowledge_chunks WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()

        return {
            "doc_id": row["doc_id"],
            "title": row["title"],
            "source_type": row["source_type"],
            "status": row["status"],
            "tags": self._database.json_load(row["tags_json"], []),
            "chunk_count": int(chunk_count_row["count"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def search_chunks(self, query: str, top_k: int, doc_id: str | None = None) -> dict[str, Any]:
        hits = self._vector_store.search(query=query, top_k=top_k, doc_id=doc_id)
        return {"hits": hits}

    def delete_document(self, doc_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            existing = conn.execute(
                "SELECT 1 FROM knowledge_documents WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()
            if existing is None:
                raise KeyError(f"Document not found: {doc_id}")
            conn.execute("DELETE FROM knowledge_chunks WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM knowledge_documents WHERE doc_id = ?", (doc_id,))
        self._vector_store.delete_document(doc_id)
        return {"doc_id": doc_id, "deleted": True}
