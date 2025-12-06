"""
Admin API Router
관리자 전용 API 엔드포인트
"""
from datetime import datetime, timedelta, timezone
import httpx
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_admin_user
from src.database import get_db_session
from src.config import settings
from src.models.user import User
from src.models.schedule import Schedule
from src.models.admin import LLMUsage, APILog

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard")
async def get_dashboard(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    관리자 대시보드 통계
    """
    # 전체 사용자 수
    users_count = await db.scalar(select(func.count()).select_from(User))
    
    # 오늘 가입한 사용자
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_users = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )
    
    # 전체 일정 수
    schedules_count = await db.scalar(select(func.count()).select_from(Schedule))
    
    # 오늘 생성된 일정
    today_schedules = await db.scalar(
        select(func.count()).select_from(Schedule).where(Schedule.created_at >= today_start)
    )
    
    # 오늘 LLM 토큰 사용량
    today_tokens = await db.scalar(
        select(func.sum(LLMUsage.total_tokens)).where(LLMUsage.created_at >= today_start)
    ) or 0
    
    # 오늘 LLM 비용
    today_cost = await db.scalar(
        select(func.sum(LLMUsage.cost)).where(LLMUsage.created_at >= today_start)
    ) or 0
    
    # 오늘 API 호출 수
    today_api_calls = await db.scalar(
        select(func.count()).select_from(APILog).where(APILog.created_at >= today_start)
    ) or 0
    
    return {
        "users": {
            "total": users_count,
            "today": today_users
        },
        "schedules": {
            "total": schedules_count,
            "today": today_schedules
        },
        "llm_usage": {
            "today_tokens": int(today_tokens),
            "today_cost": float(today_cost)
        },
        "api_calls": {
            "today": today_api_calls
        }
    }


@router.get("/users")
async def get_users(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    사용자 목록 조회
    """
    result = await db.execute(
        select(User)
        .order_by(desc(User.created_at))
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]
    }


@router.get("/llm-usage")
async def get_llm_usage(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(7, ge=1, le=90),
    user_id: Optional[int] = Query(None)
):
    """
    LLM 사용량 통계 (일별)
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 조건 설정
    conditions = [LLMUsage.created_at >= start_date]
    if user_id:
        conditions.append(LLMUsage.user_id == user_id)
    
    # 일별 토큰 사용량
    result = await db.execute(
        select(
            func.date(LLMUsage.created_at).label('date'),
            func.sum(LLMUsage.prompt_tokens).label('prompt_tokens'),
            func.sum(LLMUsage.completion_tokens).label('completion_tokens'),
            func.sum(LLMUsage.total_tokens).label('total_tokens'),
            func.sum(LLMUsage.cost).label('cost')
        )
        .where(and_(*conditions))
        .group_by(func.date(LLMUsage.created_at))
        .order_by(func.date(LLMUsage.created_at))
    )
    
    daily_usage = [
        {
            "date": str(row.date),
            "prompt_tokens": int(row.prompt_tokens or 0),
            "completion_tokens": int(row.completion_tokens or 0),
            "total_tokens": int(row.total_tokens or 0),
            "cost": float(row.cost or 0)
        }
        for row in result
    ]
    
    # 모델별 사용량
    model_result = await db.execute(
        select(
            LLMUsage.model,
            func.sum(LLMUsage.total_tokens).label('total_tokens'),
            func.sum(LLMUsage.cost).label('cost'),
            func.count().label('count')
        )
        .where(and_(*conditions))
        .group_by(LLMUsage.model)
    )
    
    model_usage = [
        {
            "model": row.model,
            "total_tokens": int(row.total_tokens or 0),
            "cost": float(row.cost or 0),
            "count": row.count
        }
        for row in model_result
    ]
    
    return {
        "daily_usage": daily_usage,
        "model_usage": model_usage
    }


@router.get("/api-logs")
async def get_api_logs(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """
    API 호출 로그 조회
    """
    result = await db.execute(
        select(APILog)
        .order_by(desc(APILog.created_at))
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "endpoint": log.endpoint,
                "method": log.method,
                "status_code": log.status_code,
                "response_time_ms": log.response_time_ms,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    }


@router.get("/system-status")
async def get_system_status(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    시스템 상태 확인
    """
    # DB 연결 테스트
    try:
        await db.execute(select(1))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Elasticsearch 연결 테스트 (Serverless 모드 호환)
    es_status = "disconnected"
    es_error = None
    try:
        es_url = settings.elasticsearch_url
        es_api_key = settings.elasticsearch_api_key
        
        headers = {}
        if es_api_key:
            headers["Authorization"] = f"ApiKey {es_api_key}"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Serverless Elasticsearch는 /_cluster/health를 지원하지 않음
            # 대신 인덱스 존재 여부로 확인
            resp = await client.get(f"{es_url}/jeju_attractions/_count", headers=headers)
            if resp.status_code == 200:
                es_status = "connected"
            else:
                es_error = f"status={resp.status_code}"
    except Exception as e:
        es_error = str(e)
    
    # 한국 시간 (KST = UTC+9)
    kst = timezone(timedelta(hours=9))
    
    result = {
        "database": db_status,
        "elasticsearch": es_status,
        "timestamp": datetime.now(kst).isoformat()
    }
    
    # 디버깅용 정보 추가
    if es_error:
        result["es_error"] = es_error
    result["es_url"] = settings.elasticsearch_url
    
    return result


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    is_admin: bool,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    사용자 권한 변경 (관리자 ↔ 일반)
    """
    # 자기 자신의 권한은 변경 불가
    if user_id == current_admin.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="자신의 권한은 변경할 수 없습니다")
    
    # 사용자 조회
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 권한 변경
    user.is_admin = is_admin
    await db.commit()
    
    return {
        "message": f"사용자 권한이 {'관리자' if is_admin else '일반'}로 변경되었습니다",
        "user_id": user_id,
        "is_admin": is_admin
    }


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    사용자 활성화/비활성화
    """
    # 자기 자신은 비활성화 불가
    if user_id == current_admin.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="자신을 비활성화할 수 없습니다")
    
    # 사용자 조회
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 상태 변경
    user.is_active = is_active
    await db.commit()
    
    return {
        "message": f"사용자가 {'활성화' if is_active else '비활성화'}되었습니다",
        "user_id": user_id,
        "is_active": is_active
    }


