#!/usr/bin/env python
"""
Database Initialization Script
데이터베이스 테이블 생성 및 샘플 데이터 삽입
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db, engine
from src.config import settings


def main():
    """데이터베이스 초기화"""
    print(f"🔧 Initializing database: {settings.database_url.split('@')[-1]}")
    
    try:
        # 테이블 생성
        init_db()
        print("✅ Database initialized successfully")
        
        # 연결 테스트
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            version = result.fetchone()[0]
            print(f"📊 PostgreSQL version: {version}")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()





