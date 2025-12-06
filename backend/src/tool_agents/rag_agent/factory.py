"""
RAG Agent Factory (klid-aicb 패턴)
"""
from typing import Any, Dict, Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig

from src.tool_agents.base import BaseToolFactory
from src.tool_agents.rag_agent.prompts.for_supervisor import SUPERVISOR_PROMPT


class RAGSearchToolFactory(BaseToolFactory):
    """RAG Search Tool Factory
    
    자연어 검색(시맨틱 검색)으로 관광지를 찾는 Tool을 생성합니다.
    현재는 키워드 매칭 기반이지만 추후 Elasticsearch로 전환 예정입니다.
    """
    
    def __init__(self):
        self._tool_instance: Optional[BaseTool] = None
    
    def is_target_tool(self, tool_type: str) -> bool:
        """rag_search 타입인지 확인"""
        return tool_type == "rag_search"
    
    async def create_tool(self, tool_config: Dict[str, Any]) -> Optional[BaseTool]:
        """RAG Search Tool 생성
        
        이미 생성된 인스턴스가 있으면 재사용합니다.
        """
        # 이미 생성된 인스턴스가 있으면 재사용
        if self._tool_instance:
            print(f"   ♻️ Reusing existing RAGSearchTool")
            return self._tool_instance
        
        try:
            from src.tool_agents.rag_agent.tool import JejuAttractionSearchTool
            
            print(f"   Creating JejuAttractionSearchTool...")
            tool = JejuAttractionSearchTool()
            print(f"   ✅ Tool created: {tool.name}")
            
            self._tool_instance = tool
            return tool
        
        except Exception as e:
            print(f"   ❌ Error creating rag_search tool: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def generate_tool_prompt(self, config: RunnableConfig = None) -> str:
        """Supervisor에게 전달할 RAG Search Tool 사용 가이드"""
        return SUPERVISOR_PROMPT




