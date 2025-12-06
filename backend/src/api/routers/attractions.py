"""
Attractions API Router
관광지 정보 조회 API (OR-Tools 기반 동선 최적화 포함)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.database import get_db_session
from src.tool_agents.route_optimizer_agent.utils import (
    haversine_distance,
    build_distance_matrix,
    nearest_neighbor_tsp,  # 빠른 TSP (대안 추천용)
    ORTOOLS_AVAILABLE
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/attractions", tags=["attractions"])


# ===== Pydantic 스키마 =====
class PlaceInfo(BaseModel):
    """장소 정보"""
    id: Optional[int] = None
    name: str
    category: str
    lat: float
    lng: float
    rating: Optional[float] = 0
    
class RecommendAlternativesRequest(BaseModel):
    """대안 장소 추천 요청"""
    current_places: List[PlaceInfo] = Field(..., description="현재 일정의 장소들")
    replace_index: int = Field(..., description="교체하려는 장소의 인덱스")
    category: Optional[str] = Field(None, description="추천받을 카테고리 (기본: 기존 장소와 동일)")
    limit: int = Field(10, description="추천 개수")


class AlternativePlace(BaseModel):
    """추천 대안 장소"""
    id: int
    name: str
    category: str
    lat: float
    lng: float
    rating: float
    address: str
    source: str
    distance_impact: float = Field(..., description="이 장소를 선택 시 총 이동거리 변화 (km)")
    total_route_distance: float = Field(..., description="이 장소 선택 시 총 이동거리 (km)")


@router.post("/recommend-alternatives")
async def recommend_alternative_places(
    request: RecommendAlternativesRequest,
    db: AsyncSession = Depends(get_db_session)
) -> List[AlternativePlace]:
    """
    일정 내 장소 교체를 위한 대안 추천 (OR-Tools 동선 최적화 기반)
    
    - 현재 일정의 장소들과 교체하려는 위치를 받음
    - 같은 카테고리의 다른 장소들 중 동선에 최적인 장소들 추천
    - 각 대안 선택 시 총 이동거리 변화를 계산
    
    Examples:
        POST /api/attractions/recommend-alternatives
        {
            "current_places": [
                {"name": "성산일출봉", "category": "자연", "lat": 33.4, "lng": 126.9},
                {"name": "흑돼지거리", "category": "맛집", "lat": 33.5, "lng": 126.5},
                {"name": "협재해변", "category": "해변", "lat": 33.4, "lng": 126.2}
            ],
            "replace_index": 1,
            "category": "맛집",
            "limit": 10
        }
    """
    try:
        current_places = request.current_places
        replace_idx = request.replace_index
        
        if replace_idx < 0 or replace_idx >= len(current_places):
            raise HTTPException(status_code=400, detail="잘못된 인덱스입니다")
        
        # 교체하려는 장소의 카테고리 (미지정 시 기존 장소와 동일)
        target_category = request.category or current_places[replace_idx].category
        
        logger.info(f"🔄 대안 추천 요청: {len(current_places)}개 장소, 인덱스 {replace_idx}, 카테고리: {target_category}")
        
        # 1. 현재 일정의 총 이동거리 계산 (Nearest Neighbor - 빠름)
        current_locations = [{"lat": p.lat, "lng": p.lng} for p in current_places]
        current_distance_matrix = build_distance_matrix(current_locations)
        _, current_total_distance = nearest_neighbor_tsp(current_distance_matrix, start_index=0)
        
        logger.info(f"   현재 일정 총 거리: {current_total_distance:.2f}km")
        
        # 2. 같은 카테고리의 대안 장소 조회
        candidates = []
        
        # 카테고리 매핑
        attraction_categories = ["자연", "문화", "해변", "액티비티", "관광지"]
        place_categories = ["맛집", "카페"]
        
        # 이미 일정에 있는 장소 이름들 (중복 방지)
        existing_names = {p.name for p in current_places}
        
        # attractions 테이블 조회
        if target_category in attraction_categories or target_category == "관광지":
            cat_filter = f"AND category ILIKE '%{target_category}%'" if target_category != "관광지" else ""
            query = text(f"""
                SELECT id, name, category, lat, lng, avg_rating as rating, address
                FROM attractions
                WHERE lat IS NOT NULL AND lng IS NOT NULL
                {cat_filter}
                ORDER BY avg_rating DESC NULLS LAST
                LIMIT 100
            """)
            result = await db.execute(query)
            for row in result.fetchall():
                if row[1] not in existing_names:
                    candidates.append({
                        "id": row[0], "name": row[1], "category": row[2] or target_category,
                        "lat": float(row[3]), "lng": float(row[4]),
                        "rating": float(row[5]) if row[5] else 0, "address": row[6] or "",
                        "source": "attraction"
                    })
        
        # places 테이블 조회 (맛집, 카페)
        if target_category in place_categories:
            if target_category == "맛집":
                cat_filter = """AND (
                    category ILIKE '%고기%' OR category ILIKE '%한식%' OR 
                    category ILIKE '%중식%' OR category ILIKE '%일식%' OR 
                    category ILIKE '%양식%' OR category ILIKE '%회%' OR 
                    category ILIKE '%국수%' OR category ILIKE '%해물%' OR
                    category ILIKE '%해장국%' OR category ILIKE '%돈가스%'
                )"""
            else:
                cat_filter = "AND category ILIKE '%카페%'"
            
            query = text(f"""
                SELECT id, name, category, lat, lng, rating, address
                FROM places
                WHERE lat IS NOT NULL AND lng IS NOT NULL
                {cat_filter}
                AND name NOT ILIKE '%호텔%' AND name NOT ILIKE '%리조트%'
                ORDER BY rating DESC NULLS LAST
                LIMIT 100
            """)
            result = await db.execute(query)
            for row in result.fetchall():
                if row[1] not in existing_names:
                    candidates.append({
                        "id": row[0], "name": row[1], "category": target_category,
                        "lat": float(row[3]), "lng": float(row[4]),
                        "rating": float(row[5]) if row[5] else 0, "address": row[6] or "",
                        "source": "place"
                    })
        
        logger.info(f"   {len(candidates)}개 대안 후보 조회됨")
        
        # 3. 하이브리드 방식: 1단계 - 앞뒤 거리로 빠르게 필터링
        prev_loc = current_locations[replace_idx - 1] if replace_idx > 0 else None
        next_loc = current_locations[replace_idx + 1] if replace_idx < len(current_locations) - 1 else None
        current_loc = current_locations[replace_idx]
        
        # 현재 장소의 앞뒤 거리
        current_prev_dist = haversine_distance(prev_loc["lat"], prev_loc["lng"], current_loc["lat"], current_loc["lng"]) if prev_loc else 0
        current_next_dist = haversine_distance(current_loc["lat"], current_loc["lng"], next_loc["lat"], next_loc["lng"]) if next_loc else 0
        current_segment_dist = current_prev_dist + current_next_dist
        
        # 1단계: 앞뒤 거리로 대략적인 점수 계산 (빠름)
        candidates_with_rough_score = []
        for candidate in candidates:
            cand_prev_dist = haversine_distance(prev_loc["lat"], prev_loc["lng"], candidate["lat"], candidate["lng"]) if prev_loc else 0
            cand_next_dist = haversine_distance(candidate["lat"], candidate["lng"], next_loc["lat"], next_loc["lng"]) if next_loc else 0
            rough_impact = (cand_prev_dist + cand_next_dist) - current_segment_dist
            candidates_with_rough_score.append({**candidate, "rough_impact": rough_impact})
        
        # 대략적 점수로 정렬 후 상위 30개만 선택
        candidates_with_rough_score.sort(key=lambda x: x["rough_impact"])
        top_candidates = candidates_with_rough_score[:30]
        
        logger.info(f"   1단계 필터링: {len(top_candidates)}개 상위 후보 선택")
        
        # 2단계: 상위 후보들만 TSP로 정확히 계산
        alternatives_with_impact = []
        
        for candidate in top_candidates:
            # 후보로 대체한 새 일정
            test_locations = current_locations.copy()
            test_locations[replace_idx] = {"lat": candidate["lat"], "lng": candidate["lng"]}
            
            # TSP로 정확한 거리 계산 (Nearest Neighbor - 빠름)
            test_distance_matrix = build_distance_matrix(test_locations)
            _, test_total_distance = nearest_neighbor_tsp(test_distance_matrix, start_index=0)
            
            # 정확한 거리 변화량
            distance_impact = test_total_distance - current_total_distance
            
            alternatives_with_impact.append({
                "id": candidate["id"],
                "name": candidate["name"],
                "category": candidate["category"],
                "lat": candidate["lat"],
                "lng": candidate["lng"],
                "rating": candidate["rating"],
                "address": candidate["address"],
                "source": candidate["source"],
                "distance_impact": round(distance_impact, 2),
                "total_route_distance": round(test_total_distance, 2)
            })
        
        logger.info(f"   2단계 TSP 계산 완료: {len(alternatives_with_impact)}개")
        
        # 4. 동선 효율성 기준 정렬 (거리 증가량 낮은 순)
        # 단, 평점도 고려 (가중치: 거리 70%, 평점 30%)
        for alt in alternatives_with_impact:
            # 정규화 점수 (거리 영향이 작을수록, 평점이 높을수록 좋음)
            distance_score = -alt["distance_impact"]  # 음수일수록 좋음
            rating_score = alt["rating"] * 2  # 0~10 범위
            alt["combined_score"] = distance_score * 0.7 + rating_score * 0.3
        
        alternatives_with_impact.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # 상위 N개 반환
        top_alternatives = alternatives_with_impact[:request.limit]
        
        logger.info(f"✅ {len(top_alternatives)}개 대안 추천 완료")
        if top_alternatives:
            best = top_alternatives[0]
            logger.info(f"   최적 대안: {best['name']} (거리 변화: {best['distance_impact']:+.1f}km)")
        
        return top_alternatives
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 대안 추천 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"대안 추천 중 오류: {str(e)}")


@router.get("")
async def get_attractions_list(
    category: Optional[str] = Query(None, description="카테고리 필터 (전체, 자연, 문화, 해변, 맛집, 카페, 액티비티)"),
    search: Optional[str] = Query(None, description="검색어"),
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db_session)
):
    """
    관광지/맛집/카페 통합 목록 조회
    
    - attractions 테이블: 관광지 (자연, 문화, 해변, 액티비티)
    - places 테이블: 맛집, 카페
    
    Examples:
        /api/attractions?category=맛집&search=흑돼지
        /api/attractions?category=자연&limit=20
    """
    results = []
    
    # 카테고리 매핑
    attraction_categories = ["자연", "문화", "해변", "액티비티", "관광지"]
    place_categories = ["맛집", "카페", "숙박"]
    
    # 검색 조건 생성
    search_condition = ""
    if search:
        search_condition = f"AND name ILIKE '%{search}%'"
    
    # 1. attractions 테이블에서 조회 (관광지)
    if category is None or category == "전체" or category in attraction_categories:
        category_filter = ""
        if category and category != "전체" and category in attraction_categories:
            category_filter = f"AND category ILIKE '%{category}%'"
        
        attractions_query = text(f"""
            SELECT 
                id, name, category, lat, lng, avg_rating as rating, 
                price_range as price, address, 'attraction' as source,
                description, phone, kid_friendly
            FROM attractions
            WHERE 1=1 {category_filter} {search_condition}
            ORDER BY avg_rating DESC NULLS LAST
            LIMIT :limit OFFSET :skip
        """)
        
        result = await db.execute(attractions_query, {"limit": limit, "skip": skip})
        for row in result.fetchall():
            results.append({
                "id": row[0],
                "name": row[1],
                "category": row[2] or "관광지",
                "lat": float(row[3]) if row[3] else 0,
                "lng": float(row[4]) if row[4] else 0,
                "rating": float(row[5]) if row[5] else 0,
                "price": row[6] or "",
                "address": row[7] or "",
                "source": row[8],
                "description": row[9] or "",
                "phone": row[10] or "",
                "kid_friendly": row[11] or False,
            })
    
    # 2. places 테이블에서 조회 (맛집, 카페, 숙박)
    if category is None or category == "전체" or category in place_categories:
        category_filter = ""
        exclude_accommodation = ""
        
        if category == "맛집":
            category_filter = """AND (
                category ILIKE '%고기%' OR category ILIKE '%한식%' OR 
                category ILIKE '%중식%' OR category ILIKE '%일식%' OR 
                category ILIKE '%양식%' OR category ILIKE '%회%' OR 
                category ILIKE '%국수%' OR category ILIKE '%해물%' OR
                category ILIKE '%해장국%' OR category ILIKE '%돈가스%' OR
                category ILIKE '%분식%' OR category ILIKE '%라면%' OR
                category ILIKE '%햄버거%' OR category ILIKE '%치킨%'
            )"""
            exclude_accommodation = """
                AND category NOT ILIKE '%호텔%'
                AND category NOT ILIKE '%리조트%'
                AND category NOT ILIKE '%펜션%'
                AND category NOT ILIKE '%숙박%'
                AND category NOT ILIKE '%게스트하우스%'
                AND category NOT ILIKE '%민박%'
            """
        elif category == "카페":
            category_filter = "AND category ILIKE '%카페%'"
        elif category == "숙박":
            category_filter = """AND (
                category ILIKE '%호텔%' OR category ILIKE '%리조트%' OR 
                category ILIKE '%펜션%' OR category ILIKE '%숙박%' OR
                category ILIKE '%게스트하우스%' OR category ILIKE '%민박%'
            )"""
        # 전체 조회 시 모든 카테고리 포함 (숙박 포함)
        
        places_query = text(f"""
            SELECT 
                id, name, category, lat, lng, rating, 
                price_range as price, address, 'place' as source
            FROM places
            WHERE 1=1 {category_filter} {search_condition} {exclude_accommodation}
            ORDER BY rating DESC NULLS LAST
            LIMIT :limit OFFSET :skip
        """)
        
        result = await db.execute(places_query, {"limit": limit, "skip": skip})
        for row in result.fetchall():
            # 카테고리 분류
            cat = row[2] or ""
            display_category = "맛집"
            if "카페" in cat or "디저트" in cat:
                display_category = "카페"
            elif any(x in cat for x in ["호텔", "리조트", "펜션", "숙박", "게스트하우스", "민박"]):
                display_category = "숙박"
            
            results.append({
                "id": row[0],
                "name": row[1],
                "category": display_category,
                "lat": float(row[3]) if row[3] else 0,
                "lng": float(row[4]) if row[4] else 0,
                "rating": float(row[5]) if row[5] else 0,
                "price": row[6] or "",
                "address": row[7] or "",
                "source": row[8],
            })
    
    # 평점 기준 정렬
    results.sort(key=lambda x: x["rating"], reverse=True)
    return results


@router.get("/by-names")
async def get_attractions_by_names(
    names: str = Query(..., description="관광지 이름 목록 (쉼표로 구분)"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    관광지 이름으로 위치 정보 조회
    
    Examples:
        /api/attractions/by-names?names=한라산,성산일출봉,협재해수욕장
    """
    # 쉼표로 구분된 이름 파싱
    name_list = [name.strip() for name in names.split(',') if name.strip()]
    
    if not name_list:
        return []
    
    # SQL 쿼리 생성 (ILIKE로 부분 매칭)
    # 예: "한라산" 검색 시 "한라산국립공원"도 매칭
    conditions = []
    for name in name_list:
        conditions.append(f"name ILIKE '%{name}%'")
    
    where_clause = " OR ".join(conditions)
    
    query = text(f"""
        SELECT DISTINCT
            id, name, category, lat, lng, avg_rating, price_range, address
        FROM attractions
        WHERE {where_clause}
        LIMIT 50
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    # 결과 포맷팅
    attractions = []
    for row in rows:
        attractions.append({
            "id": row[0],
            "name": row[1],
            "category": row[2] or "",
            "lat": float(row[3]) if row[3] else 0,
            "lng": float(row[4]) if row[4] else 0,
            "rating": float(row[5]) if row[5] else 0,
            "price": row[6] or "",
            "address": row[7] or "",
        })
    
    return attractions


@router.get("/places/{place_id}")
async def get_place_detail(
    place_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Places 테이블 상세 정보 조회
    """
    query = text("""
        SELECT id, name, category, address, phone, rating, review_count,
               min_price, max_price, price_range, parking, kid_friendly,
               wheelchair, pet_friendly, reservation, wifi, business_hours,
               lat, lng, region, url
        FROM places
        WHERE id = :id
    """)
    
    result = await db.execute(query, {"id": place_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="장소를 찾을 수 없습니다")
    
    return {
        "id": row[0],
        "name": row[1],
        "category": row[2],
        "address": row[3],
        "phone": row[4],
        "rating": float(row[5]) if row[5] else 0,
        "review_count": row[6] or 0,
        "min_price": row[7],
        "max_price": row[8],
        "price_range": row[9],
        "parking": row[10] or False,
        "kid_friendly": row[11] or False,
        "wheelchair": row[12] or False,
        "pet_friendly": row[13] or False,
        "reservation": row[14] or False,
        "wifi": row[15] or False,
        "business_hours": row[16],
        "lat": float(row[17]) if row[17] else 0,
        "lng": float(row[18]) if row[18] else 0,
        "region": row[19],
        "url": row[20],
    }


@router.get("/filters/options")
async def get_filter_options(
    db: AsyncSession = Depends(get_db_session)
):
    """
    필터 옵션 조회 (카테고리, 지역 목록)
    실제 DB 데이터 기반으로 반환
    """
    # 카테고리 목록 조회
    category_query = text("""
        SELECT DISTINCT category, COUNT(*) as count
        FROM places
        WHERE category IS NOT NULL AND category != ''
        GROUP BY category
        ORDER BY count DESC
        LIMIT 30
    """)
    cat_result = await db.execute(category_query)
    categories = [{"name": row[0], "count": row[1]} for row in cat_result.fetchall()]
    
    # 지역 목록 조회
    region_query = text("""
        SELECT DISTINCT region, COUNT(*) as count
        FROM places
        WHERE region IS NOT NULL AND region != ''
        GROUP BY region
        ORDER BY count DESC
    """)
    region_result = await db.execute(region_query)
    regions = [{"name": row[0], "count": row[1]} for row in region_result.fetchall()]
    
    return {
        "categories": categories,
        "regions": regions
    }


@router.get("/{attraction_id}")
async def get_attraction_by_id(
    attraction_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    관광지 ID로 상세 정보 조회
    """
    query = text("""
        SELECT id, name, category, lat, lng, avg_rating, price_range, 
               address, phone, description
        FROM attractions
        WHERE id = :id
    """)
    
    result = await db.execute(query, {"id": attraction_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="관광지를 찾을 수 없습니다")
    
    return {
        "id": row[0],
        "name": row[1],
        "category": row[2],
        "lat": float(row[3]) if row[3] else 0,
        "lng": float(row[4]) if row[4] else 0,
        "rating": float(row[5]) if row[5] else 0,
        "price": row[6],
        "address": row[7],
        "phone": row[8],
        "description": row[9],
    }


# ===== 경로 최적화 API =====

class OptimalPositionRequest(BaseModel):
    """최적 삽입 위치 계산 요청"""
    current_places: List[PlaceInfo] = Field(..., description="현재 일정의 장소들")
    new_place: PlaceInfo = Field(..., description="추가하려는 장소")


class OptimalPositionResponse(BaseModel):
    """최적 삽입 위치 응답"""
    optimal_index: int = Field(..., description="최적 삽입 위치 (0-based)")
    distance_increase: float = Field(..., description="거리 증가량 (km)")
    total_distance_before: float = Field(..., description="삽입 전 총 거리 (km)")
    total_distance_after: float = Field(..., description="삽입 후 총 거리 (km)")
    message: str = Field(..., description="설명 메시지")


class OptimizeRouteRequest(BaseModel):
    """전체 경로 최적화 요청"""
    places: List[PlaceInfo] = Field(..., description="최적화할 장소들")
    fix_first: bool = Field(True, description="첫 번째 장소 고정 여부 (시작점)")


class RoutePath(BaseModel):
    """경로 정보"""
    from_place: Dict[str, Any] = Field(..., description="출발지 정보")
    to_place: Dict[str, Any] = Field(..., description="도착지 정보")
    path: List[List[float]] = Field(..., description="경로 좌표 [[lat, lng], ...]")
    distance: Optional[float] = Field(None, description="거리 (km)")
    duration: Optional[float] = Field(None, description="소요 시간 (분)")


class OptimizeRouteResponse(BaseModel):
    """전체 경로 최적화 응답"""
    optimized_order: List[int] = Field(..., description="최적화된 순서 (원본 인덱스)")
    total_distance_before: float = Field(..., description="최적화 전 총 거리 (km)")
    total_distance_after: float = Field(..., description="최적화 후 총 거리 (km)")
    distance_saved: float = Field(..., description="절약된 거리 (km)")
    message: str = Field(..., description="설명 메시지")
    routes: Optional[List[RoutePath]] = Field(None, description="경로 정보 (최적화된 순서)")


@router.post("/find-optimal-position", response_model=OptimalPositionResponse)
async def find_optimal_position(request: OptimalPositionRequest):
    """
    새 장소를 추가할 때 최적 삽입 위치 계산 (TSP 기반)
    """
    try:
        if len(request.current_places) == 0:
            return OptimalPositionResponse(
                optimal_index=0,
                distance_increase=0,
                total_distance_before=0,
                total_distance_after=0,
                message="첫 번째 장소로 추가됩니다"
            )
        
        # 현재 장소들의 좌표
        current_locations = [{"lat": p.lat, "lng": p.lng} for p in request.current_places]
        new_loc = {"lat": request.new_place.lat, "lng": request.new_place.lng}
        
        # 현재 총 거리 계산
        total_before = 0.0
        for i in range(len(current_locations) - 1):
            total_before += haversine_distance(
                current_locations[i]["lat"], current_locations[i]["lng"],
                current_locations[i+1]["lat"], current_locations[i+1]["lng"]
            )
        
        # 각 위치에 삽입했을 때 총 거리 계산
        best_index = 0
        best_total = float('inf')
        
        for insert_idx in range(len(current_locations) + 1):
            # 삽입 후 리스트
            test_locations = current_locations[:insert_idx] + [new_loc] + current_locations[insert_idx:]
            
            # 총 거리 계산
            test_total = 0.0
            for i in range(len(test_locations) - 1):
                test_total += haversine_distance(
                    test_locations[i]["lat"], test_locations[i]["lng"],
                    test_locations[i+1]["lat"], test_locations[i+1]["lng"]
                )
            
            if test_total < best_total:
                best_total = test_total
                best_index = insert_idx
        
        distance_increase = best_total - total_before
        
        # 위치 설명
        if best_index == 0:
            position_desc = "맨 앞"
        elif best_index == len(current_locations):
            position_desc = "맨 뒤"
        else:
            prev_name = request.current_places[best_index - 1].name
            next_name = request.current_places[best_index].name
            position_desc = f"'{prev_name}' 다음"
        
        logger.info(f"✅ 최적 삽입 위치: {best_index} ({position_desc}), 거리 증가: {distance_increase:+.1f}km")
        
        return OptimalPositionResponse(
            optimal_index=best_index,
            distance_increase=round(distance_increase, 2),
            total_distance_before=round(total_before, 2),
            total_distance_after=round(best_total, 2),
            message=f"{position_desc}에 추가하면 가장 효율적입니다 (이동거리 {distance_increase:+.1f}km)"
        )
        
    except Exception as e:
        logger.error(f"❌ 최적 위치 계산 오류: {e}")
        raise HTTPException(status_code=500, detail=f"최적 위치 계산 오류: {str(e)}")


@router.post("/optimize-route", response_model=OptimizeRouteResponse)
async def optimize_route(request: OptimizeRouteRequest):
    """
    전체 경로 TSP 최적화
    """
    try:
        if len(request.places) < 2:
            return OptimizeRouteResponse(
                optimized_order=list(range(len(request.places))),
                total_distance_before=0,
                total_distance_after=0,
                distance_saved=0,
                message="장소가 2개 미만이어서 최적화가 필요 없습니다"
            )
        
        # 좌표 리스트
        locations = [{"lat": p.lat, "lng": p.lng} for p in request.places]
        
        # 실제 도로 거리로 거리 행렬 생성 (카카오맵 API 사용)
        distance_matrix = build_distance_matrix(locations, use_road_distance=True)
        
        # 현재 순서대로의 총 거리 (거리 행렬에서 가져오기)
        total_before = 0.0
        for i in range(len(locations) - 1):
            total_before += distance_matrix[i][i+1]
        
        # TSP로 최적 순서 계산
        start_index = 0 if request.fix_first else None
        optimized_order, total_after = nearest_neighbor_tsp(distance_matrix, start_index=start_index)
        
        distance_saved = total_before - total_after
        
        if distance_saved <= 0.5:
            message = "현재 경로가 이미 최적에 가깝습니다!"
        else:
            message = f"경로를 재정렬해서 총 {distance_saved:.1f}km 단축했습니다!"
        
        logger.info(f"✅ 경로 최적화: {total_before:.1f}km → {total_after:.1f}km (절약: {distance_saved:.1f}km)")
        
        # 최적화된 순서대로 경로 정보 생성 (장소명 기반 좌표 보정)
        routes = []
        try:
            from src.tool_agents.route_optimizer_agent.utils import (
                get_road_route_kakao_by_name,
                haversine_distance
            )
            
            optimized_places = [request.places[idx] for idx in optimized_order]
            for i in range(len(optimized_places) - 1):
                p1 = optimized_places[i]
                p2 = optimized_places[i + 1]
                
                # 장소명 기반 좌표 보정 후 길찾기 (성공률 향상)
                route_info = get_road_route_kakao_by_name(
                    p1.name, p1.lat, p1.lng,
                    p2.name, p2.lat, p2.lng
                )
                if route_info and route_info.get("path"):
                    routes.append(RoutePath(
                        from_place={"name": p1.name, "lat": p1.lat, "lng": p1.lng},
                        to_place={"name": p2.name, "lat": p2.lat, "lng": p2.lng},
                        path=route_info["path"],
                        distance=route_info.get("distance"),
                        duration=route_info.get("duration")
                    ))
                else:
                    # 경로 정보를 가져오지 못한 경우: 추정 거리/시간 제공
                    straight_dist = haversine_distance(p1.lat, p1.lng, p2.lat, p2.lng)
                    estimated_dist = straight_dist * 1.35  # 제주도 평균 우회 계수
                    estimated_dur = (estimated_dist / 40) * 60  # 평균 40km/h
                    
                    routes.append(RoutePath(
                        from_place={"name": p1.name, "lat": p1.lat, "lng": p1.lng},
                        to_place={"name": p2.name, "lat": p2.lat, "lng": p2.lng},
                        path=[[p1.lat, p1.lng], [p2.lat, p2.lng]],
                        distance=round(estimated_dist, 1),
                        duration=round(estimated_dur, 0)
                    ))
        except Exception as e:
            logger.warning(f"경로 정보 생성 실패: {e}")
            routes = None
        
        return OptimizeRouteResponse(
            optimized_order=optimized_order,
            total_distance_before=round(total_before, 2),
            total_distance_after=round(total_after, 2),
            distance_saved=round(distance_saved, 2),
            message=message,
            routes=routes
        )
        
    except Exception as e:
        logger.error(f"❌ 경로 최적화 오류: {e}")
        raise HTTPException(status_code=500, detail=f"경로 최적화 오류: {str(e)}")
