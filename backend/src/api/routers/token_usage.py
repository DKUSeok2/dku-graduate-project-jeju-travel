"""
Token Usage API Router - LLM 토큰 사용량 조회
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

from src.database import get_db_session
from src.services.token_usage_service import TokenUsageService

router = APIRouter(prefix="/api/admin/token-usage", tags=["token-usage"])


@router.get("/daily")
async def get_daily_usage(
    days: int = Query(7, ge=1, le=90, description="조회할 일수"),
    model: Optional[str] = Query(None, description="특정 모델만 조회 (예: gpt-4o-mini)"),
    db: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """일별 토큰 사용량 조회 (모델별 필터링 가능)"""
    service = TokenUsageService(db)
    return await service.get_daily_usage(days=days, model=model)


@router.get("/hourly")
async def get_hourly_usage(
    hours: int = Query(24, ge=1, le=168, description="조회할 시간"),
    db: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """시간별 토큰 사용량 조회"""
    service = TokenUsageService(db)
    return await service.get_hourly_usage(hours=hours)


@router.get("/by-model")
async def get_model_usage(
    days: int = Query(7, ge=1, le=90, description="조회할 일수"),
    db: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """모델별 토큰 사용량 조회"""
    service = TokenUsageService(db)
    return await service.get_model_usage(days=days)


@router.get("/summary")
async def get_usage_summary(
    days: int = Query(30, ge=1, le=365, description="조회할 일수"),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """토큰 사용량 요약"""
    service = TokenUsageService(db)
    return await service.get_summary(days=days)

