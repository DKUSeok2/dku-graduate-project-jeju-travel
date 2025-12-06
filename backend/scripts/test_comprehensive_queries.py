"""
다양한 질의 종합 테스트 스크립트
- SQL Agent 테스트 (맛집, 카페 검색)
- RAG Agent 테스트 (관광지 검색)
- 일정 생성 테스트
- 복합 질의 테스트
"""
import asyncio
import uuid
import httpx
import json
import os
import sys
import argparse
import re
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import select, desc
from src.database import get_db_session
from src.models.user import User
from src.database import ChatSession
from src.auth.jwt import create_access_token
from src.config import settings

# 테스트 질의 목록
TEST_QUERIES = {
    "SQL Agent (맛집/카페)": [
        "애월 카페 추천해줘",
        "중문 평점 4.5 이상 맛집",
        "제주시 주차 가능한 카페 5개",
        "서귀포 아이 동반 가능한 맛집",
        "협재 해산물 빼고 평점 높은 식당",
    ],
    "RAG Agent (관광지)": [
        "우도에서 뭘 하면 좋을까?",
        "제주도 오름 추천해줘",
        "바다가 보이는 카페 어디있어?",
        "성산일출봉 정보 알려줘",
        "제주도 박물관 추천",
        "한라산 트레킹 코스",
        "제주도 야경 명소",
    ],
    "일정 생성": [
        "2박3일 여행 일정 짜줘",  # 충분한 정보 - 바로 생성
        "1박2일 커플 여행 계획",  # 충분한 정보 - 바로 생성
        "3박4일 가족 여행 일정",  # 충분한 정보 - 바로 생성
        "여행 일정 만들어줘",  # 기간 없음 - 질문해야 함
        "맛집 중심으로 일정 짜줘",  # 기간 없음 - 질문해야 함
        "커플 여행 일정",  # 기간 없음 - 질문해야 함
        "가족 여행 계획해줘",  # 기간 없음 - 질문해야 함
    ],
    "복합 질의": [
        "애월에서 바다 보이는 카페 추천하고, 그 근처 맛집도 알려줘",
        "우도 여행 일정 짜줘",
        "제주시 숙소 근처 카페와 관광지 추천",
    ],
}


