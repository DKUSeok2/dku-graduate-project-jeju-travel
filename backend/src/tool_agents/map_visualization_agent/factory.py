"""
Map Visualization Agent Factory (klid-aicb 패턴)
"""
from typing import Any, Dict, Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig

from src.tool_agents.base import BaseToolFactory
from src.tool_agents.map_visualization_agent.prompts.for_supervisor import SUPERVISOR_PROMPT


class MapVisualizationToolFactory(BaseToolFactory):
    """Map Visualization Tool Factory
    
    관광지를 지도에 시각화하는 Tool을 생성합니다.
    """
    
    def __init__(self):
        self._tool_instance: Optional[BaseTool] = None
    
    def is_target_tool(self, tool_type: str) -> bool:
        """map_visualization 타입인지 확인"""
        return tool_type == "map_visualization"
    
    async def create_tool(self, tool_config: Dict[str, Any]) -> Optional[BaseTool]:
        """Map Visualization Tool 생성
        
        이미 생성된 인스턴스가 있으면 재사용합니다.
        """
        # 이미 생성된 인스턴스가 있으면 재사용
        if self._tool_instance:
            print(f"   ♻️ Reusing existing MapVisualizationTool")
            return self._tool_instance
        
        try:
            from src.tool_agents.map_visualization_agent.tool import MapVisualizationTool
            
            print(f"   Creating MapVisualizationTool...")
            tool = MapVisualizationTool()
            print(f"   ✅ Tool created: {tool.name}")
            
            self._tool_instance = tool
            return tool
        
        except Exception as e:
            print(f"   ❌ Error creating map_visualization tool: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def generate_tool_prompt(self, config: RunnableConfig = None) -> str:
        """Supervisor에게 전달할 Map Visualization Tool 사용 가이드"""
        return SUPERVISOR_PROMPT




