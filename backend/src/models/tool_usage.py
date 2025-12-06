"""
Tool Usage 모델 - 도구 사용 통계 추적
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from src.database import Base


class ToolUsage(Base):
    """도구 사용 로그"""
    __tablename__ = "tool_usage"

    id = Column(Integer, primary_key=True, index=True)
    tool_name = Column(String(50), nullable=False, index=True)  # sql_agent, rag_agent, web_search, itinerary
    session_id = Column(String(100), nullable=True)  # 세션 ID (선택)
    user_id = Column(Integer, nullable=True)  # 사용자 ID (선택)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ToolUsage(id={self.id}, tool={self.tool_name})>"


