"""Configuration Management Module."""

import os
from functools import lru_cache
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8888, description="Server port")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins",
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/stock_analysis.db",
        description="Database connection URL",
    )
    DATABASE_POOL_SIZE: int = Field(default=5, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Encryption
    ENCRYPTION_KEY: Optional[str] = Field(
        default=None,
        description="Encryption key for sensitive data",
    )

    # AI Models - Gemini (Primary)
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash", description="Default Gemini model")

    # AI Models - OpenAI (Backup)
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, description="OpenAI base URL")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="Default OpenAI model")

    # AI Models - Qwen (Domestic)
    DASHSCOPE_API_KEY: Optional[str] = Field(default=None, description="Alibaba DashScope API key")
    DASHSCOPE_MODEL: str = Field(default="qwen-plus", description="Default Qwen model")

    # AI Models - DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = Field(default=None, description="DeepSeek API key")
    DEEPSEEK_BASE_URL: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek base URL",
    )
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", description="Default DeepSeek model")

    # AI Models - Doubao (Cost optimization)
    DOUBAO_API_KEY: Optional[str] = Field(default=None, description="Doubao API key")
    DOUBAO_MODEL: str = Field(default="doubao-1-5", description="Default Doubao model")

    # Data Sources
    EFICONFIG_PATH: Optional[str] = Field(
        default=None,
        description="Efinance configuration path",
    )
    TUSHARE_TOKEN: Optional[str] = Field(default=None, description="Tushare API token")

    # Search Services
    TAVILY_API_KEY: Optional[str] = Field(default=None, description="Tavily search API key")
    BOCHA_API_KEY: Optional[str] = Field(default=None, description="Bocha search API key")
    SERPAPI_API_KEY: Optional[str] = Field(default=None, description="SerpAPI key")

    # Notification Channels
    FEISHU_APP_ID: Optional[str] = Field(default=None, description="Feishu app ID")
    FEISHU_APP_SECRET: Optional[str] = Field(default=None, description="Feishu app secret")
    FEISHU_WEBHOOK_URL: Optional[str] = Field(default=None, description="Feishu webhook URL")

    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, description="Telegram bot token")
    TELEGRAM_CHAT_ID: Optional[str] = Field(default=None, description="Telegram chat ID")

    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")

    WECHAT_CORP_ID: Optional[str] = Field(default=None, description="WeChat Work corp ID")
    WECHAT_CORP_SECRET: Optional[str] = Field(default=None, description="WeChat Work secret")
    WECHAT_AGENT_ID: Optional[str] = Field(default=None, description="WeChat Work agent ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Singleton instance
_config: Optional[Settings] = None


def get_config() -> Settings:
    """Get configuration singleton (legacy compatibility)."""
    global _config
    if _config is None:
        _config = get_settings()
    return _config
