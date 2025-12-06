"""
Authentication Dependencies for FastAPI
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import verify_token
from src.database import get_db_session
from src.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    현재 로그인한 사용자 가져오기
    
    Args:
        credentials: JWT 토큰
        db: 데이터베이스 세션
    
    Returns:
        User 객체
    
    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증에 실패했습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None or token_data.user_id is None:
        raise credentials_exception
    
    # DB에서 사용자 조회
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    현재 로그인한 사용자 가져오기 (선택적)
    로그인하지 않아도 에러를 발생시키지 않음
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    관리자 권한 확인
    
    Args:
        current_user: 현재 로그인한 사용자
    
    Returns:
        관리자 User 객체
    
    Raises:
        HTTPException: 관리자가 아닐 경우
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    return current_user



