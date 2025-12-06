"""
Admin-related Database Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class LLMUsage(Base):
    """LLM 사용량 추적 모델"""
    __tablename__ = "llm_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # ForeignKey 제거 (다른 Base 사용 문제)
    session_id = Column(String(100))
    model = Column(String(50), nullable=False, index=True)  # 'gpt-4', 'gpt-3.5-turbo' 등
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    cost = Column(DECIMAL(10, 6))  # 예상 비용 (달러)
    endpoint = Column(String(100))  # 어느 API 엔드포인트에서 사용했는지
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<LLMUsage(id={self.id}, model='{self.model}', total_tokens={self.total_tokens})>"


class APILog(Base):
    """API 호출 로그 모델"""
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # ForeignKey 제거
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer)  # 응답 시간 (밀리초)
    error_message = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<APILog(id={self.id}, endpoint='{self.endpoint}', status={self.status_code})>"


