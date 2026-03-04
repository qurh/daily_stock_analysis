from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_agent_service
from app.services.agent_service import AgentService, ToolNotFoundError, ToolSpec

router = APIRouter(prefix="/agent")


class ToolRegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    version: str = "v1"
    description: str | None = None
    timeout_sec: int = Field(default=5, ge=1, le=300)
    max_retries: int = Field(default=0, ge=0, le=10)
    keywords: list[str] = Field(default_factory=list)
    degrade_payload: dict[str, Any] | None = None
    static_response: dict[str, Any] = Field(default_factory=dict)
    overwrite: bool = False


class ToolInvokeRequest(BaseModel):
    intent: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    force_tools: list[str] | None = None


@router.post("/tools/register", status_code=201)
def register_tool(
    request: ToolRegisterRequest,
    service: AgentService = Depends(get_agent_service),
) -> dict[str, Any]:
    try:
        return service.register_static_tool(
            tool_spec=ToolSpec(
                name=request.name,
                version=request.version,
                description=request.description or request.name,
                timeout_sec=request.timeout_sec,
                max_retries=request.max_retries,
                keywords=tuple(request.keywords),
                degrade_payload=request.degrade_payload,
            ),
            static_response=request.static_response,
            overwrite=request.overwrite,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tools")
def list_tools(
    service: AgentService = Depends(get_agent_service),
) -> dict[str, Any]:
    items = service.list_tools()
    return {"items": items, "count": len(items)}


@router.post("/invoke")
def invoke_tools(
    request: ToolInvokeRequest,
    service: AgentService = Depends(get_agent_service),
) -> dict[str, Any]:
    try:
        return service.invoke(
            intent=request.intent,
            payload=request.payload,
            context=request.context,
            force_tools=request.force_tools,
        )
    except ToolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
