from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session

from backend.app.api.response import ok
from backend.app.config import get_config
from backend.app.db.api_database import get_db
from backend.app.models.api_models import Stock
from backend.app.models.api_models import utcnow
from backend.app.schemas.api_schemas import StockSyncItem, StockSyncRequest

router = APIRouter()


def _guess_market(code: str) -> str:
    if code.startswith("6"):
        return "SH"
    if code.startswith(("0", "3")):
        return "SZ"
    return "CN"


def _resolve_sort(sort: str | None):
    sortable = {
        "code": Stock.code,
        "name": Stock.name,
        "industry": Stock.industry,
        "market": Stock.market,
        "updated_at": Stock.updated_at,
    }
    if not sort:
        return desc(Stock.updated_at)
    field, _, direction = sort.partition(":")
    column = sortable.get(field, Stock.updated_at)
    if direction.lower() == "asc":
        return asc(column)
    return desc(column)


@router.get("/stocks")
def list_stocks(
    request: Request,
    q: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    sort: str | None = Query(default="updated_at:desc"),
    db: Session = Depends(get_db),
):
    query = db.query(Stock)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Stock.code.ilike(like), Stock.name.ilike(like)))
    if industry:
        query = query.filter(Stock.industry == industry)

    total = query.with_entities(func.count()).scalar() or 0
    items = (
        query.order_by(_resolve_sort(sort))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    data = {
        "items": [
            {
                "code": item.code,
                "name": item.name,
                "industry": item.industry,
                "market": item.market,
                "is_active": item.is_active,
                "updated_at": item.updated_at.isoformat(),
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return ok(data=data, request=request)


@router.post("/stocks/sync")
def sync_stocks(
    payload: StockSyncRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    stock_items: list[StockSyncItem]
    if payload.stocks:
        stock_items = payload.stocks
    else:
        stock_items = [
            StockSyncItem(code=code, name=code, market=_guess_market(code))
            for code in get_config().stock_list
        ]

    now = utcnow()
    synced = 0
    upserted_codes: set[str] = set()

    for item in stock_items:
        code = item.code.strip()
        if not code or code in upserted_codes:
            continue
        upserted_codes.add(code)

        stock = db.get(Stock, code)
        if stock is None:
            stock = Stock(
                code=code,
                name=item.name or code,
                industry=item.industry,
                market=item.market or _guess_market(code),
                is_active=item.is_active,
                updated_at=now,
            )
            db.add(stock)
            synced += 1
            continue

        stock.name = item.name or stock.name
        stock.industry = item.industry if item.industry is not None else stock.industry
        stock.market = item.market or stock.market or _guess_market(code)
        stock.is_active = item.is_active
        stock.updated_at = now
        synced += 1

    db.commit()
    return ok(data={"synced": synced}, request=request)
