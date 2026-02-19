from fastapi import FastAPI

from app.api.router import api_router
from app.core.settings import load_settings
from app.knowledge.vector_store import ChromaVectorStore
from app.llm.provider import create_llm_provider
from app.memory.vector_store import MemoryVectorStore
from app.persistence.sqlite_db import SQLiteDatabase
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
from app.services.task_queue_service import TaskQueueService
from app.services.workflow_service import WorkflowService
from app.shared.logging_config import setup_logging


def create_app() -> FastAPI:
    setup_logging(level="INFO")
    settings = load_settings()
    database = SQLiteDatabase(settings.database_url)
    database.init_schema()
    knowledge_vector_store = ChromaVectorStore(
        path=settings.chroma_path,
        collection_name=settings.chroma_collection,
    )
    memory_vector_store = MemoryVectorStore(
        path=settings.chroma_path,
        collection_name=settings.memory_collection,
    )
    llm_provider = create_llm_provider(
        provider_name=settings.llm_provider,
        model_name=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout_sec=settings.llm_timeout_sec,
        max_retries=settings.llm_max_retries,
        retry_backoff_ms=settings.llm_retry_backoff_ms,
        circuit_failure_threshold=settings.llm_circuit_failure_threshold,
        circuit_reset_timeout_ms=settings.llm_circuit_reset_timeout_ms,
        dashscope_api_key=settings.dashscope_api_key,
        dashscope_base_http_api_url=settings.dashscope_base_http_api_url,
        dashscope_enable_thinking=settings.dashscope_enable_thinking,
    )

    task_queue = TaskQueueService(database=database)
    workflow_service = WorkflowService(
        database=database,
        task_queue=task_queue,
        queue_auto_process=settings.queue_auto_process,
    )
    prompt_service = PromptService(database=database)
    knowledge_service = KnowledgeService(database=database, vector_store=knowledge_vector_store)
    strategy_service = StrategyService(database=database, knowledge_service=knowledge_service)
    prompt_lock_audit_service = PromptLockAuditService(
        database=database,
        overview_cache_ttl_sec=settings.prompt_lock_overview_cache_ttl_sec,
        overview_cache_max_size=settings.prompt_lock_overview_cache_max_size,
        overview_module_timeout_sec=settings.prompt_lock_overview_module_timeout_sec,
        overview_module_timeouts_sec={
            "summary": settings.prompt_lock_overview_timeout_summary_sec,
            "grouped": settings.prompt_lock_overview_timeout_grouped_sec,
            "trends": settings.prompt_lock_overview_timeout_trends_sec,
        },
    )
    analysis_service = AnalysisService(
        database=database,
        workflow_service=workflow_service,
        task_queue=task_queue,
        strategy_service=strategy_service,
        prompt_service=prompt_service,
        prompt_lock_audit_service=prompt_lock_audit_service,
        default_prompt_lock_mode=settings.prompt_ref_lock_mode,
        queue_auto_process=settings.queue_auto_process,
    )
    backtest_service = BacktestService(
        database=database,
        task_queue=task_queue,
        queue_auto_process=settings.queue_auto_process,
    )
    feedback_service = FeedbackService(database=database)
    optimization_service = OptimizationService(
        database=database,
        task_queue=task_queue,
        feedback_service=feedback_service,
        queue_auto_process=settings.queue_auto_process,
    )
    memory_service = MemoryService(database=database, vector_store=memory_vector_store)
    chat_service = ChatService(
        memory_service=memory_service,
        knowledge_service=knowledge_service,
        prompt_service=prompt_service,
        llm_provider=llm_provider,
        strategy_service=strategy_service,
        prompt_lock_audit_service=prompt_lock_audit_service,
        default_prompt_lock_mode=settings.prompt_ref_lock_mode,
    )

    app = FastAPI(
        title="Daily Stock Analysis Refactor API",
        version="0.3.145-m3-error-code-lint-profile-command-context",
    )
    app.state.workflow_service = workflow_service
    app.state.analysis_service = analysis_service
    app.state.backtest_service = backtest_service
    app.state.feedback_service = feedback_service
    app.state.optimization_service = optimization_service
    app.state.strategy_service = strategy_service
    app.state.prompt_service = prompt_service
    app.state.knowledge_service = knowledge_service
    app.state.memory_service = memory_service
    app.state.chat_service = chat_service
    app.state.prompt_lock_audit_service = prompt_lock_audit_service
    app.state.task_queue_service = task_queue
    app.state.database = database
    app.state.settings = settings
    app.include_router(api_router)
    return app


app = create_app()
