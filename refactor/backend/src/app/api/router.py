from fastapi import APIRouter

from app.api.routes.analysis import router as analysis_router
from app.api.routes.backtest import router as backtest_router
from app.api.routes.chat import router as chat_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.health import router as health_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.memory import router as memory_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.optimization import router as optimization_router
from app.api.routes.prompt_lock import router as prompt_lock_router
from app.api.routes.prompts import router as prompts_router
from app.api.routes.strategy import router as strategy_router
from app.api.routes.workflows import router as workflows_router

api_router = APIRouter(prefix="/api/v2")
api_router.include_router(health_router)
api_router.include_router(analysis_router)
api_router.include_router(backtest_router)
api_router.include_router(workflows_router)
api_router.include_router(prompts_router)
api_router.include_router(knowledge_router)
api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(feedback_router)
api_router.include_router(optimization_router)
api_router.include_router(notifications_router)
api_router.include_router(strategy_router)
api_router.include_router(prompt_lock_router)
api_router.include_router(metrics_router)
