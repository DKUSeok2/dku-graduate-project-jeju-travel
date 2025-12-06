"""
Itinerary Agent Factory
"""
from typing import Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig
import logging

from src.tool_agents.base import BaseToolFactory
from src.tool_agents.itinerary_agent.tool import ItineraryGeneratorTool

logger = logging.getLogger(__name__)


class ItineraryToolFactory(BaseToolFactory):
    """일정 생성 Tool Factory"""
    
    def is_target_tool(self, tool_type: str) -> bool:
        """이 Factory가 처리할 수 있는 Tool 타입인지 확인"""
        return tool_type in ["itinerary", "itinerary_generator", "travel_itinerary"]
    
    async def create_tool(self, config: Dict[str, Any]) -> Optional[BaseTool]:
        """Tool 생성"""
        if not config.get("enabled", True):
            return None
        
        return create_itinerary_tool(config)
    
    async def generate_tool_prompt(self, config: RunnableConfig) -> str:
        """Supervisor용 프롬프트 생성"""
        return TOOL_DESCRIPTION_FOR_SUPERVISOR


def create_itinerary_tool(config: Dict[str, Any] = None) -> Optional[BaseTool]:
    """
    Itinerary Generator Tool 생성
    
    Args:
        config: 설정 (현재 미사용)
    
    Returns:
        ItineraryGeneratorTool 인스턴스
    """
    try:
        logger.info("🗓️ Itinerary Generator Tool 생성 중...")
        tool = ItineraryGeneratorTool()
        logger.info("✅ Itinerary Generator Tool 생성 완료")
        return tool
    except Exception as e:
        logger.error(f"❌ Itinerary Generator Tool 생성 실패: {e}")
        return None


# Supervisor 프롬프트용 도구 설명
TOOL_DESCRIPTION_FOR_SUPERVISOR = """
### generate_travel_itinerary (일정 생성)

**용도**: 제주도 여행 일정 자동 생성

**사용 시점**:
- "2박3일 여행 일정 짜줘"
- "3박4일 가족여행 일정"
- "맛집 중심 2박3일 코스"
- "힐링 여행 일정 추천"

**입력 파라미터**:
- `query`: 일정 요청 (필수)
- `kid_friendly`: 아이 동반 여부 (선택)
- `parking`: 주차 필요 여부 (선택)

**출력**:
- 일별 상세 일정 (시간대별 장소)
- 지역별 동선
- 숙소 추천

**예시**:
```
query: "2박3일 가족여행 일정"
kid_friendly: true
```
"""


def get_supervisor_prompt() -> str:
    """Supervisor 프롬프트용 도구 설명 반환"""
    return TOOL_DESCRIPTION_FOR_SUPERVISOR

