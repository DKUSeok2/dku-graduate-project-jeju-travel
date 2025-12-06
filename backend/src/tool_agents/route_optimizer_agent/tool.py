"""
Route Optimizer Agent Tool - 경로 최적화 (klid-aicb 패턴)
"""
from typing import Any, Dict, List, Optional, Type
from pydantic import Field, BaseModel, ConfigDict
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
import logging
import json

from src.tool_agents.base import BaseAgentTool
from src.tool_agents.route_optimizer_agent.utils import (
    haversine_distance,
    build_distance_matrix,
    solve_tsp,  # OR-Tools 기반 TSP 솔버
    calculate_travel_time,
    format_time,
    ORTOOLS_AVAILABLE,
    get_road_route_kakao_by_name,  # 실제 도로 경로 가져오기
)
from sqlalchemy import create_engine, text
from src.config import settings

logger = logging.getLogger(__name__)


class RouteOptimizerInputArgs(BaseModel):
    """경로 최적화 입력 파라미터"""
    attraction_names: List[str] = Field(
        ...,
        description="방문할 장소 이름 리스트 (관광지, 맛집, 카페 모두 가능. 예: ['성산일출봉', '고국수', '협재해수욕장'])"
    )
    start_location: Optional[Dict[str, float]] = Field(
        default=None,
        description="시작 위치 좌표 {'lat': 33.5, 'lng': 126.5} (선택사항)"
    )


