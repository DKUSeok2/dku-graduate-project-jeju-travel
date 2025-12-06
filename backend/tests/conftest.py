"""
Test Configuration
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base


@pytest.fixture
def test_db():
    """테스트용 데이터베이스"""
    # In-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    TestSessionLocal = sessionmaker(bind=engine)
    db = TestSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def mock_llm():
    """Mock LLM"""
    # TODO: Mock LLM implementation
    pass





