"""Configuration API Routes."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.config_service import ConfigService

router = APIRouter()


@router.get("/system")
async def get_system_settings():
    """Get system settings."""
    service = ConfigService()
    return service.get_all_settings()


@router.put("/system")
async def update_system_settings(settings: dict):
    """Update system settings."""
    service = ConfigService()
    return service.update_settings(settings)


@router.get("/prompts")
async def get_prompt_templates(
    category: Optional[str] = None,
):
    """Get prompt templates."""
    service = ConfigService()
    return service.get_prompts(category=category)


@router.post("/prompts")
async def create_prompt_template(
    template: dict,
):
    """Create a prompt template."""
    service = ConfigService()
    return service.create_prompt(template)


@router.put("/prompts/{template_id}")
async def update_prompt_template(
    template_id: int,
    template: dict,
):
    """Update a prompt template."""
    service = ConfigService()
    return service.update_prompt(template_id, template)


@router.get("/notifications")
async def get_notification_channels():
    """Get notification channel configurations."""
    service = ConfigService()
    return service.get_notification_channels()


@router.post("/notifications")
async def create_notification_channel(
    channel: dict,
):
    """Create a notification channel."""
    service = ConfigService()
    return service.create_notification_channel(channel)


@router.put("/notifications/{channel_id}")
async def update_notification_channel(
    channel_id: int,
    channel: dict,
):
    """Update a notification channel."""
    service = ConfigService()
    return service.update_notification_channel(channel_id, channel)
