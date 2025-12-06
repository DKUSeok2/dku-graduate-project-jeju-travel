"""
Mock Schedule 데이터 생성 스크립트
AI 대화 내역, 추천 이유, 지도 데이터를 포함한 완전한 일정 생성
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_db_session
from src.models.schedule import Schedule
from src.models.user import User
from sqlalchemy import select


async def create_mock_schedules():
    """Mock 일정 데이터 생성"""
    
    async for db in get_db_session():
        try:
            # 첫 번째 사용자 가져오기
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ 사용자가 없습니다. 먼저 사용자를 생성해주세요.")
                return
            
            print(f"✅ 사용자 찾음: {user.name} (ID: {user.id})")
            
            # Mock 일정 데이터
            mock_schedules = [
                {
                    "title": "🏖️ 액티브 제주 여행 (개인일정)",
                    "start_date": datetime.now().date() + timedelta(days=7),
                    "end_date": datetime.now().date() + timedelta(days=9),
                    "memo": "등산과 트레킹을 즐기는 제주 여행",
                    "is_public": False,
                    "chat_history": [
                        {
                            "role": "user",
                            "content": "3박 4일 가족여행 계획 좀 도와줘",
                            "timestamp": datetime.now().isoformat()
                        },
                        {
                            "role": "assistant",
                            "content": "3박 4일 가족 여행이시군요!\n아이들과 함께 즐길 수 있는 장소들을 추천해드릴게요 🎉\n\n가족 여행객을 위해 제주도의 대표적인 관광지들을 추천해드렸습니다. 각 장소는 접근성이 좋고, 안전하며, 다양한 연령대가 즐길 수 있는 곳들로 선정했습니다.",
                            "timestamp": datetime.now().isoformat()
                        }
                    ],
                    "ai_reasoning": "가족 여행객을 위해 제주도의 대표적인 관광지들을 추천해드렸습니다. 각 장소는 접근성이 좋고, 안전하며, 다양한 연령대가 즐길 수 있는 곳들로 선정했습니다. 특히 아이들이 좋아할 체험형 관광지와 자연 경관이 아름다운 장소들을 균형있게 배치했습니다.",
                    "attractions": {
                        "day1": [
                            {"name": "협재해수욕장", "category": "해변", "time": "2시간", "price": "무료", "emoji": "🏖️", "lat": 33.394, "lng": 126.239},
                            {"name": "애월 카페거리", "category": "카페", "time": "1.5시간", "price": "10,000원", "emoji": "☕", "lat": 33.466, "lng": 126.319},
                        ],
                        "day2": [
                            {"name": "아쿠아플라넷 제주", "category": "체험", "time": "3시간", "price": "38,000원", "emoji": "🐠", "lat": 33.432, "lng": 126.920},
                            {"name": "성산일출봉", "category": "자연", "time": "2시간", "price": "5,000원", "emoji": "🌄", "lat": 33.458, "lng": 126.942},
                        ],
                        "day3": [
                            {"name": "테디베어박물관", "category": "문화", "time": "1.5시간", "price": "11,000원", "emoji": "🧸", "lat": 33.248, "lng": 126.411},
                            {"name": "주상절리", "category": "자연", "time": "1시간", "price": "무료", "emoji": "🪨", "lat": 33.238, "lng": 126.425},
                        ]
                    },
                    "map_data": {
                        "markers": [
                            {"name": "협재해수욕장", "lat": 33.394, "lng": 126.239, "emoji": "🏖️"},
                            {"name": "애월 카페거리", "lat": 33.466, "lng": 126.319, "emoji": "☕"},
                            {"name": "아쿠아플라넷 제주", "lat": 33.432, "lng": 126.920, "emoji": "🐠"},
                            {"name": "성산일출봉", "lat": 33.458, "lng": 126.942, "emoji": "🌄"},
                            {"name": "테디베어박물관", "lat": 33.248, "lng": 126.411, "emoji": "🧸"},
                            {"name": "주상절리", "lat": 33.238, "lng": 126.425, "emoji": "🪨"},
                        ],
                        "center": {"lat": 33.45, "lng": 126.57}
                    }
                },
                {
                    "title": "🍊 제주 맛집 투어 2박 3일",
                    "start_date": datetime.now().date() + timedelta(days=14),
                    "end_date": datetime.now().date() + timedelta(days=16),
                    "memo": "제주도의 유명 맛집들을 탐방하는 미식 여행",
                    "is_public": True,
                    "chat_history": [
                        {
                            "role": "user",
                            "content": "맛집 위주로 2박3일 여행 추천해줘",
                            "timestamp": datetime.now().isoformat()
                        },
                        {
                            "role": "assistant",
                            "content": "맛집 투어 여행이시군요! 🍊\n제주도의 대표 맛집들을 소개해드릴게요.\n\n제주도 현지인들이 인정하는 맛집들과 관광객들에게 인기 있는 식당들을 균형있게 선정했습니다.",
                            "timestamp": datetime.now().isoformat()
                        }
                    ],
                    "ai_reasoning": "미식 여행을 위해 제주도의 대표 음식(흑돼지, 해산물, 감귤 디저트 등)을 맛볼 수 있는 유명 맛집들을 선정했습니다. 각 식당은 맛과 분위기가 검증된 곳들로 구성했습니다.",
                    "attractions": {
                        "day1": [
                            {"name": "흑돼지거리", "category": "식당", "time": "2시간", "price": "30,000원", "emoji": "🥩", "lat": 33.489, "lng": 126.499},
                            {"name": "오메기떡 카페", "category": "디저트", "time": "1시간", "price": "8,000원", "emoji": "🍡", "lat": 33.512, "lng": 126.521},
                        ],
                        "day2": [
                            {"name": "해녀의 집", "category": "해산물", "time": "1.5시간", "price": "25,000원", "emoji": "🦞", "lat": 33.449, "lng": 126.931},
                            {"name": "감귤 체험 농장", "category": "체험", "time": "2시간", "price": "15,000원", "emoji": "🍊", "lat": 33.308, "lng": 126.358},
                        ]
                    },
                    "map_data": {
                        "markers": [
                            {"name": "흑돼지거리", "lat": 33.489, "lng": 126.499, "emoji": "🥩"},
                            {"name": "오메기떡 카페", "lat": 33.512, "lng": 126.521, "emoji": "🍡"},
                            {"name": "해녀의 집", "lat": 33.449, "lng": 126.931, "emoji": "🦞"},
                            {"name": "감귤 체험 농장", "lat": 33.308, "lng": 126.358, "emoji": "🍊"},
                        ],
                        "center": {"lat": 33.45, "lng": 126.57}
                    }
                },
                {
                    "title": "📸 인스타 감성 제주 4박 5일",
                    "start_date": datetime.now().date() + timedelta(days=21),
                    "end_date": datetime.now().date() + timedelta(days=25),
                    "memo": "감성 사진 찍기 좋은 제주 명소들",
                    "is_public": True,
                    "chat_history": [
                        {
                            "role": "user",
                            "content": "사진 찍기 좋은 곳으로 4박5일 계획해줘",
                            "timestamp": datetime.now().isoformat()
                        },
                        {
                            "role": "assistant",
                            "content": "포토 스팟 여행이시군요! 📸\n인스타그램에서 핫한 제주 명소들을 추천드려요.\n\n감성적인 사진을 찍을 수 있는 카페, 자연 경관, 이색 건축물들을 중심으로 구성했습니다.",
                            "timestamp": datetime.now().isoformat()
                        }
                    ],
                    "ai_reasoning": "SNS에서 인기 있는 포토 스팟들을 중심으로 일정을 구성했습니다. 자연광이 아름다운 오전/오후 시간대에 맞춰 방문할 수 있도록 순서를 배치했습니다.",
                    "attractions": {
                        "day1": [
                            {"name": "카멜리아힐", "category": "정원", "time": "2시간", "price": "9,000원", "emoji": "🌺", "lat": 33.291, "lng": 126.359},
                            {"name": "월정리해변", "category": "해변", "time": "1.5시간", "price": "무료", "emoji": "🌊", "lat": 33.556, "lng": 126.796},
                        ],
                        "day2": [
                            {"name": "섭지코지", "category": "자연", "time": "2시간", "price": "무료", "emoji": "🏝️", "lat": 33.424, "lng": 126.929},
                            {"name": "우도", "category": "섬", "time": "4시간", "price": "15,000원", "emoji": "🏖️", "lat": 33.505, "lng": 126.954},
                        ],
                        "day3": [
                            {"name": "애월 한담해변", "category": "해변", "time": "1.5시간", "price": "무료", "emoji": "🌅", "lat": 33.475, "lng": 126.308},
                            {"name": "본태박물관", "category": "미술관", "time": "2시간", "price": "16,000원", "emoji": "🎨", "lat": 33.276, "lng": 126.352},
                        ],
                        "day4": [
                            {"name": "산굼부리", "category": "자연", "time": "1시간", "price": "6,000원", "emoji": "🌳", "lat": 33.431, "lng": 126.772},
                            {"name": "제주민속촌", "category": "문화", "time": "2시간", "price": "11,000원", "emoji": "🏘️", "lat": 33.318, "lng": 126.638},
                        ]
                    },
                    "map_data": {
                        "markers": [
                            {"name": "카멜리아힐", "lat": 33.291, "lng": 126.359, "emoji": "🌺"},
                            {"name": "월정리해변", "lat": 33.556, "lng": 126.796, "emoji": "🌊"},
                            {"name": "섭지코지", "lat": 33.424, "lng": 126.929, "emoji": "🏝️"},
                            {"name": "우도", "lat": 33.505, "lng": 126.954, "emoji": "🏖️"},
                            {"name": "애월 한담해변", "lat": 33.475, "lng": 126.308, "emoji": "🌅"},
                            {"name": "본태박물관", "lat": 33.276, "lng": 126.352, "emoji": "🎨"},
                            {"name": "산굼부리", "lat": 33.431, "lng": 126.772, "emoji": "🌳"},
                            {"name": "제주민속촌", "lat": 33.318, "lng": 126.638, "emoji": "🏘️"},
                        ],
                        "center": {"lat": 33.45, "lng": 126.57}
                    }
                }
            ]
            
            # 일정 생성
            created_count = 0
            for schedule_data in mock_schedules:
                schedule = Schedule(
                    user_id=user.id,
                    **schedule_data
                )
                db.add(schedule)
                created_count += 1
            
            await db.commit()
            print(f"✅ {created_count}개의 Mock 일정이 생성되었습니다!")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


if __name__ == "__main__":
    print("🚀 Mock Schedule 데이터 생성 시작...\n")
    asyncio.run(create_mock_schedules())
    print("\n✨ 완료!")


