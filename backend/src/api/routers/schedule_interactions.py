"""
Schedule Interactions API - 좋아요, 북마크, 조회수
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from pydantic import BaseModel

from src.auth.dependencies import get_current_user
from src.database import get_db_session
from src.models.user import User
from src.models.schedule import Schedule
from src.models.schedule_interaction import ScheduleLike, ScheduleBookmark, ScheduleView

router = APIRouter(prefix="/api/schedules", tags=["Schedule Interactions"])


# Pydantic Schemas
class InteractionResponse(BaseModel):
    """좋아요/북마크 응답"""
    success: bool
    is_active: bool  # 좋아요/북마크 활성 여부
    total_count: int  # 전체 좋아요/북마크 수

    class Config:
        from_attributes = True


class ScheduleStatsResponse(BaseModel):
    """일정 통계 응답"""
    schedule_id: int
    likes_count: int
    bookmarks_count: int
    views_count: int
    is_liked: bool  # 현재 사용자가 좋아요 했는지
    is_bookmarked: bool  # 현재 사용자가 북마크 했는지

    class Config:
        from_attributes = True


# ===== 좋아요 API =====

@router.post("/{schedule_id}/like", response_model=InteractionResponse)
async def toggle_like(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    일정 좋아요 토글
    """
    # 일정 존재 확인
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일정을 찾을 수 없습니다")
    
    # 기존 좋아요 확인
    result = await db.execute(
        select(ScheduleLike).where(
            ScheduleLike.user_id == current_user.id,
            ScheduleLike.schedule_id == schedule_id
        )
    )
    existing_like = result.scalar_one_or_none()
    
    if existing_like:
        # 좋아요 취소
        await db.delete(existing_like)
        await db.commit()
        is_active = False
    else:
        # 좋아요 추가
        new_like = ScheduleLike(user_id=current_user.id, schedule_id=schedule_id)
        db.add(new_like)
        await db.commit()
        is_active = True
    
    # 전체 좋아요 수 조회
    result = await db.execute(
        select(func.count(ScheduleLike.id)).where(ScheduleLike.schedule_id == schedule_id)
    )
    total_count = result.scalar() or 0
    
    return InteractionResponse(
        success=True,
        is_active=is_active,
        total_count=total_count
    )


# ===== 북마크 API =====

@router.post("/{schedule_id}/bookmark", response_model=InteractionResponse)
async def toggle_bookmark(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    일정 북마크 토글
    """
    # 일정 존재 확인
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일정을 찾을 수 없습니다")
    
    # 기존 북마크 확인
    result = await db.execute(
        select(ScheduleBookmark).where(
            ScheduleBookmark.user_id == current_user.id,
            ScheduleBookmark.schedule_id == schedule_id
        )
    )
    existing_bookmark = result.scalar_one_or_none()
    
    if existing_bookmark:
        # 북마크 취소
        await db.delete(existing_bookmark)
        await db.commit()
        is_active = False
    else:
        # 북마크 추가
        new_bookmark = ScheduleBookmark(user_id=current_user.id, schedule_id=schedule_id)
        db.add(new_bookmark)
        await db.commit()
        is_active = True
    
    # 전체 북마크 수 조회
    result = await db.execute(
        select(func.count(ScheduleBookmark.id)).where(ScheduleBookmark.schedule_id == schedule_id)
    )
    total_count = result.scalar() or 0
    
    return InteractionResponse(
        success=True,
        is_active=is_active,
        total_count=total_count
    )


# ===== 조회수 API =====

@router.post("/{schedule_id}/view", status_code=status.HTTP_201_CREATED)
async def record_view(
    schedule_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    일정 조회수 기록 (중복 체크 없음)
    """
    from src.auth.dependencies import get_current_user_optional
    
    # 일정 존재 확인
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일정을 찾을 수 없습니다")
    
    # 현재 사용자 (선택 사항 - 비로그인 사용자도 허용)
    try:
        from src.auth.jwt import decode_token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_id = None
        if token:
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
            except:
                pass
    except:
        user_id = None
    
    # 조회 기록 추가
    new_view = ScheduleView(
        schedule_id=schedule_id,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:255]
    )
    db.add(new_view)
    await db.commit()
    
    return {"success": True}


# ===== 통계 조회 API =====

@router.get("/{schedule_id}/stats", response_model=ScheduleStatsResponse)
async def get_schedule_stats(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    일정 통계 조회 (좋아요, 북마크, 조회수)
    """
    # 일정 존재 확인
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일정을 찾을 수 없습니다")
    
    # 좋아요 수
    result = await db.execute(
        select(func.count(ScheduleLike.id)).where(ScheduleLike.schedule_id == schedule_id)
    )
    likes_count = result.scalar() or 0
    
    # 북마크 수
    result = await db.execute(
        select(func.count(ScheduleBookmark.id)).where(ScheduleBookmark.schedule_id == schedule_id)
    )
    bookmarks_count = result.scalar() or 0
    
    # 조회수
    result = await db.execute(
        select(func.count(ScheduleView.id)).where(ScheduleView.schedule_id == schedule_id)
    )
    views_count = result.scalar() or 0
    
    # 현재 사용자 좋아요 여부
    result = await db.execute(
        select(ScheduleLike).where(
            ScheduleLike.user_id == current_user.id,
            ScheduleLike.schedule_id == schedule_id
        )
    )
    is_liked = result.scalar_one_or_none() is not None
    
    # 현재 사용자 북마크 여부
    result = await db.execute(
        select(ScheduleBookmark).where(
            ScheduleBookmark.user_id == current_user.id,
            ScheduleBookmark.schedule_id == schedule_id
        )
    )
    is_bookmarked = result.scalar_one_or_none() is not None
    
    return ScheduleStatsResponse(
        schedule_id=schedule_id,
        likes_count=likes_count,
        bookmarks_count=bookmarks_count,
        views_count=views_count,
        is_liked=is_liked,
        is_bookmarked=is_bookmarked
    )


# ===== 내 북마크 목록 조회 =====

@router.get("/bookmarks/my")
async def get_my_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    내가 북마크한 일정 목록
    """
    result = await db.execute(
        select(Schedule, User)
        .join(ScheduleBookmark, ScheduleBookmark.schedule_id == Schedule.id)
        .join(User, Schedule.user_id == User.id)
        .where(ScheduleBookmark.user_id == current_user.id)
        .order_by(ScheduleBookmark.created_at.desc())
    )
    rows = result.all()
    
    from src.api.routers.schedules import ScheduleResponse
    
    return [
        ScheduleResponse.from_schedule(schedule, user.name)
        for schedule, user in rows
    ]

