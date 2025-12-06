"""
Web Search Agent Factory (klid-aicb 패턴)
"""
from typing import Any, Dict, Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig

from src.tool_agents.base import BaseToolFactory
from src.tool_agents.web_search_agent.prompts.for_supervisor import SUPERVISOR_PROMPT


class WebSearchToolFactory(BaseToolFactory):
    """Web Search Tool Factory
    
    Tavily API를 사용하여 실시간 웹 검색을 수행하는 Tool을 생성합니다.
    """
    
    def __init__(self):
        self._tool_instance: Optional[BaseTool] = None
    
    def is_target_tool(self, tool_type: str) -> bool:
        """web_search 타입인지 확인"""
        return tool_type == "web_search"
    
    async def create_tool(self, tool_config: Dict[str, Any]) -> Optional[BaseTool]:
        """Web Search Tool 생성
        
        이미 생성된 인스턴스가 있으면 재사용합니다.
        """
        # 이미 생성된 인스턴스가 있으면 재사용
        if self._tool_instance:
            print(f"   ♻️ Reusing existing WebSearchTool")
            return self._tool_instance
        
        try:
            from src.tool_agents.web_search_agent.tool import JejuRealtimeSearchTool
            from src.tool_agents.web_search_agent.searcher import WebSearchSearcher
            from src.config import settings
            from tavily import AsyncTavilyClient
            
            # Tavily 클라이언트 생성
            print(f"   Checking TAVILY_API_KEY: {bool(settings.tavily_api_key)}")
            if not settings.tavily_api_key:
                print(f"   ❌ TAVILY_API_KEY is empty!")
                return None
            
            print(f"   Creating AsyncTavilyClient...")
            tavily_client = AsyncTavilyClient(api_key=settings.tavily_api_key)
            print(f"   ✅ Tavily client created")
            
            print(f"   Creating WebSearchSearcher...")
            searcher = WebSearchSearcher(tavily_client)
            print(f"   ✅ Searcher created")
            
            print(f"   Creating JejuRealtimeSearchTool...")
            tool = JejuRealtimeSearchTool(searcher=searcher)
            print(f"   ✅ Tool created: {tool.name}")
            
            self._tool_instance = tool
            return tool
        
        except Exception as e:
            print(f"   ❌ Error creating web_search tool: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def generate_tool_prompt(self, config: RunnableConfig = None) -> str:
        """Supervisor에게 전달할 Web Search Tool 사용 가이드"""
        return SUPERVISOR_PROMPT




