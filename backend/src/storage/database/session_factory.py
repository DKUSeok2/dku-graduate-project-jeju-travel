"""
Database Storage Settings
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from src.config import settings

# SQLAlchemy Base
Base = declarative_base()

# Database Engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_database():
    """데이터베이스 초기화"""
    from src.database import Base
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")





