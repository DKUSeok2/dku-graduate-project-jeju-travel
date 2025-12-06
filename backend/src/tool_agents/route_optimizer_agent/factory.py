"""
Route Optimizer Agent Factory (klid-aicb 패턴)
"""
from typing import Any, Dict, Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig

from src.tool_agents.base import BaseToolFactory
from src.tool_agents.route_optimizer_agent.prompts.for_supervisor import SUPERVISOR_PROMPT


class RouteOptimizerToolFactory(BaseToolFactory):
    """Route Optimizer Tool Factory
    
    TSP 알고리즘을 사용하여 최적 경로를 계산하는 Tool을 생성합니다.
    """
    
    def __init__(self):
        self._tool_instance: Optional[BaseTool] = None
    
    def is_target_tool(self, tool_type: str) -> bool:
        """route_optimizer 타입인지 확인"""
        return tool_type == "route_optimizer"
    
    async def create_tool(self, tool_config: Dict[str, Any]) -> Optional[BaseTool]:
        """Route Optimizer Tool 생성
        
        이미 생성된 인스턴스가 있으면 재사용합니다.
        """
        # 이미 생성된 인스턴스가 있으면 재사용
        if self._tool_instance:
            print(f"   ♻️ Reusing existing RouteOptimizerTool")
            return self._tool_instance
        
        try:
            from src.tool_agents.route_optimizer_agent.tool import RouteOptimizerTool
            
            print(f"   Creating RouteOptimizerTool...")
            tool = RouteOptimizerTool()
            print(f"   ✅ Tool created: {tool.name}")
            
            self._tool_instance = tool
            return tool
        
        except Exception as e:
            print(f"   ❌ Error creating route_optimizer tool: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def generate_tool_prompt(self, config: RunnableConfig = None) -> str:
        """Supervisor에게 전달할 Route Optimizer Tool 사용 가이드"""
        return SUPERVISOR_PROMPT




