from fastapi import APIRouter

from backend.app.api.routes.reports import router as reports_router
from backend.app.api.routes.stocks import router as stocks_router
from backend.app.api.routes.watchlists import router as watchlists_router

api_router = APIRouter()
api_router.include_router(stocks_router)
api_router.include_router(watchlists_router)
api_router.include_router(reports_router)
