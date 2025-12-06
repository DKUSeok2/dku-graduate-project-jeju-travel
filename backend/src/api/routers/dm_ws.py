"""
DM WebSocket Router - 실시간 1:1 채팅
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json
from typing import Dict, Set

from src.database import get_db_session
from src.models.user import User
from src.models.conversation import Conversation
from src.models.message import Message
from src.auth.jwt import verify_token

router = APIRouter()

# 활성 연결 관리: {conversation_id: {websocket1, websocket2, ...}}
active_connections: Dict[int, Set[WebSocket]] = {}


async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """JWT 토큰에서 사용자 정보 추출"""
    try:
        token_data = verify_token(token)
        if not token_data or not token_data.user_id:
            return None

        result = await db.execute(select(User).where(User.id == int(token_data.user_id)))
        return result.scalar_one_or_none()
    except Exception as e:
        print(f"Token validation error: {e}")
        return None


async def connect_ws(conv_id: int, ws: WebSocket):
    """WebSocket 연결 추가"""
    await ws.accept()
    if conv_id not in active_connections:
        active_connections[conv_id] = set()
    active_connections[conv_id].add(ws)
    print(f"WebSocket connected: conversation {conv_id}, total: {len(active_connections[conv_id])}")


def disconnect_ws(conv_id: int, ws: WebSocket):
    """WebSocket 연결 제거"""
    if conv_id in active_connections:
        active_connections[conv_id].discard(ws)
        if not active_connections[conv_id]:
            del active_connections[conv_id]
        print(f"WebSocket disconnected: conversation {conv_id}")


async def broadcast(conv_id: int, data: dict, exclude_ws: WebSocket | None = None):
    """같은 conversation의 모든 연결에 메시지 브로드캐스트"""
    if conv_id not in active_connections:
        return
    
    message = json.dumps(data, ensure_ascii=False)
    disconnected = []
    
    for ws in active_connections[conv_id]:
        if ws == exclude_ws:
            continue
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    
    # 끊어진 연결 정리
    for ws in disconnected:
        active_connections[conv_id].discard(ws)


@router.websocket("/ws/dm/{conversation_id}")
async def dm_websocket(
    websocket: WebSocket,
    conversation_id: int,
    token: str = Query(...),
):
    """
    DM WebSocket 엔드포인트
    
    연결: ws://host/ws/dm/{conversation_id}?token={jwt_token}
    
    클라이언트 → 서버:
        { "type": "message", "content": "안녕하세요!" }
    
    서버 → 클라이언트:
        { "type": "message", "id": 1, "sender_id": 1, "sender_name": "홍길동", "content": "안녕하세요!", "created_at": "..." }
        { "type": "error", "message": "..." }
        { "type": "connected", "user_id": 1 }
    """
    from src.database import AsyncSessionLocal
    
    # 인증 및 권한 확인 (DB 세션을 짧게 사용 후 즉시 해제)
    user_id = None
    user_name = None
    
    try:
        async with AsyncSessionLocal() as db:
            # 토큰 검증
            user = await get_user_from_token(token, db)
            if not user:
                await websocket.close(code=4001, reason="Unauthorized")
                return
            
            # conversation 존재 및 권한 확인
            result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conv = result.scalar_one_or_none()
            
            if not conv:
                await websocket.close(code=4004, reason="Conversation not found")
                return
            
            if user.id not in (conv.user1_id, conv.user2_id):
                await websocket.close(code=4003, reason="Access denied")
                return
            
            # 사용자 정보 저장 (DB 세션 외부에서 사용)
            user_id = user.id
            user_name = user.name
    except Exception as e:
        print(f"Auth error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # 연결 수락 (DB 세션 없이 진행)
    await connect_ws(conversation_id, websocket)
    
    try:
        # 연결 성공 알림
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": user_id,
            "user_name": user_name,
        }))
        
        while True:
            text = await websocket.receive_text()
            
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                continue
            
            msg_type = payload.get("type")
            
            if msg_type == "message":
                content = payload.get("content", "").strip()
                if not content:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Empty message"
                    }))
                    continue
                
                # 새 DB 세션으로 메시지 저장 (짧게 사용 후 즉시 해제)
                try:
                    async with AsyncSessionLocal() as msg_db:
                        msg = Message(
                            conversation_id=conversation_id,
                            sender_id=user_id,
                            content=content,
                            context=payload.get("context"),
                            created_at=datetime.utcnow(),
                        )
                        msg_db.add(msg)
                        await msg_db.commit()
                        await msg_db.refresh(msg)
                        
                        # conversation 업데이트
                        conv_result = await msg_db.execute(
                            select(Conversation).where(Conversation.id == conversation_id)
                        )
                        conv_to_update = conv_result.scalar_one()
                        conv_to_update.last_message_id = msg.id
                        conv_to_update.last_message_at = msg.created_at
                        conv_to_update.updated_at = datetime.utcnow()
                        await msg_db.commit()
                        
                        msg_id = msg.id
                        msg_content = msg.content
                        msg_created_at = msg.created_at.isoformat() + 'Z'  # UTC 표시 추가
                    
                    # 메시지 브로드캐스트 (DB 세션 외부에서)
                    await broadcast(
                        conversation_id,
                        {
                            "type": "message",
                            "id": msg_id,
                            "sender_id": user_id,
                            "sender_name": user_name,
                            "content": msg_content,
                            "created_at": msg_created_at,
                        }
                    )
                except Exception as e:
                    print(f"Message save error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to save message"
                    }))
            
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                }))
                
    except WebSocketDisconnect:
        disconnect_ws(conversation_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        disconnect_ws(conversation_id, websocket)

