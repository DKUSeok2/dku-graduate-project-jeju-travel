"""
SQL Agent State
paip-stack-rag 방식: messages 기반
"""
from typing import Annotated, TypedDict, Optional, List, Dict, Any
from langgraph.graph.message import add_messages


class SQLAgentInputState(TypedDict):
    """SQL Agent의 Input"""
    query: str


class SQLAgentOutputState(TypedDict):
    """SQL Agent의 Output"""
    sql_query: str
    data: str
    attractions: List[Dict[str, Any]]  # 추가: 관광지 데이터 (지도용)


class SQLAgentOverallState(SQLAgentInputState, SQLAgentOutputState):
    """SQL Agent의 전체 상태 (input + output + hidden)"""
    messages: Annotated[list, add_messages]





