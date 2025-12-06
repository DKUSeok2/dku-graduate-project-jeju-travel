"""
Supervisor Agent State - LangGraph 상태 관리
"""
from typing import List, Dict, Any, Optional, Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages  # 🔥 add_messages reducer!

# MessagesState를 직접 정의 (LangGraph 버전 호환성)
class LangGraphAgentState(TypedDict):
    """
    LangGraph Agent의 상태
    """
    # 메시지 히스토리 (MessagesState의 핵심)
    messages: Annotated[list, add_messages]  # 🔥 add_messages로 자동 병합!
    
    # 사용자 정보
    session_id: Optional[str]
    user_id: Optional[str]
    
    # 대화 컨텍스트
    user_profile: Optional[Dict[str, Any]]  # 사용자 프로필 (가족 구성, 선호도 등)
    conversation_metadata: Optional[Dict[str, Any]]
    
    # 도구 실행 결과
    tool_results: Optional[List[Dict[str, Any]]]
    
    # 최종 응답
    final_response: Optional[str]





