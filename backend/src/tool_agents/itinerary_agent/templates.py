"""
여행 일정 템플릿 정의
지역 이동과 시간대별 활동을 정의합니다.
"""
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class TimeSlot:
    """시간대 정의"""
    name: str  # 오전, 점심, 오후, 저녁
    start_time: str  # "09:00"
    end_time: str  # "12:00"
    place_type: str  # 관광지, 맛집, 카페
    duration_hours: float = 2.0


@dataclass
class DaySchedule:
    """하루 일정"""
    day: int
    regions: List[str]  # 해당 일에 방문할 지역들
    slots: List[TimeSlot]
    accommodation_region: str = ""  # 숙소 지역


# 기본 시간대 정의
MORNING_ACTIVITY = TimeSlot(
    name="오전", 
    start_time="09:00", 
    end_time="12:00", 
    place_type="관광지",
    duration_hours=3.0
)

LUNCH = TimeSlot(
    name="점심", 
    start_time="12:00", 
    end_time="13:30", 
    place_type="맛집",
    duration_hours=1.5
)

AFTERNOON_ACTIVITY = TimeSlot(
    name="오후", 
    start_time="14:00", 
    end_time="17:00", 
    place_type="관광지",
    duration_hours=3.0
)

CAFE_TIME = TimeSlot(
    name="카페", 
    start_time="17:00", 
    end_time="18:00", 
    place_type="카페",
    duration_hours=1.0
)

DINNER = TimeSlot(
    name="저녁", 
    start_time="18:30", 
    end_time="20:00", 
    place_type="맛집",
    duration_hours=1.5
)


