"""
Password Reset API - 비밀번호 재설정
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import uuid

from src.database import get_db_session
from src.models.user import User
from src.utils.email import email_service
import bcrypt

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    비밀번호 재설정 요청
    - 이메일로 재설정 링크 발송
    """
    # 사용자 찾기
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    # 보안상 이메일이 없어도 성공 메시지 반환 (계정 존재 여부 숨김)
    if not user:
        return {
            "message": "비밀번호 재설정 이메일이 발송되었습니다. 이메일을 확인해주세요."
        }
    
    # 소셜 로그인 사용자는 비밀번호 재설정 불가
    if user.provider != 'local':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{user.provider} 계정은 비밀번호 재설정이 불가능합니다"
        )
    
    # 재설정 토큰 생성
    reset_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    # DB에 토큰 저장
    await db.execute(
        text("""
        INSERT INTO password_reset_tokens (user_id, token, expires_at)
        VALUES (:user_id, :token, :expires_at)
        """),
        {"user_id": user.id, "token": reset_token, "expires_at": expires_at}
    )
    await db.commit()
    
    # 이메일 발송
    success = email_service.send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        user_name=user.name
    )
    
    if not success:
        print(f"⚠️ 이메일 발송 실패: {user.email}")
        # 이메일 발송 실패해도 사용자에게는 성공 메시지 반환
    
    return {
        "message": "비밀번호 재설정 이메일이 발송되었습니다. 이메일을 확인해주세요."
    }


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    비밀번호 재설정
    - 토큰 검증 후 새 비밀번호 설정
    """
    # 토큰 조회
    result = await db.execute(
        text("""
        SELECT * FROM password_reset_tokens
        WHERE token = :token
        """),
        {"token": request.token}
    )
    token_data = result.first()
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 토큰입니다"
        )
    
    # 토큰 만료 확인
    if token_data.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="만료된 토큰입니다. 비밀번호 재설정을 다시 요청해주세요"
        )
    
    # 이미 사용된 토큰 확인
    if token_data.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용된 토큰입니다"
        )
    
    # 사용자 조회
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 비밀번호 유효성 검사
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 최소 6자 이상이어야 합니다"
        )
    
    # 새 비밀번호 해시화
    hashed_password = bcrypt.hashpw(
        request.new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    # 비밀번호 업데이트
    user.password_hash = hashed_password
    user.updated_at = datetime.utcnow()  # DB 스키마에 맞게 timezone 없이
    
    # 토큰 사용 처리
    await db.execute(
        text("""
        UPDATE password_reset_tokens
        SET used = TRUE
        WHERE token = :token
        """),
        {"token": request.token}
    )
    
    await db.commit()
    
    return {
        "message": "비밀번호가 성공적으로 변경되었습니다"
    }


@router.get("/validate-reset-token/{token}")
async def validate_reset_token(
    token: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    토큰 유효성 검증 (프론트엔드에서 토큰 확인용)
    """
    result = await db.execute(
        text("""
        SELECT * FROM password_reset_tokens
        WHERE token = :token
        """),
        {"token": token}
    )
    token_data = result.first()
    
    if not token_data:
        return {"valid": False, "message": "유효하지 않은 토큰입니다"}
    
    if token_data.expires_at < datetime.now(timezone.utc):
        return {"valid": False, "message": "만료된 토큰입니다"}
    
    if token_data.used:
        return {"valid": False, "message": "이미 사용된 토큰입니다"}
    
    return {"valid": True, "message": "유효한 토큰입니다"}

