"""
Base Tool Agent & Tool Factory (klid-aicb 패턴)
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig


class BaseAgentTool(BaseTool):
    """Base class for all agent tools (klid-aicb 패턴)
    
    모든 Tool은 이 클래스를 상속받아야 합니다.
    format_content 메서드를 override하여 Tool 결과를 LLM에게 전달하기 전에 포맷팅합니다.
    """
    
    def format_content(self, message: ToolMessage) -> ToolMessage:
        """메시지의 내용을 LLM에게 전달하기 위한 형식으로 변환
        
        각 Tool이 override해서:
        1. 결과를 마크다운으로 포맷팅
        2. 다음 단계 지시사항 추가 (예: [중요] 이 결과를 바탕으로...)
        
        Args:
            message: Tool 실행 결과가 담긴 ToolMessage
            
        Returns:
            포맷팅된 ToolMessage
        """
        return message


class BaseToolFactory(ABC):
    """Tool Factory 기본 클래스 (klid-aicb 패턴)
    
    각 Tool 타입별로 Factory를 구현합니다.
    - is_target_tool: 해당 tool_type을 처리할 수 있는지
    - create_tool: Tool 인스턴스 생성
    - generate_tool_prompt: Supervisor에게 전달할 Tool 사용 가이드
    """
    
    @abstractmethod
    def is_target_tool(self, tool_type: str) -> bool:
        """해당 tool_type을 처리할 수 있는지 확인
        
        Args:
            tool_type: Tool 타입 문자열 (예: "web_search", "sql_query")
            
        Returns:
            처리 가능 여부
        """
        pass
    
    @abstractmethod
    async def create_tool(self, tool_config: Dict[str, Any]) -> Optional[BaseTool]:
        """Tool 인스턴스 생성
        
        Args:
            tool_config: Tool 설정 {"type": "web_search", "enabled": True, ...}
            
        Returns:
            생성된 Tool 또는 None (생성 실패 시)
        """
        pass
    
    async def generate_tool_prompt(self, config: RunnableConfig = None) -> str:
        """Supervisor에게 전달할 Tool 사용 가이드
        
        각 Factory가 자체 프롬프트를 반환합니다.
        프롬프트에는 다음 내용이 포함되어야 합니다:
        - Tool 설명
        - 사용 시점 (언제 이 Tool을 사용해야 하는지)
        - 올바른 예시 (✅)
        - 잘못된 예시 (❌)
        - 주의사항
        
        Args:
            config: RunnableConfig (선택적)
            
        Returns:
            Tool 사용 가이드 프롬프트 문자열
        """
        return ""
