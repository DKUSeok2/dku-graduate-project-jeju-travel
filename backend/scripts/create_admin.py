"""
관리자 계정 생성 스크립트
Usage: poetry run python scripts/create_admin.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from src.database import AsyncSessionLocal
from src.models.user import User
from src.auth.password import hash_password


async def create_admin_user(email: str, password: str, name: str):
    """관리자 계정 생성"""
    async with AsyncSessionLocal() as session:
        # 이미 존재하는지 확인
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ 이미 존재하는 이메일입니다: {email}")
            return
        
        # 관리자 계정 생성
        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            is_admin=True,
            is_active=True
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print(f"✅ 관리자 계정이 생성되었습니다!")
        print(f"   이메일: {admin_user.email}")
        print(f"   이름: {admin_user.name}")
        print(f"   관리자: {admin_user.is_admin}")


async def main():
    """메인 함수"""
    print("=" * 50)
    print("관리자 계정 생성")
    print("=" * 50)
    
    # 기본 관리자 계정 생성
    admin_email = input("관리자 이메일 (기본: admin@jeju.com): ").strip() or "admin@jeju.com"
    admin_password = input("관리자 비밀번호 (기본: admin123!@#): ").strip() or "admin123!@#"
    admin_name = input("관리자 이름 (기본: 관리자): ").strip() or "관리자"
    
    await create_admin_user(admin_email, admin_password, admin_name)


if __name__ == "__main__":
    asyncio.run(main())

