"""
Schedules Router - 일정 관리 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import date

from src.auth.dependencies import get_current_user
from src.database import get_db_session
from src.models.user import User
from src.models.schedule import Schedule
from pydantic import BaseModel

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


# Pydantic Schemas
class ScheduleCreate(BaseModel):
    title: str
    start_date: date
    end_date: date
    attractions: Optional[dict] = None
    route_data: Optional[dict] = None
    memo: Optional[str] = None
    chat_history: Optional[list] = None  # AI 대화 내역
    ai_reasoning: Optional[str] = None   # AI 추천 이유
    map_data: Optional[dict] = None      # 지도 데이터
    chat_session_id: Optional[str] = None  # 채팅 세션 ID


class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    attractions: Optional[dict] = None
    route_data: Optional[dict] = None
    memo: Optional[str] = None
    is_public: Optional[bool] = None
    chat_history: Optional[list] = None  # AI 대화 내역
    ai_reasoning: Optional[str] = None   # AI 추천 이유
    map_data: Optional[dict] = None      # 지도 데이터
    chat_session_id: Optional[str] = None  # 채팅 세션 ID


class ScheduleResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    title: str
    start_date: date
    end_date: date
    attractions: Optional[dict]
    route_data: Optional[dict]
    memo: Optional[str]
    is_public: bool
    created_at: str
    updated_at: str
    likes_count: int = 0  # 좋아요 수 추가
    bookmarks_count: int = 0  # 북마크 수 추가
    chat_history: Optional[list] = None  # AI 대화 내역
    ai_reasoning: Optional[str] = None   # AI 추천 이유
    map_data: Optional[dict] = None      # 지도 데이터
    chat_session_id: Optional[str] = None  # 채팅 세션 ID

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_schedule(cls, schedule, user_name: str, likes_count: int = 0, bookmarks_count: int = 0):
        """Schedule 객체에서 Response 생성"""
        return cls(
            id=schedule.id,
            user_id=schedule.user_id,
            user_name=user_name,
            title=schedule.title,
            start_date=schedule.start_date,
            end_date=schedule.end_date,
            attractions=schedule.attractions,
            route_data=schedule.route_data,
            memo=schedule.memo,
            is_public=schedule.is_public,
            created_at=schedule.created_at.isoformat() if hasattr(schedule.created_at, 'isoformat') else str(schedule.created_at),
            updated_at=schedule.updated_at.isoformat() if hasattr(schedule.updated_at, 'isoformat') else str(schedule.updated_at),
            likes_count=likes_count,
            bookmarks_count=bookmarks_count,
            chat_history=schedule.chat_history,
            ai_reasoning=schedule.ai_reasoning,
            map_data=schedule.map_data,
            chat_session_id=schedule.chat_session_id
        )


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    새 일정 생성
    """
    new_schedule = Schedule(
        user_id=current_user.id,
        title=schedule_data.title,
        start_date=schedule_data.start_date,
        end_date=schedule_data.end_date,
        attractions=schedule_data.attractions,
        route_data=schedule_data.route_data,
        memo=schedule_data.memo,
        chat_history=schedule_data.chat_history,
        ai_reasoning=schedule_data.ai_reasoning,
        map_data=schedule_data.map_data,
        chat_session_id=schedule_data.chat_session_id,
        is_public=False
    )
    
    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)
    
    return ScheduleResponse.from_schedule(new_schedule, current_user.name)


@router.get("/my", response_model=List[ScheduleResponse])
async def get_my_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    내 일정 목록 조회
    """
    result = await db.execute(
        select(Schedule)
        .where(Schedule.user_id == current_user.id)
        .order_by(desc(Schedule.created_at))
    )
    schedules = result.scalars().all()
    
    return [
        ScheduleResponse.from_schedule(schedule, current_user.name)
        for schedule in schedules
    ]


@router.get("/public", response_model=List[ScheduleResponse])
async def get_public_schedules(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session)
):
    """
    공개된 일정 목록 조회 (추천 코스)
    """
    from src.models.schedule_interaction import ScheduleLike, ScheduleBookmark
    
    result = await db.execute(
        select(Schedule, User)
        .join(User, Schedule.user_id == User.id)
        .where(Schedule.is_public == True)
        .order_by(desc(Schedule.created_at))
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()
    
    # 각 일정의 좋아요/북마크 수 조회
    response_list = []
    for schedule, user in rows:
        # 좋아요 수
        likes_result = await db.execute(
            select(func.count(ScheduleLike.id)).where(ScheduleLike.schedule_id == schedule.id)
        )
        likes_count = likes_result.scalar() or 0
        
        # 북마크 수
        bookmarks_result = await db.execute(
            select(func.count(ScheduleBookmark.id)).where(ScheduleBookmark.schedule_id == schedule.id)
        )
        bookmarks_count = bookmarks_result.scalar() or 0
        
        response_list.append(
            ScheduleResponse.from_schedule(schedule, user.name, likes_count, bookmarks_count)
        )
    
    return response_list


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    특정 일정 조회 (본인 일정 또는 공개 일정만)
    """
    result = await db.execute(
        select(Schedule, User)
        .join(User, Schedule.user_id == User.id)
        .where(Schedule.id == schedule_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다"
        )
    
    schedule, user = row
    
    # 본인 일정이 아니고 비공개 일정이면 접근 불가
    if schedule.user_id != current_user.id and not schedule.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다"
        )
    
    return ScheduleResponse.from_schedule(schedule, user.name)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    일정 수정 (공유하기 포함)
    """
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다"
        )
    
    if schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="수정 권한이 없습니다"
        )
    
    # Update fields
    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    await db.commit()
    await db.refresh(schedule)
    
    return ScheduleResponse.from_schedule(schedule, current_user.name)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    일정 삭제
    """
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다"
        )
    
    if schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="삭제 권한이 없습니다"
        )
    
    await db.delete(schedule)
    await db.commit()
    
    return None

