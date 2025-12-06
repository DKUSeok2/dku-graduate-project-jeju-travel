"""
JWT Token Management
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
from src.config import settings

# config.py의 설정 사용
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expire_minutes


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
    email: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터 (user_id, email 등)
        expires_delta: 만료 시간 (기본: 30일)
    
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    JWT 토큰 검증 및 데이터 추출
    
    Args:
        token: JWT 토큰 문자열
    
    Returns:
        TokenData 또는 None (검증 실패 시)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, email=email)
    
    except JWTError:
        return None




