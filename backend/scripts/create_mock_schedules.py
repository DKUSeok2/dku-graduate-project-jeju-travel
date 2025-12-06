#!/usr/bin/env python
"""
Mock 일정 데이터 생성 스크립트
"""
import asyncio
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.models.user import User
from src.models.schedule import Schedule


# Mock 데이터
MOCK_SCHEDULES = [
    {
        "title": "🌊 힐링 제주 3박 4일",
        "start_date": date(2025, 11, 15),
        "end_date": date(2025, 11, 18),
        "attractions": {
            "day1": [
                {"name": "제주국제공항", "time": "09:00", "emoji": "✈️"},
                {"name": "협재해수욕장", "time": "10:30", "emoji": "🏖️"},
                {"name": "한림공원", "time": "13:30", "emoji": "🌺"},
            ],
            "day2": [
                {"name": "성산일출봉", "time": "06:00", "emoji": "🌋"},
                {"name": "섭지코지", "time": "09:00", "emoji": "🌊"},
                {"name": "아쿠아플라넷", "time": "11:30", "emoji": "🐠"},
            ],
            "day3": [
                {"name": "한라산 등반", "time": "08:00", "emoji": "🏔️"},
                {"name": "테디베어 박물관", "time": "15:30", "emoji": "🧸"},
            ],
        },
        "route_data": {"total_distance": 87, "total_time": 5.5},
        "memo": "자연과 함께하는 여유로운 제주 여행",
        "is_public": True,
    },
    {
        "title": "🍊 제주 맛집 투어 2박 3일",
        "start_date": date(2025, 12, 1),
        "end_date": date(2025, 12, 3),
        "attractions": {
            "day1": [
                {"name": "흑돼지거리", "time": "12:00", "emoji": "🐷"},
                {"name": "동문시장", "time": "15:00", "emoji": "🏪"},
                {"name": "애월 카페거리", "time": "17:00", "emoji": "☕"},
            ],
            "day2": [
                {"name": "해녀의 집", "time": "11:00", "emoji": "🍽️"},
                {"name": "올레시장", "time": "14:00", "emoji": "🛒"},
                {"name": "중문 맛집거리", "time": "18:00", "emoji": "🍜"},
            ],
        },
        "route_data": {"total_distance": 45, "total_time": 3},
        "memo": "제주의 모든 맛을 경험하는 미식 여행",
        "is_public": True,
    },
    {
        "title": "🚗 제주 드라이브 코스 당일치기",
        "start_date": date(2025, 11, 20),
        "end_date": date(2025, 11, 20),
        "attractions": {
            "day1": [
                {"name": "제주 올레길 7코스", "time": "08:00", "emoji": "🚶"},
                {"name": "사려니숲길", "time": "11:00", "emoji": "🌲"},
                {"name": "천지연폭포", "time": "14:00", "emoji": "💧"},
                {"name": "서귀포 매일올레시장", "time": "17:00", "emoji": "🏪"},
            ],
        },
        "route_data": {"total_distance": 62, "total_time": 4.5},
        "memo": "제주의 자연을 느끼는 드라이브",
        "is_public": True,
    },
    {
        "title": "👨‍👩‍👧‍👦 가족 여행 제주 4박 5일",
        "start_date": date(2025, 12, 10),
        "end_date": date(2025, 12, 14),
        "attractions": {
            "day1": [
                {"name": "제주미니랜드", "time": "10:00", "emoji": "🏰"},
                {"name": "제주러브랜드", "time": "13:00", "emoji": "🎨"},
            ],
            "day2": [
                {"name": "에코랜드", "time": "09:00", "emoji": "🚂"},
                {"name": "김녕미로공원", "time": "14:00", "emoji": "🌿"},
            ],
            "day3": [
                {"name": "우도", "time": "08:00", "emoji": "🏝️"},
                {"name": "해녀박물관", "time": "15:00", "emoji": "🏛️"},
            ],
            "day4": [
                {"name": "제주민속촌", "time": "10:00", "emoji": "🏘️"},
                {"name": "중문해수욕장", "time": "14:00", "emoji": "🏖️"},
            ],
        },
        "route_data": {"total_distance": 120, "total_time": 8},
        "memo": "온 가족이 즐기는 행복한 제주 여행",
        "is_public": True,
    },
    {
        "title": "📸 인스타 감성 제주 여행",
        "start_date": date(2025, 11, 25),
        "end_date": date(2025, 11, 27),
        "attractions": {
            "day1": [
                {"name": "카멜리아힐", "time": "10:00", "emoji": "🌺"},
                {"name": "월정리해변", "time": "13:00", "emoji": "🏖️"},
                {"name": "애월 카페거리", "time": "16:00", "emoji": "☕"},
            ],
            "day2": [
                {"name": "성산일출봉", "time": "06:00", "emoji": "🌋"},
                {"name": "광치기해변", "time": "09:00", "emoji": "🌊"},
                {"name": "섭지코지", "time": "11:00", "emoji": "🌅"},
            ],
        },
        "route_data": {"total_distance": 78, "total_time": 5},
        "memo": "사진으로 남기는 제주의 순간들",
        "is_public": True,
    },
    {
        "title": "🏃 액티브 제주 여행 (개인 일정)",
        "start_date": date(2025, 12, 5),
        "end_date": date(2025, 12, 7),
        "attractions": {
            "day1": [
                {"name": "한라산 등반", "time": "05:00", "emoji": "🏔️"},
                {"name": "천지연폭포", "time": "14:00", "emoji": "💧"},
            ],
            "day2": [
                {"name": "올레길 1코스", "time": "07:00", "emoji": "🚶"},
                {"name": "수월봉", "time": "15:00", "emoji": "⛰️"},
            ],
        },
        "route_data": {"total_distance": 95, "total_time": 12},
        "memo": "등산과 트레킹으로 제주 정복하기",
        "is_public": False,  # 비공개 일정
    },
]


async def create_mock_schedules():
    """Mock 일정 데이터 생성"""
    
    # DB 연결 (async 드라이버 사용)
    db_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 첫 번째 사용자 찾기 (관리자 제외)
        result = await session.execute(
            select(User).where(User.is_admin == False).limit(1)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ 일반 사용자를 찾을 수 없습니다. 먼저 회원가입을 해주세요.")
            return
        
        print(f"✅ 사용자 발견: {user.name} ({user.email})")
        
        # 기존 일정 삭제 (선택사항)
        result = await session.execute(select(Schedule).where(Schedule.user_id == user.id))
        existing_schedules = result.scalars().all()
        if existing_schedules:
            response = input(f"⚠️  기존 일정 {len(existing_schedules)}개가 있습니다. 삭제하고 새로 생성할까요? (y/N): ")
            if response.lower() == 'y':
                for schedule in existing_schedules:
                    await session.delete(schedule)
                await session.commit()
                print("🗑️  기존 일정 삭제 완료")
        
        # Mock 일정 생성
        created_count = 0
        for schedule_data in MOCK_SCHEDULES:
            new_schedule = Schedule(
                user_id=user.id,
                **schedule_data
            )
            session.add(new_schedule)
            created_count += 1
            print(f"📝 일정 생성: {schedule_data['title']}")
        
        await session.commit()
        print(f"\n✅ 총 {created_count}개의 Mock 일정이 생성되었습니다!")
        print(f"   - 공개 일정: {sum(1 for s in MOCK_SCHEDULES if s['is_public'])}개")
        print(f"   - 비공개 일정: {sum(1 for s in MOCK_SCHEDULES if not s['is_public'])}개")


if __name__ == "__main__":
    asyncio.run(create_mock_schedules())

