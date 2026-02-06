from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from backend.app.api.response import ok
from backend.app.db.api_database import get_db
from backend.app.models.api_models import AnalysisReport

router = APIRouter()


def _resolve_sort(sort: str | None):
    sortable = {
        "generated_at": AnalysisReport.generated_at,
        "report_date": AnalysisReport.report_date,
        "code": AnalysisReport.code,
    }
    if not sort:
        return desc(AnalysisReport.generated_at)
    field, _, direction = sort.partition(":")
    column = sortable.get(field, AnalysisReport.generated_at)
    if direction.lower() == "asc":
        return asc(column)
    return desc(column)


def _list_payload(query, page: int, page_size: int, sort: str | None) -> dict:
    total = query.with_entities(func.count()).scalar() or 0
    items = (
        query.order_by(_resolve_sort(sort))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {
                "id": item.id,
                "code": item.code,
                "report_type": item.report_type,
                "report_date": item.report_date.isoformat(),
                "generated_at": item.generated_at.isoformat(),
                "status": item.status,
                "source": item.source,
                "model": item.model,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _read_markdown(markdown_path: str) -> str:
    path = Path(markdown_path)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    else:
        path = path.resolve()
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="report markdown not found")
    return path.read_text(encoding="utf-8")


@router.get("/stock/{code}/reports")
def list_stock_reports(
    code: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    sort: str | None = Query(default="generated_at:desc"),
    db: Session = Depends(get_db),
):
    query = db.query(AnalysisReport).filter(AnalysisReport.code == code)
    return ok(data=_list_payload(query, page, page_size, sort), request=request)


@router.get("/reports")
def list_reports(
    request: Request,
    code: str | None = Query(default=None),
    report_date: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    sort: str | None = Query(default="generated_at:desc"),
    db: Session = Depends(get_db),
):
    query = db.query(AnalysisReport)
    if code:
        query = query.filter(AnalysisReport.code == code)
    if report_date:
        try:
            parsed_date = date.fromisoformat(report_date)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid report_date format") from exc
        query = query.filter(AnalysisReport.report_date == parsed_date)
    return ok(data=_list_payload(query, page, page_size, sort), request=request)


@router.get("/reports/{report_id}")
def report_detail(report_id: int, request: Request, db: Session = Depends(get_db)):
    report = db.get(AnalysisReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")

    markdown = _read_markdown(report.markdown_path)
    metadata = {
        "id": report.id,
        "code": report.code,
        "report_type": report.report_type,
        "report_date": report.report_date.isoformat(),
        "generated_at": report.generated_at.isoformat(),
        "status": report.status,
        "source": report.source,
        "model": report.model,
    }
    return ok(data={"markdown": markdown, "metadata": metadata}, request=request)
