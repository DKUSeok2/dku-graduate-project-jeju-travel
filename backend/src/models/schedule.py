"""
Schedule Database Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Date, ForeignKey
from src.database import Base


class Schedule(Base):
    """Schedule model"""
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    attractions = Column(JSON)  # 관광지 리스트 및 순서
    route_data = Column(JSON)   # 최적화된 경로 정보
    memo = Column(Text)
    is_public = Column(Boolean, default=False)
    
    # AI 대화 및 지도 데이터 추가
    chat_history = Column(JSON)  # AI 대화 내역
    ai_reasoning = Column(Text)  # AI 추천 이유/맥락
    map_data = Column(JSON)      # 지도 시각화 데이터 (마커, 경로선 등)
    chat_session_id = Column(String(255), index=True)  # 연결된 채팅 세션 ID
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, user_id={self.user_id}, title='{self.title}')>"

