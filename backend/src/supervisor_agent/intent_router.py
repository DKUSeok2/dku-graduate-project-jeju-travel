"""
Intent Router - 규칙 기반 도구 선택 + 조건 추출

LLM에 의존하지 않고 100% 정확하게 도구 선택과 조건 추출을 수행합니다.
"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


# 지역 키워드 → region 매핑 (DB의 실제 region 값과 일치)
# DB에는 구체적인 지역명(애월, 중문, 성산 등)과 큰 지역(제주시, 서귀포시, 동부, 서부)이 모두 있음
REGION_MAPPING = {
    # 구체적인 지역명 (우선순위 높음 - DB에 직접 저장됨)
    "애월": "애월", "애월읍": "애월", "애월해안": "애월",
    "한림": "한림", "한림읍": "한림",
    "협재": "협재",
    "조천": "조천", "조천읍": "조천",
    "함덕": "함덕",
    "중문": "중문", "중문관광단지": "중문",
    "안덕": "안덕", "안덕면": "안덕", "남원": "안덕", "남원읍": "안덕", "화순": "안덕", "위미": "안덕",
    "성산": "성산", "성산일출봉": "성산", "섭지코지": "성산",
    "표선": "표선", "표선해수욕장": "표선",
    "우도": "우도", "우도면": "우도",
    "구좌": "구좌", "구좌읍": "구좌",
    "김녕": "김녕",
    "세화": "세화",
    "대정": "대정", "대정읍": "대정", "모슬포": "대정", "마라도": "대정",
    "한경": "한경", "한경면": "한경",
    
    # 큰 지역 (구체적 지역명이 없을 때 사용)
    "제주시": "제주시", "제주공항": "제주시", "용두암": "제주시",
    "서귀포": "서귀포시", "서귀포시": "서귀포시",
}

# Intent → Tool 매핑
INTENT_TO_TOOL = {
    "itinerary": "generate_travel_itinerary",
    "attraction": "search_jeju_attractions",
    "subjective_place": "search_jeju_attractions",  # 감성 검색 → RAG (소개 기반)
    "realtime": "search_realtime_info",
    "place_search": "query_jeju_database",
    "accommodation": "query_jeju_database",  # 숙소도 PostgreSQL 검색
    "route_optimize": "optimize_travel_route",
    "map": "visualize_attractions_on_map",
}

# Intent 패턴 (우선순위 순서 - 위에서부터 매칭!)
INTENT_PATTERNS = [
    # 1. 일정/코스 요청
    ("itinerary", [
        r"\d+박\d*일", r"일정", r"코스", r"계획", r"스케줄", 
        r"여행\s*짜", r"여행\s*계획"
    ]),
    # 2. 감성/분위기 검색 → RAG (SQL보다 먼저!)
    #    "예쁜 카페", "바다가 보이는 카페", "분위기 좋은 맛집" 등
    ("subjective_place", [
        r"예쁜", r"분위기", r"감성", r"힙한", r"인스타",
        r"바다.*(보이|뷰)", r"오션\s*뷰", r"바다\s*뷰", r"뷰\s*맛집", r"뷰\s*카페",
        r"루프탑", r"야경", r"노을", r"일출",
        r"조용한", r"한적한", r"숨은", r"로컬"
    ]),
    # 3. 관광지 정보/활동 (맛집보다 먼저 체크!)
    ("attraction", [
        r"관광지", r"관광", r"볼거리", r"놀거리", r"명소",
        r"뭘\s*하면", r"뭐\s*할까", r"뭐가\s*있", r"갈만한\s*곳",
        r"할\s*거", r"어떤\s*곳", r"은\s*어때", r"액티비티",
        r"실내", r"야외", r"체험", r"투어", r"트레킹", r"등산",
        r"해변", r"바다", r"오름", r"폭포", r"동굴", r"박물관", r"미술관",
        r"테마파크", r"수족관", r"식물원"
    ]),
    # 3. 실시간 정보
    ("realtime", [
        r"날씨", r"축제", r"행사", r"이벤트", r"지금", r"오늘", r"이번\s*주"
    ]),
    # 4. 경로 최적화
    ("route_optimize", [
        r"순서", r"동선", r"최적화", r"효율"
    ]),
    # 5. 지도
    ("map", [
        r"지도", r"위치"
    ]),
    # 6. 숙소 검색 (호텔, 펜션 등)
    ("accommodation", [
        r"숙소", r"호텔", r"펜션", r"리조트", r"게스트하우스", r"민박",
        r"잘\s*곳", r"묵을\s*곳", r"숙박"
    ]),
    # 7. 장소 검색 (맛집/카페 - 기본값)
    ("place_search", [
        r"맛집", r"카페", r"식당", r"음식점", r"밥집", r"술집", r"횟집",
        r"평점", r"리뷰", r"주차", r"아이"
    ]),
]


@dataclass
class ParsedQuery:
    """파싱된 쿼리 결과"""
    original_query: str
    intent: str
    tool_name: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class IntentRouter:
    """규칙 기반 Intent Router"""
    
    def parse(self, query: str) -> ParsedQuery:
        """쿼리를 파싱하여 intent, tool, conditions 추출"""
        
        # 1. Intent 결정 (키워드 매칭)
        intent = self._detect_intent(query)
        tool_name = INTENT_TO_TOOL.get(intent, "query_jeju_database")
        
        # 2. 조건 추출
        conditions = self._extract_conditions(query)
        
        return ParsedQuery(
            original_query=query,
            intent=intent,
            tool_name=tool_name,
            conditions=conditions,
            confidence=1.0
        )
    
    def _detect_intent(self, query: str) -> str:
        """키워드 매칭으로 intent 결정"""
        query_lower = query.lower()
        
        for intent, patterns in INTENT_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        # 기본값: 장소 검색
        return "place_search"
    
    def _extract_conditions(self, query: str) -> Dict[str, Any]:
        """쿼리에서 조건 추출 (100% 규칙 기반)"""
        conditions = {}
        
        # 1. 지역 추출
        for keyword, region in REGION_MAPPING.items():
            if keyword in query:
                conditions["region"] = region
                conditions["region_keyword"] = keyword
                break
        
        # 2. 평점 추출
        rating_patterns = [
            r"평점\s*(\d+\.?\d*)\s*이상",
            r"(\d+\.?\d*)\s*점\s*이상",
            r"평점\s*(\d+\.?\d*)",
        ]
        for pattern in rating_patterns:
            match = re.search(pattern, query)
            if match:
                conditions["min_rating"] = float(match.group(1))
                break
        
        # 2-1. "평점 높은", "최고 평점", "인기", "TOP" 등 표현 처리
        # 명시적 평점이 없고, 이런 표현이 있으면 기본 평점 조건 추가
        if "min_rating" not in conditions:
            high_rating_keywords = [
                "평점 높은", "평점높은", "평점이 높은", "평점 높", "평점 좋은", "평점좋은",
                "별점 높은", "별점높은", "별점 높", "별점 좋은",
                "최고 평점", "최고평점", "최고 평", "최고점",
                "인기", "유명한", "추천", "베스트", "BEST", "best",
                "TOP", "top", "탑", "1위", "상위"
            ]
            if any(kw in query for kw in high_rating_keywords):
                conditions["min_rating"] = 3.5  # 기본값: 3.5 이상
        
        # 3. 주차 조건
        if any(kw in query for kw in ["주차 가능", "주차되는", "주차 되는", "주차"]):
            conditions["parking"] = True
        
        # 4. 아이 동반 조건
        if any(kw in query for kw in ["아이 동반", "아이랑", "아이와", "애들", "가족", "아이"]):
            conditions["kid_friendly"] = True
        
        # 5. 개수 추출
        num_match = re.search(r"(\d+)\s*개", query)
        if num_match:
            conditions["limit"] = int(num_match.group(1))
        else:
            conditions["limit"] = 10  # 기본값
        
        # 6. 카테고리 힌트 추출
        if "맛집" in query or "음식" in query or "식당" in query:
            conditions["category_hint"] = "restaurant"
        elif "카페" in query:
            conditions["category_hint"] = "cafe"
        elif any(kw in query for kw in ["숙소", "호텔", "펜션", "리조트", "게스트하우스"]):
            conditions["category_hint"] = "accommodation"
        
        # 7. 부정 조건 추출 (~빼고, ~말고, ~제외)
        exclude_patterns = [
            r"(.+?)\s*(?:빼고|말고|제외|없이|안\s*되는)",
            r"(?:빼고|말고|제외)\s*(.+)",
        ]
        excludes = []
        for pattern in exclude_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                if match and len(match) > 1:
                    # 음식 종류 키워드 추출
                    food_keywords = ["해산물", "고기", "회", "생선", "돼지", "소고기", "닭", 
                                   "매운", "중식", "일식", "양식", "한식"]
                    for kw in food_keywords:
                        if kw in match:
                            excludes.append(kw)
        
        if excludes:
            conditions["excludes"] = list(set(excludes))
        
        return conditions
    
    def build_enhanced_query(self, parsed: ParsedQuery) -> str:
        """파싱 결과를 기반으로 강화된 쿼리 생성"""
        parts = [parsed.original_query]
        
        conditions = parsed.conditions
        if conditions:
            parts.append("\n\n[자동 추출된 조건 - 반드시 SQL에 반영하세요!]")
            
            if "region" in conditions:
                parts.append(f"- 지역: region = '{conditions['region']}' ({conditions.get('region_keyword', '')})")
            
            if "min_rating" in conditions:
                parts.append(f"- 평점: rating >= {conditions['min_rating']}")
            
            if conditions.get("parking"):
                parts.append("- 주차: parking = true")
            
            if conditions.get("kid_friendly"):
                parts.append("- 아이동반: kid_friendly = true")
            
            if "limit" in conditions:
                parts.append(f"- 개수: LIMIT {conditions['limit']}")
            
            if "excludes" in conditions:
                excludes_str = ", ".join(conditions["excludes"])
                parts.append(f"- 제외: {excludes_str} 포함된 것 제외 (category NOT ILIKE)")
        
        return "\n".join(parts)


# 싱글톤 인스턴스
_router_instance: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    """Intent Router 싱글톤 반환"""
    global _router_instance
    if _router_instance is None:
        _router_instance = IntentRouter()
    return _router_instance

