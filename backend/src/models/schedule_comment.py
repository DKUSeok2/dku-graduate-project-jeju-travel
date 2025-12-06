"""
ScheduleComment model - 일정 댓글
"""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Boolean

from src.database import Base


class ScheduleComment(Base):
    __tablename__ = "schedule_comments"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(
        Integer,
        ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    parent_id = Column(
        Integer,
        ForeignKey("schedule_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ScheduleComment(id={self.id}, schedule_id={self.schedule_id}, user_id={self.user_id})>"