async def get_test_credentials(user_email: str, create_new_session: bool = False):
    """테스트용 사용자/세션/토큰 가져오기"""
    result_data = None
    
    async for db in get_db_session():
        try:
            # 사용자 조회/생성
            result = await db.execute(
                select(User).where(User.email == user_email)
            )
            test_user = result.scalar_one_or_none()
            
            if not test_user:
                print(f"⚠️ 사용자 '{user_email}'를 찾을 수 없습니다. 새로 생성합니다.")
                test_user = User(
                    email=user_email,
                    name="테스트유저",
                    password_hash="$2b$12$test",
                    provider="local" if "@" in user_email else "google",
                    provider_id=user_email
                )
                db.add(test_user)
                await db.commit()
                await db.refresh(test_user)
                print(f"✅ 사용자 생성: ID={test_user.id}, email={test_user.email}")
            else:
                print(f"✅ 기존 테스트 사용자 사용: ID={test_user.id}, email={test_user.email}")
            
            test_session = None
            if create_new_session:
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
                print(f"✅ 새 세션 생성: session_id={test_session.session_id}")
            else:
                result = await db.execute(
                    select(ChatSession).where(
                        ChatSession.user_id == test_user.id,
                        ChatSession.is_active == True
                    ).order_by(desc(ChatSession.created_at))
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
                    print(f"✅ 새 세션 생성: session_id={test_session.session_id}")
                else:
                    print(f"✅ 기존 테스트 세션 사용: session_id={test_session.session_id}")
            
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


async def test_query(
    client: httpx.AsyncClient,
    session_id: str,
    token: str,
    query: str,
    category: str
) -> Dict:
    """단일 질의 테스트"""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{base_url}/api/chat/sessions/{session_id}/stream"
    payload = {"message": query}
    
    result = {
        "query": query,
        "category": category,
        "success": False,
        "response_length": 0,
        "has_sql_marker": False,
        "has_rag_result": False,
        "has_itinerary": False,
        "needs_info": False,
        "error": None,
        "response_preview": ""
    }
    
    try:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                result["error"] = f"HTTP {response.status_code}: {error_text.decode()}"
                return result
            
            full_response = ""
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        if data.get("type") == "AIMessageChunk" and "content" in data:
                            full_response += data["content"]
                    except json.JSONDecodeError:
                        continue
            
            result["success"] = True
            result["response_length"] = len(full_response)
            result["response_preview"] = full_response[:200] + "..." if len(full_response) > 200 else full_response
            
            # 마커 확인
            if "[SQL_QUERY_RESULT]" in full_response:
                result["has_sql_marker"] = True
                # SQL 결과 파싱 시도
                try:
                    sql_match = re.search(r'\[SQL_QUERY_RESULT\](.*?)\[/SQL_QUERY_RESULT\]', full_response, re.DOTALL)
                    if sql_match:
                        sql_data = json.loads(sql_match.group(1))
                        result["sql_row_count"] = sql_data.get("row_count", 0)
                except Exception as e:
                    pass
            
            if "[ATTRACTIONS_DATA]" in full_response or "관광지" in full_response:
                result["has_rag_result"] = True
            
            if "[ITINERARY_DATA]" in full_response:
                result["has_itinerary"] = True
                try:
                    itinerary_match = re.search(r'\[ITINERARY_DATA\](.*?)\[/ITINERARY_DATA\]', full_response, re.DOTALL)
                    if itinerary_match:
                        itinerary_data = json.loads(itinerary_match.group(1))
                        result["itinerary_days"] = len(itinerary_data.get("days", []))
                except Exception as e:
                    pass
            
            # 추가 정보 필요 확인
            if "일정을 생성하기 위해 다음 정보가 필요합니다" in full_response or "부족한 정보를 질문" in full_response:
                result["needs_info"] = True
            
            return result
    
    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()
        return result


async def run_comprehensive_tests(
    user_email: str,
    use_same_session: bool = False,
    categories: Optional[List[str]] = None
):
    """종합 테스트 실행"""
    print("=" * 80)
    print("🧪 종합 질의 테스트")
    print("=" * 80)
    print(f"\n📌 모드: {'같은 세션 사용 (대화 누적)' if use_same_session else '각 테스트마다 새 세션 생성'}")
    print(f"📌 사용자 이메일: {user_email}")
    print(f"📌 테스트 카테고리: {categories or '전체'}")
    print()
    
    # 테스트할 카테고리 필터링
    if categories:
        filtered_queries = {k: v for k, v in TEST_QUERIES.items() if k in categories}
    else:
        filtered_queries = TEST_QUERIES
    
    # 세션 관리
    creds = None
    if use_same_session:
        creds = await get_test_credentials(user_email, create_new_session=False)
        if not creds:
            print("❌ 테스트 사용자/세션 생성 실패")
            return
    else:
        creds = await get_test_credentials(user_email, create_new_session=True)
        if not creds:
            print("❌ 테스트 사용자/세션 생성 실패")
            return
    
    all_results = []
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        for category, queries in filtered_queries.items():
            print(f"\n{'='*80}")
            print(f"📂 {category} ({len(queries)}개 질의)")
            print(f"{'='*80}")
            
            for i, query in enumerate(queries, 1):
                # 🔥 각 질의마다 새 세션 생성
                if not use_same_session:
                    creds = await get_test_credentials(user_email, create_new_session=True)
                    if not creds:
                        print(f"⚠️ 세션 생성 실패 - 이 질의 건너뜀")
                        continue
                
                print(f"\n[{i}/{len(queries)}] {query}")
                print("-" * 80)
                
                result = await test_query(
                    client,
                    creds['session_id'],
                    creds['token'],
                    query,
                    category
                )
                
                all_results.append(result)
                
                # 결과 출력
                if result["success"]:
                    status = "✅ 성공"
                    if result.get("needs_info"):
                        status = "❓ 추가 정보 필요"
                    print(f"{status} (응답 길이: {result['response_length']}자)")
                    if result["has_sql_marker"]:
                        print(f"   📊 SQL 결과: {result.get('sql_row_count', 'N/A')}개 행")
                    if result["has_rag_result"]:
                        print(f"   🗺️ RAG 결과: 관광지 정보 포함")
                    if result["has_itinerary"]:
                        print(f"   📅 일정 생성: {result.get('itinerary_days', 'N/A')}일")
                    if result.get("needs_info"):
                        print(f"   💬 사용자 질문 필요")
                    print(f"   미리보기: {result['response_preview']}")
                else:
                    print(f"❌ 실패: {result['error']}")
                
                # 질의 간 대기 (API 부하 방지)
                await asyncio.sleep(2)
            
            # 카테고리 간 대기
            await asyncio.sleep(3)
    
    # 결과 요약
    print(f"\n{'='*80}")
    print("📊 테스트 결과 요약")
    print(f"{'='*80}")
    
    total = len(all_results)
    successful = sum(1 for r in all_results if r["success"])
    sql_results = sum(1 for r in all_results if r["has_sql_marker"])
    rag_results = sum(1 for r in all_results if r["has_rag_result"])
    itinerary_results = sum(1 for r in all_results if r["has_itinerary"])
    
    print(f"\n총 질의: {total}개")
    print(f"성공: {successful}개 ({successful/total*100:.1f}%)")
    print(f"SQL 결과 포함: {sql_results}개")
    print(f"RAG 결과 포함: {rag_results}개")
    print(f"일정 생성: {itinerary_results}개")
    
    # 카테고리별 통계
    print(f"\n📂 카테고리별 통계:")
    for category in filtered_queries.keys():
        category_results = [r for r in all_results if r["category"] == category]
        if category_results:
            cat_success = sum(1 for r in category_results if r["success"])
            print(f"  {category}: {cat_success}/{len(category_results)} 성공")
    
    # 추가 정보 필요 질의
    needs_info = [r for r in all_results if r.get("needs_info")]
    if needs_info:
        print(f"\n❓ 추가 정보 필요 ({len(needs_info)}개):")
        for r in needs_info:
            print(f"  - [{r['category']}] {r['query']}")
    
    # 실패한 질의
    failed = [r for r in all_results if not r["success"]]
    if failed:
        print(f"\n❌ 실패한 질의 ({len(failed)}개):")
        for r in failed:
            print(f"  - [{r['category']}] {r['query']}: {r['error']}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="종합 질의 테스트")
    parser.add_argument("--same-session", action="store_true", help="각 테스트마다 같은 세션을 사용합니다.")
    parser.add_argument("--user-email", type=str, default=None, help="테스트에 사용할 사용자 이메일")
    parser.add_argument("--user-id", type=int, default=None, help="테스트에 사용할 사용자 ID")
    parser.add_argument("--categories", type=str, nargs="+", help="테스트할 카테고리 (예: 'SQL Agent' 'RAG Agent')")
    args = parser.parse_args()
    
    # user_id가 제공되면 이메일 조회 (동기적으로)
    if args.user_id:
        import asyncio
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from src.config import settings
        
        # 동기 엔진 사용
        sync_database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_database_url)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            result = session.execute(select(User).where(User.id == args.user_id))
            user = result.scalar_one_or_none()
            if user:
                args.user_email = user.email
                print(f"✅ 사용자 ID {args.user_id}의 이메일: {user.email}")
            else:
                print(f"❌ 사용자 ID {args.user_id}를 찾을 수 없습니다.")
                sys.exit(1)
    elif not args.user_email:
        args.user_email = "yuseokoh20@gmail.com"  # 기본값

    print("⚠️ API 서버가 실행 중이어야 합니다 (http://localhost:8000)")
    print()
    
    asyncio.run(run_comprehensive_tests(
        args.user_email,
        use_same_session=args.same_session,
        categories=args.categories
    ))

