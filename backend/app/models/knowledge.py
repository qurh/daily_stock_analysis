"""Knowledge Base Models."""

from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Date, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampMixin


class KBCategory(TimestampMixin):
    """Knowledge base categories."""

    __tablename__ = "kb_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class KBDocument(TimestampMixin):
    """Knowledge base documents."""

    __tablename__ = "kb_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200))
    category_id: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/published/archived
    content: Mapped[str] = mapped_column(Text)
    content_html: Mapped[str] = mapped_column(Text)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String))
    related_codes: Mapped[List[str]] = mapped_column(ARRAY(String))
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)


class KBEntity(TimestampMixin):
    """Knowledge entities (companies, industries, concepts)."""

    __tablename__ = "kb_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # company/industry/concept
    code: Mapped[str] = mapped_column(String(10))
    description: Mapped[str] = mapped_column(Text)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)


class KBEntityRelation(TimestampMixin):
    """Entity relations for knowledge graph."""

    __tablename__ = "kb_entity_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(default=1.0)


class KBEmbedding(TimestampMixin):
    """Vector embeddings for RAG."""

    __tablename__ = "kb_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[List[float]] = mapped_column(JSON)  # pgvector stores as JSON in async
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)


class KBSearchLog(TimestampMixin):
    """RAG search logs."""

    __tablename__ = "kb_search_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_doc_ids: Mapped[List[int]] = mapped_column(ARRAY(Integer))
    result: Mapped[str] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(String(50))
    execution_time_ms: Mapped[int] = mapped_column(Integer)
