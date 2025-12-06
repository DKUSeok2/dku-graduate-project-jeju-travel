"""
Admin Data Statistics API - 관리자용 데이터 통계 + Places CRUD
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from datetime import datetime, timedelta
from pydantic import BaseModel

from src.auth.dependencies import get_current_admin_user
from src.database import get_db_session
from src.models.user import User
from src.models.schedule import Schedule
from src.models.schedule_interaction import ScheduleLike, ScheduleBookmark, ScheduleView
from src.database import ChatSession

router = APIRouter(prefix="/api/admin/data", tags=["Admin Data"])


# ==================== Places CRUD ====================

class PlaceCreate(BaseModel):
    name: str
    category: str
    address: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    price_range: Optional[str] = None
    parking: Optional[bool] = None
    kid_friendly: Optional[bool] = None
    wheelchair: Optional[bool] = None
    pet_friendly: Optional[bool] = None
    reservation: Optional[bool] = None
    wifi: Optional[bool] = None
    business_hours: Optional[str] = None
    region: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    naver_id: Optional[str] = None
    url: Optional[str] = None

class PlaceUpdate(PlaceCreate):
    pass

class PlaceResponse(BaseModel):
    id: int
    name: str
    category: str
    address: Optional[str]
    phone: Optional[str]
    rating: Optional[float]
    review_count: Optional[int]
    min_price: Optional[int]
    max_price: Optional[int]
    price_range: Optional[str]
    parking: Optional[bool]
    kid_friendly: Optional[bool]
    wheelchair: Optional[bool]
    pet_friendly: Optional[bool]
    reservation: Optional[bool]
    wifi: Optional[bool]
    business_hours: Optional[str]
    region: Optional[str]
    lat: Optional[float]
    lng: Optional[float]


@router.get("/places")
async def get_places(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Places 목록 조회 (검색, 필터링 지원)
    """
    query_parts = ["SELECT * FROM places WHERE 1=1"]
    count_parts = ["SELECT COUNT(*) FROM places WHERE 1=1"]
    params = {}
    
    if search:
        query_parts.append("AND (name ILIKE :search OR address ILIKE :search)")
        count_parts.append("AND (name ILIKE :search OR address ILIKE :search)")
        params["search"] = f"%{search}%"
    
    if category:
        query_parts.append("AND category ILIKE :category")
        count_parts.append("AND category ILIKE :category")
        params["category"] = f"%{category}%"
    
    if region:
        query_parts.append("AND region = :region")
        count_parts.append("AND region = :region")
        params["region"] = region
    
    # 총 개수 조회
    count_query = text(" ".join(count_parts))
    count_result = await db.execute(count_query, params)
    total = count_result.scalar() or 0
    
    # 데이터 조회
    query_parts.append("ORDER BY id DESC")
    query_parts.append(f"OFFSET {skip} LIMIT {limit}")
    
    data_query = text(" ".join(query_parts))
    result = await db.execute(data_query, params)
    rows = result.fetchall()
    
    places = []
    for row in rows:
        places.append({
            "id": row[0],
            "naver_id": row[1],
            "name": row[2],
            "category": row[3],
            "address": row[4],
            "phone": row[5],
            "rating": float(row[6]) if row[6] else None,
            "review_count": row[7],
            "min_price": row[8],
            "max_price": row[9],
            "price_range": row[10],
            "parking": row[11],
            "kid_friendly": row[12],
            "wheelchair": row[13],
            "pet_friendly": row[14],
            "reservation": row[15],
            "wifi": row[16],
            "business_hours": row[17],
            "url": row[18],
            "region": row[19] if len(row) > 19 else None,
            "lat": float(row[20]) if len(row) > 20 and row[20] else None,
            "lng": float(row[21]) if len(row) > 21 and row[21] else None,
        })
    
    return {
        "places": places,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/places/{place_id}")
async def get_place(
    place_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Place 상세 조회
    """
    query = text("SELECT * FROM places WHERE id = :id")
    result = await db.execute(query, {"id": place_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="장소를 찾을 수 없습니다")
    
    return {
        "id": row[0],
        "naver_id": row[1],
        "name": row[2],
        "category": row[3],
        "address": row[4],
        "phone": row[5],
        "rating": float(row[6]) if row[6] else None,
        "review_count": row[7],
        "min_price": row[8],
        "max_price": row[9],
        "price_range": row[10],
        "parking": row[11],
        "kid_friendly": row[12],
        "wheelchair": row[13],
        "pet_friendly": row[14],
        "reservation": row[15],
        "wifi": row[16],
        "business_hours": row[17],
        "url": row[18],
        "region": row[19] if len(row) > 19 else None,
        "lat": float(row[20]) if len(row) > 20 and row[20] else None,
        "lng": float(row[21]) if len(row) > 21 and row[21] else None,
    }


@router.post("/places")
async def create_place(
    place: PlaceCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    새 Place 추가
    """
    query = text("""
        INSERT INTO places (name, category, address, phone, rating, review_count, 
                           min_price, max_price, price_range, parking, kid_friendly,
                           wheelchair, pet_friendly, reservation, wifi, business_hours,
                           region, lat, lng, naver_id, url)
        VALUES (:name, :category, :address, :phone, :rating, :review_count,
                :min_price, :max_price, :price_range, :parking, :kid_friendly,
                :wheelchair, :pet_friendly, :reservation, :wifi, :business_hours,
                :region, :lat, :lng, :naver_id, :url)
        RETURNING id
    """)
    
    result = await db.execute(query, place.model_dump())
    await db.commit()
    
    new_id = result.scalar()
    return {"id": new_id, "message": "장소가 추가되었습니다"}


@router.put("/places/{place_id}")
async def update_place(
    place_id: int,
    place: PlaceUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Place 수정
    """
    # 존재 여부 확인
    check_query = text("SELECT id FROM places WHERE id = :id")
    check_result = await db.execute(check_query, {"id": place_id})
    if not check_result.fetchone():
        raise HTTPException(status_code=404, detail="장소를 찾을 수 없습니다")
    
    query = text("""
        UPDATE places SET
            name = :name, category = :category, address = :address, phone = :phone,
            rating = :rating, review_count = :review_count, min_price = :min_price,
            max_price = :max_price, price_range = :price_range, parking = :parking,
            kid_friendly = :kid_friendly, wheelchair = :wheelchair, pet_friendly = :pet_friendly,
            reservation = :reservation, wifi = :wifi, business_hours = :business_hours,
            region = :region, lat = :lat, lng = :lng, naver_id = :naver_id, url = :url
        WHERE id = :id
    """)
    
    params = place.model_dump()
    params["id"] = place_id
    
    await db.execute(query, params)
    await db.commit()
    
    return {"message": "장소가 수정되었습니다"}


@router.delete("/places/{place_id}")
async def delete_place(
    place_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Place 삭제
    """
    # 존재 여부 확인
    check_query = text("SELECT id FROM places WHERE id = :id")
    check_result = await db.execute(check_query, {"id": place_id})
    if not check_result.fetchone():
        raise HTTPException(status_code=404, detail="장소를 찾을 수 없습니다")
    
    # 관련 메뉴 삭제
    await db.execute(text("DELETE FROM menus WHERE place_id = :id"), {"id": place_id})
    
    # 장소 삭제
    await db.execute(text("DELETE FROM places WHERE id = :id"), {"id": place_id})
    await db.commit()
    
    return {"message": "장소가 삭제되었습니다"}


class DataStatsResponse(BaseModel):
    total_users: int
    total_schedules: int
    total_chat_sessions: int
    total_likes: int
    total_bookmarks: int
    total_views: int
    
class PopularAttractionItem(BaseModel):
    rank: int
    name: str
    category: str
    count: int
    emoji: str
    
class CategoryDistribution(BaseModel):
    name: str
    count: int
    percentage: float


@router.get("/stats")
async def get_data_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    전체 데이터 통계 조회
    """
    # 사용자 수
    users_count = await db.execute(select(func.count(User.id)))
    total_users = users_count.scalar() or 0
    
    # 일정 수
    schedules_count = await db.execute(select(func.count(Schedule.id)))
    total_schedules = schedules_count.scalar() or 0
    
    # 채팅 세션 수
    sessions_count = await db.execute(select(func.count(ChatSession.id)))
    total_chat_sessions = sessions_count.scalar() or 0
    
    # 좋아요 수
    likes_count = await db.execute(select(func.count(ScheduleLike.id)))
    total_likes = likes_count.scalar() or 0
    
    # 북마크 수
    bookmarks_count = await db.execute(select(func.count(ScheduleBookmark.id)))
    total_bookmarks = bookmarks_count.scalar() or 0
    
    # 조회수
    views_count = await db.execute(select(func.count(ScheduleView.id)))
    total_views = views_count.scalar() or 0
    
    return {
        "total_users": total_users,
        "total_schedules": total_schedules,
        "total_chat_sessions": total_chat_sessions,
        "total_likes": total_likes,
        "total_bookmarks": total_bookmarks,
        "total_views": total_views
    }


@router.get("/popular-attractions", response_model=List[PopularAttractionItem])
async def get_popular_attractions(
    limit: int = 10,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    인기 관광지 통계 (일정에 포함된 횟수 기준)
    """
    # 모든 일정의 attractions 조회
    result = await db.execute(select(Schedule.attractions))
    all_schedules = result.scalars().all()
    
    # 관광지별 카운트
    attraction_counts: Dict[str, Dict] = {}
    
    for attractions in all_schedules:
        if not attractions or not isinstance(attractions, dict):
            continue
            
        for day_key, day_attractions in attractions.items():
            if not isinstance(day_attractions, list):
                continue
                
            for attraction in day_attractions:
                if not isinstance(attraction, dict) or 'name' not in attraction:
                    continue
                    
                name = attraction['name']
                if name not in attraction_counts:
                    attraction_counts[name] = {
                        'name': name,
                        'category': attraction.get('category', '기타'),
                        'emoji': attraction.get('emoji', '📍'),
                        'count': 0
                    }
                attraction_counts[name]['count'] += 1
    
    # 카운트 순으로 정렬
    sorted_attractions = sorted(
        attraction_counts.values(),
        key=lambda x: x['count'],
        reverse=True
    )[:limit]
    
    # 순위 추가
    return [
        PopularAttractionItem(
            rank=idx + 1,
            name=attr['name'],
            category=attr['category'],
            count=attr['count'],
            emoji=attr['emoji']
        )
        for idx, attr in enumerate(sorted_attractions)
    ]


@router.get("/category-distribution", response_model=List[CategoryDistribution])
async def get_category_distribution(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    카테고리별 관광지 분포
    """
    # 모든 일정의 attractions 조회
    result = await db.execute(select(Schedule.attractions))
    all_schedules = result.scalars().all()
    
    # 카테고리별 카운트
    category_counts: Dict[str, int] = {}
    total_count = 0
    
    for attractions in all_schedules:
        if not attractions or not isinstance(attractions, dict):
            continue
            
        for day_key, day_attractions in attractions.items():
            if not isinstance(day_attractions, list):
                continue
                
            for attraction in day_attractions:
                if not isinstance(attraction, dict):
                    continue
                    
                category = attraction.get('category', '기타')
                category_counts[category] = category_counts.get(category, 0) + 1
                total_count += 1
    
    # 퍼센트 계산
    return [
        CategoryDistribution(
            name=category,
            count=count,
            percentage=round((count / total_count * 100), 1) if total_count > 0 else 0
        )
        for category, count in sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
    ]


