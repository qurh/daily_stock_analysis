from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_workflow_service
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows")


class WorkflowExecutionStartRequest(BaseModel):
    flow_id: str = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionAcceptedResponse(BaseModel):
    execution_id: str
    status: str


@router.post("/executions", status_code=202, response_model=WorkflowExecutionAcceptedResponse)
def create_workflow_execution(
    request: WorkflowExecutionStartRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, str]:
    return service.start_execution(flow_id=request.flow_id, flow_input=request.input)


@router.get("/executions/{execution_id}")
def get_workflow_execution(
    execution_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, Any]:
    execution = service.get_execution(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")
    return execution


@router.post("/executions/{execution_id}/cancel")
def cancel_workflow_execution(
    execution_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, Any]:
    cancelled = service.cancel_execution(execution_id)
    if cancelled is None:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")
    return cancelled