# 일정 템플릿 정의
ITINERARY_TEMPLATES: Dict[str, List[DaySchedule]] = {
    # 당일치기
    "당일치기_기본": [
        DaySchedule(
            day=1,
            regions=["제주시", "애월", "한림"],  # 서부 드라이브 코스
            slots=[
                TimeSlot("오전", "10:00", "12:00", "관광지", 2.0),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "14:30", "17:00", "관광지", 2.5),
                TimeSlot("카페", "17:30", "18:30", "카페", 1.0),
            ],
            accommodation_region=""  # 당일치기는 숙소 없음
        ),
    ],
    
    "당일치기_동부": [
        DaySchedule(
            day=1,
            regions=["동부", "성산", "표선"],
            slots=[
                TimeSlot("오전", "09:00", "12:00", "관광지", 3.0),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "14:30", "17:00", "관광지", 2.5),
                TimeSlot("카페", "17:30", "18:30", "카페", 1.0),
            ],
            accommodation_region=""
        ),
    ],
    
    "당일치기_서부": [
        DaySchedule(
            day=1,
            regions=["애월", "한림", "서부"],
            slots=[
                TimeSlot("오전", "10:00", "12:00", "관광지", 2.0),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "15:00", "17:30", "카페", 2.5),  # 애월 카페거리
                TimeSlot("저녁", "18:00", "19:30", "맛집", 1.5),
            ],
            accommodation_region=""
        ),
    ],
    
    # 1박2일
    "1박2일_기본": [
        DaySchedule(
            day=1,
            regions=["제주시"],
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="제주시"
        ),
        DaySchedule(
            day=2,
            regions=["서귀포시"],
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY],
            accommodation_region=""  # 마지막 날
        ),
    ],
    
    # 2박3일 기본 (현실적인 동선: 제주시 → 서귀포 → 동부 → 공항)
    "2박3일_기본": [
        DaySchedule(
            day=1,
            regions=["제주시"],  # 공항 도착 → 제주시 관광
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="제주시"  # 제주시 숙소
        ),
        DaySchedule(
            day=2,
            regions=["서귀포시"],  # 서귀포/중문 집중 관광
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="서귀포시"  # 서귀포시 숙소
        ),
        DaySchedule(
            day=3,
            regions=["동부"],  # 성산/우도 → 공항 방향
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY],
            accommodation_region=""  # 마지막 날 숙소 없음
        ),
    ],
    
    # 2박3일 맛집 중심 (현실적인 동선)
    "2박3일_맛집": [
        DaySchedule(
            day=1,
            regions=["제주시"],  # 제주시 맛집 투어
            slots=[
                TimeSlot("오전", "10:00", "11:30", "관광지", 1.5),
                TimeSlot("점심", "12:00", "13:30", "맛집", 1.5),
                TimeSlot("오후", "14:30", "16:00", "카페", 1.5),
                TimeSlot("간식", "16:30", "17:30", "맛집", 1.0),
                TimeSlot("저녁", "18:30", "20:00", "맛집", 1.5),
            ],
            accommodation_region="제주시"
        ),
        DaySchedule(
            day=2,
            regions=["서귀포시"],  # 서귀포시 맛집 투어
            slots=[
                TimeSlot("아침", "09:00", "10:00", "맛집", 1.0),
                TimeSlot("오전", "10:30", "12:00", "관광지", 1.5),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "14:30", "16:30", "카페", 2.0),
                TimeSlot("저녁", "18:00", "20:00", "맛집", 2.0),
            ],
            accommodation_region="서귀포시"
        ),
        DaySchedule(
            day=3,
            regions=["동부"],  # 동부 맛집 → 공항
            slots=[
                TimeSlot("오전", "10:00", "11:30", "관광지", 1.5),
                TimeSlot("점심", "12:00", "13:30", "맛집", 1.5),
                TimeSlot("오후", "14:00", "15:30", "카페", 1.5),
            ],
            accommodation_region=""
        ),
    ],
    
    # 3박4일 기본 (시계방향: 제주시 → 동부 → 서귀포 → 서부 → 공항)
    "3박4일_기본": [
        DaySchedule(
            day=1,
            regions=["제주시"],  # 공항 도착 → 제주시
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="제주시"
        ),
        DaySchedule(
            day=2,
            regions=["동부"],  # 성산/우도 관광
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="서귀포시"  # 동부에서 서귀포로 이동 후 숙박
        ),
        DaySchedule(
            day=3,
            regions=["서귀포시"],  # 중문/서귀포 관광
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="서귀포시"
        ),
        DaySchedule(
            day=4,
            regions=["서부"],  # 서부 → 공항 방향
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY],
            accommodation_region=""
        ),
    ],
    
    # 3박4일 가족여행 (아이 동반, 여유로운 일정)
    "3박4일_가족": [
        DaySchedule(
            day=1,
            regions=["제주시"],  # 공항 → 제주시 (아이 친화적 장소)
            slots=[
                TimeSlot("오전", "10:00", "12:00", "관광지", 2.0),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "14:30", "17:00", "관광지", 2.5),
                TimeSlot("저녁", "18:00", "19:30", "맛집", 1.5),
            ],
            accommodation_region="제주시"
        ),
        DaySchedule(
            day=2,
            regions=["동부"],  # 성산 (아쿠아플라넷, 섭지코지 등)
            slots=[
                TimeSlot("오전", "09:30", "12:00", "관광지", 2.5),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "14:30", "17:00", "관광지", 2.5),
                TimeSlot("카페", "17:30", "18:30", "카페", 1.0),
                TimeSlot("저녁", "19:00", "20:30", "맛집", 1.5),
            ],
            accommodation_region="서귀포시"  # 동부에서 서귀포로 이동
        ),
        DaySchedule(
            day=3,
            regions=["서귀포시"],  # 중문 (테디베어, 여미지 등)
            slots=[
                TimeSlot("오전", "10:00", "12:30", "관광지", 2.5),
                TimeSlot("점심", "13:00", "14:30", "맛집", 1.5),
                TimeSlot("오후", "15:00", "17:30", "관광지", 2.5),
                TimeSlot("저녁", "18:30", "20:00", "맛집", 1.5),
            ],
            accommodation_region="서귀포시"
        ),
        DaySchedule(
            day=4,
            regions=["서부"],  # 서부 → 공항 (오설록 등)
            slots=[
                TimeSlot("오전", "09:30", "11:30", "관광지", 2.0),
                TimeSlot("점심", "12:00", "13:30", "맛집", 1.5),
            ],
            accommodation_region=""
        ),
    ],
    
    # ========== 지역 고정 템플릿 (한 지역 중심) ==========
    
    # 서귀포 중심 2박3일 (이동 최소화)
    "2박3일_서귀포": [
        DaySchedule(
            day=1,
            regions=["서귀포시"],
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="서귀포시"
        ),
        DaySchedule(
            day=2,
            regions=["서귀포시"],  # 같은 지역!
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="서귀포시"
        ),
        DaySchedule(
            day=3,
            regions=["서귀포시", "제주시"],  # 공항 방향 이동
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY],
            accommodation_region=""
        ),
    ],
    
    # 제주시 중심 2박3일
    "2박3일_제주시": [
        DaySchedule(
            day=1,
            regions=["제주시"],
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="제주시"
        ),
        DaySchedule(
            day=2,
            regions=["제주시", "애월"],  # 제주시 + 인근 애월
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="제주시"
        ),
        DaySchedule(
            day=3,
            regions=["제주시"],
            slots=[MORNING_ACTIVITY, LUNCH],
            accommodation_region=""
        ),
    ],
    
    # 성산/동부 중심 2박3일
    "2박3일_성산": [
        DaySchedule(
            day=1,
            regions=["동부", "성산"],
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="동부"
        ),
        DaySchedule(
            day=2,
            regions=["동부", "성산"],  # 우도, 섭지코지 등
            slots=[
                TimeSlot("새벽", "05:30", "07:00", "관광지", 1.5),  # 일출
                TimeSlot("아침", "08:00", "09:30", "맛집", 1.5),
                TimeSlot("오전", "10:00", "12:00", "관광지", 2.0),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "14:30", "17:00", "관광지", 2.5),
                TimeSlot("저녁", "18:00", "19:30", "맛집", 1.5),
            ],
            accommodation_region="동부"
        ),
        DaySchedule(
            day=3,
            regions=["동부", "제주시"],  # 공항 방향
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY],
            accommodation_region=""
        ),
    ],
    
    # 애월 중심 1박2일 (카페투어)
    "1박2일_애월": [
        DaySchedule(
            day=1,
            regions=["애월", "한림"],
            slots=[
                TimeSlot("오전", "10:00", "12:00", "카페", 2.0),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "14:30", "16:30", "카페", 2.0),
                TimeSlot("카페", "17:00", "18:30", "카페", 1.5),
                TimeSlot("저녁", "19:00", "20:30", "맛집", 1.5),
            ],
            accommodation_region="애월"
        ),
        DaySchedule(
            day=2,
            regions=["애월", "제주시"],
            slots=[
                TimeSlot("오전", "10:00", "12:00", "관광지", 2.0),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("카페", "14:30", "16:00", "카페", 1.5),
            ],
            accommodation_region=""
        ),
    ],
    
    # 중문 중심 2박3일 (리조트 휴양)
    "2박3일_중문": [
        DaySchedule(
            day=1,
            regions=["서귀포시"],  # 중문관광단지
            slots=[MORNING_ACTIVITY, LUNCH, AFTERNOON_ACTIVITY, CAFE_TIME, DINNER],
            accommodation_region="서귀포시"
        ),
        DaySchedule(
            day=2,
            regions=["서귀포시"],  # 중문 집중
            slots=[
                TimeSlot("오전", "10:00", "12:00", "관광지", 2.0),
                TimeSlot("점심", "12:30", "14:00", "맛집", 1.5),
                TimeSlot("오후", "15:00", "17:00", "관광지", 2.0),
                TimeSlot("카페", "17:30", "19:00", "카페", 1.5),
                TimeSlot("저녁", "19:30", "21:00", "맛집", 1.5),
            ],
            accommodation_region="서귀포시"
        ),
        DaySchedule(
            day=3,
            regions=["서귀포시", "제주시"],
            slots=[MORNING_ACTIVITY, LUNCH],
            accommodation_region=""
        ),
    ],
}


