"""
Supervisor Agent Helper
LangGraph 실행을 위한 헬퍼 클래스
"""
from typing import Dict, Optional
from langchain_core.runnables import RunnableConfig
from src.supervisor_agent.prompts import get_prompt_by_bot_id
from src.config import settings


class AgentHelper:
    """LangGraph Agent 실행을 위한 헬퍼 서비스"""
    
    def __init__(self):
        pass
    
    async def get_runnable_config(
        self,
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> RunnableConfig:
        """
        RunnableConfig을 구성합니다.
        
        Args:
            session_id: 세션 ID (thread_id로 사용)
            metadata: 추가 메타데이터 (user_id, bot_id 등)
        
        Returns:
            RunnableConfig
        """
        metadata = metadata or {}
        # 🔥 여러 종류의 챗봇을 지원하기 위한 식별자
        # - itinerary: 기본 제주 여행 일정 플래너 (모든 도구 사용)
        # - sql: SQL 분석 전용
        # - rag: 관광지 RAG 검색 전용
        # - web: 실시간 웹 검색 전용
        bot_id = metadata.get("bot_id", "itinerary")

        # 챗봇 프로필별 활성화할 tool 목록 정의
        # tool_type 값은 각 ToolFactory의 is_target_tool에서 기대하는 타입과 동일해야 한다.
        # 각 전문 챗봇은 해당 도구 하나만 사용
        if bot_id == "sql":
            tool_agents = {
                "sql_query": {"type": "sql_query", "enabled": True},
            }
        elif bot_id == "rag":
            tool_agents = {
                "rag_search": {"type": "rag_search", "enabled": True},
            }
        elif bot_id == "web":
            tool_agents = {
                "web_search": {"type": "web_search", "enabled": True},
            }
        else:
            # 기본값: 여행 일정 플래너
            # itinerary 도구가 내부에서 sql_query, rag_search 도구를 병렬 호출
            tool_agents = {
                "sql_query": {"type": "sql_query", "enabled": True},
                "rag_search": {"type": "rag_search", "enabled": True},
                "itinerary": {"type": "itinerary", "enabled": True},
            }

        # 챗봇별 프롬프트 가져오기
        chatbot_prompt = get_prompt_by_bot_id(bot_id)
        
        config = {
            "configurable": {
                "thread_id": session_id,  # LangGraph가 대화 상태를 관리하는 키
                "metadata": metadata,
                "chatbot_prompt": chatbot_prompt,
                "model_id": "gpt-5-mini",  # 기본 모델
                # 활성화할 도구 설정 (챗봇 프로필별로 다르게 구성)
                "tool_agents": tool_agents,
                # Web Search 설정
                "web_search": {
                    "search_depth": "basic",  # or "advanced"
                    "include_domains": [
                        "visitjeju.net",       # 제주관광공사
                        "jeju.go.kr",          # 제주도청
                        "weather.go.kr",       # 기상청
                        "naver.com",           # 네이버
                        "blog.naver.com",      # 네이버 블로그
                        "daum.net",            # 다음
                        "instagram.com",       # 인스타그램
                        "tripadvisor.co.kr",   # 트립어드바이저
                        "youtube.com",         # 유튜브
                    ]
                },
                # SQL Agent 설정
                "sql_agent": {
                    "db_url": settings.database_url,  # PostgreSQL URL
                }
            },
            # 재귀 제한 증가 (기본 25 → 50)
            "recursion_limit": 50
        }
        
        return config


