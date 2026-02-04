"""Configuration Schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """AI Model configuration schema."""

    id: Optional[int] = None
    name: str
    provider: str  # google/openai/doubao/tongyi/ERNIE
    api_key_encrypted: Optional[str] = None
    base_url: Optional[str] = None
    model: str
    enabled: bool = True
    priority: int = 100
    config: Dict[str, Any] = Field(default_factory=dict)
    cost_per_1k_tokens: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ModelConfigUpdate(BaseModel):
    """Model configuration update schema."""

    name: Optional[str] = None
    api_key_encrypted: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class PromptTemplate(BaseModel):
    """Prompt template schema."""

    id: Optional[int] = None
    name: str
    category: str
    content: str
    variables: List[str] = Field(default_factory=list)
    version: int = 1
    description: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    usage_count: int = 0
    avg_rating: Optional[Decimal] = None
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NotificationChannel(BaseModel):
    """Notification channel schema."""

    id: Optional[int] = None
    name: str
    type: str  # wechat/feishu/telegram/email/pushover/webhook
    config: Dict[str, Any]
    enabled: bool = True
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
