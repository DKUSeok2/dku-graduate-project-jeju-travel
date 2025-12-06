"""
테스트용 사용자/세션 생성 및 API 호출로 DB 저장 테스트
"""
import asyncio
import uuid
import httpx
import json
import os
from sqlalchemy import select
from src.database import get_db_session
from src.models.user import User
from src.database import ChatSession
from src.auth.jwt import create_access_token
from src.config import settings

async def get_test_credentials(create_new_session=False, user_email=None):
    """테스트용 사용자/세션/토큰 가져오기
    
    Args:
        create_new_session: True면 항상 새 세션 생성, False면 기존 세션 재사용
        user_email: 사용자 이메일 (None이면 구글 계정 사용)
    """
    result_data = None
    
    # 기본값: 구글 계정
    if user_email is None:
        user_email = "yuseokoh20@gmail.com"
    
    async for db in get_db_session():
        try:
            # 사용자 조회
            result = await db.execute(
                select(User).where(User.email == user_email)
            )
            test_user = result.scalar_one_or_none()
            
            if not test_user:
                print(f"❌ 사용자를 찾을 수 없습니다: {user_email}")
                return None
            
            # 세션 처리
            if create_new_session:
                # 항상 새 세션 생성
                session_id = "test-session-" + str(uuid.uuid4())
                test_session = ChatSession(
                    user_id=test_user.id,
                    session_id=session_id,
                    title="테스트 세션",
                    messages=[],
                    context={},
                    is_active=True
                )
                db.add(test_session)
                await db.commit()
                await db.refresh(test_session)
            else:
                # 기존 세션 조회/생성
                result = await db.execute(
                    select(ChatSession).where(
                        ChatSession.user_id == test_user.id,
                        ChatSession.is_active == True
                    ).order_by(ChatSession.created_at.desc())
                )
                test_session = result.scalar_one_or_none()
                
                if not test_session:
                    session_id = "test-session-" + str(uuid.uuid4())
                    test_session = ChatSession(
                        user_id=test_user.id,
                        session_id=session_id,
                        title="테스트 세션",
                        messages=[],
                        context={},
                        is_active=True
                    )
                    db.add(test_session)
                    await db.commit()
                    await db.refresh(test_session)
            
            # 토큰 생성
            token = create_access_token(data={"sub": str(test_user.id), "user_id": test_user.id})
            
            result_data = {
                "user_id": test_user.id,
                "session_id": test_session.session_id,
                "token": token
            }
        
        except Exception as e:
            print(f"❌ get_test_credentials 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break
    
    return result_data

async def test_api_with_db_save(use_same_session=False):
    """API 호출로 DB 저장 테스트
    
    Args:
        use_same_session: True면 같은 세션 사용 (대화 누적), False면 각 테스트마다 새 세션
    """
    
    # API 호출
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    test_queries = [
        "애월 카페 추천해줘",
        "2박3일 여행 일정 짜줘"
    ]
    
    # 세션 관리
    all_sessions = []  # 저장 확인용
    creds = None  # 초기화
    
    if use_same_session:
        # 같은 세션 사용 (대화 맥락 유지)
        creds = await get_test_credentials(create_new_session=False)
        if not creds:
            print("❌ 테스트 사용자/세션 생성 실패")
            return
        print(f"✅ 테스트 정보 (같은 세션 사용):")
        print(f"   User ID: {creds['user_id']}")
        print(f"   Session ID: {creds['session_id']}")
        print()
        all_sessions.append(creds['session_id'])
    else:
        # 각 테스트마다 새 세션 생성
        print(f"✅ 각 테스트마다 새 세션 생성")
        print()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*80}")
            print(f"{i}. 질의: {query}")
            print(f"{'='*80}")
            
            # 각 테스트마다 새 세션이면 생성
            if not use_same_session:
                creds = await get_test_credentials(create_new_session=True)
                if not creds:
                    print(f"❌ 세션 생성 실패 - 이 질의 건너뜀")
                    continue
                session_id = creds['session_id']
                all_sessions.append(session_id)
                print(f"   📝 새 세션: {session_id}")
            else:
                if not creds:
                    print(f"❌ 세션 정보 없음 - 이 질의 건너뜀")
                    continue
                session_id = creds['session_id']
            
            headers = {
                "Authorization": f"Bearer {creds['token']}",
                "Content-Type": "application/json"
            }
            
            url = f"{base_url}/api/chat/sessions/{session_id}/stream"
            payload = {"message": query}
            
            try:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        print(f"❌ API 오류: {response.status_code}")
                        error_text = await response.aread()
                        print(f"오류 내용: {error_text.decode()}")
                        continue
                    
                    print(f"✅ API 호출 성공")
                    full_response = ""
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if "content" in data:
                                    full_response += data["content"]
                            except json.JSONDecodeError:
                                continue
                    
                    print(f"✅ 응답 수신 완료 (길이: {len(full_response)}자)")
            
            except Exception as e:
                print(f"❌ 오류: {e}")
            
            await asyncio.sleep(1)
    
    # DB에 저장되었는지 확인
    print(f"\n{'='*80}")
    print("📊 DB 저장 확인")
    print(f"{'='*80}")
    
    sessions_to_check = all_sessions
    
    async for db in get_db_session():
        try:
            for session_id in sessions_to_check:
                result = await db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                session = result.scalar_one_or_none()
                
                if session:
                    messages = session.messages or []
                    print(f"\n✅ 세션 {session_id[:20]}...: 총 {len(messages)}개 메시지")
                    
                    for j, msg in enumerate(messages, 1):
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')[:100]
                        print(f"  {j}. [{role}] {content}...")
                else:
                    print(f"❌ 세션을 찾을 수 없음: {session_id}")
        
        finally:
            await db.close()
            break

if __name__ == "__main__":
    import sys
    
    print("=" * 80)
    print("🧪 API 호출로 DB 저장 테스트")
    print("=" * 80)
    print("\n⚠️ API 서버가 실행 중이어야 합니다 (http://localhost:8000)")
    print()
    
    # 명령줄 인자로 세션 사용 방식 선택
    # python test_api_with_db_save.py --same-session  : 같은 세션 사용 (대화 누적)
    # python test_api_with_db_save.py                 : 각 테스트마다 새 세션 (기본값)
    
    use_same_session = "--same-session" in sys.argv
    
    if use_same_session:
        print("📌 모드: 같은 세션 사용 (대화 누적)")
    else:
        print("📌 모드: 각 테스트마다 새 세션 생성 (독립 테스트)")
    
    print()
    asyncio.run(test_api_with_db_save(use_same_session=use_same_session))

