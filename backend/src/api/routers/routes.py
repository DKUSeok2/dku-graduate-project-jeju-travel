"""
경로 계산 API
- 카카오맵 API를 사용하여 장소 간 도로 경로 계산
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from src.tool_agents.route_optimizer_agent.utils import (
    get_road_route_kakao_by_name,
    get_kakao_api_key
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/routes", tags=["routes"])


class PlaceCoord(BaseModel):
    """장소 좌표"""
    name: str
    lat: float
    lng: float
    day: Optional[int] = 1


class CalculateRoutesRequest(BaseModel):
    """경로 계산 요청"""
    places: List[PlaceCoord]


class RouteSegment(BaseModel):
    """경로 구간"""
    from_place: Dict[str, Any]
    to_place: Dict[str, Any]
    path: List[List[float]]  # [[lat, lng], ...]
    distance: Optional[float] = None  # km
    duration: Optional[float] = None  # 분
    is_estimated: Optional[bool] = False  # 추정치 여부


class DayRoutes(BaseModel):
    """일별 경로"""
    day: int
    routes: List[RouteSegment]


class CalculateRoutesResponse(BaseModel):
    """경로 계산 응답"""
    routes: List[DayRoutes]
    success: bool
    message: Optional[str] = None


@router.post("/calculate", response_model=CalculateRoutesResponse)
async def calculate_routes(request: CalculateRoutesRequest):
    """
    장소 목록에 대한 도로 경로 계산
    
    카카오맵 API를 사용하여 순차적인 장소 간 도로 경로를 계산합니다.
    실패 시 직선 경로로 fallback합니다.
    """
    if not request.places or len(request.places) < 2:
        return CalculateRoutesResponse(
            routes=[],
            success=True,
            message="장소가 2개 미만이어서 경로 계산 불필요"
        )
    
    # API 키 확인
    api_key = get_kakao_api_key()
    if not api_key:
        logger.warning("카카오 API 키 없음 - 직선 경로로 대체")
        return _create_straight_line_routes(request.places)
    
    # 일별로 장소 그룹화
    places_by_day: Dict[int, List[PlaceCoord]] = {}
    for place in request.places:
        day = place.day or 1
        if day not in places_by_day:
            places_by_day[day] = []
        places_by_day[day].append(place)
    
    all_day_routes: List[DayRoutes] = []
    total_success = 0
    total_fallback = 0
    
    for day in sorted(places_by_day.keys()):
        day_places = places_by_day[day]
        if len(day_places) < 2:
            continue
        
        routes: List[RouteSegment] = []
        
        for i in range(len(day_places) - 1):
            p1 = day_places[i]
            p2 = day_places[i + 1]
            
            # 카카오맵 API로 경로 계산
            route_info = get_road_route_kakao_by_name(
                p1.name, p1.lat, p1.lng,
                p2.name, p2.lat, p2.lng
            )
            
            if route_info and route_info.get("path"):
                # 성공: 도로 경로
                routes.append(RouteSegment(
                    from_place={"name": p1.name, "lat": p1.lat, "lng": p1.lng},
                    to_place={"name": p2.name, "lat": p2.lat, "lng": p2.lng},
                    path=route_info["path"],
                    distance=route_info.get("distance"),
                    duration=route_info.get("duration"),
                    is_estimated=False
                ))
                total_success += 1
            else:
                # 실패: 직선 경로로 fallback
                routes.append(RouteSegment(
                    from_place={"name": p1.name, "lat": p1.lat, "lng": p1.lng},
                    to_place={"name": p2.name, "lat": p2.lat, "lng": p2.lng},
                    path=[[p1.lat, p1.lng], [p2.lat, p2.lng]],
                    distance=None,
                    duration=None,
                    is_estimated=True
                ))
                total_fallback += 1
        
        if routes:
            all_day_routes.append(DayRoutes(day=day, routes=routes))
    
    logger.info(f"✅ 경로 계산 완료: 성공 {total_success}개, 직선 {total_fallback}개")
    
    return CalculateRoutesResponse(
        routes=all_day_routes,
        success=True,
        message=f"경로 계산 완료: 도로 {total_success}개, 직선 {total_fallback}개"
    )


def _create_straight_line_routes(places: List[PlaceCoord]) -> CalculateRoutesResponse:
    """직선 경로 생성 (fallback)"""
    places_by_day: Dict[int, List[PlaceCoord]] = {}
    for place in places:
        day = place.day or 1
        if day not in places_by_day:
            places_by_day[day] = []
        places_by_day[day].append(place)
    
    all_day_routes: List[DayRoutes] = []
    
    for day in sorted(places_by_day.keys()):
        day_places = places_by_day[day]
        if len(day_places) < 2:
            continue
        
        routes: List[RouteSegment] = []
        for i in range(len(day_places) - 1):
            p1 = day_places[i]
            p2 = day_places[i + 1]
            routes.append(RouteSegment(
                from_place={"name": p1.name, "lat": p1.lat, "lng": p1.lng},
                to_place={"name": p2.name, "lat": p2.lat, "lng": p2.lng},
                path=[[p1.lat, p1.lng], [p2.lat, p2.lng]],
                is_estimated=True
            ))
        
        if routes:
            all_day_routes.append(DayRoutes(day=day, routes=routes))
    
    return CalculateRoutesResponse(
        routes=all_day_routes,
        success=True,
        message="API 키 없음 - 직선 경로로 대체"
    )


