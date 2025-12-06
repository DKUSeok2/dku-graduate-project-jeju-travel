"""
SQL Agent Factory (klid-aicb 패턴)
"""
from typing import Any, Dict, Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig

from src.tool_agents.base import BaseToolFactory
from src.tool_agents.sql_agent.prompts.for_supervisor import SUPERVISOR_PROMPT


class SQLQueryToolFactory(BaseToolFactory):
    """SQL Query Tool Factory
    
    LangGraph 기반 SQL Agent를 사용하여 자연어 질문을 SQL로 변환하고 실행하는 Tool을 생성합니다.
    """
    
    def __init__(self):
        self._tool_instance: Optional[BaseTool] = None
        self._sql_agent = None
    
    def is_target_tool(self, tool_type: str) -> bool:
        """sql_query 타입인지 확인"""
        return tool_type == "sql_query"
    
    async def create_tool(self, tool_config: Dict[str, Any]) -> Optional[BaseTool]:
        """SQL Query Tool 생성
        
        이미 생성된 인스턴스가 있으면 재사용합니다.
        """
        # 이미 생성된 인스턴스가 있으면 재사용
        if self._tool_instance:
            print(f"   ♻️ Reusing existing SQLQueryTool")
            return self._tool_instance
        
        try:
            from src.tool_agents.sql_agent.tool import JejuDataQueryTool
            from src.tool_agents.sql_agent.graph import create_sql_agent
            from src.model.model_execution_service import ModelExecutionService
            
            print(f"   Creating SQL Agent...")
            
            # Model Execution Service 생성
            print(f"   Creating ModelExecutionService...")
            execution_service = ModelExecutionService()
            print(f"   ✅ ModelExecutionService created")
            
            # SQL Agent Graph 생성
            print(f"   Creating SQL Agent Graph...")
            self._sql_agent = create_sql_agent(execution_service)
            print(f"   ✅ SQL Agent Graph created")
            
            # Tool 생성
            print(f"   Creating JejuDataQueryTool...")
            tool = JejuDataQueryTool(sql_agent=self._sql_agent)
            print(f"   ✅ Tool created: {tool.name}")
            
            self._tool_instance = tool
            return tool
        
        except Exception as e:
            print(f"   ❌ Error creating sql_query tool: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def generate_tool_prompt(self, config: RunnableConfig = None) -> str:
        """Supervisor에게 전달할 SQL Query Tool 사용 가이드"""
        return SUPERVISOR_PROMPT




