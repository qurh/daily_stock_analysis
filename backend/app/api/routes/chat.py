"""Chat Service API Routes."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.db.database import get_db
from app.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatHistory,
    ModelInfo,
    ImportRequest,
    ImportResponse,
)
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db=Depends(get_db),
):
    """Send chat message and get response."""
    service = ChatService(db)
    return await service.process_message(request)


@router.get("/history", response_model=List[ChatHistory])
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_db),
):
    """Get chat history."""
    service = ChatService(db)
    return await service.get_history(limit=limit, offset=offset)


@router.get("/models", response_model=List[ModelInfo])
async def get_available_models():
    """Get list of available AI models."""
    from app.services.ai_router import get_available_models

    return get_available_models()


@router.post("/import", response_model=ImportResponse)
async def import_to_knowledge(
    request: ImportRequest,
    db=Depends(get_db),
):
    """Import chat content to knowledge base."""
    service = ChatService(db)
    return await service.import_to_knowledge(request)
