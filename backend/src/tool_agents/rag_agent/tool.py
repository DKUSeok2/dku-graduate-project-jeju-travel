"""
RAG Agent Tool - 관광지 정보 검색 (Elasticsearch 벡터 검색)
klid-aicb 패턴 적용: response_format = "content_and_artifact"
"""
from typing import Any, Dict, Optional, Type, Literal, Tuple
import asyncio
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
import logging

from src.tool_agents.base import BaseAgentTool
from src.tool_agents.rag_agent.retriever import get_retriever

logger = logging.getLogger(__name__)


class RAGSearchInputArgs(BaseModel):
    """RAG 검색 입력 파라미터"""
    query: str = Field(
        ...,
        description="검색할 쿼리 (자연어, 예: '일몰이 아름다운 해변', '아이들과 함께 갈 수 있는 체험 시설')"
    )
    limit: int = Field(
        default=5,
        description="반환할 결과 개수 (기본값: 5)"
    )


class JejuAttractionSearchTool(BaseAgentTool):
    """제주 관광지 시맨틱 검색 도구 (Elasticsearch 벡터 검색)
    
    klid-aicb 패턴: artifact에 검색 결과를 담아 프론트엔드에서 표시
    """
    
    name: str = "search_jeju_attractions"
    description: str = """제주도 관광지, 음식점, 숙박시설을 자연어로 검색합니다. 
시맨틱 검색을 통해 사용자의 의도를 파악하여 적합한 장소를 추천합니다.
예: '일몰이 아름다운 해변', '아이와 함께 가기 좋은 카페', '제주 흑돼지 맛집'"""
    args_schema: Type[BaseModel] = RAGSearchInputArgs
    
    # klid-aicb 핵심: artifact 사용
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _run(
        self,
        query: str,
        limit: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """동기 실행"""
        return asyncio.run(self._arun(query, limit, run_manager))
    
    async def _arun(
        self, 
        query: str,
        limit: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        RAG 검색 실행 (Elasticsearch hybrid search)
        
        Returns:
            Tuple[str, dict]: ("", artifact) - klid-aicb 패턴
        """
        logger.info(f"🔍 RAG 검색 시작: {query} (limit={limit})")
        
        try:
            # Elasticsearch 검색
            retriever = get_retriever()
            results, search_type = await retriever.retrieve(
                query=query,
                num_results=limit,
                search_type="vector"
            )
            
            if not results:
                artifact = {
                    "type": "rag_search",
                    "query": query,
                    "error": f"'{query}'에 대한 검색 결과를 찾을 수 없습니다.",
                    "results": []
                }
                return "", artifact
            
            # 검색 결과를 artifact로 변환
            rag_results = []
            for i, result in enumerate(results, 1):
                metadata = result.metadata
                rag_results.append({
                    "id": i,
                    "title": metadata.get("title", "이름 없음"),
                    "category": metadata.get("category", ""),
                    "rating": float(metadata.get("rating", 0)) if metadata.get("rating") else 0,
                    "address": metadata.get("address", ""),
                    "lat": float(metadata.get("lat")) if metadata.get("lat") else None,
                    "lng": float(metadata.get("lng")) if metadata.get("lng") else None,
                    "score": round(result.score, 3),
                    "description": result.document[:300] if result.document else ""
                })
            
            artifact = {
                "type": "rag_search",
                "query": query,
                "search_type": search_type,
                "total_results": len(results),
                "results": rag_results
            }
            
            logger.info(f"✅ RAG 검색 완료: {len(results)}개 결과 ({search_type})")
            
            # klid-aicb 핵심: content는 빈 문자열, artifact에 데이터
            return "", artifact
            
        except Exception as e:
            logger.error(f"❌ RAG 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            artifact = {
                "type": "rag_search",
                "query": query,
                "error": f"검색 중 오류가 발생했습니다: {str(e)}",
                "results": []
            }
            return "", artifact
    
    def format_content(self, message: ToolMessage) -> ToolMessage:
        """RAG 검색 결과를 LLM에게 전달하기 위한 형식으로 변환 (klid-aicb 패턴)"""
        logger.info("🔧 RAG format_content 호출됨")
        
        # artifact가 없으면 에러
        if message.artifact is None:
            error_content = "검색 중 오류가 발생했습니다."
            instruction = "\n\n[중요] 사용자에게 오류가 발생했음을 알리고, 다른 키워드를 제안하세요."
            return message.model_copy(update={"content": f"{error_content}{instruction}"})
        
        artifact = message.artifact
        
        # 에러 케이스
        if artifact.get("error"):
            instruction = "\n\n[중요] 검색 결과가 없거나 오류가 발생했습니다. 사용자에게 다른 키워드를 제안하세요."
            return message.model_copy(update={"content": f"{artifact['error']}{instruction}"})
        
        # 결과를 마크다운으로 변환 (LLM 컨텍스트용)
        results = artifact.get("results", [])
        query = artifact.get("query", "")
        
        markdown = f"## 🔍 '{query}' 검색 결과 ({len(results)}개)\n\n"
        for r in results[:5]:  # LLM에게는 상위 5개만
            markdown += f"**{r['id']}. {r['title']}**\n"
            if r.get('category'):
                markdown += f"- 카테고리: {r['category']}\n"
            if r.get('rating') and r['rating'] > 0:
                markdown += f"- 평점: ⭐ {r['rating']:.1f}\n"
            if r.get('address'):
                markdown += f"- 주소: {r['address']}\n"
            markdown += "\n"
        
        # 지시사항
        instruction = """

## 응답 규칙 (친근하게 요약!)

✅ 해야 할 것:
- 친근한 말투로 대답하세요 (예: "찾았어요!", "좋은 곳이에요~")
- 검색된 정보를 자연스럽게 요약해서 설명
  예: "성산일출봉은 제주 동쪽에 있는 화산 분화구예요! 일출 명소로 유명해요 🌅"
- 방문 팁이나 추천 포인트를 알려주세요
- 이모지를 적절히 사용

❌ 하지 말 것:
- "N개의 검색 결과를 찾았습니다" 같은 딱딱한 시작
- 전체 목록을 번호 매겨서 나열

말투 예시:
- ❌ "검색 결과 5개를 찾았습니다."
- ✅ "성산일출봉 정보 가져왔어요! 🌅 일출 보려면 새벽 5시쯤 가야 해요~"

검색 결과는 아래 UI에 표시되니까, 핵심 정보 위주로 친절하게 설명해주세요!"""

        content = f"{markdown}{instruction}"
        
        logger.info(f"   ✅ RAG format_content 완료 ({len(content)} chars)")
        
        return message.model_copy(update={"content": content})
