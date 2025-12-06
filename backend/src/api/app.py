"""
FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import secrets

from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"🚀 Starting {settings.app_name}...")
    print(f"📊 Database: {settings.database_url.split('@')[-1]}")
    print(f"🔍 Elasticsearch: {settings.elasticsearch_url}")
    
    # 🔑 카카오 API 키 확인 (디버깅)
    import os
    kakao_from_settings = settings.kakao_api_key
    kakao_from_env = os.getenv("KAKAO_API_KEY")
    print(f"🔑 KAKAO_API_KEY 상태:")
    print(f"   - settings.kakao_api_key: {'있음 (' + kakao_from_settings[:8] + '...)' if kakao_from_settings else 'None'}")
    print(f"   - os.getenv(): {'있음 (' + kakao_from_env[:8] + '...)' if kakao_from_env else 'None'}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="LangGraph 기반 제주도 여행 일정 추천 AI 챗봇",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False  # 307 리다이렉트 비활성화
)

# Session Middleware (Google OAuth에 필요)
# 배포 환경에서는 https_only=True, same_site="none" 설정 필요
import os
is_production = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("FRONTEND_URL", "").startswith("https")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    https_only=is_production,  # 배포 시 HTTPS only
    same_site="none" if is_production else "lax",  # Cross-site 쿠키 허용
)

# CORS 설정 - 환경변수 또는 기본값 사용
cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://jeju-travel-chatbot.vercel.app",
    # Vercel 프리뷰/브랜치 배포 URL 패턴
    "https://jeju-travel-chatbot-git-ai-langgraph-agent-yooseoks-projects.vercel.app",
]
# 빈 문자열 제거
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

# Vercel 프리뷰 URL 패턴 지원을 위한 커스텀 origin 검증
import re
VERCEL_PATTERN = re.compile(r"https://jeju-travel-chatbot.*\.vercel\.app$")

def is_allowed_origin(origin: str) -> bool:
    """Vercel 프리뷰 URL 패턴 매칭"""
    if origin in cors_origins:
        return True
    if VERCEL_PATTERN.match(origin):
        return True
    return False

# allow_origin_regex로 Vercel 모든 프리뷰 URL 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://jeju-travel-chatbot.*\.vercel\.app",  # 모든 Vercel 프리뷰 URL 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: 실제 DB 연결 체크
        "elasticsearch": "connected"  # TODO: 실제 ES 연결 체크
    }


# Import routers
from src.api.routers import (
    auth, stats, admin, schedules, schedule_interactions, 
    chat_sessions, admin_data, password_reset, google_oauth, attractions,
    token_usage, comments, photos, dm, dm_ws, routes
)

app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(admin.router)
app.include_router(schedules.router)
app.include_router(schedule_interactions.router)
app.include_router(chat_sessions.router)
app.include_router(admin_data.router)
app.include_router(password_reset.router)
app.include_router(google_oauth.router)
app.include_router(attractions.router)
app.include_router(token_usage.router)
app.include_router(comments.router)
app.include_router(photos.router)
app.include_router(dm.router)
app.include_router(dm_ws.router)
app.include_router(routes.router)  # 경로 계산 API

# 정적 파일 서빙 (사진 업로드용)
from fastapi.staticfiles import StaticFiles
import os
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
# app.include_router(attractions.router, prefix="/api/attractions", tags=["Attractions"])
# app.include_router(route.router, prefix="/api/route", tags=["Route"])





