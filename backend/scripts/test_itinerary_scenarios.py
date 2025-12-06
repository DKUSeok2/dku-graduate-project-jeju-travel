#!/usr/bin/env python3
"""
여행 일정 챗봇 다양한 시나리오 테스트
- 기간별: 당일치기, 1박2일, 2박3일, 3박4일
- 유형별: 커플, 가족(아이동반), 친구, 혼자
- 테마별: 맛집, 카페, 액티비티, 힐링, 사진스팟
- 특수 조건: 비오는날, 예산, 지역 선호 등
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"


def login():
    """로그인하여 토큰 획득"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]
    print(f"❌ 로그인 실패: {resp.text}")
    sys.exit(1)


def create_session(token: str):
    """채팅 세션 생성"""
    resp = requests.post(
        f"{BASE_URL}/api/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "일정 테스트"}
    )
    if resp.status_code == 201:
        return resp.json()["session_id"]
    return None


def chat(token: str, session_id: str, message: str, bot_id: str = "itinerary"):
    """채팅 요청 (스트리밍)"""
    print(f"\n{'='*70}")
    print(f"💬 질의: {message}")
    print(f"{'='*70}")
    
    start_time = time.time()
    full_response = ""
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat/sessions/{session_id}/stream",
            headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"},
            json={"message": message, "bot_id": bot_id},
            stream=True,
            timeout=180
        )
        
        if resp.status_code != 200:
            print(f"❌ 요청 실패: {resp.status_code}")
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
        
        # 일정 데이터 파싱
        itinerary_count = full_response.count("[ITINERARY_DATA]")
        
        print(f"\n\n⏱️ 응답 시간: {elapsed:.2f}초 | 📊 {len(full_response)}자")
        if itinerary_count > 0:
            print(f"✅ 일정 데이터 생성됨!")
        
        return full_response
        
    except Exception as e:
        print(f"❌ 에러: {e}")
        return None


def run_scenario_tests(token: str, session_id: str):
    """다양한 시나리오 테스트"""
    
    scenarios = [
        # ===== 기간별 테스트 =====
        {
            "category": "📅 기간별 테스트",
            "queries": [
                "제주도 당일치기 여행 코스 추천해줘",
                "제주 1박2일 알찬 여행 일정 짜줘",
                "3박4일 제주도 여행 계획 세워줘",
            ]
        },
        
        # ===== 여행 유형별 테스트 =====
        {
            "category": "💕 여행 유형별 테스트",
            "queries": [
                "커플 여행으로 제주도 2박3일 로맨틱한 코스 추천해줘",
                "5살 아이랑 가는 제주도 가족여행 2박3일 일정 추천해줘. 아이가 좋아할만한 곳 위주로",
                "친구 4명이서 가는 제주 2박3일 여행 재밌는 곳 위주로 짜줘",
                "혼자 힐링하러 가는 제주 여행 2박3일 조용한 곳 위주로 추천해줘",
            ]
        },
        
        # ===== 테마별 테스트 =====
        {
            "category": "🎯 테마별 테스트", 
            "queries": [
                "제주도 2박3일 맛집 투어 일정 짜줘. 흑돼지랑 해산물 꼭 먹고 싶어",
                "제주 카페 투어 1박2일 일정 추천해줘. 인스타 감성 카페 위주로",
                "제주도 액티비티 위주로 2박3일 일정 추천해줘. 서핑이나 스노클링 같은 거",
                "제주도 사진 찍기 좋은 스팟 위주로 2박3일 일정 짜줘",
            ]
        },
        
        # ===== 특수 조건 테스트 =====
        {
            "category": "🌧️ 특수 조건 테스트",
            "queries": [
                "비 오는 날도 즐길 수 있는 제주 1박2일 실내 위주 일정 추천해줘",
                "예산 30만원으로 제주도 2박3일 알뜰 여행 일정 짜줘",
                "서귀포 쪽만 집중적으로 2박3일 여행 일정 추천해줘",
                "성산일출봉 일출 보고 싶은데 2박3일 일정에 포함시켜줘",
            ]
        },
        
        # ===== 복합 조건 테스트 =====
        {
            "category": "🎨 복합 조건 테스트",
            "queries": [
                "부모님 모시고 가는 효도여행 2박3일, 편하게 다닐 수 있는 코스로 추천해줘. 해산물 좋아하시고 걷는 건 힘들어하셔",
                "신혼여행으로 제주 3박4일 럭셔리하게 다니고 싶어. 좋은 호텔이랑 분위기 좋은 레스토랑 위주로",
                "7살, 10살 아이 둘이랑 제주도 2박3일 여행인데 아이들이 지루해하지 않을 체험 위주로 짜줘",
            ]
        },
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n\n{'🌴'*35}")
        print(f"  {scenario['category']}")
        print(f"{'🌴'*35}")
        
        for query in scenario["queries"]:
            response = chat(token, session_id, query, "itinerary")
            
            # 결과 저장
            results.append({
                "category": scenario["category"],
                "query": query,
                "success": response is not None and "[ITINERARY_DATA]" in (response or ""),
                "response_length": len(response) if response else 0
            })
            
            time.sleep(3)  # API 부하 방지
    
    return results


def print_summary(results):
    """테스트 결과 요약"""
    print("\n\n" + "="*70)
    print("📊 테스트 결과 요약")
    print("="*70)
    
    # 카테고리별 집계
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0}
        categories[cat]["total"] += 1
        if r["success"]:
            categories[cat]["success"] += 1
    
    total_success = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"\n총 테스트: {total}개 | 성공: {total_success}개 | 성공률: {total_success/total*100:.1f}%\n")
    
    for cat, stats in categories.items():
        emoji = "✅" if stats["success"] == stats["total"] else "⚠️"
        print(f"  {emoji} {cat}: {stats['success']}/{stats['total']}")
    
    # 실패한 케이스 출력
    failed = [r for r in results if not r["success"]]
    if failed:
        print("\n❌ 실패한 케이스:")
        for f in failed:
            print(f"  - {f['query'][:50]}...")


def main():
    print("🚀 여행 일정 챗봇 시나리오 테스트 시작")
    print("="*70)
    
    # 로그인
    token = login()
    print(f"✅ 로그인 성공")
    
    # 세션 생성
    session_id = create_session(token)
    if not session_id:
        print("❌ 세션 생성 실패")
        sys.exit(1)
    print(f"✅ 세션 생성: {session_id[:8]}...")
    
    # 시나리오 테스트 실행
    results = run_scenario_tests(token, session_id)
    
    # 결과 요약
    print_summary(results)
    
    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()


