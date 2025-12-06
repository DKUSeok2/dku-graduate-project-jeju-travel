"""
Web Search Searcher - Tavily API 래퍼
"""
from typing import Dict
import logging
from langchain_core.runnables import RunnableConfig
from src.tool_agents.web_search_agent.utils import get_search_depth, get_include_domains


logger = logging.getLogger(__name__)


class WebSearchSearcher:
    """Tavily API를 사용한 웹 검색"""

    def __init__(self, tavily_client):
        self.tavily_client = tavily_client

    async def search(self, query: str, config: RunnableConfig = None) -> Dict:
        """
        웹 검색 실행
        
        Args:
            query: 검색 쿼리
            config: 설정 (search_depth, include_domains)
        
        Returns:
            Tavily 검색 결과
        """
        # config에서 동적으로 설정 가져오기
        search_depth = get_search_depth(config)
        include_domains = get_include_domains(config)
        
        logger.info(f"Web search: query='{query}', depth={search_depth}, domains={include_domains}")
        
        try:
            # Tavily 비동기 검색 (도메인 제한 없이 폭넓게)
            response = await self.tavily_client.search(
                query=query, 
                max_results=5,
                # include_domains 제거 - 모든 도메인에서 검색하여 결과 보장
                search_depth=search_depth,
                topic="general",
                include_answer=True,
            )

            if not isinstance(response, dict):
                raise ValueError("Tavily 응답 형식이 dict가 아닙니다")

            return response
        
        except Exception as e:
            logger.error(f"Tavily 검색 실패: {e}", exc_info=True)
            return {
                "results": [],
                "answer": None,
                "error": str(e)
            }

