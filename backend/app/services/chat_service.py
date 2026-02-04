"""Chat Service.

Provides:
- Chat message processing
- Streaming response support
- RAG integration
- Knowledge base import
"""

import uuid
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatHistory,
    ImportRequest,
    ImportResponse,
)
from app.services.ai_router import AIRouter
from app.services.rag_engine import RAGEngine
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


class ChatService:
    """Chat service for AI conversations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter()
        self.rag_engine = RAGEngine(db)

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Process a chat message and generate response."""
        # Build context from history
        context = self._build_context(request.context)

        # Get RAG context if enabled
        sources = None
        if request.use_rag:
            await self.rag_engine.initialize(self.db)
            sources = await self.rag_engine.search(request.message, limit=5)

        # Generate response
        response_text = await self.ai_router.generate(
            message=request.message,
            context=context,
            sources=sources,
            model=request.model,
            stream=False,
        )

        # Build response
        response = ChatResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            message=ChatMessage(
                role="assistant",
                content=response_text,
                model=request.model or self.ai_router.get_default_model(),
            ),
            sources=sources,
            model=request.model or self.ai_router.get_default_model(),
        )

        return response

    async def process_message_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """Process a chat message with streaming response."""
        # Build context from history
        context = self._build_context(request.context)

        # Get RAG context if enabled
        sources = None
        if request.use_rag:
            await self.rag_engine.initialize(self.db)
            sources = await self.rag_engine.search(request.message, limit=5)

        # Stream response
        async for chunk in self.ai_router.generate_stream(
            message=request.message,
            context=context,
            sources=sources,
            model=request.model,
        ):
            yield chunk

    async def get_history(self, limit: int = 50, offset: int = 0) -> List[ChatHistory]:
        """Get chat history."""
        # TODO: Implement with chat history table
        return []

    async def import_to_knowledge(self, request: ImportRequest) -> ImportResponse:
        """Import chat content to knowledge base."""
        knowledge_service = KnowledgeService(self.db)

        # Create document from chat content
        doc = await knowledge_service.create_document_from_content(
            title=request.title,
            content=request.content,
            category_id=request.category_id,
            tags=request.tags,
            related_codes=request.related_codes,
        )

        return ImportResponse(
            id=doc.id,
            title=doc.title,
            url=f"/kb/docs/{doc.id}",
            message="Successfully imported to knowledge base",
        )

    def _build_context(self, messages: Optional[List[ChatMessage]]) -> List[Dict[str, str]]:
        """Build context list from chat messages."""
        if not messages:
            return []

        context = []
        for msg in messages:
            context.append({
                "role": msg.role,
                "content": msg.content,
            })
        return context
