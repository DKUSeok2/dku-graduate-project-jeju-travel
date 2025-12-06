"""
Itinerary Generator Tool - 여행 일정 생성 도구
+ LLM 기반 조건 추출 (특정 장소 포함, 선호도 반영)
"""
from typing import Any, Dict, List, Optional, Type, Tuple
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
import logging
import json

from src.tool_agents.base import BaseAgentTool
from src.tool_agents.itinerary_agent.scheduler import ItineraryScheduler
from src.tool_agents.itinerary_agent.templates import parse_duration, parse_style
from src.tool_agents.route_optimizer_agent.utils import get_road_route_kakao
from src.config import settings

logger = logging.getLogger(__name__)


class ItineraryInputArgs(BaseModel):
    """일정 생성 입력 파라미터"""
    query: str = Field(
        ...,
        description="여행 일정 요청 (예: '2박3일 가족여행 일정', '3박4일 맛집 중심 여행')"
    )
    kid_friendly: Optional[bool] = Field(
        default=None,
        description="아이 동반 여부 (True: 아이 동반 가능한 곳만)"
    )
    parking: Optional[bool] = Field(
        default=None,
        description="주차 필요 여부 (True: 주차 가능한 곳만)"
    )


class ItineraryGeneratorTool(BaseAgentTool):
    """여행 일정 생성 도구
    
    사용자 요청을 분석하여 제주 여행 일정을 자동 생성합니다.
    - 템플릿 기반 일정 구조
    - 지역별 동선 최적화
    - 시간대별 장소 배치
    """
    
    name: str = "generate_travel_itinerary"
    description: str = """제주도 여행 일정을 생성합니다.
사용자가 '2박3일 여행 일정', '3박4일 가족여행' 등을 요청하면 이 도구를 사용하세요.
시간대별로 관광지, 맛집, 카페를 배치하고 동선을 최적화합니다."""
    args_schema: Type[BaseModel] = ItineraryInputArgs
    response_format: str = "content_and_artifact"
    
    scheduler: Optional[ItineraryScheduler] = None
    _llm: Optional[ChatOpenAI] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        # LLM 생성 (조건 추출용)
        self._llm = ChatOpenAI(
            model=settings.openai_model or "gpt-4o-mini",
            temperature=0.3,  # 정확한 추출을 위해 낮은 온도
        )
        # Scheduler에 LLM 전달
        self.scheduler = ItineraryScheduler(llm=self._llm)
    
    def _run(
        self,
        query: str,
        kid_friendly: Optional[bool] = None,
        parking: Optional[bool] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """동기 실행"""
        import asyncio
        return asyncio.run(self._arun(query, kid_friendly, parking, run_manager))
    
    async def _arun(
        self,
        query: str,
        kid_friendly: Optional[bool] = None,
        parking: Optional[bool] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        config: RunnableConfig = None
    ) -> Tuple[str, Dict[str, Any]]:
        """비동기 실행
        
        Returns:
            Tuple[str, dict]: (요약 문자열, artifact)
        """
        logger.info(f"🗓️ 일정 생성 도구 호출: {query}")
        
        try:
            # 🔥 매우 빠른 정보 확인 (도구 호출 전에 체크해야 하지만, 여기서도 체크)
            missing_info = self._check_required_info(query)
            
            if missing_info:
                # 추가 정보 필요 - 즉시 반환 (thinking 최소화)
                question_msg = f"일정을 생성하기 위해 다음 정보가 필요합니다:\n\n"
                for info in missing_info:
                    question_msg += f"- {info}\n"
                question_msg += "\n위 정보를 알려주시면 바로 일정을 만들어드리겠습니다."
                
                logger.info(f"⚠️ 추가 정보 필요: {missing_info} → 즉시 반환")
                return question_msg, {"type": "itinerary", "needs_info": True, "missing_info": missing_info}
            
            # 선호도 설정
            preferences = {}
            if kid_friendly:
                preferences["kid_friendly"] = True
            if parking:
                preferences["parking"] = True
            
            # 일정 생성 (비동기) - 이제 (itinerary, routes_data) 튜플 반환
            result = await self.scheduler.create_itinerary(query, preferences)
            
            # 튜플 언패킹
            if isinstance(result, tuple):
                itinerary, routes_data = result
            else:
                itinerary = result
                routes_data = None
            
            if not itinerary:
                error_msg = "일정을 생성할 수 없습니다. 다른 조건으로 시도해주세요."
                return error_msg, {"type": "itinerary", "error": error_msg}
            
            # 요약 생성
            duration = parse_duration(query)
            style = parse_style(query)
            total_places = sum(len(day.places) for day in itinerary)
            
            summary = f"## 📅 {duration} 제주 여행 일정 ({style})\n\n"
            summary += f"- 총 **{len(itinerary)}일** 일정\n"
            summary += f"- 총 **{total_places}곳** 방문 예정\n\n"
            
            # 간단한 일정 요약
            for day in itinerary:
                summary += f"### {day.date_label}\n"
                summary += f"지역: {', '.join(day.regions)}\n"
                for place in day.places:
                    rating = f"⭐{place.rating:.1f}" if place.rating else ""
                    summary += f"- **{place.time_slot}** {place.name} ({place.category}) {rating}\n"
                if day.accommodation:
                    summary += f"- 🏨 숙소: {day.accommodation['name']}\n"
                summary += "\n"
            
            # Artifact 생성
            artifact = self.scheduler.to_json(itinerary)
            
            # 지도용 마커 데이터 추가
            markers = []
            
            for day in itinerary:
                for place in day.places:
                    if place.lat and place.lng:
                        markers.append({
                            "id": place.id,
                            "position": {"lat": place.lat, "lng": place.lng},
                            "label": f"D{day.day}",
                            "name": place.name,
                            "category": place.category,
                            "day": day.day,
                            "time_slot": place.time_slot
                        })
            
            if markers:
                center_lat = sum(m["position"]["lat"] for m in markers) / len(markers)
                center_lng = sum(m["position"]["lng"] for m in markers) / len(markers)
                artifact["map_data"] = {
                    "markers": markers,
                    "center": {"lat": center_lat, "lng": center_lng},
                    "zoom": 10,
                    "routes": routes_data  # scheduler에서 반환한 경로 정보 사용
                }
            
            logger.info(f"✅ 일정 생성 완료: {len(itinerary)}일, {total_places}곳")
            
            return summary, artifact
            
        except Exception as e:
            error_msg = f"일정 생성 중 오류가 발생했습니다: {str(e)}"
            logger.error(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg, {"type": "itinerary", "error": str(e)}
    
    def _check_required_info(self, query: str) -> List[str]:
        """필수 정보 확인
        
        Returns:
            부족한 정보 리스트 (없으면 빈 리스트)
        """
        import re
        missing = []
        
        # 1. 기간 확인 (필수)
        duration_patterns = [
            r'\d+박\s*\d+일',
            r'\d+일',
            r'\d+박',
            r'[일이삼사오육칠팔구십]+박\s*[일이삼사오육칠팔구십]+일',
            r'[일이삼사오육칠팔구십]+일'
        ]
        has_duration = any(re.search(pattern, query) for pattern in duration_patterns)
        
        if not has_duration:
            missing.append("여행 기간 (예: 2박3일, 3박4일)")
        
        return missing
    
    def format_content(self, message: ToolMessage) -> ToolMessage:
        """일정 생성 결과를 LLM에게 전달하기 위한 형식으로 변환"""
        content = message.content or ""
        
        # 추가 정보 필요 케이스
        if message.artifact and message.artifact.get("needs_info"):
            missing_info = message.artifact.get("missing_info", [])
            # Supervisor Agent가 사용자에게 질문하도록 명확히 지시
            instruction = f"""
[중요] 일정 생성에 필요한 정보가 부족합니다.

다음 정보를 사용자에게 친절하고 간결하게 질문하세요:
{chr(10).join(f"- {info}" for info in missing_info)}

⚠️ 주의사항:
- 도구를 다시 호출하지 마세요
- 위 내용을 그대로 복사하지 말고, 자연스러운 한국어로 질문하세요
- 예시를 포함하면 좋습니다 (예: "몇 박 며칠 여행인가요? (예: 2박3일, 3박4일)")

질문 예시:
"네, 일정을 만들어드리겠습니다! 먼저 몇 박 며칠 여행인지 알려주세요 (예: 2박3일, 3박4일)."
"""
            return message.model_copy(update={"content": f"{content}{instruction}"})
        
        # 에러 케이스
        if "오류" in content or "생성할 수 없습니다" in content:
            instruction = "\n\n[중요] 일정 생성에 실패했습니다. 사용자에게 다른 조건을 제안하세요."
            return message.model_copy(update={"content": f"{content}{instruction}"})
        
        # 정상 결과
        instruction = """

## 응답 규칙 (artifact 패턴)

✅ 해야 할 것:
- 일정 요약을 자연스럽게 설명
- "위 일정을 확인해주세요" 로 안내
- 일정의 특징 설명 (지역 이동, 맛집 포인트 등)

❌ 하지 말 것:
- 장소 이름을 하나씩 다시 나열하지 마세요 (이미 위에 있음)
- 새로운 장소를 추가하지 마세요

이유: 상세 일정 데이터는 화면에 별도로 표시됩니다.
"""
        
        return message.model_copy(update={"content": f"{content}{instruction}"})

