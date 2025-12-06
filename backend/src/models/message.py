"""
DM Message model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, JSON

from src.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    context = Column(JSON)  # 어떤 일정/댓글에서 시작됐는지 메타

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, sender_id={self.sender_id})>"