class RouteOptimizerTool(BaseAgentTool):
    """경로 최적화 도구 (klid-aicb 패턴)
    
    TSP 알고리즘을 사용하여 최적 경로를 계산합니다.
    """
    
    name: str = "optimize_travel_route"
    description: str = """여러 장소(관광지, 맛집, 카페)의 최적 방문 순서를 계산합니다. TSP 알고리즘을 사용하여 이동 시간과 거리를 최소화합니다."""
    args_schema: Type[BaseModel] = RouteOptimizerInputArgs
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _run(
        self,
        attraction_names: List[str],
        start_location: Optional[Dict[str, float]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """동기 실행"""
        logger.info(f"🗺️ 경로 최적화 호출: {len(attraction_names)}개 관광지")
        
        try:
            # 1. DB에서 관광지 좌표 조회
            engine = create_engine(settings.database_url)
            attractions = []
            
            with engine.connect() as conn:
                for name in attraction_names:
                    # 1. 먼저 attractions 테이블에서 검색
                    query = text("""
                        SELECT id, name, lat, lng, category
                        FROM attractions
                        WHERE name ILIKE :name
                        LIMIT 1
                    """)
                    result = conn.execute(query, {"name": f"%{name}%"}).fetchone()
                    
                    # 2. attractions에 없으면 places 테이블에서 검색 (맛집/카페)
                    if not result:
                        query = text("""
                            SELECT id, name, lat, lng, category
                            FROM places
                            WHERE name ILIKE :name AND lat IS NOT NULL AND lng IS NOT NULL
                        LIMIT 1
                    """)
                    result = conn.execute(query, {"name": f"%{name}%"}).fetchone()
                    
                    if result:
                        attractions.append({
                            "id": result[0],
                            "name": result[1],
                            "lat": float(result[2]) if result[2] else 0.0,  # Decimal → float 변환
                            "lng": float(result[3]) if result[3] else 0.0,  # Decimal → float 변환
                            "category": result[4] or ""
                        })
                    else:
                        logger.warning(f"   ⚠️ '{name}' 위치 정보 없음 (attractions/places 모두 검색)")
            
            engine.dispose()
            
            if len(attractions) < 2:
                return f"경로 최적화를 위해서는 최소 2개 이상의 관광지가 필요합니다. (현재: {len(attractions)}개)"
            
            logger.info(f"   조회된 관광지: {len(attractions)}개")
            
            # 2. 거리 행렬 생성
            locations = [{"lat": attr["lat"], "lng": attr["lng"]} for attr in attractions]
            
            # 시작 위치가 지정되면 맨 앞에 추가
            if start_location:
                locations.insert(0, start_location)
                attractions.insert(0, {
                    "id": 0,
                    "name": "출발지",
                    "lat": start_location["lat"],
                    "lng": start_location["lng"],
                    "category": "시작"
                })
            
            distance_matrix = build_distance_matrix(locations)
            
            # 3. TSP 알고리즘으로 최적 경로 계산 (OR-Tools 사용)
            route_indices, total_distance = solve_tsp(distance_matrix, start_index=0)
            
            if ORTOOLS_AVAILABLE:
                logger.info("   🚀 OR-Tools TSP 솔버 사용")
            else:
                logger.info("   📍 Fallback: Nearest Neighbor 알고리즘 사용")
            
            # 4. 이동 시간 계산 (제주도 평균 속도: 40km/h)
            travel_time = calculate_travel_time(total_distance, avg_speed_kmh=40.0)
            
            # 5. 결과 포맷팅
            result_text = f"# 🗺️ 최적 경로 계산 완료\n\n"
            result_text += f"**{len(attractions)}개 관광지**의 최적 방문 순서를 계산했습니다.\n\n"
            
            result_text += f"## 📍 방문 순서\n\n"
            for i, idx in enumerate(route_indices, 1):
                attr = attractions[idx]
                result_text += f"{i}. **{attr['name']}** ({attr['category']})\n"
                
                # 다음 지점까지의 거리
                if i < len(route_indices):
                    next_idx = route_indices[i]
                    dist = distance_matrix[idx][next_idx]
                    time = calculate_travel_time(dist)
                    result_text += f"   ↓ {dist:.1f}km ({format_time(time)})\n"
            
            result_text += f"\n## 📊 요약\n\n"
            result_text += f"- **총 이동거리**: {total_distance:.1f}km\n"
            result_text += f"- **예상 이동시간**: {format_time(travel_time)}\n"
            result_text += f"- **평균 이동거리**: {total_distance / (len(attractions) - 1):.1f}km/구간\n"
            
            # 최적화 효과 계산 (단순 순서 vs 최적화)
            if len(attractions) > 2:
                simple_distance = sum(distance_matrix[i][i+1] for i in range(len(attractions) - 1))
                savings = simple_distance - total_distance
                savings_pct = (savings / simple_distance) * 100 if simple_distance > 0 else 0
                
                if savings > 0:
                    result_text += f"- **절감 효과**: 기존 순서 대비 {savings:.1f}km ({savings_pct:.1f}%) 단축\n"
            
            result_text += f"\n💡 **팁**: 각 관광지에서 1-2시간 정도 여유를 두고 계획하세요!"
            
            # 경로에 포함된 관광지들의 지도 데이터 추가 (프론트엔드 표시용)
            if attractions:
                # 최적화된 순서대로 관광지 정렬
                ordered_attractions = [attractions[idx] for idx in route_indices]
                
                # 중심점 계산
                lats = [a['lat'] for a in ordered_attractions if a.get('lat')]
                lngs = [a['lng'] for a in ordered_attractions if a.get('lng')]
                center_lat = sum(lats) / len(lats) if lats else 33.3617
                center_lng = sum(lngs) / len(lngs) if lngs else 126.5292
                
                # 🔥 실제 도로 경로 가져오기 (카카오 모빌리티 API)
                road_routes = []
                for i in range(len(ordered_attractions) - 1):
                    from_attr = ordered_attractions[i]
                    to_attr = ordered_attractions[i + 1]
                    
                    route_info = get_road_route_kakao_by_name(
                        from_attr["name"], float(from_attr["lat"]), float(from_attr["lng"]),
                        to_attr["name"], float(to_attr["lat"]), float(to_attr["lng"])
                    )
                    
                    if route_info and route_info.get("path"):
                        road_routes.append({
                            "from_place": {"name": from_attr["name"], "lat": float(from_attr["lat"]), "lng": float(from_attr["lng"])},
                            "to_place": {"name": to_attr["name"], "lat": float(to_attr["lat"]), "lng": float(to_attr["lng"])},
                            "path": route_info["path"],
                            "distance": route_info.get("distance", 0),
                            "duration": route_info.get("duration", 0)
                        })
                        logger.info(f"   🛣️ 도로 경로 획득: {from_attr['name']} → {to_attr['name']} ({route_info['distance']:.1f}km)")
                    else:
                        # fallback: 직선 경로
                        road_routes.append({
                            "from_place": {"name": from_attr["name"], "lat": float(from_attr["lat"]), "lng": float(from_attr["lng"])},
                            "to_place": {"name": to_attr["name"], "lat": float(to_attr["lat"]), "lng": float(to_attr["lng"])},
                            "path": [[float(from_attr["lat"]), float(from_attr["lng"])], [float(to_attr["lat"]), float(to_attr["lng"])]],
                            "distance": distance_matrix[route_indices[i]][route_indices[i+1]],
                            "duration": 0
                        })
                        logger.info(f"   📍 직선 경로 사용: {from_attr['name']} → {to_attr['name']}")
                
                map_data = {
                    "type": "route_map",
                    "markers": [
                        {
                            "id": attr["id"],
                            "position": {"lat": float(attr["lat"]), "lng": float(attr["lng"])},
                            "label": str(i + 1),
                            "name": attr["name"],
                            "category": attr.get("category", ""),
                            "rating": 0,
                            "price": "",
                            "day": 1,
                            "order": i + 1
                        }
                        for i, attr in enumerate(ordered_attractions)
                    ],
                    "center": {"lat": center_lat, "lng": center_lng},
                    "zoom": 10,
                    "showDayColors": True,
                    # 🔥 실제 도로 경로 데이터 추가
                    "routes": [{"day": 1, "routes": road_routes}] if road_routes else []
                }
                
                result_text += f"\n\n[ATTRACTIONS_DATA]{json.dumps(map_data, ensure_ascii=False)}[/ATTRACTIONS_DATA]"
                logger.info(f"   📍 경로 지도 데이터 추가됨: {len(ordered_attractions)}개 관광지, {len(road_routes)}개 도로 경로")
            
            logger.info(f"✅ 경로 최적화 완료: {total_distance:.1f}km, {format_time(travel_time)}")
            
            return result_text
            
        except Exception as e:
            logger.error(f"❌ 경로 최적화 오류: {e}")
            import traceback
            traceback.print_exc()
            return f"경로 최적화 중 오류가 발생했습니다: {str(e)}"
    
    async def _arun(
        self,
        attraction_names: List[str],
        start_location: Optional[Dict[str, float]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """비동기 실행 (동기 버전 호출)"""
        return self._run(attraction_names, start_location, run_manager)
    
    def format_content(self, message: ToolMessage) -> ToolMessage:
        """경로 최적화 결과를 LLM에게 전달하기 위한 형식으로 변환
        
        결과에 다음 단계 지시사항을 추가합니다.
        """
        content = message.content or ""
        
        # 에러 케이스 처리
        if "오류" in content or "필요합니다" in content:
            instruction = "\n\n[중요] 경로 최적화에 실패했습니다. 사용자에게 오류를 알리고 필요한 정보를 요청하세요."
            return message.model_copy(update={"content": f"{content}{instruction}"})
        
        # 정상 결과에 지시사항 추가
        instruction = """

[중요] 위 경로 최적화 결과를 바탕으로 사용자에게 안내하세요.
- 최적 방문 순서를 자연스럽게 설명하세요
- 총 이동거리와 예상 소요시간을 알려주세요
- 자연스러운 대화체로 답변하세요
"""
        
        return message.model_copy(update={"content": f"{content}{instruction}"})