# 사용 가능한 모델 목록
AVAILABLE_MODELS = [
    {"id": "gpt-5-mini", "name": "GPT-5 Mini", "description": "최신 경량 모델"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "빠르고 효율적인 모델"},
    {"id": "gpt-4o", "name": "GPT-4o", "description": "고성능 멀티모달 모델"},
]

# 현재 선택된 모델 (런타임 설정)
_current_model = settings.openai_model


@router.get("/settings/model")
async def get_current_model(
    current_admin: User = Depends(get_current_admin_user),
):
    """현재 선택된 LLM 모델 조회"""
    global _current_model
    return {
        "current_model": _current_model,
        "available_models": AVAILABLE_MODELS
    }


@router.put("/settings/model")
async def update_model(
    model_id: str,
    current_admin: User = Depends(get_current_admin_user),
):
    """LLM 모델 변경"""
    global _current_model
    from fastapi import HTTPException
    
    # 유효한 모델인지 확인
    valid_models = [m["id"] for m in AVAILABLE_MODELS]
    if model_id not in valid_models:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 모델입니다. 사용 가능: {valid_models}")
    
    _current_model = model_id
    
    # settings 객체도 업데이트 (런타임)
    settings.openai_model = model_id
    
    return {
        "message": f"모델이 {model_id}로 변경되었습니다",
        "current_model": _current_model
    }


@router.get("/tool-usage")
async def get_tool_usage(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365)
):
    """
    도구 사용 통계 (sql_agent, rag_agent, web_search, itinerary)
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # tool_name별 사용 횟수
    from sqlalchemy import text
    
    result = await db.execute(
        text("""
            SELECT tool_name, COUNT(*) as count
            FROM tool_usage
            WHERE created_at >= :start_date
            GROUP BY tool_name
            ORDER BY count DESC
        """),
        {"start_date": start_date}
    )
    
    rows = result.fetchall()
    
    # 전체 합계 계산
    total = sum(row[1] for row in rows) if rows else 0
    
    # 결과 포맷팅
    tool_stats = []
    for row in rows:
        tool_name, count = row
        percentage = round((count / total) * 100, 1) if total > 0 else 0
        
        # 도구 이름 표시용 매핑
        display_names = {
            "sql_agent": "SQL Agent",
            "rag_agent": "RAG Agent",
            "web_search": "Web Search",
            "itinerary": "Itinerary"
        }
        
        tool_stats.append({
            "name": display_names.get(tool_name, tool_name),
            "value": count,
            "percentage": percentage
        })
    
    # 4개 도구 중 데이터 없는 것도 포함 (0으로)
    existing_names = {stat["name"] for stat in tool_stats}
    for display_name in ["SQL Agent", "RAG Agent", "Web Search", "Itinerary"]:
        if display_name not in existing_names:
            tool_stats.append({
                "name": display_name,
                "value": 0,
                "percentage": 0
            })
    
    # value 기준 내림차순 정렬
    tool_stats.sort(key=lambda x: x["value"], reverse=True)
    
    return {
        "tool_usage": tool_stats,
        "total": total,
        "period_days": days
    }


