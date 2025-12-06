"""
Supervisor Agent Graph - LangGraph 기반 멀티 에이전트 시스템
"""
from typing import Optional, Any
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# AsyncPostgresSaver 임포트
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg_pool import AsyncNullConnectionPool  # 🔥 klid-aicb 방식
    HAS_POSTGRES_SAVER = True
except ImportError:
    AsyncPostgresSaver = Any  # type: ignore
    AsyncNullConnectionPool = Any  # type: ignore
    HAS_POSTGRES_SAVER = False

from src.supervisor_agent.state import LangGraphAgentState
from src.supervisor_agent.nodes import create_agent_node, create_dynamic_tool_node, tools_condition
from src.config import settings

logger = logging.getLogger(__name__)


async def create_langgraph_agent(
    execution_service,
    tool_factory,
    helper=None
):
    """
    LangGraph Agent 생성 (klid-aicb 방식 + PostgreSQL Checkpointer)
    
    Args:
        execution_service: LLM 실행 서비스
        tool_factory: 동적 도구 팩토리
        helper: Agent 헬퍼
    
    Returns:
        컴파일된 LangGraph
    """
    # StateGraph 생성
    graph = StateGraph(LangGraphAgentState)
    
    # 노드 생성 (의존성 주입)
    agent_node_func = create_agent_node(execution_service, tool_factory)
    tool_node_func = create_dynamic_tool_node(tool_factory)
    
    # 노드 추가
    graph.add_node("agent", agent_node_func)
    graph.add_node("tools", tool_node_func)
    
    # 엣지 연결
    graph.set_entry_point("agent")
    
    # 조건부 엣지: Agent → Tools or END
    graph.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END
        }
    )
    
    # Tools → Agent (반복)
    graph.add_edge("tools", "agent")
    
    # Checkpointer 설정 (PostgreSQL 우선, 실패 시 MemorySaver)
    checkpointer = None
    
    print("=" * 80)
    print("🔧 create_langgraph_agent 호출됨!")
    print(f"   HAS_POSTGRES_SAVER: {HAS_POSTGRES_SAVER}")
    print(f"   DATABASE_URL 존재: {bool(settings.database_url)}")
    
    if HAS_POSTGRES_SAVER and settings.database_url:
        try:
            print("🔧 PostgreSQL Checkpointer 설정 시작...")
            logger.info("🔧 PostgreSQL Checkpointer 설정 중...")
            logger.info(f"   DATABASE_URL: {settings.database_url[:50]}...")
            
            # AsyncNullConnectionPool 생성 (klid-aicb 방식)
            pool = AsyncNullConnectionPool(
                conninfo=settings.database_url,
                max_size=5,
                kwargs={
                    "autocommit": True,
                    "prepare_threshold": None,
                },
            )
            
            # 🔥 명시적으로 pool 열기 (klid-aicb 방식)
            print("   Connection Pool 열기...")
            await pool.open(wait=True)
            print("   ✅ Connection Pool 열림")
            logger.info("   ✅ Connection Pool 열림")
            
            # Checkpointer 생성
            checkpointer = AsyncPostgresSaver(pool)
            
            # Checkpointer 테이블 초기화 (매우 중요!)
            print("   Checkpointer 테이블 초기화 중...")
            await checkpointer.setup()
            print("   ✅ Checkpointer 테이블 초기화 완료")
            logger.info("   ✅ Checkpointer 테이블 초기화 완료")
            
            print("✅ PostgreSQL Checkpointer 설정 완료!")
            logger.info("✅ PostgreSQL Checkpointer 설정 완료! 대화 히스토리가 자동 저장됩니다.")
            
        except Exception as e:
            print(f"⚠️ PostgreSQL Checkpointer 설정 실패: {e}")
            logger.error(f"⚠️ PostgreSQL Checkpointer 설정 실패: {e}", exc_info=True)
            logger.warning("ℹ️ MemorySaver로 대체합니다 (서버 재시작 시 대화 기록 손실)")
            checkpointer = MemorySaver()
    else:
        reason = "패키지 미설치" if not HAS_POSTGRES_SAVER else "DATABASE_URL 없음"
        print(f"ℹ️ PostgreSQL Checkpointer 미사용 ({reason}), MemorySaver 사용")
        logger.warning(f"ℹ️ PostgreSQL Checkpointer 미사용 ({reason}), MemorySaver 사용")
        checkpointer = MemorySaver()
    
    # 컴파일 (checkpointer로 대화 상태 저장)
    # recursion_limit 설정 (기본값 50 → 100으로 증가)
    compiled_graph = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=[],  # 중단점 없음
        interrupt_after=[],
    )
    print("✅ LangGraph 컴파일 완료! (recursion_limit: 기본값 사용)")
    print("=" * 80)
    logger.info("✅ LangGraph 컴파일 완료!")
    
    return compiled_graph


# 그래프 구조 (시각화용)
# 
#     START
#       ↓
#    [Agent] ←─────┐
#       ↓           │
#   (조건 분기)     │
#    ↙    ↘        │
# [Tools]  END     │
#    └──────────────┘





