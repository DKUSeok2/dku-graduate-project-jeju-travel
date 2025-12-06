"""
DM (Direct Message) Router - 1:1 채팅 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from pydantic import BaseModel
from datetime import datetime

from src.auth.dependencies import get_current_user
from src.database import get_db_session
from src.models.user import User
from src.models.conversation import Conversation
from src.models.message import Message

router = APIRouter(prefix="/api/dm", tags=["Direct Messages"])


class ConversationSummary(BaseModel):
    id: int
    partner_id: int
    partner_name: str
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    content: str
    created_at: str


class MessageCreate(BaseModel):
    content: str
    context: Optional[dict] = None  # 어디서 시작했는지 메타 (schedule_id, comment_id 등)


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    내 DM 목록 조회
    """
    uid = current_user.id
    res = await db.execute(
        select(Conversation).where(
            or_(Conversation.user1_id == uid, Conversation.user2_id == uid)
        ).order_by(desc(Conversation.last_message_at))
    )
    convs = res.scalars().all()
    summaries: List[ConversationSummary] = []

    for conv in convs:
        partner_id = conv.user2_id if conv.user1_id == uid else conv.user1_id
        ures = await db.execute(select(User).where(User.id == partner_id))
        partner = ures.scalar_one_or_none()
        if not partner:
            continue

        last_msg = None
        if conv.last_message_id:
            mres = await db.execute(select(Message).where(Message.id == conv.last_message_id))
            m = mres.scalar_one_or_none()
            if m:
                last_msg = m.content[:50] + ("..." if len(m.content) > 50 else "")

        summaries.append(
            ConversationSummary(
                id=conv.id,
                partner_id=partner.id,
                partner_name=partner.name,
                last_message=last_msg,
                last_message_at=(conv.last_message_at.isoformat() + 'Z') if conv.last_message_at else None,
            )
        )
    return summaries


@router.post("/conversations/{target_user_id}", response_model=ConversationSummary)
async def get_or_create_conversation(
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    대상 사용자와의 DM 방 조회 또는 생성
    """
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="자기 자신과는 대화를 시작할 수 없습니다")

    ures = await db.execute(select(User).where(User.id == target_user_id))
    target = ures.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="상대 사용자를 찾을 수 없습니다")

    # user1_id < user2_id로 정규화
    a, b = sorted([current_user.id, target_user_id])
    res = await db.execute(
        select(Conversation).where(
            and_(Conversation.user1_id == a, Conversation.user2_id == b)
        )
    )
    conv = res.scalar_one_or_none()
    
    if not conv:
        conv = Conversation(
            user1_id=a,
            user2_id=b,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    return ConversationSummary(
        id=conv.id,
        partner_id=target.id,
        partner_name=target.name,
        last_message=None,
        last_message_at=(conv.last_message_at.isoformat() + 'Z') if conv.last_message_at else None,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationSummary)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    특정 DM 방 정보 조회
    """
    res = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = res.scalar_one_or_none()
    
    if not conv:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")
    
    if current_user.id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(status_code=403, detail="대화에 접근할 수 없습니다")

    partner_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id
    ures = await db.execute(select(User).where(User.id == partner_id))
    partner = ures.scalar_one_or_none()

    last_msg = None
    if conv.last_message_id:
        mres = await db.execute(select(Message).where(Message.id == conv.last_message_id))
        m = mres.scalar_one_or_none()
        if m:
            last_msg = m.content[:50] + ("..." if len(m.content) > 50 else "")

    return ConversationSummary(
        id=conv.id,
        partner_id=partner.id if partner else 0,
        partner_name=partner.name if partner else "알 수 없음",
        last_message=last_msg,
        last_message_at=(conv.last_message_at.isoformat() + 'Z') if conv.last_message_at else None,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    before: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    DM 방의 메시지 목록 조회 (페이지네이션)
    """
    res = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = res.scalar_one_or_none()
    
    if not conv:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")
    
    if current_user.id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(status_code=403, detail="대화에 접근할 수 없습니다")

    query = select(Message, User).join(User, Message.sender_id == User.id).where(
        Message.conversation_id == conversation_id
    )
    
    if before:
        query = query.where(Message.id < before)
    
    query = query.order_by(desc(Message.created_at)).limit(limit)
    
    mres = await db.execute(query)
    rows = mres.all()
    
    # 최신순으로 가져왔으니 reverse해서 오래된 순으로 반환
    return [
        MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            sender_name=user.name,
            content=msg.content,
            created_at=msg.created_at.isoformat() + 'Z',  # UTC 표시 추가
        )
        for msg, user in reversed(rows)
    ]


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    DM 방에 메시지 전송 (REST API - WebSocket 대안)
    """
    res = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = res.scalar_one_or_none()
    
    if not conv:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")
    
    if current_user.id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(status_code=403, detail="대화에 접근할 수 없습니다")

    if not data.content.strip():
        raise HTTPException(status_code=400, detail="메시지 내용을 입력해주세요")

    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=data.content.strip(),
        context=data.context,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # conversation의 last_message 업데이트
    conv.last_message_id = msg.id
    conv.last_message_at = msg.created_at
    conv.updated_at = datetime.utcnow()
    await db.commit()

    return MessageResponse(
        id=msg.id,
        sender_id=msg.sender_id,
        sender_name=current_user.name,
        content=msg.content,
        created_at=msg.created_at.isoformat() + 'Z',  # UTC 표시 추가
    )

