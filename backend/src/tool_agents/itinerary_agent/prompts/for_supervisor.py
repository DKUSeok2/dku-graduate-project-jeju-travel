"""
Supervisor Agent용 Itinerary Tool 프롬프트
"""

SUPERVISOR_PROMPT = """
### generate_travel_itinerary (일정 생성)

**용도**: 제주도 여행 일정 자동 생성

**반드시 사용해야 하는 경우**:
- 사용자가 "일정", "코스", "여행 계획"을 요청할 때
- "N박M일", "N일" 형태의 기간이 언급될 때
- "여행 짜줘", "계획 세워줘" 등의 요청

**입력**:
- query: 사용자의 일정 요청 그대로 전달
- kid_friendly: "아이", "가족", "어린이" 언급 시 true
- parking: "주차", "렌트카" 언급 시 true

**사용 예시**:
- "2박3일 제주 여행 일정 짜줘" → generate_travel_itinerary(query="2박3일 제주 여행 일정")
- "3박4일 가족여행 계획" → generate_travel_itinerary(query="3박4일 가족여행", kid_friendly=true)
- "맛집 중심 2박3일" → generate_travel_itinerary(query="맛집 중심 2박3일")

⚠️ 주의: 일정 요청에는 반드시 이 도구를 사용하세요. 직접 일정을 만들지 마세요!
"""

