"""
Map Visualization Agent Tool - 지도 시각화 (klid-aicb 패턴)
"""
from typing import Any, Dict, List, Optional, Type
from pydantic import Field, BaseModel, ConfigDict
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
from sqlalchemy import create_engine, text
import logging
import json

from src.tool_agents.base import BaseAgentTool
from src.config import settings

logger = logging.getLogger(__name__)


class MapVisualizationInput(BaseModel):
    """지도 시각화 입력 스키마"""
    query: str = Field(description="지도에 표시할 관광지 조건 (예: '평점 4.5 이상', '해변 카테고리', '제주시 동쪽')")


class MapVisualizationTool(BaseAgentTool):
    """제주도 관광지를 지도에 시각화하는 도구 (klid-aicb 패턴)"""
    
    name: str = "visualize_attractions_on_map"
    description: str = """제주도 관광지를 지도에 시각화합니다. 지도에 표시할 관광지 조건을 입력하세요."""
    args_schema: Type[BaseModel] = MapVisualizationInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """동기 실행 (사용 안 함)"""
        raise NotImplementedError("Use _arun instead")
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        관광지를 지도에 시각화
        
        Args:
            query: 관광지 조건
        
        Returns:
            마크다운 형식의 응답 + [MAP_DATA] 마커
        """
        logger.info(f"🗺️ Map Visualization 시작: {query}")
        
        try:
            # DB에서 관광지 조회
            attractions = await self._fetch_attractions(query)
            
            if not attractions:
                return "조건에 맞는 관광지를 찾을 수 없습니다."
            
            # 지도 데이터 생성
            map_data = self._generate_map_data(attractions)
            
            # 응답 생성
            response = self._format_response(attractions, map_data)
            
            logger.info(f"✅ 지도 시각화 완료: {len(attractions)}개 관광지")
            return response
            
        except Exception as e:
            logger.error(f"❌ Map Visualization 오류: {e}")
            return f"지도 생성 중 오류가 발생했습니다: {str(e)}"
    
    def format_content(self, message: ToolMessage) -> ToolMessage:
        """지도 시각화 결과를 LLM에게 전달하기 위한 형식으로 변환
        
        결과에 다음 단계 지시사항을 추가합니다.
        """
        content = message.content or ""
        
        # 에러 케이스 처리
        if "오류" in content or "찾을 수 없습니다" in content:
            instruction = "\n\n[중요] 지도 시각화에 실패했습니다. 사용자에게 오류를 알리고 다른 조건을 제안하세요."
            return message.model_copy(update={"content": f"{content}{instruction}"})
        
        # 정상 결과에 지시사항 추가
        instruction = """

[중요] 위 지도 시각화 결과를 바탕으로 사용자에게 안내하세요.
- 표시된 관광지 목록을 간략히 소개하세요
- [MAP_DATA] 같은 마커는 응답에 포함하지 마세요
- 자연스러운 대화체로 답변하세요
"""
        
        return message.model_copy(update={"content": f"{content}{instruction}"})
    
    async def _fetch_attractions(self, query: str) -> List[Dict[str, Any]]:
        """DB에서 관광지 조회"""
        import asyncio
        
        # 간단한 키워드 기반 SQL 생성
        sql_query = self._build_sql_query(query)
        
        logger.info(f"📜 SQL Query: {sql_query}")
        
        # 동기 방식으로 DB 조회 (asyncio.to_thread 사용)
        def execute_query():
            engine = create_engine(settings.database_url)
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(sql_query))
                    columns = result.keys()
                    rows = result.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
            finally:
                engine.dispose()
        
        return await asyncio.to_thread(execute_query)
    
    def _build_sql_query(self, query: str) -> str:
        """쿼리에서 SQL 생성 (간단한 키워드 매칭)"""
        base_query = """
        SELECT id, name, category, lat, lng, avg_rating, price_range, address
        FROM attractions
        WHERE 1=1
        """
        
        conditions = []
        
        # 카테고리 필터
        categories = ["해변", "폭포", "박물관", "숲", "체험", "테마파크", "수족관", "문화", "카페"]
        for cat in categories:
            if cat in query:
                conditions.append(f"category LIKE '%{cat}%'")
        
        # 평점 필터
        if "평점" in query or "높은" in query or "좋은" in query:
            if "4.5 이상" in query or "높은" in query:
                conditions.append("avg_rating >= 4.5")
            elif "4.0 이상" in query:
                conditions.append("avg_rating >= 4.0")
        
        # 조건 추가
        if conditions:
            base_query += " AND (" + " OR ".join(conditions) + ")"
        
        # 제한
        base_query += " LIMIT 10"
        
        return base_query
    
    def _generate_map_data(self, attractions: List[Dict]) -> Dict[str, Any]:
        """지도 데이터 생성"""
        markers = []
        lats = []
        lngs = []
        
        for idx, attr in enumerate(attractions, 1):
            if attr.get("lat") and attr.get("lng"):
                markers.append({
                    "id": attr["id"],
                    "position": {
                        "lat": float(attr["lat"]),
                        "lng": float(attr["lng"])
                    },
                    "label": str(idx),
                    "name": attr["name"],
                    "category": attr.get("category", ""),
                    "rating": float(attr["avg_rating"]) if attr.get("avg_rating") else 0,
                    "price": attr.get("price_range", "")
                })
                lats.append(float(attr["lat"]))
                lngs.append(float(attr["lng"]))
        
        # 중심점 계산
        center_lat = sum(lats) / len(lats) if lats else 33.3617
        center_lng = sum(lngs) / len(lngs) if lngs else 126.5292
        
        return {
            "type": "map_visualization",
            "markers": markers,
            "center": {"lat": center_lat, "lng": center_lng},
            "zoom": 10
        }
    
    def _format_response(self, attractions: List[Dict], map_data: Dict) -> str:
        """응답 포맷팅"""
        # 마크다운 응답
        response = f"지도에 {len(attractions)}개의 관광지를 표시했어요! 🗺️\n\n"
        
        for idx, attr in enumerate(attractions, 1):
            rating_str = f"⭐ {attr['avg_rating']}" if attr.get('avg_rating') else ""
            price_str = f"💰 {attr['price_range']}" if attr.get('price_range') else ""
            response += f"{idx}. **{attr['name']}** ({attr.get('category', '')}) {rating_str} {price_str}\n"
        
        response += "\n지도에서 위치를 확인해보세요!\n\n"
        
        # JSON 마커 추가 (프론트엔드 파싱용)
        response += f"[MAP_DATA]{json.dumps(map_data, ensure_ascii=False)}[/MAP_DATA]"
        
        return response
