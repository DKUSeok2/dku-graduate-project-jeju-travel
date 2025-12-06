"""
SQL Agent Nodes
paip-stack-rag 방식: 4개 노드
"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.callbacks import UsageMetadataCallbackHandler
from typing import List, Tuple, Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from src.tool_agents.sql_agent.state import (
    SQLAgentInputState,
    SQLAgentOverallState,
    SQLAgentOutputState
)
from src.tool_agents.sql_agent.prompt import QUERY_GENERATION_PROMPT
from src.tool_agents.sql_agent.database import CustomSQLDatabase
from src.model.model_execution_service import ModelExecutionService
import logging
import json
import re

logger = logging.getLogger(__name__)


class QueryGenerationPromptNode:
    """스키마 정보를 프롬프트에 추가하는 노드"""
    
    def __call__(
        self, 
        state: SQLAgentInputState, 
        config: RunnableConfig = None
    ) -> SQLAgentOverallState:
        logger.info("📝 Query Generation Prompt Node 시작")
        
        # DB 연결 및 스키마 조회
        db_url = config["configurable"]["sql_agent"]["db_url"]
        db = CustomSQLDatabase.from_uri(db_url)
        
        # 사용자 질의
        query = state["query"]
        logger.info(f"   사용자 질의: {query}")
        
        # 사용자 요청에서 숫자 추출 (예: "5개", "10개")
        import re
        num_match = re.search(r'(\d+)\s*개', query)
        requested_limit = int(num_match.group(1)) if num_match else 10
        logger.info(f"   요청 개수: {requested_limit}개")
        
        # 스키마 정보 조회
        table_infos = db.get_table_info()
        logger.info(f"   스키마 정보 조회 완료 ({len(table_infos)} chars)")
        
        # LIMIT 지시를 사용자 메시지에 명시적으로 추가
        user_message = f"{query}\n\n[중요] 이 질의에서 LIMIT {requested_limit}을 사용하세요."
        
        # 시스템 프롬프트 생성 (스키마 포함!)
        messages = [
            SystemMessage(
                QUERY_GENERATION_PROMPT.format(
                    table_infos=table_infos
                )
            ),
            HumanMessage(user_message),
        ]
        
        logger.info("✅ Query Generation Prompt Node 완료")
        return {"messages": messages}


class QueryGenerationAgentNode:
    """LLM이 Tool을 호출하여 SQL 생성하는 노드"""
    
    def __init__(
        self,
        execution_service: ModelExecutionService,
        tools: List[BaseTool],
    ):
        self.execution_service = execution_service
        self.tools = tools
    
    async def __call__(
        self, 
        state: SQLAgentOverallState, 
        config: RunnableConfig = None
    ) -> SQLAgentOverallState:
        logger.info("🤖 Query Generation Agent Node 시작")
        
        # LLM은 execution_service에 이미 있음
        model = self.execution_service.llm
        logger.info(f"   모델 로드 완료: {self.execution_service.model_name}")
        
        # Tool 바인딩
        model_with_tools = model.bind_tools(self.tools)
        logger.info(f"   Tool 바인딩 완료 ({len(self.tools)}개)")
        
        # 🔥 klid-aicb 방식: 콜백으로 토큰 수집
        cb = UsageMetadataCallbackHandler()
        
        # LLM 호출 (콜백 포함)
        message = await model_with_tools.ainvoke(
            state["messages"], 
            config={"callbacks": [cb]}
        )
        logger.info(f"   LLM 응답 수신: {type(message)}")
        
        # 토큰 사용량 로깅 및 저장
        if cb.usage_metadata:
            for usage in cb.usage_metadata.values():
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                logger.info(f"   📊 SQL Agent 토큰: input={input_tokens}, output={output_tokens}")
                
                # DB 저장
                await self._save_token_usage(input_tokens, output_tokens, config)
        
        # Tool Call 확인
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                logger.info(f"   🔧 Tool Call: {tool_call['name']}")
                logger.info(f"      Args: {tool_call['args']}")
        
        logger.info("✅ Query Generation Agent Node 완료")
        return {"messages": [message]}
    
    async def _save_token_usage(
        self, 
        input_tokens: int, 
        output_tokens: int, 
        config: RunnableConfig
    ):
        """토큰 사용량 DB 저장"""
        try:
            from src.services.token_usage_service import TokenUsageService
            from src.database import AsyncSessionLocal
            from src.config import settings
            
            session_id = config.get("configurable", {}).get("thread_id", "unknown")
            
            async with AsyncSessionLocal() as db:
                token_service = TokenUsageService(db)
                await token_service.record_usage(
                    user_id=None,
                    session_id=session_id,
                    model=settings.openai_model,
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    endpoint="sql_agent"
                )
                logger.info(f"   💾 SQL Agent 토큰 저장 완료")
        except Exception as e:
            logger.warning(f"   ⚠️ 토큰 저장 실패: {e}")


class QuerySummaryNode:
    """쿼리 결과를 정리하는 노드"""
    
    def __call__(
        self, 
        state: SQLAgentOverallState, 
        config: RunnableConfig = None
    ) -> SQLAgentOutputState:
        logger.info("📊 Query Summary Node 시작")
        
        # 마지막 SQL 쿼리 추출
        sql_query, tool_call_id = self._get_last_tool_call(state["messages"])
        logger.info(f"   SQL 쿼리: {sql_query[:100]}...")
        
        # 실행 결과 추출
        data = self._get_data_from_tool_call_id(state["messages"], tool_call_id)
        logger.info(f"   결과 데이터: {len(data)} chars")
        
        # 관광지 데이터 추출 (lat, lng가 있으면)
        attractions_data = self._extract_attractions_data(data, sql_query, config)
        
        logger.info("✅ Query Summary Node 완료")
        return {
            "sql_query": sql_query,
            "data": data,
            "attractions": attractions_data,  # 추가!
        }
    
    def _get_last_tool_call(self, messages: List) -> Tuple[str, str]:
        """마지막 Tool Call ID 반환"""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if tool_call["name"] == "sql_db_query":
                        query = tool_call["args"]["query"]
                        tool_call_id = tool_call["id"]
                        return query, tool_call_id
        return "쿼리를 찾을 수 없습니다.", None
    
    def _get_data_from_tool_call_id(self, messages: List, tool_call_id: str) -> str:
        """Tool Call ID에 해당하는 데이터 반환"""
        if tool_call_id is None:
            return "Tool Call ID를 찾을 수 없습니다."
        
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage) and msg.tool_call_id == tool_call_id:
                return msg.content
        return "결과 데이터를 찾을 수 없습니다."
    
    def _extract_attractions_data(
        self, 
        data: str, 
        sql_query: str, 
        config: RunnableConfig
    ) -> List[Dict[str, Any]]:
        """
        DB 결과에서 관광지 데이터 추출 (lat, lng 포함 시)
        프론트엔드 지도 표시용
        """
        # SQL에 lat, lng가 포함되어 있는지 확인
        if 'lat' not in sql_query.lower() or 'lng' not in sql_query.lower():
            return []
        
        try:
            # DB 재쿼리로 구조화된 데이터 가져오기
            db_url = config["configurable"]["sql_agent"]["db_url"]
            db = CustomSQLDatabase.from_uri(db_url)
            
            # SQL 실행
            from sqlalchemy import text
            result_str = db.run_with_headers(sql_query)
            
            # 마크다운 테이블 파싱
            attractions = self._parse_markdown_table(result_str)
            
            logger.info(f"   📍 관광지 데이터 추출: {len(attractions)}개")
            return attractions
            
        except Exception as e:
            logger.error(f"   ❌ 관광지 데이터 추출 실패: {e}")
            return []
    
    def _parse_markdown_table(self, markdown_result: str) -> List[Dict[str, Any]]:
        """마크다운 테이블을 파싱하여 리스트로 변환"""
        attractions = []
        
        try:
            # 테이블 라인 추출
            lines = markdown_result.split('\n')
            header_line = None
            data_lines = []
            
            for i, line in enumerate(lines):
                if '|' in line and not line.strip().startswith('---'):
                    if header_line is None:
                        header_line = line
                    else:
                        data_lines.append(line)
            
            if not header_line or not data_lines:
                return []
            
            # 헤더 파싱
            headers = [h.strip().lower() for h in header_line.split('|')[1:-1]]
            
            # 데이터 파싱
            for line in data_lines:
                cols = [c.strip() for c in line.split('|')[1:-1]]
                if len(cols) == len(headers):
                    row = dict(zip(headers, cols))
                    
                    # lat, lng가 있는 경우만 추가
                    if 'lat' in row and 'lng' in row and row['lat'] and row['lng']:
                        try:
                            attractions.append({
                                'id': int(row.get('id', 0)) if row.get('id') else 0,
                                'name': row.get('name', ''),
                                'category': row.get('category', ''),
                                'lat': float(row['lat']),
                                'lng': float(row['lng']),
                                'avg_rating': float(row.get('avg_rating', 0)) if row.get('avg_rating') else 0,
                                'price_range': row.get('price_range', ''),
                            })
                        except (ValueError, KeyError) as e:
                            logger.warning(f"   ⚠️ 행 파싱 실패: {e}")
                            continue
            
            return attractions
            
        except Exception as e:
            logger.error(f"   ❌ 테이블 파싱 오류: {e}")
            return []

