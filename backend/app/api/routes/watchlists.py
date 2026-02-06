from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.api.response import ok
from backend.app.db.api_database import get_db
from backend.app.models.api_models import Stock, Watchlist, WatchlistStock
from backend.app.models.api_models import utcnow
from backend.app.schemas.api_schemas import WatchlistCreate, WatchlistStockCreate, WatchlistUpdate

router = APIRouter()

DEFAULT_USER_ID = 1


def _guess_market(code: str) -> str:
    if code.startswith("6"):
        return "SH"
    if code.startswith(("0", "3")):
        return "SZ"
    return "CN"


def _get_watchlist_or_404(db: Session, watchlist_id: int) -> Watchlist:
    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == DEFAULT_USER_ID)
        .first()
    )
    if watchlist is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    return watchlist


@router.get("/watchlists")
def list_watchlists(request: Request, db: Session = Depends(get_db)):
    watchlists = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == DEFAULT_USER_ID)
        .order_by(Watchlist.sort_order.asc(), Watchlist.id.asc())
        .all()
    )
    data = {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "sort_order": item.sort_order,
                "stock_count": len(item.stocks),
                "created_at": item.created_at.isoformat(),
            }
            for item in watchlists
        ]
    }
    return ok(data=data, request=request)


@router.post("/watchlists")
def create_watchlist(payload: WatchlistCreate, request: Request, db: Session = Depends(get_db)):
    existing = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == DEFAULT_USER_ID,
            Watchlist.name == payload.name.strip(),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=422, detail="watchlist name already exists")

    watchlist = Watchlist(
        user_id=DEFAULT_USER_ID,
        name=payload.name.strip(),
        sort_order=payload.sort_order,
    )
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)

    data = {
        "id": watchlist.id,
        "name": watchlist.name,
        "sort_order": watchlist.sort_order,
        "stock_count": 0,
        "created_at": watchlist.created_at.isoformat(),
    }
    return ok(data=data, request=request)


@router.put("/watchlists/{watchlist_id}")
def update_watchlist(
    watchlist_id: int,
    payload: WatchlistUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    watchlist = _get_watchlist_or_404(db, watchlist_id)

    if payload.name is not None:
        new_name = payload.name.strip()
        duplicate = (
            db.query(Watchlist)
            .filter(
                Watchlist.user_id == DEFAULT_USER_ID,
                Watchlist.name == new_name,
                Watchlist.id != watchlist.id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=422, detail="watchlist name already exists")
        watchlist.name = new_name

    if payload.sort_order is not None:
        watchlist.sort_order = payload.sort_order

    db.commit()
    db.refresh(watchlist)

    data = {
        "id": watchlist.id,
        "name": watchlist.name,
        "sort_order": watchlist.sort_order,
        "stock_count": len(watchlist.stocks),
        "created_at": watchlist.created_at.isoformat(),
    }
    return ok(data=data, request=request)


@router.delete("/watchlists/{watchlist_id}")
def delete_watchlist(watchlist_id: int, request: Request, db: Session = Depends(get_db)):
    watchlist = _get_watchlist_or_404(db, watchlist_id)
    db.query(WatchlistStock).filter(WatchlistStock.watchlist_id == watchlist.id).delete()
    db.delete(watchlist)
    db.commit()
    return ok(data={"id": watchlist_id}, request=request)


@router.post("/watchlists/{watchlist_id}/stocks")
def add_stock_to_watchlist(
    watchlist_id: int,
    payload: WatchlistStockCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    watchlist = _get_watchlist_or_404(db, watchlist_id)
    code = payload.code.strip()

    existing = (
        db.query(WatchlistStock)
        .filter(WatchlistStock.watchlist_id == watchlist.id, WatchlistStock.code == code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=422, detail="stock already exists in watchlist")

    stock = db.get(Stock, code)
    if stock is None:
        stock = Stock(
            code=code,
            name=code,
            market=_guess_market(code),
            is_active=True,
            updated_at=utcnow(),
        )
        db.add(stock)

    relation = WatchlistStock(
        watchlist_id=watchlist.id,
        code=code,
        sort_order=payload.sort_order,
    )
    db.add(relation)
    db.commit()
    return ok(data={"watchlist_id": watchlist.id, "code": code}, request=request)


@router.delete("/watchlists/{watchlist_id}/stocks/{code}")
def remove_stock_from_watchlist(
    watchlist_id: int,
    code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    watchlist = _get_watchlist_or_404(db, watchlist_id)
    relation = (
        db.query(WatchlistStock)
        .filter(WatchlistStock.watchlist_id == watchlist.id, WatchlistStock.code == code)
        .first()
    )
    if relation is None:
        raise HTTPException(status_code=404, detail="stock not found in watchlist")

    db.delete(relation)
    db.commit()
    return ok(data={"watchlist_id": watchlist.id, "code": code}, request=request)
