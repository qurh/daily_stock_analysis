from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_memory_service
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memory")


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


@router.get("/sessions/{session_id}")
def get_memory_session(
    session_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> dict[str, Any]:
    try:
        return service.get_session(session_id=session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/summarize")
def summarize_memory_session(
    session_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> dict[str, Any]:
    try:
        return service.summarize_session(session_id=session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/search")
def search_memory(
    request: MemorySearchRequest,
    service: MemoryService = Depends(get_memory_service),
) -> dict[str, Any]:
    return service.search_long_term(query=request.query, top_k=request.top_k)


@router.delete("/sessions/{session_id}")
def delete_memory_session(
    session_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> dict[str, Any]:
    try:
        return service.delete_session(session_id=session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
