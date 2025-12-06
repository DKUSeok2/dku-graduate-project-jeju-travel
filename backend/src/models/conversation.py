"""
Conversation model - 1:1 DM 대화방
"""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime

from src.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    last_message_id = Column(Integer, index=True)
    last_message_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Conversation(id={self.id}, user1_id={self.user1_id}, user2_id={self.user2_id})>"



