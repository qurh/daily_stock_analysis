"""Chat Service Schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message."""

    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    model: Optional[str] = Field(None, description="Model used for this message")


class ChatRequest(BaseModel):
    """Chat request schema."""

    message: str = Field(..., description="User message")
    context: Optional[List[ChatMessage]] = Field(
        default=None, description="Previous messages for context"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional options",
    )
    use_rag: bool = Field(default=True, description="Use RAG for this query")
    model: Optional[str] = Field(
        default=None, description="Specific model to use (overrides default)"
    )
    stream: bool = Field(default=True, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat response schema."""

    response_id: str = Field(..., description="Unique response ID")
    message: ChatMessage = Field(..., description="Assistant response")
    sources: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="RAG source documents"
    )
    tokens_used: Optional[int] = Field(None, description="Total tokens used")
    model: str = Field(..., description="Model used")
    finish_reason: Optional[str] = Field(None, description="Completion reason")


class ChatHistory(BaseModel):
    """Chat history entry."""

    id: int
    message: str
    response: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime


class ModelInfo(BaseModel):
    """AI model information."""

    id: str
    name: str
    provider: str
    description: Optional[str] = None
    strengths: Optional[List[str]] = None
    enabled: bool = True
    priority: int = 100


class ImportRequest(BaseModel):
    """Request to import chat content to knowledge base."""

    message_id: Optional[str] = Field(None, description="Original message ID")
    content: str = Field(..., description="Content to import")
    title: str = Field(..., description="Document title")
    category_id: Optional[int] = Field(None, description="Target category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags")
    related_codes: Optional[List[str]] = Field(
        default_factory=list, description="Related stock codes"
    )


class ImportResponse(BaseModel):
    """Import response schema."""

    id: int = Field(..., description="Created document ID")
    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Document URL")
    message: str = Field(default="Successfully imported")
