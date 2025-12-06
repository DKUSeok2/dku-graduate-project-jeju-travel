"""
Web Search Agent Tool - 실시간 정보 검색 (klid-aicb 패턴)
response_format = "content_and_artifact"
"""
from typing import Any, Dict, Optional, Type, Literal, Tuple
import asyncio
import json
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
from tavily.errors import UsageLimitExceededError
import logging

from src.tool_agents.base import BaseAgentTool
from src.tool_agents.web_search_agent.searcher import WebSearchSearcher

logger = logging.getLogger(__name__)


class WebSearchToolInputArgs(BaseModel):
    """웹 검색 입력 파라미터"""
    query: str = Field(
        ...,
        description="검색할 쿼리 (예: '제주 날씨', '성산일출봉 운영시간')"
    )


class JejuRealtimeSearchTool(BaseAgentTool):
    """제주 실시간 정보 검색 도구 (Tavily API)
    
    klid-aicb 패턴: artifact에 검색 결과를 담아 프론트엔드에서 표시
    """
    
    searcher: WebSearchSearcher = Field(exclude=True)
    name: str = "search_realtime_info"
    description: str = """제주도의 실시간 정보를 웹에서 검색합니다. 날씨, 교통, 축제, 운영시간 등 최신 정보를 제공합니다."""
    args_schema: Type[BaseModel] = WebSearchToolInputArgs
    
    # klid-aicb 핵심: artifact 사용
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """동기 실행 (asyncio.run 사용)"""
        return asyncio.run(self._arun(query, run_manager))
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        웹 검색 실행
        
        Returns:
            Tuple[str, dict]: ("", artifact) - klid-aicb 패턴
        """
        try:
            # 제주 관련 쿼리로 보강
            jeju_query = f"제주 {query}" if "제주" not in query else query
            
            logger.info(f"🔍 Tavily 검색 시작: {jeju_query}")
            
            # 실제 검색 수행
            response = await self.searcher.search(jeju_query, config=None)
            
            # 결과 파싱
            results = response.get("results", [])
            answer = response.get("answer", "")
            error = response.get("error")
            
            logger.info(f"✅ Tavily 검색 완료: {len(results)}개 결과")
            
            # 필터링된 결과
            filtered_results = []
            for item in results:
                url = item.get("url", "")
                summary = (item.get("content") or "").strip()
                title = (item.get("title") or "").strip()
                
                if self._is_valid_text(summary):
                    filtered_results.append({
                        "title": title,
                        "url": url,
                        "summary": summary[:500],  # 요약 길이 제한
                        "score": item.get("score", 0)
                    })
            
            # artifact 생성
            artifact = {
                "type": "web_search",
                "query": query,
                "total_results": len(filtered_results),
                "answer": answer,
                "results": filtered_results,
                "error": error
            }
            
            # klid-aicb 핵심: content는 빈 문자열, artifact에 데이터
            return "", artifact
        
        except UsageLimitExceededError as e:
            error_msg = "웹 검색 월간 제한(1000회)을 초과했습니다."
            logger.error(f"❌ {error_msg}")
            artifact = {
                "type": "web_search",
                "query": query,
                "error": error_msg,
                "results": []
            }
            return "", artifact
        
        except Exception as e:
            error_msg = f"웹 검색 중 오류 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            artifact = {
                "type": "web_search",
                "query": query,
                "error": error_msg,
                "results": []
            }
            return "", artifact
    
    def format_content(self, message: ToolMessage) -> ToolMessage:
        """웹 검색 결과를 LLM에게 전달하기 위한 형식으로 변환 (klid-aicb 패턴)"""
        logger.info("🔧 Web Search format_content 호출됨")
        
        # artifact가 없으면 에러
        if message.artifact is None:
            error_content = "웹 검색 중 오류가 발생했습니다."
            instruction = "\n\n[중요] 사용자에게 오류가 발생했음을 알리고, 다른 방법을 제안하세요."
            return message.model_copy(update={"content": f"{error_content}{instruction}"})
        
        artifact = message.artifact
        
        # 에러 케이스
        if artifact.get("error"):
            instruction = "\n\n[중요] 웹 검색에 실패했습니다. 사용자에게 오류를 알리고 다른 방법을 제안하세요."
            return message.model_copy(update={"content": f"{artifact['error']}{instruction}"})
        
        # 결과를 마크다운으로 변환 (LLM 컨텍스트용)
        results = artifact.get("results", [])
        query = artifact.get("query", "")
        answer = artifact.get("answer", "")
        
        markdown = f"## 🌐 '{query}' 웹 검색 결과\n\n"
        
        if answer:
            markdown += f"**요약**: {answer}\n\n"
        
        markdown += f"**{len(results)}개**의 웹 페이지를 찾았습니다:\n\n"
        
        for i, r in enumerate(results[:5], 1):  # 상위 5개
            markdown += f"### {i}. {r['title']}\n"
            markdown += f"- URL: {r['url']}\n"
            markdown += f"- 내용: {r['summary'][:200]}...\n\n"
        
        # 지시사항
        instruction = f"""

## 응답 규칙 (artifact 패턴)

✅ 해야 할 것:
- 검색 결과의 핵심 정보를 요약해서 전달
- 출처(URL)를 언급하여 신뢰성 확보
- 자연스러운 대화체로 답변

❌ 하지 말 것:
- 모든 검색 결과를 나열하지 마세요
- URL 전체를 복사하지 마세요

이유: 검색 결과는 화면에 별도로 표시됩니다."""

        content = f"{markdown}{instruction}"
        
        logger.info(f"   ✅ Web Search format_content 완료 ({len(content)} chars)")
        
        return message.model_copy(update={"content": content})
    
    @staticmethod
    def _is_valid_text(text: str) -> bool:
        """유효한 텍스트인지 확인 (깨진 텍스트 필터링)"""
        if not text or len(text.strip()) < 10:
            return False
        total = len(text)
        meaningful = sum(1 for c in text if c.isalnum() or c.isspace())
        return meaningful / total >= 0.3
