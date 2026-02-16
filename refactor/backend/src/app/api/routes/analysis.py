from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_analysis_service
from app.services.analysis_service import AnalysisService

router = APIRouter()


class AnalysisJobCreateRequest(BaseModel):
    symbol: str = Field(min_length=1)
    report_type: str = "detailed"


class AnalysisJobAcceptedResponse(BaseModel):
    job_id: str
    status: str


@router.post("/analysis/jobs", status_code=202, response_model=AnalysisJobAcceptedResponse)
def create_analysis_job(
    request: AnalysisJobCreateRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> dict[str, str]:
    return service.submit_job(symbol=request.symbol, report_type=request.report_type)


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> dict[str, Any]:
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job
