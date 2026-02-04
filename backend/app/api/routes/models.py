"""AI Model Management API Routes."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.config import ModelConfig, ModelConfigUpdate
from app.services.config_service import ConfigService

router = APIRouter()


@router.get("/", response_model=List[ModelConfig])
async def list_models(
    enabled_only: bool = False,
    db=Depends(get_db),
):
    """List available AI models."""
    service = ConfigService(db)
    return await service.list_models(enabled_only=enabled_only)


@router.post("/", response_model=ModelConfig)
async def create_model_config(
    config: ModelConfig,
    db=Depends(get_db),
):
    """Create a new model configuration."""
    service = ConfigService(db)
    return await service.create_model(config)


@router.put("/{model_id}", response_model=ModelConfig)
async def update_model_config(
    model_id: int,
    update: ModelConfigUpdate,
    db=Depends(get_db),
):
    """Update model configuration."""
    service = ConfigService(db)
    return await service.update_model(model_id, update)


@router.delete("/{model_id}")
async def delete_model_config(
    model_id: int,
    db=Depends(get_db),
):
    """Delete model configuration."""
    service = ConfigService(db)
    await service.delete_model(model_id)
    return {"message": "Model deleted"}


@router.post("/{model_id}/test")
async def test_model_connection(
    model_id: int,
    db=Depends(get_db),
):
    """Test model API connection."""
    service = ConfigService(db)
    result = await service.test_model(model_id)
    return result
