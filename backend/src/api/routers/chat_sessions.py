"""
Chat Sessions Router - 채팅 세션 관리 API
"""
import uuid
import json
import asyncio
from typing import List, Optional, AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel

from src.auth.dependencies import get_current_user
from src.database import get_db_session, ChatSession
from src.models.user import User
from src.model.model_execution_service import ModelExecutionService
from src.supervisor_agent.service import SupervisorAgentService
from src.tool_agents.factory import create_default_tool_factory


router = APIRouter(prefix="/api/chat", tags=["Chat Sessions"])

# 전역 Supervisor Agent Service 인스턴스 (싱글톤)
_supervisor_service: Optional[SupervisorAgentService] = None
_supervisor_initialized: bool = False


async def get_supervisor_service() -> SupervisorAgentService:
    """Supervisor Agent Service 싱글톤 인스턴스 반환 (비동기)"""
    global _supervisor_service, _supervisor_initialized
    
    if _supervisor_service is None:
        print("🚀 SupervisorAgentService 최초 생성 중...")
        
        # ModelExecutionService 초기화
        execution_service = ModelExecutionService()
        
        # ToolFactory 초기화 (klid-aicb 패턴 - 모든 Factory 등록)
        tool_factory = create_default_tool_factory()
        print(f"   ✅ ToolFactory 생성 완료: {len(tool_factory._factories)}개 Factory 등록")
        
        # SupervisorAgentService 생성 (PostgreSQL Checkpointer는 내부에서 자동 설정)
        _supervisor_service = SupervisorAgentService(
            execution_service=execution_service,
            tool_factory=tool_factory
        )
    
    # 🔥 초기화는 한 번만 실행 (create_langgraph_agent 호출)
    if not _supervisor_initialized:
        print("🚀 SupervisorAgentService 초기화 시작...")
        await _supervisor_service.initialize()
        _supervisor_initialized = True
        print("✅ SupervisorAgentService 초기화 완료!")
    
    return _supervisor_service


# ===== Pydantic Schemas =====

