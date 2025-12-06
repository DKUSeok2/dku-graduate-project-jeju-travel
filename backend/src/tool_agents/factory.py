"""
Dynamic Tool Factory (klid-aicb 패턴)

각 Tool별 Factory를 관리하고 Tool 생성을 위임합니다.
"""
from typing import Dict, List, Optional, Any
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig

from src.tool_agents.base import BaseToolFactory, BaseAgentTool


class DynamicToolFactory:
    """동적 Tool Factory (klid-aicb 패턴)
    
    각 Tool별 Factory를 등록하고 관리합니다.
    Tool 생성과 프롬프트 생성을 각 Factory에 위임합니다.
    """
    
    def __init__(self, tool_factories: List[BaseToolFactory] = None):
        """
        Args:
            tool_factories: Tool Factory 목록 (선택적)
        """
        self._factories: List[BaseToolFactory] = tool_factories or []
        self._tools: Dict[str, BaseAgentTool] = {}
    
    def add_factory(self, factory: BaseToolFactory):
        """Factory 추가"""
        self._factories.append(factory)
    
    def register_tool(self, tool: BaseAgentTool):
        """생성된 Tool 등록 (캐싱용)"""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseAgentTool]:
        """이름으로 Tool 조회"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[BaseAgentTool]:
        """모든 등록된 Tool 조회"""
        return list(self._tools.values())
    
    def get_tool_names(self) -> List[str]:
        """등록된 Tool 이름 목록"""
        return list(self._tools.keys())
    
    async def create_tool(self, tool_config: Dict[str, Any]) -> Optional[BaseTool]:
        """
        Tool 생성 (Factory에 위임)
        
        Args:
            tool_config: Tool 설정 {"type": "web_search", "enabled": True, ...}
        
        Returns:
            생성된 Tool 또는 None
        """
        tool_type = tool_config.get("type")
        
        print(f"🔧 create_tool 호출: type={tool_type}")
        
        # 해당 타입을 처리할 수 있는 Factory 찾기
        for factory in self._factories:
            if factory.is_target_tool(tool_type):
                print(f"   Found factory for type: {tool_type}")
                tool = await factory.create_tool(tool_config)
                if tool:
                    # 생성된 Tool 캐싱
                    self._tools[tool.name] = tool
                return tool
        
        print(f"   ❌ No factory found for tool type: {tool_type}")
        return None
    
    async def generate_tool_prompt(self, config: RunnableConfig) -> str:
        """
        활성화된 Tool들의 프롬프트 생성 (각 Factory에 위임)
        
        Args:
            config: RunnableConfig (tool_agents 설정 포함)
        
        Returns:
            통합된 Tool 프롬프트
        """
        configurable = config.get("configurable", {})
        tool_agents = configurable.get("tool_agents", {})
        
        prompts = []
        
        # 각 활성화된 Tool에 대해 프롬프트 수집
        for tool_type, tool_config in tool_agents.items():
            agent_type = tool_config.get("type", tool_type)
            
            for factory in self._factories:
                if factory.is_target_tool(agent_type):
                    prompt = await factory.generate_tool_prompt(config)
                    if prompt:
                        prompts.append(prompt)
                    break
        
        return "\n\n".join(prompts) if prompts else ""
    
    async def create_tools_for_chatbot(
        self,
        chatbot_id: int,
        enabled_tools: List[str]
    ) -> List[BaseAgentTool]:
        """
        챗봇별 활성화된 Tool 생성
        
        Args:
            chatbot_id: 챗봇 ID
            enabled_tools: 활성화된 Tool 이름 목록
        
        Returns:
            활성화된 Tool 리스트
        """
        tools = []
        for tool_name in enabled_tools:
            tool = self.get_tool(tool_name)
            if tool:
                tools.append(tool)
        
        return tools


def create_default_tool_factory() -> DynamicToolFactory:
    """기본 Tool Factory 생성 (모든 Factory 등록)"""
    from src.tool_agents.web_search_agent.factory import WebSearchToolFactory
    from src.tool_agents.sql_agent.factory import SQLQueryToolFactory
    from src.tool_agents.rag_agent.factory import RAGSearchToolFactory
    from src.tool_agents.route_optimizer_agent.factory import RouteOptimizerToolFactory
    from src.tool_agents.map_visualization_agent.factory import MapVisualizationToolFactory
    from src.tool_agents.itinerary_agent.factory import ItineraryToolFactory
    
    factories = [
        WebSearchToolFactory(),
        SQLQueryToolFactory(),
        RAGSearchToolFactory(),
        RouteOptimizerToolFactory(),
        MapVisualizationToolFactory(),
        ItineraryToolFactory(),  # 일정 생성 도구 추가
    ]
    
    return DynamicToolFactory(tool_factories=factories)
