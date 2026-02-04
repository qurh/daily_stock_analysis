"""API Router Configuration."""

from fastapi import APIRouter

from app.api.routes import (
    chat,
    knowledge,
    market,
    portfolio,
    monitor,
    strategy,
    review,
    config,
    models,
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(knowledge.router, prefix="/kb", tags=["Knowledge Base"])
api_router.include_router(market.router, prefix="/market", tags=["Market Data"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(monitor.router, prefix="/monitor", tags=["Monitor"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["Strategy"])
api_router.include_router(review.router, prefix="/review", tags=["Review"])
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
api_router.include_router(models.router, prefix="/models", tags=["AI Models"])
