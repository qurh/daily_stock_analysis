from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_knowledge_service
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge")


class DocumentUploadRequest(BaseModel):
    title: str = Field(min_length=1)
    markdown: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


@router.post("/documents/upload", status_code=201)
def upload_document(
    request: DocumentUploadRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    return service.upload_document(title=request.title, markdown=request.markdown, tags=request.tags)


@router.post("/documents/{doc_id}/optimize")
def optimize_document(
    doc_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    try:
        return service.optimize_document(doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/documents/{doc_id}/ingest", status_code=202)
def ingest_document(
    doc_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    try:
        return service.ingest_document(doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/documents/{doc_id}")
def get_document(
    doc_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    try:
        return service.get_document(doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/chunks/search")
def search_chunks(
    query: str = Query(min_length=1),
    top_k: int = Query(default=5, ge=1, le=20),
    doc_id: str | None = Query(default=None),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    return service.search_chunks(query=query, top_k=top_k, doc_id=doc_id)


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    try:
        return service.delete_document(doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
