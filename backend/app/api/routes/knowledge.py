"""Knowledge Base API Routes."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.knowledge import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    CategoryCreate,
    CategoryResponse,
    SearchRequest,
    SearchResponse,
    KnowledgeGraphResponse,
    ImportFromChatRequest,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.get("/docs", response_model=DocumentListResponse)
async def list_documents(
    category_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_db),
):
    """List documents with optional filters."""
    service = KnowledgeService(db)
    return await service.list_documents(
        category_id=category_id,
        tags=tags,
        limit=limit,
        offset=offset,
    )


@router.post("/docs", response_model=DocumentResponse)
async def create_document(
    doc: DocumentCreate,
    db=Depends(get_db),
):
    """Create a new document."""
    service = KnowledgeService(db)
    return await service.create_document(doc)


@router.get("/docs/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    db=Depends(get_db),
):
    """Get document by ID."""
    service = KnowledgeService(db)
    return await service.get_document(doc_id)


@router.put("/docs/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: int,
    doc: DocumentUpdate,
    db=Depends(get_db),
):
    """Update document."""
    service = KnowledgeService(db)
    return await service.update_document(doc_id, doc)


@router.delete("/docs/{doc_id}")
async def delete_document(
    doc_id: int,
    db=Depends(get_db),
):
    """Delete document."""
    service = KnowledgeService(db)
    await service.delete_document(doc_id)
    return {"message": "Document deleted"}


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    db=Depends(get_db),
):
    """Search knowledge base with vector similarity."""
    service = KnowledgeService(db)
    return await service.search(request)


@router.get("/graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    entity_type: Optional[str] = None,
    entity_code: Optional[str] = None,
    db=Depends(get_db),
):
    """Get knowledge graph for visualization."""
    service = KnowledgeService(db)
    return await service.get_graph(entity_type=entity_type, entity_code=entity_code)


@router.post("/from-chat")
async def import_from_chat(
    request: ImportFromChatRequest,
    db=Depends(get_db),
):
    """Import content from chat to knowledge base."""
    service = KnowledgeService(db)
    return await service.import_from_chat(request)
