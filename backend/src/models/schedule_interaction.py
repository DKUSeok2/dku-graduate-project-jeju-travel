"""
Schedule Interaction Models - 좋아요, 북마크, 조회수
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from src.database import Base


class ScheduleLike(Base):
    """일정 좋아요 모델"""
    __tablename__ = "schedule_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 한 사용자가 한 일정에 좋아요 한 번만 가능
    __table_args__ = (
        UniqueConstraint('user_id', 'schedule_id', name='unique_schedule_like'),
    )
    
    def __repr__(self):
        return f"<ScheduleLike(user_id={self.user_id}, schedule_id={self.schedule_id})>"


class ScheduleBookmark(Base):
    """일정 북마크 모델"""
    __tablename__ = "schedule_bookmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 한 사용자가 한 일정을 북마크 한 번만 가능
    __table_args__ = (
        UniqueConstraint('user_id', 'schedule_id', name='unique_schedule_bookmark'),
    )
    
    def __repr__(self):
        return f"<ScheduleBookmark(user_id={self.user_id}, schedule_id={self.schedule_id})>"


class ScheduleView(Base):
    """일정 조회수 모델"""
    __tablename__ = "schedule_views"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)  # 비로그인 사용자는 NULL
    ip_address = Column(String(45))  # IPv6 지원
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScheduleView(schedule_id={self.schedule_id}, user_id={self.user_id})>"

