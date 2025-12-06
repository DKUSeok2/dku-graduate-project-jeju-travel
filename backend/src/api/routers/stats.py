from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Attraction, get_db_session
from src.models.user import User
from src.models.schedule import Schedule

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db_session)):
    """
    플랫폼 통계 조회
    - 관광지 데이터 개수
    - 생성된 일정 개수
    - 누적 사용자 수
    """
    # 관광지 개수
    attractions_result = await db.execute(select(func.count()).select_from(Attraction))
    attractions_count = attractions_result.scalar()

    # 일정 개수
    schedules_result = await db.execute(select(func.count()).select_from(Schedule))
    schedules_count = schedules_result.scalar()

    # 사용자 수
    users_result = await db.execute(select(func.count()).select_from(User))
    users_count = users_result.scalar()

    return {
        "attractions": attractions_count or 0,
        "schedules": schedules_count or 0,
        "users": users_count or 0,
    }

