#!/usr/bin/env python3
"""
챗봇별 API 테스트 스크립트
- itinerary: 여행 일정 추천
- sql: SQL 기반 데이터 조회
- rag: RAG 기반 관광지 정보 검색
- web: 웹 검색 기반 실시간 정보
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

# 테스트 계정
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"
TEST_NAME = "테스트유저"


def register_or_login():
    """회원가입 또는 로그인하여 토큰 획득"""
    # 먼저 로그인 시도
    login_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if login_resp.status_code == 200:
        data = login_resp.json()
        print(f"✅ 로그인 성공: {data['user']['name']}")
        return data["access_token"]
    
    # 로그인 실패 시 회원가입
    print("🔄 로그인 실패, 회원가입 시도...")
    register_resp = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME}
    )
    
    if register_resp.status_code == 201:
        data = register_resp.json()
        print(f"✅ 회원가입 성공: {data['user']['name']}")
        return data["access_token"]
    
    print(f"❌ 인증 실패: {register_resp.text}")
    sys.exit(1)


def create_session(token: str, title: str = "테스트 세션"):
    """채팅 세션 생성"""
    resp = requests.post(
        f"{BASE_URL}/api/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title}
    )
    
    if resp.status_code == 201:
        data = resp.json()
        print(f"✅ 세션 생성: {data['session_id'][:8]}...")
        return data["session_id"]
    
    print(f"❌ 세션 생성 실패: {resp.text}")
    return None


def stream_chat(token: str, session_id: str, message: str, bot_id: str = "itinerary"):
    """스트리밍 채팅 요청"""
    print(f"\n{'='*60}")
    print(f"🤖 [{bot_id.upper()}] 질의: {message}")
    print(f"{'='*60}")
    
    start_time = time.time()
    full_response = ""
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat/sessions/{session_id}/stream",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "text/event-stream"
            },
            json={"message": message, "bot_id": bot_id},
            stream=True,
            timeout=120  # 2분 타임아웃
        )
        
        if resp.status_code != 200:
            print(f"❌ 요청 실패: {resp.status_code} - {resp.text}")
            return None
        
        print("\n📝 응답:")
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if data["type"] == "AIMessageChunk":
                        content = data["content"]
                        full_response += content
                        print(content, end="", flush=True)
                    elif data["type"] == "done":
                        break
                    elif data["type"] == "error":
                        print(f"\n❌ 에러: {data['content']}")
                        return None
                except json.JSONDecodeError:
                    continue
        
        elapsed = time.time() - start_time
        print(f"\n\n⏱️ 응답 시간: {elapsed:.2f}초")
        print(f"📊 응답 길이: {len(full_response)}자")
        return full_response
        
    except requests.exceptions.Timeout:
        print("❌ 타임아웃!")
        return None
    except Exception as e:
        print(f"❌ 에러: {e}")
        return None


def test_itinerary_chatbot(token: str, session_id: str):
    """여행 일정 추천 챗봇 테스트"""
    print("\n" + "🗺️ "*20)
    print("🗺️  ITINERARY CHATBOT 테스트")
    print("🗺️ "*20)
    
    queries = [
        "제주도 2박3일 여행 일정 추천해줘",
        "서귀포 쪽으로 맛집이랑 카페 위주로 추천해줘",
        "비 오는 날 갈만한 실내 관광지 알려줘",
    ]
    
    for q in queries:
        stream_chat(token, session_id, q, "itinerary")
        time.sleep(2)


def test_sql_chatbot(token: str, session_id: str):
    """SQL 기반 데이터 조회 챗봇 테스트"""
    print("\n" + "🔍 "*20)
    print("🔍  SQL CHATBOT 테스트")
    print("🔍 "*20)
    
    queries = [
        "제주시에 있는 카페 중에서 평점 4.5 이상인 곳 알려줘",
        "서귀포시 맛집 중에서 리뷰가 가장 많은 곳 5개 알려줘",
        "제주도 숙소 중에서 가격대별로 추천해줘",
    ]
    
    for q in queries:
        stream_chat(token, session_id, q, "sql")
        time.sleep(2)


def test_rag_chatbot(token: str, session_id: str):
    """RAG 기반 관광지 정보 검색 챗봇 테스트"""
    print("\n" + "📚 "*20)
    print("📚  RAG CHATBOT 테스트")
    print("📚 "*20)
    
    queries = [
        "성산일출봉에 대해 자세히 알려줘",
        "우도에서 꼭 가봐야 할 곳은?",
        "한라산 등반 코스 추천해줘",
    ]
    
    for q in queries:
        stream_chat(token, session_id, q, "rag")
        time.sleep(2)


def test_web_chatbot(token: str, session_id: str):
    """웹 검색 기반 실시간 정보 챗봇 테스트"""
    print("\n" + "🌐 "*20)
    print("🌐  WEB CHATBOT 테스트")
    print("🌐 "*20)
    
    queries = [
        "제주도 이번 주 날씨 어때?",
        "제주도 12월 축제나 행사 있어?",
        "제주공항 근처 렌트카 가격 정보 알려줘",
    ]
    
    for q in queries:
        stream_chat(token, session_id, q, "web")
        time.sleep(2)


def main():
    print("🚀 챗봇 API 테스트 시작")
    print("="*60)
    
    # 1. 인증
    token = register_or_login()
    
    # 2. 세션 생성
    session_id = create_session(token, "API 테스트 세션")
    if not session_id:
        sys.exit(1)
    
    # 3. 테스트할 챗봇 선택 (인자로 받기)
    if len(sys.argv) > 1:
        bot_type = sys.argv[1].lower()
        if bot_type == "itinerary":
            test_itinerary_chatbot(token, session_id)
        elif bot_type == "sql":
            test_sql_chatbot(token, session_id)
        elif bot_type == "rag":
            test_rag_chatbot(token, session_id)
        elif bot_type == "web":
            test_web_chatbot(token, session_id)
        elif bot_type == "all":
            test_itinerary_chatbot(token, session_id)
            test_sql_chatbot(token, session_id)
            test_rag_chatbot(token, session_id)
            test_web_chatbot(token, session_id)
        else:
            print(f"❌ 알 수 없는 챗봇 유형: {bot_type}")
            print("사용법: python test_chatbot_api.py [itinerary|sql|rag|web|all]")
    else:
        # 기본: 각 챗봇에 1개씩만 질의
        print("\n📋 간단 테스트 (각 챗봇 1개 질의)")
        
        stream_chat(token, session_id, "제주도 1박2일 추천", "itinerary")
        time.sleep(2)
        
        stream_chat(token, session_id, "제주시 평점 좋은 카페 3개 알려줘", "sql")
        time.sleep(2)
        
        stream_chat(token, session_id, "성산일출봉 가는 방법 알려줘", "rag")
        time.sleep(2)
        
        stream_chat(token, session_id, "제주도 오늘 날씨", "web")
    
    print("\n" + "="*60)
    print("✅ 테스트 완료!")


if __name__ == "__main__":
    main()


