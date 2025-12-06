"""
SQL Agent Tools
SQL 쿼리 실행 도구
"""
from typing import Optional, Type
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, BaseToolkit
from langchain_core.runnables import RunnableConfig
from src.tool_agents.sql_agent.database import CustomSQLDatabase
import logging

logger = logging.getLogger(__name__)


class SQLExecutionToolKit(BaseToolkit):
    """SQL 쿼리를 실행하는 ToolKit"""
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    
    def get_tools(self) -> list[BaseTool]:
        return [QueryExecutionTool()]


class QueryExecutionToolInputArgs(BaseModel):
    """Query Execution Tool 입력 인자"""
    query: str = Field(..., description="실행할 SQL 쿼리 (SELECT만 가능)")


class QueryExecutionTool(BaseTool):
    """SQL 쿼리 실행 도구"""
    
    name: str = "sql_db_query"
    description: str = """
    제주 여행 데이터베이스에 SQL 쿼리를 실행합니다.
    쿼리가 잘못되면 에러 메시지가 반환됩니다.
    에러 발생 시 쿼리를 수정하여 다시 시도하세요.
    """
    args_schema: Type[BaseModel] = QueryExecutionToolInputArgs
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        config: RunnableConfig = None,
    ) -> str:
        """쿼리 실행"""
        try:
            logger.info(f"🔍 SQL 쿼리 실행: {query}")
            
            # Config에서 DB URL 가져오기
            db_url = config["configurable"]["sql_agent"]["db_url"]
            db = CustomSQLDatabase.from_uri(db_url)
            
            # 쿼리 실행
            result = db.run_with_headers(query)
            
            logger.info(f"✅ SQL 쿼리 실행 성공 ({len(result)} chars)")
            return result
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"❌ SQL 쿼리 실행 실패: {error_msg}")
            return error_msg


