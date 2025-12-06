"""
SQL Agent Graph - LangGraph 기반 SQL 에이전트
paip-stack-rag 방식
"""
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import ToolMessage
import logging

from src.tool_agents.sql_agent.state import SQLAgentOverallState
from src.tool_agents.sql_agent.nodes import (
    QueryGenerationPromptNode,
    QueryGenerationAgentNode,
    QuerySummaryNode,
)
from src.tool_agents.sql_agent.tools import SQLExecutionToolKit
from src.model.model_execution_service import ModelExecutionService

logger = logging.getLogger(__name__)


def create_sql_agent(
    execution_service: ModelExecutionService,
) -> CompiledStateGraph:
    """SQL Agent 생성 (paip-stack-rag 방식)
    
    실행 흐름:
        query_generation_prompt → query_generation_agent → tools
        → (에러 체크) → query_summarization → END
    
    Args:
        execution_service: 모델 실행 서비스
    
    Returns:
        컴파일된 LangGraph Agent
    """
    logger.info("🔧 SQL Agent 생성 시작")
    
    # 노드 초기화
    prompt_node = QueryGenerationPromptNode()
    summary_node = QuerySummaryNode()
    
    toolkit = SQLExecutionToolKit()
    tools = toolkit.get_tools()
    logger.info(f"   Tools 초기화: {[t.name for t in tools]}")
    
    agent_node = QueryGenerationAgentNode(
        execution_service=execution_service,
        tools=tools
    )
    
    # Graph 정의
    graph = StateGraph(SQLAgentOverallState)
    
    # 노드 추가
    graph.add_node("query_generation_prompt", prompt_node)
    graph.add_node("query_generation_agent", agent_node)
    graph.add_node("tools", ToolNode(tools))  # LangGraph 내장 ToolNode!
    graph.add_node("query_summarization", summary_node)
    
    logger.info("   노드 추가 완료: prompt, agent, tools, summarization")
    
    # 에러 재시도 로직
    def retry_if_error_exists(
        state: SQLAgentOverallState,
    ) -> Literal["query_generation_agent", "query_summarization"]:
        """에러가 있으면 Agent로 다시, 없으면 요약으로"""
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage) and msg.content.startswith("Error"):
                logger.warning("   ⚠️ SQL 에러 감지, 재시도...")
                return "query_generation_agent"  # Retry!
        logger.info("   ✅ SQL 실행 성공, 요약 단계로")
        return "query_summarization"
    
    # 엣지 연결
    graph.add_edge(START, "query_generation_prompt")
    graph.add_edge("query_generation_prompt", "query_generation_agent")
    graph.add_edge("query_generation_agent", "tools")
    graph.add_conditional_edges("tools", retry_if_error_exists)  # 자동 재시도!
    graph.add_edge("query_summarization", END)
    
    logger.info("   엣지 연결 완료")
    logger.info("✅ SQL Agent 생성 완료!")
    
    return graph.compile()





