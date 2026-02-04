"""Knowledge Base Service."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.schemas.knowledge import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    KnowledgeGraphResponse,
    ImportFromChatRequest,
)
from app.models.knowledge import (
    KBDocument,
    KBCategory,
    KBEntity,
    KBEntityRelation,
    KBEmbedding,
)
from app.services.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Knowledge base service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rag_engine = RAGEngine()

    async def list_documents(
        self,
        category_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> DocumentListResponse:
        """List documents with filters."""
        query = select(KBDocument)

        if category_id:
            query = query.where(KBDocument.category_id == category_id)

        if tags:
            query = query.where(KBDocument.tags.contains(tags))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # Get documents
        query = query.offset(offset).limit(limit).order_by(KBDocument.updated_at.desc())
        result = await self.db.execute(query)
        documents = result.scalars().all()

        return DocumentListResponse(
            documents=[self._to_document_response(d) for d in documents],
            total=total or 0,
            limit=limit,
            offset=offset,
        )

    async def get_document(self, doc_id: int) -> DocumentResponse:
        """Get document by ID."""
        query = select(KBDocument).where(KBDocument.id == doc_id)
        result = await self.db.execute(query)
        doc = result.scalar_one_or_none()

        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        return self._to_document_response(doc)

    async def create_document(self, doc: DocumentCreate) -> DocumentResponse:
        """Create a new document."""
        document = KBDocument(
            title=doc.title,
            slug=doc.slug or self._generate_slug(doc.title),
            category_id=doc.category_id,
            content=doc.content,
            tags=doc.tags,
            related_codes=doc.related_codes,
            metadata=doc.metadata or {},
            status="draft",
        )

        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        # Generate embedding
        await self.rag_engine.index_document(document)

        return self._to_document_response(document)

    async def update_document(
        self, doc_id: int, update: DocumentUpdate
    ) -> DocumentResponse:
        """Update document."""
        query = select(KBDocument).where(KBDocument.id == doc_id)
        result = await self.db.execute(query)
        doc = result.scalar_one_or_none()

        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        # Update fields
        if update.title is not None:
            doc.title = update.title
        if update.content is not None:
            doc.content = update.content
        if update.category_id is not None:
            doc.category_id = update.category_id
        if update.tags is not None:
            doc.tags = update.tags
        if update.related_codes is not None:
            doc.related_codes = update.related_codes
        if update.metadata is not None:
            doc.metadata = update.metadata
        if update.status is not None:
            doc.status = update.status

        doc.version += 1
        await self.db.flush()
        await self.db.refresh(doc)

        # Re-index if content changed
        if update.content:
            await self.rag_engine.index_document(doc)

        return self._to_document_response(doc)

    async def delete_document(self, doc_id: int) -> None:
        """Delete document."""
        query = select(KBDocument).where(KBDocument.id == doc_id)
        result = await self.db.execute(query)
        doc = result.scalar_one_or_none()

        if doc:
            await self.db.delete(doc)
            await self.db.flush()

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Search knowledge base with vector similarity."""
        results = await self.rag_engine.search(
            query=request.query,
            limit=request.limit,
            filters=request.filters,
        )

        return SearchResponse(
            query=request.query,
            results=[
                SearchResult(
                    document_id=r.document_id,
                    title=r.title,
                    content=r.content,
                    score=r.score,
                    highlights=r.highlights,
                    metadata=r.metadata or {},
                )
                for r in results
            ],
            total=len(results),
            took_ms=0,
        )

    async def get_graph(
        self,
        entity_type: Optional[str] = None,
        entity_code: Optional[str] = None,
    ) -> KnowledgeGraphResponse:
        """Get knowledge graph for visualization."""
        # Get entities
        query = select(KBEntity)
        if entity_type:
            query = query.where(KBEntity.type == entity_type)
        if entity_code:
            query = query.where(KBEntity.code == entity_code)

        result = await self.db.execute(query)
        entities = result.scalars().all()

        # Get relations
        entity_ids = [e.id for e in entities]
        if entity_ids:
            rel_query = select(KBEntityRelation).where(
                (KBEntityRelation.source_entity_id.in_(entity_ids))
                | (KBEntityRelation.target_entity_id.in_(entity_ids))
            )
            rel_result = await self.db.execute(rel_query)
            relations = rel_result.scalars().all()
        else:
            relations = []

        return KnowledgeGraphResponse(
            nodes=[{"id": e.id, "name": e.name, "type": e.type, "code": e.code, "metadata": e.metadata or {}} for e in entities],
            edges=[
                {
                    "source": r.source_entity_id,
                    "target": r.target_entity_id,
                    "relation_type": r.relation_type,
                    "weight": r.weight,
                }
                for r in relations
            ],
        )

    async def import_from_chat(self, request: ImportFromChatRequest):
        """Import content from chat to knowledge base."""
        return await self.create_document(
            DocumentCreate(
                title=request.title,
                content=request.content,
                category_id=request.category_id,
                tags=request.tags,
                related_codes=request.related_codes,
                metadata={"source": "chat_import", "message_id": request.message_id},
            )
        )

    async def create_document_from_content(
        self,
        title: str,
        content: str,
        category_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        related_codes: Optional[List[str]] = None,
    ) -> KBDocument:
        """Create document from content (internal helper)."""
        doc = KBDocument(
            title=title,
            slug=self._generate_slug(title),
            category_id=category_id,
            content=content,
            tags=tags or [],
            related_codes=related_codes or [],
            metadata={"source": "chat_import"},
            auto_generated=False,
        )

        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)

        # Index in RAG
        await self.rag_engine.index_document(doc)

        return doc

    def _to_document_response(self, doc: KBDocument) -> DocumentResponse:
        """Convert model to response schema."""
        return DocumentResponse(
            id=doc.id,
            title=doc.title,
            slug=doc.slug,
            category_id=doc.category_id,
            status=doc.status,
            content=doc.content,
            tags=doc.tags or [],
            related_codes=doc.related_codes or [],
            auto_generated=doc.auto_generated,
            version=doc.version,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title."""
        import re
        slug = title.lower().replace(" ", "-")
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        return slug[:100]
