"""Configuration Models."""

from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Numeric, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampMixin


class CFGAIModel(TimestampMixin):
    """AI Model configurations."""

    __tablename__ = "cfg_ai_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # google/openai/doubao/tongyi/ERNIE
    api_key_encrypted: Mapped[str] = mapped_column(Text)  # Encrypted
    base_url: Mapped[str] = mapped_column(String(200))
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    cost_per_1k_tokens: Mapped[Decimal] = mapped_column(Numeric(10, 4))


class CFGPromptTemplate(TimestampMixin):
    """Prompt templates."""

    __tablename__ = "cfg_prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[List[str]] = mapped_column(ARRAY(String))
    version: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(Text)
    example_input: Mapped[str] = mapped_column(Text)
    example_output: Mapped[str] = mapped_column(Text)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)


class CFGPromptVersion(TimestampMixin):
    """Prompt template version history."""

    __tablename__ = "cfg_prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    changes: Mapped[str] = mapped_column(Text)
    performance_metrics: Mapped[dict] = mapped_column(JSON)


class CFGPromptLog(TimestampMixin):
    """Prompt usage logs."""

    __tablename__ = "cfg_prompt_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, nullable=False)
    model: Mapped[str] = mapped_column(String(50))
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    execution_time_ms: Mapped[int] = mapped_column(Integer)
    result_rating: Mapped[int] = mapped_column(Integer)  # User rating 1-5
    feedback: Mapped[str] = mapped_column(Text)


class CFGNotificationChannel(TimestampMixin):
    """Notification channel configurations."""

    __tablename__ = "cfg_notification_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # wechat/feishu/telegram/email/pushover/webhook
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class CFGSystemSettings(TimestampMixin):
    """System settings key-value store."""

    __tablename__ = "cfg_system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20), default="string")
    group_name: Mapped[str] = mapped_column(String(50))