# 지역 키워드 매핑 (사용자 입력 → 템플릿 지역명)
REGION_KEYWORDS = {
    "서귀포": "서귀포",
    "중문": "중문",
    "성산": "성산",
    "동부": "성산",
    "우도": "성산",
    "애월": "애월",
    "한림": "애월",
    "협재": "애월",
    "제주시": "제주시",
    "제주": "제주시",
}


def get_template(duration: str, style: str = "기본", region: str = None) -> List[DaySchedule]:
    """
    일정 템플릿 가져오기
    
    Args:
        duration: "당일치기", "1박2일", "2박3일", "3박4일"
        style: "기본", "맛집", "가족"
        region: 특정 지역 중심 (예: "서귀포", "성산", "애월")
    
    Returns:
        DaySchedule 리스트
    """
    # 1. 지역 중심 템플릿 우선 (사용자가 특정 지역 요청 시)
    if region:
        region_key = f"{duration}_{region}"
        if region_key in ITINERARY_TEMPLATES:
            return ITINERARY_TEMPLATES[region_key]
    
    # 2. 스타일 템플릿
    template_key = f"{duration}_{style}"
    if template_key in ITINERARY_TEMPLATES:
        return ITINERARY_TEMPLATES[template_key]
    
    # 3. 기본 템플릿 반환
    default_key = f"{duration}_기본"
    if default_key in ITINERARY_TEMPLATES:
        return ITINERARY_TEMPLATES[default_key]
    
    # 4. fallback: 2박3일 기본
    return ITINERARY_TEMPLATES.get("2박3일_기본", [])


def parse_duration(text: str) -> str:
    """
    텍스트에서 여행 기간 추출
    
    Args:
        text: 사용자 입력 텍스트
    
    Returns:
        "1박2일", "2박3일", "3박4일" 등
    """
    import re
    
    # 당일치기 먼저 체크
    if any(kw in text for kw in ["당일치기", "당일여행", "당일 여행", "하루 여행", "원데이", "1일 여행"]):
        return "당일치기"
    
    # 패턴 매칭
    patterns = [
        (r"(\d+)\s*박\s*(\d+)\s*일", lambda m: f"{m.group(1)}박{m.group(2)}일"),
        (r"(\d+)\s*day", lambda m: f"{int(m.group(1))-1}박{m.group(1)}일" if int(m.group(1)) > 1 else "당일치기"),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, text)
        if match:
            return formatter(match)
    
    # 기본값
    return "2박3일"


def parse_style(text: str) -> str:
    """
    텍스트에서 여행 스타일 추출
    
    Args:
        text: 사용자 입력 텍스트
    
    Returns:
        "기본", "맛집", "가족"
    """
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ["맛집", "음식", "먹방", "미식"]):
        return "맛집"
    elif any(kw in text_lower for kw in ["가족", "아이", "아기", "어린이", "부모님"]):
        return "가족"
    elif any(kw in text_lower for kw in ["힐링", "휴양", "조용"]):
        return "힐링"
    elif any(kw in text_lower for kw in ["액티비티", "체험", "활동적"]):
        return "액티비티"
    
    return "기본"

