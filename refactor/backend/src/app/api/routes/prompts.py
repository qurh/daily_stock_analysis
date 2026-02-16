from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_prompt_service
from app.services.prompt_service import PromptService

router = APIRouter(prefix="/prompts")


class PromptTemplateCreateRequest(BaseModel):
    prompt_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    module: str = Field(min_length=1)


class PromptTemplateVersionCreateRequest(BaseModel):
    content: str
    variables: list[str] = Field(default_factory=list)
    output_schema: str = Field(min_length=1)


@router.post("/templates", status_code=201)
def create_prompt_template(
    request: PromptTemplateCreateRequest,
    service: PromptService = Depends(get_prompt_service),
) -> dict[str, Any]:
    try:
        return service.create_template(prompt_id=request.prompt_id, name=request.name, module=request.module)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/templates/{prompt_id}/versions", status_code=201)
def create_prompt_version(
    prompt_id: str,
    request: PromptTemplateVersionCreateRequest,
    service: PromptService = Depends(get_prompt_service),
) -> dict[str, Any]:
    try:
        return service.add_version(
            prompt_id=prompt_id,
            content=request.content,
            variables=request.variables,
            output_schema=request.output_schema,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/templates/{prompt_id}/versions/{version}/publish")
def publish_prompt_version(
    prompt_id: str,
    version: int,
    service: PromptService = Depends(get_prompt_service),
) -> dict[str, Any]:
    try:
        return service.publish_version(prompt_id=prompt_id, version=version)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/templates/{prompt_id}/rollback")
def rollback_prompt_version(
    prompt_id: str,
    service: PromptService = Depends(get_prompt_service),
) -> dict[str, Any]:
    try:
        return service.rollback(prompt_id=prompt_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/templates/{prompt_id}")
def get_prompt_template(
    prompt_id: str,
    service: PromptService = Depends(get_prompt_service),
) -> dict[str, Any]:
    try:
        return service.get_template(prompt_id=prompt_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