class MessageSchema(BaseModel):
    """메시지 스키마"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[str] = None
    attractions: Optional[list] = None


class ChatSessionCreate(BaseModel):
    """채팅 세션 생성 요청"""
    title: Optional[str] = None
    context: Optional[dict] = None


class ChatSessionResponse(BaseModel):
    """채팅 세션 응답"""
    id: int
    session_id: str
    user_id: int
    title: Optional[str]
    messages: List[dict]
    context: Optional[dict]
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_session(cls, session: ChatSession):
        """ChatSession 객체에서 Response 생성"""
        return cls(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            messages=session.messages or [],
            context=session.context,
            is_active=session.is_active,
            created_at=session.created_at.isoformat() if hasattr(session.created_at, 'isoformat') else str(session.created_at),
            updated_at=session.updated_at.isoformat() if hasattr(session.updated_at, 'isoformat') else str(session.updated_at)
        )


class ChatSessionListItem(BaseModel):
    """채팅 세션 목록 아이템 (간략 정보)"""
    id: int
    session_id: str
    title: Optional[str]
    message_count: int
    last_message_preview: Optional[str]
    created_at: str
    updated_at: str


class AddMessageRequest(BaseModel):
    """메시지 추가 요청"""
    message: MessageSchema


class UpdateSessionRequest(BaseModel):
    """세션 업데이트 요청"""
    title: Optional[str] = None
    is_active: Optional[bool] = None


class StreamChatRequest(BaseModel):
    """스트리밍 채팅 요청"""
    message: str
    # 🔥 여러 종류의 챗봇(여행일정, SQL, RAG, WebSearch 등)을 지원하기 위한 식별자
    # - 예: "itinerary", "sql", "rag", "web"
    # - 지정되지 않으면 기본값은 "itinerary"
    bot_id: Optional[str] = "itinerary"


class FeedbackRequest(BaseModel):
    """피드백 요청"""
    message_id: str
    is_like: bool  # true: 좋아요, false: 싫어요


# ===== API Endpoints =====

@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    새 채팅 세션 생성
    """
    session_id = str(uuid.uuid4())
    
    new_session = ChatSession(
        user_id=current_user.id,
        session_id=session_id,
        title=data.title or "새로운 대화",
        messages=[],
        context=data.context or {},
        is_active=True
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return ChatSessionResponse.from_session(new_session)


@router.get("/sessions", response_model=List[ChatSessionListItem])
async def get_user_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    내 채팅 세션 목록 조회 (최근순)
    """
    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.user_id == current_user.id,
            ChatSession.is_active == True
        )
        .order_by(desc(ChatSession.updated_at))
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    # 간략 정보로 변환
    session_list = []
    for session in sessions:
        messages = session.messages or []
        message_count = len(messages)
        
        # 마지막 메시지 미리보기 (사용자 메시지 우선)
        last_message_preview = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_message_preview = msg.get('content', '')[:50]
                if len(msg.get('content', '')) > 50:
                    last_message_preview += '...'
                break
        
        if not last_message_preview and messages:
            last_message_preview = messages[-1].get('content', '')[:50]
        
        session_list.append(
            ChatSessionListItem(
                id=session.id,
                session_id=session.session_id,
                title=session.title or "새로운 대화",
                message_count=message_count,
                last_message_preview=last_message_preview,
                created_at=session.created_at.isoformat() if hasattr(session.created_at, 'isoformat') else str(session.created_at),
                updated_at=session.updated_at.isoformat() if hasattr(session.updated_at, 'isoformat') else str(session.updated_at)
            )
        )
    
    return session_list


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    특정 채팅 세션 조회
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )
    
    return ChatSessionResponse.from_session(session)


@router.post("/sessions/{session_id}/messages", status_code=status.HTTP_201_CREATED)
async def add_message(
    session_id: str,
    data: AddMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    세션에 메시지 추가
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )
    
    # 메시지 추가
    messages = list(session.messages or [])  # 새 리스트로 복사
    message_dict = data.message.dict()
    if not message_dict.get('timestamp'):
        message_dict['timestamp'] = datetime.utcnow().isoformat()
    
    messages.append(message_dict)
    session.messages = messages
    flag_modified(session, 'messages')  # SQLAlchemy에 변경 알림
    
    # 제목이 없으면 첫 사용자 메시지로 자동 생성
    if not session.title or session.title == "새로운 대화":
        if message_dict.get('role') == 'user':
            content = message_dict.get('content', '')
            session.title = content[:30] + ('...' if len(content) > 30 else '')
    
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    return {"success": True, "message_count": len(messages)}


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: str,
    data: UpdateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    세션 정보 업데이트 (제목, 활성 상태)
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )
    
    if data.title is not None:
        session.title = data.title
    if data.is_active is not None:
        session.is_active = data.is_active
    
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    return ChatSessionResponse.from_session(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    세션 삭제 (실제로는 is_active를 False로 설정)
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )
    
    # Soft delete
    session.is_active = False
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return None


@router.get("/sessions/{session_id}/context")
async def get_session_context(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    세션의 컨텍스트 조회 (선택한 관광지 등)
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )
    
    return session.context or {}


@router.put("/sessions/{session_id}/context")
async def update_session_context(
    session_id: str,
    context: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    세션의 컨텍스트 업데이트
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )
    
    session.context = context
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"success": True, "context": context}


async def generate_chat_stream(
    message: str,
    session_id: str,
    db: AsyncSession,
    user_id: int,
    bot_id: str = "itinerary",
) -> AsyncGenerator[str, None]:
    """
    채팅 스트림 생성 (실제 Supervisor Agent와 연동)
    """
    # OpenAI API 키 확인
    from src.config import settings
    if not settings.openai_api_key:
        error_chunk = {
            "type": "error",
            "content": "OpenAI API 키가 설정되지 않았습니다. 환경 변수 OPENAI_API_KEY를 설정해주세요.",
            "id": "error"
        }
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        return
    
    # 사용자 메시지를 세션에 저장
    print(f"📝 사용자 메시지 저장 시작: session_id={session_id}")
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    print(f"📝 세션 조회 결과: {session is not None}")
    
    if session:
        messages = list(session.messages or [])  # 새 리스트로 복사
        messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        session.messages = messages
        flag_modified(session, 'messages')  # SQLAlchemy에 변경 알림
        await db.commit()
        print(f"✅ 사용자 메시지 저장 완료: 총 {len(messages)}개")
    
    # Supervisor Agent Service 가져오기
    try:
        supervisor_service = await get_supervisor_service()
    except Exception as e:
        # Supervisor Service 초기화 실패 시
        error_chunk = {
            "type": "error",
            "content": f"AI 서비스 초기화 실패: {str(e)}",
            "id": "error"
        }
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        return
    
    try:
        # 스트리밍 채팅 실행
        full_response = ""
        async for chunk in supervisor_service.stream_chat(
            message=message,
            session_id=session_id,
            # user_profile에 bot_id를 포함시켜 Supervisor가 챗봇 유형별로
            # 사용할 도구 세트나 프롬프트를 다르게 구성할 수 있도록 한다.
            user_profile={"user_id": user_id, "bot_id": bot_id}
        ):
            if chunk:
                full_response += chunk
                # SSE 형식으로 전송
                chunk_data = {
                    "type": "AIMessageChunk",
                    "content": chunk,
                    "id": f"chunk_{len(full_response)}"
                }
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
        
        # AI 응답을 세션에 저장
        print(f"🤖 AI 응답 저장 시작: session_id={session_id}, response_len={len(full_response)}")
        if session and full_response:
            try:
                # 세션을 다시 조회 (스트리밍 중 세션이 변경됐을 수 있음)
                result = await db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                session = result.scalar_one_or_none()
                if session:
                    messages = list(session.messages or [])  # 새 리스트로 복사
                    
                    # 태그 제거 - 하지만 ITINERARY_DATA와 SQL_QUERY_RESULT는 유지 (프론트엔드에서 파싱 필요)
                    import re
                    clean_response = full_response
                    # [THINKING] 태그 제거 (표시용 태그)
                    clean_response = re.sub(r'\[THINKING\][\s\S]*?\[/THINKING\]', '', clean_response)
                    # 메타데이터 태그들 제거 (ITINERARY_DATA, SQL_QUERY_RESULT는 제외 - 프론트엔드에서 파싱 필요)
                    clean_response = re.sub(r'\[WEB_SEARCH_RESULT\][\s\S]*?\[/WEB_SEARCH_RESULT\]', '', clean_response)
                    # [SQL_QUERY_RESULT]는 유지! (프론트엔드에서 파싱해서 표시함)
                    # clean_response = re.sub(r'\[SQL_QUERY_RESULT\][\s\S]*?\[/SQL_QUERY_RESULT\]', '', clean_response)
                    clean_response = re.sub(r'\[MAP_DATA\][\s\S]*?\[/MAP_DATA\]', '', clean_response)
                    clean_response = re.sub(r'\[ATTRACTIONS_DATA\][\s\S]*?\[/ATTRACTIONS_DATA\]', '', clean_response)
                    # [ITINERARY_DATA]는 유지! (프론트엔드에서 파싱해서 표시함)
                    clean_response = clean_response.strip()
                    
                    messages.append({
                        "role": "assistant",
                        "content": clean_response,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    session.messages = messages
                    flag_modified(session, 'messages')  # SQLAlchemy에 변경 알림
                    session.updated_at = datetime.utcnow()
                    await db.commit()
                    print(f"✅ AI 응답 저장 완료: 총 {len(messages)}개 (태그 제거됨)")
                else:
                    print(f"❌ 세션을 찾을 수 없음: {session_id}")
            except Exception as e:
                print(f"❌ AI 응답 저장 실패: {e}")
        else:
            print(f"⚠️ 저장 스킵: session={session is not None}, response_len={len(full_response) if full_response else 0}")
        
        # 완료 신호
        done_chunk = {
            "type": "done",
            "content": "",
            "id": "done"
        }
        yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        # 에러 발생 시
        error_chunk = {
            "type": "error",
            "content": f"오류가 발생했습니다: {str(e)}",
            "id": "error"
        }
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"


@router.post("/sessions/{session_id}/stream")
async def stream_chat(
    session_id: str,
    data: StreamChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    실시간 스트리밍 채팅 (SSE)
    """
    # 세션 확인
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )

    # bot_id는 어떤 종류의 챗봇을 사용할지 식별하는 값이다.
    # 별도 값이 없으면 기본값("itinerary")을 사용한다.
    bot_id = data.bot_id or "itinerary"

    return StreamingResponse(
        generate_chat_stream(data.message, session_id, db, current_user.id, bot_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/sessions/{session_id}/feedback", status_code=status.HTTP_201_CREATED)
async def save_feedback(
    session_id: str,
    data: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    AI 응답에 대한 피드백 저장 (좋아요/싫어요)
    """
    # 세션 확인
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )
    
    # 피드백 저장 (UPSERT)
    from sqlalchemy import text
    
    await db.execute(
        text("""
            INSERT INTO chat_feedbacks (session_id, message_id, user_id, is_like)
            VALUES (:session_id, :message_id, :user_id, :is_like)
            ON CONFLICT (session_id, message_id, user_id)
            DO UPDATE SET is_like = :is_like, created_at = CURRENT_TIMESTAMP
        """),
        {
            "session_id": session_id,
            "message_id": data.message_id,
            "user_id": current_user.id,
            "is_like": data.is_like
        }
    )
    
    await db.commit()
    
    return {
        "success": True,
        "message": "피드백이 저장되었습니다",
        "is_like": data.is_like
    }

