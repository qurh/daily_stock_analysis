"""Configuration Service."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.schemas.config import (
    ModelConfig,
    ModelConfigUpdate,
    PromptTemplate,
    NotificationChannel,
)

logger = logging.getLogger(__name__)


class ConfigService:
    """Configuration management service."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def list_models(self, enabled_only: bool = False) -> List[ModelConfig]:
        """List available AI models."""
        if not self.db:
            # Return defaults when no DB
            return self._get_default_models()

        query = select(ModelConfig)
        if enabled_only:
            query = query.where(ModelConfig.enabled == True)
        query = query.order_by(desc(ModelConfig.priority))

        result = await self.db.execute(query)
        models = result.scalars().all()

        if not models:
            return self._get_default_models()

        return [self._to_model_config(m) for m in models]

    async def create_model(self, config: ModelConfig) -> ModelConfig:
        """Create model configuration."""
        from app.models.config import CFGAIModel

        model = CFGAIModel(
            name=config.name,
            provider=config.provider,
            api_key_encrypted=config.api_key_encrypted,
            base_url=config.base_url,
            model=config.model,
            enabled=config.enabled,
            priority=config.priority,
            config=config.config,
            cost_per_1k_tokens=config.cost_per_1k_tokens,
        )

        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)

        return self._to_model_config(model)

    async def update_model(
        self, model_id: int, update: ModelConfigUpdate
    ) -> ModelConfig:
        """Update model configuration."""
        from app.models.config import CFGAIModel

        query = select(CFGAIModel).where(CFGAIModel.id == model_id)
        result = await self.db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Model {model_id} not found")

        if update.name is not None:
            model.name = update.name
        if update.api_key_encrypted is not None:
            model.api_key_encrypted = update.api_key_encrypted
        if update.base_url is not None:
            model.base_url = update.base_url
        if update.model is not None:
            model.model = update.model
        if update.enabled is not None:
            model.enabled = update.enabled
        if update.priority is not None:
            model.priority = update.priority
        if update.config is not None:
            model.config = update.config

        await self.db.flush()
        await self.db.refresh(model)

        return self._to_model_config(model)

    async def delete_model(self, model_id: int) -> None:
        """Delete model configuration."""
        from app.models.config import CFGAIModel

        query = select(CFGAIModel).where(CFGAIModel.id == model_id)
        result = await self.db.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.db.delete(model)
            await self.db.flush()

    async def test_model(self, model_id: int) -> Dict[str, Any]:
        """Test model API connection."""
        from app.services.ai_router import AIRouter

        router = AIRouter()
        success = await router.test_connection(model_id)

        return {"success": success}

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all system settings."""
        # Default settings
        return {
            "risk_tolerance": "moderate",
            "default_model": "gemini-2.0-flash",
            "enable_rag": True,
            "notification_enabled": True,
        }

    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update system settings."""
        # TODO: Implement with database
        return settings

    def get_prompts(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """Get prompt templates."""
        # Return defaults for now
        return self._get_default_prompts(category)

    def create_prompt(self, template: Dict[str, Any]) -> PromptTemplate:
        """Create prompt template."""
        # TODO: Implement with database
        return PromptTemplate(**template)

    def update_prompt(
        self, template_id: int, template: Dict[str, Any]
    ) -> PromptTemplate:
        """Update prompt template."""
        # TODO: Implement with database
        return PromptTemplate(**template)

    def get_notification_channels(self) -> List[NotificationChannel]:
        """Get notification channel configurations."""
        # TODO: Implement with database
        return []

    def create_notification_channel(
        self, channel: Dict[str, Any]
    ) -> NotificationChannel:
        """Create notification channel."""
        # TODO: Implement with database
        return NotificationChannel(**channel)

    def update_notification_channel(
        self, channel_id: int, channel: Dict[str, Any]
    ) -> NotificationChannel:
        """Update notification channel."""
        # TODO: Implement with database
        return NotificationChannel(**channel)

    def _get_default_models(self) -> List[ModelConfig]:
        """Get default model configurations."""
        return [
            ModelConfig(
                id=1,
                name="Gemini 2.0 Flash",
                provider="google",
                model="gemini-2.0-flash",
                enabled=True,
                priority=1,
            ),
            ModelConfig(
                id=2,
                name="Qwen-Plus",
                provider="tongyi",
                model="qwen-plus",
                enabled=True,
                priority=2,
            ),
            ModelConfig(
                id=3,
                name="DeepSeek Chat",
                provider="deepseek",
                model="deepseek-chat",
                enabled=True,
                priority=3,
            ),
            ModelConfig(
                id=4,
                name="GPT-4o",
                provider="openai",
                model="gpt-4o",
                enabled=False,
                priority=4,
            ),
        ]

    def _get_default_prompts(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """Get default prompt templates."""
        prompts = [
            PromptTemplate(
                id=1,
                name="股票分析",
                category="analysis",
                content="分析以下股票：{code}\n\n请提供：\n1. 技术面分析\n2. 基本面分析\n3. 风险提示\n4. 买卖建议",
                variables=["code"],
            ),
            PromptTemplate(
                id=2,
                name="大盘复盘",
                category="review",
                content="请对{date}的大盘进行复盘，分析：\n1. 整体行情\n2. 热点板块\n3. 资金流向\n4. 明日展望",
                variables=["date"],
            ),
        ]

        if category:
            return [p for p in prompts if p.category == category]
        return prompts

    def _to_model_config(self, model) -> ModelConfig:
        """Convert database model to schema."""
        return ModelConfig(
            id=model.id,
            name=model.name,
            provider=model.provider,
            api_key_encrypted=model.api_key_encrypted,
            base_url=model.base_url,
            model=model.model,
            enabled=model.enabled,
            priority=model.priority,
            config=model.config or {},
            cost_per_1k_tokens=model.cost_per_1k_tokens,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
