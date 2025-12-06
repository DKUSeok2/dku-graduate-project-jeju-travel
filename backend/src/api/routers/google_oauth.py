"""
Google OAuth Authentication
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from authlib.integrations.starlette_client import OAuth
from datetime import datetime

from src.database import get_db_session
from src.models.user import User
from src.auth.jwt import create_access_token
from src.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# OAuth 설정
oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


@router.get("/google/login")
async def google_login(request: Request):
    """
    Google 로그인 시작
    - Google OAuth 페이지로 리다이렉션
    """
    # Railway 프록시 환경에서는 settings에서 직접 redirect_uri 사용
    # request.url_for()는 HTTP로 생성될 수 있음
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Google OAuth 콜백
    - 사용자 정보 받아서 로그인/회원가입 처리
    """
    try:
        # Google로부터 토큰 받기
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="사용자 정보를 가져올 수 없습니다")
        
        # Google 사용자 정보
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        profile_image = user_info.get('picture')
        
        # 기존 사용자 확인
        result = await db.execute(
            select(User).where(
                (User.provider == 'google') & (User.provider_id == google_id)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # 이메일로 기존 사용자 확인 (다른 방법으로 가입한 경우)
            result = await db.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # 이미 다른 방법으로 가입된 이메일
                raise HTTPException(
                    status_code=400,
                    detail=f"이미 {existing_user.provider} 계정으로 가입된 이메일입니다"
                )
            
            # 새 사용자 생성
            user = User(
                email=email,
                name=name,
                provider='google',
                provider_id=google_id,
                profile_image=profile_image,
                is_active=True,
                password_hash=None  # 소셜 로그인은 비밀번호 없음
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # 기존 사용자 정보 업데이트
            user.name = name
            user.profile_image = profile_image
            user.updated_at = datetime.utcnow()
            await db.commit()
        
        # JWT 토큰 발급
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email}
        )
        
        # 프론트엔드로 리다이렉션 (토큰 포함)
        frontend_url = settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={access_token}"
        )
        
    except HTTPException as e:
        # 에러 발생 시 프론트엔드로 리다이렉션 (에러 메시지 포함)
        frontend_url = settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/login?error={e.detail}"
        )
    except Exception as e:
        print(f"Google OAuth 에러: {str(e)}")
        frontend_url = settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/login?error=로그인에 실패했습니다"
        )

