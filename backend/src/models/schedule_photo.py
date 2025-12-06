"""
SchedulePhoto model - 일정 사진
"""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text

from src.database import Base


class SchedulePhoto(Base):
    __tablename__ = "schedule_photos"

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
    url = Column(Text, nullable=False)
    caption = Column(Text)
    day = Column(Integer)
    order_in_day = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SchedulePhoto(id={self.id}, schedule_id={self.schedule_id}, user_id={self.user_id})>"



