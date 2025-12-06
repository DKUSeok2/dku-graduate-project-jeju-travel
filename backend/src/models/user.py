"""
User Database Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from src.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # 소셜 로그인은 비밀번호 없음
    name = Column(String(100), nullable=False)
    is_admin = Column(Boolean, default=False)  # 관리자 권한
    provider = Column(String(20), default="local")  # 'local', 'kakao', 'google'
    provider_id = Column(String(255), nullable=True)
    profile_image = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"



