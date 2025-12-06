"""
Database Configuration and Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ARRAY, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.config import settings

# Base 선언
Base = declarative_base()


# ==================== Models ====================

class Attraction(Base):
    """관광지 테이블"""
    __tablename__ = "attractions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    avg_rating = Column(Float)
    price_range = Column(String(20))
    kid_friendly = Column(Boolean, default=False)
    estimated_time = Column(Integer)
    operating_hours = Column(JSON)
    tags = Column(ARRAY(String))
    address = Column(Text)
    phone = Column(String(20))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Accommodation(Base):
    """숙박 시설 테이블"""
    __tablename__ = "accommodations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    type = Column(String(50))
    area = Column(String(50), index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    price_per_night = Column(Integer)
    rating = Column(Float)
    amenities = Column(JSON)
    address = Column(Text)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Restaurant(Base):
    """음식점 테이블"""
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    cuisine = Column(String(50), index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    avg_price = Column(Integer)
    rating = Column(Float)
    address = Column(Text)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatSession(Base):
    """채팅 세션 테이블"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # ForeignKey 추가는 나중에
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255))
    messages = Column(JSON, nullable=False, default=list)  # 메시지 리스트
    context = Column(JSON)  # 컨텍스트 (선택한 관광지 등)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    """채팅 메시지 테이블"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON)  # metadata는 SQLAlchemy 예약어
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Async Database Engine ====================

# postgresql:// → postgresql+asyncpg://
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    async_database_url,
    echo=False,  # 프로덕션에서는 False 권장
    pool_size=10,  # 기본 연결 풀 크기 (기본값 5에서 증가)
    max_overflow=20,  # 최대 추가 연결 수 (기본값 10에서 증가)
    pool_timeout=30,  # 연결 대기 타임아웃 (초)
    pool_recycle=1800,  # 연결 재활용 시간 (30분)
    pool_pre_ping=True,  # 연결 상태 확인
)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session():
    """Async database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


