from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_chat_service
from app.llm.provider import LLMProviderError
from app.services.chat_service import ChatService
from app.services.prompt_routing import PromptLockError

router = APIRouter(prefix="/chat")


class ChatSessionCreateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    memory_policy: str = "summary_v1"


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)


@router.post("/sessions", status_code=201)
def create_chat_session(
    request: ChatSessionCreateRequest,
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    return service.create_session(user_id=request.user_id, memory_policy=request.memory_policy)


@router.post("/sessions/{session_id}/messages")
def post_chat_message(
    session_id: str,
    request: ChatMessageCreateRequest,
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    try:
        return service.handle_message(session_id=session_id, content=request.content)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PromptLockError as exc:
        raise HTTPException(status_code=409, detail=exc.to_detail()) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LLMProviderError as exc:
        if exc.category == "rate_limit":
            status_code = 429
        elif exc.category == "circuit_open":
            status_code = 503
        else:
            status_code = 502
        raise HTTPException(
            status_code=status_code,
            detail={
                "error_code": "LLM_PROVIDER_ERROR",
                "provider": exc.provider,
                "provider_error_code": exc.error_code,
                "category": exc.category,
                "retryable": exc.retryable,
                "message": exc.error_message,
            },
        ) from exc


@router.get("/sessions/{session_id}/messages")
def list_chat_messages(
    session_id: str,
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    try:
        return service.list_messages(session_id=session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
