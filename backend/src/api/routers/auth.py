"""
Authentication Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdateProfile, UserUpdatePassword
from src.models import User
from src.auth import hash_password, verify_password, create_access_token, get_current_user
from src.database import get_db_session

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    회원가입
    
    - **email**: 이메일 주소
    - **password**: 비밀번호
    - **name**: 이름
    """
    # 이메일 중복 체크
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )
    
    # 비밀번호 해싱
    hashed_password = hash_password(user_data.password)
    
    # 새 사용자 생성
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        provider="local"
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # JWT 토큰 생성
    access_token = create_access_token(
        data={"user_id": new_user.id, "email": new_user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db_session)
):
    """
    로그인
    
    - **email**: 이메일 주소
    - **password**: 비밀번호
    """
    # 사용자 조회
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    # 비밀번호 검증
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    
    # JWT 토큰 생성
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout():
    """
    로그아웃
    (클라이언트에서 토큰 삭제)
    """
    return {"message": "로그아웃되었습니다"}


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdateProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    프로필 업데이트 (이름 변경)
    
    - **name**: 새 이름
    """
    # 이름 업데이트
    current_user.name = profile_data.name
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.put("/password")
async def update_password(
    password_data: UserUpdatePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    비밀번호 변경
    
    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호
    """
    # 소셜 로그인 사용자는 비밀번호 변경 불가
    if current_user.provider != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="소셜 로그인 사용자는 비밀번호를 변경할 수 없습니다"
        )
    
    # 현재 비밀번호 확인
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다"
        )
    
    # 새 비밀번호 길이 확인
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호는 최소 6자 이상이어야 합니다"
        )
    
    # bcrypt 72바이트 제한 확인
    if len(password_data.new_password) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 72자를 초과할 수 없습니다"
        )
    
    # 비밀번호 해싱 및 업데이트
    current_user.password_hash = hash_password(password_data.new_password)
    
    await db.commit()
    
    return {"message": "비밀번호가 변경되었습니다"}


