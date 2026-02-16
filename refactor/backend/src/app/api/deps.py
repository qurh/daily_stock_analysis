from fastapi import Request

from app.services.analysis_service import AnalysisService
from app.services.backtest_service import BacktestService
from app.services.chat_service import ChatService
from app.services.feedback_service import FeedbackService
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.services.optimization_service import OptimizationService
from app.services.prompt_lock_audit_service import PromptLockAuditService
from app.services.prompt_service import PromptService
from app.services.strategy_service import StrategyService
from app.services.workflow_service import WorkflowService


def get_analysis_service(request: Request) -> AnalysisService:
    return request.app.state.analysis_service


def get_backtest_service(request: Request) -> BacktestService:
    return request.app.state.backtest_service


def get_feedback_service(request: Request) -> FeedbackService:
    return request.app.state.feedback_service


def get_optimization_service(request: Request) -> OptimizationService:
    return request.app.state.optimization_service


def get_strategy_service(request: Request) -> StrategyService:
    return request.app.state.strategy_service


def get_workflow_service(request: Request) -> WorkflowService:
    return request.app.state.workflow_service


def get_prompt_service(request: Request) -> PromptService:
    return request.app.state.prompt_service


def get_knowledge_service(request: Request) -> KnowledgeService:
    return request.app.state.knowledge_service


def get_memory_service(request: Request) -> MemoryService:
    return request.app.state.memory_service


def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


def get_prompt_lock_audit_service(request: Request) -> PromptLockAuditService:
    return request.app.state.prompt_lock_audit_service
