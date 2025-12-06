"""
Password Hashing Utilities
"""
from passlib.context import CryptContext

# bcrypt 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    비밀번호 해싱
    
    Args:
        password: 평문 비밀번호
    
    Returns:
        해시된 비밀번호
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
    
    Returns:
        비밀번호 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)




