"""
일정 스케줄러 - 시간대별 장소 배치 (하이브리드: PostgreSQL + Elasticsearch)
+ 경로 최적화 (TSP 알고리즘)
+ 다양성 확보 (가중 랜덤 선택)
+ LLM 기반 조건 추출 (특정 장소 포함, 선호도 반영)
"""
import asyncio
import random
import json
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from sqlalchemy import create_engine, text
import logging

from src.config import settings
from src.tool_agents.itinerary_agent.templates import (
    DaySchedule, TimeSlot, get_template, parse_duration, parse_style
)
from src.tool_agents.rag_agent.retriever import get_retriever
from src.tool_agents.route_optimizer_agent.utils import (
    build_distance_matrix,
    nearest_neighbor_tsp,
    get_road_route_kakao_by_name,  # 장소명 기반 좌표 보정 후 길찾기
    haversine_distance
)

logger = logging.getLogger(__name__)


@dataclass
class UserConditions:
    """사용자 요청에서 추출된 조건"""
    duration: str = "2박3일"
    style: str = "기본"
    must_visit_places: List[str] = None  # 필수 방문 장소
    interests: List[str] = None          # 관심사 (카페, 맛집, 액티비티 등)
    region_preference: str = None        # 선호 지역
    group_type: str = None               # 커플, 가족, 친구 등
    avoid_places: List[str] = None       # 제외할 장소
    subjective_keywords: List[str] = None  # 감성 키워드 (바다뷰, 예쁜, 분위기 등)
    
    def __post_init__(self):
        if self.must_visit_places is None:
            self.must_visit_places = []
        if self.interests is None:
            self.interests = []
        if self.avoid_places is None:
            self.avoid_places = []
        if self.subjective_keywords is None:
            self.subjective_keywords = []
    
    def has_subjective_condition(self) -> bool:
        """감성/분위기 조건이 있는지 확인"""
        return len(self.subjective_keywords) > 0


@dataclass
class ScheduledPlace:
    """스케줄에 배치된 장소"""
    id: Union[int, str]  # PostgreSQL은 int, Elasticsearch는 str
    name: str
    category: str
    rating: Optional[float]
    region: str
    time_slot: str  # 오전, 점심, 오후, 저녁
    start_time: str
    end_time: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    parking: Optional[bool] = None
    kid_friendly: Optional[bool] = None
    source: str = "postgresql"  # 데이터 소스 구분


@dataclass
class DayItinerary:
    """하루 일정"""
    day: int
    date_label: str  # "Day 1", "첫째 날"
    regions: List[str]
    places: List[ScheduledPlace]
    accommodation: Optional[Dict[str, Any]] = None


class ItineraryScheduler:
    """일정 스케줄러 (하이브리드 데이터 소스 + 다양성 확보 + LLM 조건 추출)"""
    
    def __init__(self, llm=None):
        self.engine = create_engine(settings.database_url)
        self._used_es_doc_ids = set()  # Elasticsearch document_id 중복 방지
        self._used_place_names = set()  # 장소명 중복 방지
        self._used_categories = set()  # 세부 카테고리 중복 방지 (다양성)
        self._llm = llm  # LLM 인스턴스 (조건 추출용)
    
    async def _extract_conditions_with_llm(self, user_query: str) -> UserConditions:
        """LLM으로 사용자 요청에서 조건 추출"""
        
        # 규칙 기반 기본 파싱
        duration = parse_duration(user_query)
        style = parse_style(user_query)
        
        conditions = UserConditions(duration=duration, style=style)
        
        # LLM이 없으면 규칙 기반만 사용
        if not self._llm:
            logger.info(f"📋 규칙 기반 조건 추출: duration={duration}, style={style}")
            return conditions
        
        # LLM으로 상세 조건 추출
        prompt = f"""사용자의 제주도 여행 요청을 분석하여 조건을 추출하세요.

**사용자 요청:** "{user_query}"

**추출할 정보:**
1. must_visit_places: 사용자가 **꼭 가고 싶다고 언급한 특정 장소명** (예: "헬로키티 카페", "성산일출봉")
2. interests: 관심사/테마 (예: ["카페", "사진", "맛집", "힐링", "액티비티", "드라이브"])
3. region_preference: 선호 지역 (**중요!** 아래 예시 참고)
4. group_type: 여행 유형 (예: "커플", "가족", "친구", "혼자")
5. avoid_places: 피하고 싶은 장소

**region_preference 추출 규칙:**
- "서귀포" 언급 → "서귀포"
- "중문" 언급 → "중문"
- "애월" 언급 → "애월"
- "성산", "일출봉", "우도" 언급 → "성산"
- "협재", "한림" 언급 → "한림"
- "제주시", "공항 근처" 언급 → "제주시"
- 특정 지역 없음 → null

**응답 형식 (JSON만):**
{{
    "must_visit_places": ["장소1", "장소2"],
    "interests": ["관심사1", "관심사2"],
    "region_preference": "지역명 또는 null",
    "group_type": "유형 또는 null",
    "avoid_places": ["장소1"]
}}

**주의:** 사용자가 명시적으로 언급한 것만 추출하세요. 추측하지 마세요."""

        try:
            response = await self._llm.ainvoke(prompt)
            content = response.content.strip()
            
            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                extracted = json.loads(json_match.group())
                
                conditions.must_visit_places = extracted.get("must_visit_places", [])
                conditions.interests = extracted.get("interests", [])
                conditions.region_preference = extracted.get("region_preference")
                conditions.group_type = extracted.get("group_type")
                conditions.avoid_places = extracted.get("avoid_places", [])
                
                logger.info(f"🎯 LLM 조건 추출 완료: {extracted}")
        except Exception as e:
            logger.warning(f"⚠️ LLM 조건 추출 실패: {e}")
        
        return conditions
    
    async def _design_schedule_with_llm(
        self, 
        user_query: str, 
        conditions: 'UserConditions'
    ) -> Optional[List[DaySchedule]]:
        """LLM으로 유연한 일정 구조 설계 (하이브리드 방식)
        
        LLM이 일정 뼈대를 설계하고, 실제 장소는 DB/ES에서 검색합니다.
        """
        if not self._llm:
            return None
        
        # 당일치기/기간 파싱
        if "당일" in conditions.duration or conditions.duration == "0박1일":
            days = 1
            nights = 0
        else:
            try:
                nights = int(conditions.duration[0])  # "2박3일" → 2
                days = nights + 1
            except (ValueError, IndexError):
                days = 3
                nights = 2
        # 사용자 지정 지역 확인
        user_region = conditions.region_preference
        
        # 당일치기 vs 숙박 여행
        if nights == 0:
            # 당일치기
            base_region = user_region or "제주시"
            accommodation_strategy = f"당일치기 - {base_region} 및 인근 지역만 방문"
        elif nights <= 2:
            # 1-2박: 한 곳 숙소 고정
            base_region = user_region or "제주시"
            accommodation_strategy = f"{base_region}에 {nights}박 숙박, {base_region} 및 인근 지역 중심"
        else:
            # 3박+: 사용자 지정 지역이 있으면 그 지역 중심
            if user_region:
                accommodation_strategy = f"{user_region}에서 {nights}박 (또는 {user_region} 중심으로 인근 지역 포함)"
            else:
                accommodation_strategy = "제주시 2박 → 서귀포 1박, 각 숙소 중심으로 인근 지역만 방문"
            base_region = user_region or "제주시"
        
        # 지역 중심 여행 강조 (사용자가 특정 지역 언급 시)
        region_emphasis = ""
        if user_region:
            region_emphasis = f"""
**🎯 사용자 지정 지역: {user_region}**
- 사용자가 "{user_region}" 지역을 언급했으므로, **{user_region} 중심**으로 일정을 구성해야 합니다.
- 불필요한 장거리 이동 없이 {user_region} + 인근 지역(30분 이내)만 방문
- 예: {user_region}가 서귀포면 → 서귀포, 중문, 성산 중심
- 예: {user_region}가 애월이면 → 애월, 한림, 제주시 서부 중심
"""
        
        prompt = f"""제주도 {conditions.duration} 여행 일정의 **구조**를 설계해주세요.

**사용자 요청:** "{user_query}"
**여행 유형:** {conditions.group_type or "일반"}
**관심사:** {", ".join(conditions.interests) if conditions.interests else "없음"}
**필수 방문:** {", ".join(conditions.must_visit_places) if conditions.must_visit_places else "없음"}
**숙소 전략:** {accommodation_strategy}
{region_emphasis}
**⚠️ 중요 규칙:**
1. **한 지역 중심 여행**: 매일 여러 지역을 돌아다니지 말고, 한 지역 + 인근 지역만 방문
   - 실제 여행자들은 한 지역에 머물며 그 주변을 집중 탐방
   - 제주시 → 애월, 한림 / 서귀포 → 중문, 성산 등 연결되는 지역만
2. **매일 다른 패턴**: 고정된 "관광지→맛집→관광지" 반복 금지
3. **시간대별 장소 유형**:
   - 오전: 카페, 시장, 오름, 해변
   - 점심/저녁: 맛집
   - 오후: 관광지, 박물관, 체험
   - 저녁 이후: 야경명소, 야시장
4. **여행 유형 반영**: 커플→감성카페/야경, 가족→체험/테마파크
5. **마지막 날**: 공항 근처(제주시) 방향으로 이동

**🔴 type 필드 규칙 (절대 규칙 - 반드시 준수하세요!):**
- type은 **반드시** "관광지", "맛집", "카페" 중 하나만 사용
- **hint와 type의 관계 (매우 중요!):**
  * hint에 "오름", "박물관", "해변", "체험", "트레킹", "등산", "산책", "전망대" → type="관광지" ✅
  * hint에 "해산물", "흑돼지", "음식", "맛집", "식당", "회", "국수", "해장국" → type="맛집" ✅
  * hint에 "카페", "커피", "브런치", "디저트" → type="카페" ✅
  
**❌ 절대 하지 마세요 (잘못된 예시):**
- {{"hint": "오름 트레킹", "type": "맛집"}} ❌ (관광지여야 함!)
- {{"hint": "박물관 방문", "type": "맛집"}} ❌ (관광지여야 함!)
- {{"hint": "해장국", "type": "관광지"}} ❌ (맛집이어야 함!)

**✅ 올바른 예시:**
- {{"hint": "오름 트레킹", "type": "관광지"}} ✅
- {{"hint": "박물관 방문", "type": "관광지"}} ✅
- {{"hint": "해장국", "type": "맛집"}} ✅
- {{"hint": "오션뷰 카페", "type": "카페"}} ✅

**응답 형식 (JSON만):**
{{
    "accommodation": {{
        "region": "제주시",  // 숙소 지역 (2박이면 2일 모두 여기)
        "nights": {nights}  // 숙박 일수
    }},
    "days": [
        {{
            "day": 1,
            "region": "제주시",  // 숙소 지역 또는 인근 지역만
            "nearby_regions": ["애월", "한림"],  // 방문 가능한 인근 지역
            "theme": "도착일 여유롭게",
            "slots": [
                {{"time": "10:00-12:00", "type": "카페", "hint": "브런치카페"}},
                {{"time": "12:30-14:00", "type": "맛집", "hint": "해산물"}},
                {{"time": "14:30-17:00", "type": "관광지", "hint": "해변산책"}},
                {{"time": "18:00-20:00", "type": "맛집", "hint": "흑돼지"}}
            ]
        }},
        {{
            "day": 2,
            "region": "제주시",  // 같은 숙소 지역 중심
            "nearby_regions": ["애월", "한림"],
            ...
        }},
        ...
    ]
}}

**주의:** 
- type은 반드시 "관광지", "맛집", "카페" 중 하나
- hint는 검색 키워드 (예: "오션뷰", "해산물", "야경")
- 각 day의 region은 accommodation.region과 같거나 nearby_regions에 포함된 지역만
- 마지막 날은 공항 근처(제주시) 또는 이동 편한 지역
- **반드시 {days}일 분량 모두 작성 (Day 1, Day 2, ..., Day {days} 모두 포함)**
- 각 day마다 최소 2-4개의 slots를 포함해야 함
- Day {days}에도 최소 2개 이상의 장소 슬롯을 포함해야 함"""

        try:
            response = await self._llm.ainvoke(prompt)
            content = response.content.strip()
            
            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                logger.warning("⚠️ LLM 일정 설계 실패: JSON 파싱 불가")
                return None
            
            design = json.loads(json_match.group())
            
            # 숙소 지역 추출
            accommodation_info = design.get("accommodation", {})
            base_region = accommodation_info.get("region", "제주시")
            
            # DaySchedule로 변환
            schedules = []
            for day_data in design.get("days", []):
                slots = []
                for slot_data in day_data.get("slots", []):
                    time_parts = slot_data.get("time", "09:00-12:00").split("-")
                    start_time = time_parts[0].strip()
                    end_time = time_parts[1].strip() if len(time_parts) > 1 else "12:00"
                    
                    # 시간 차이로 duration 계산
                    try:
                        start_h, start_m = map(int, start_time.split(":"))
                        end_h, end_m = map(int, end_time.split(":"))
                        duration = (end_h - start_h) + (end_m - start_m) / 60
                    except:
                        duration = 2.0
                    
                    slot = TimeSlot(
                        name=slot_data.get("hint", slot_data.get("type", "활동")),
                        start_time=start_time,
                        end_time=end_time,
                        place_type=slot_data.get("type", "관광지"),
                        duration_hours=max(1.0, duration)
                    )
                    slots.append(slot)
                
                # 지역: 숙소 지역 + 인근 지역
                main_region = day_data.get("region", base_region)
                nearby = day_data.get("nearby_regions", [])
                regions = [main_region] + nearby
                regions = list(dict.fromkeys(regions))  # 중복 제거
                
                day_num = day_data.get("day", 1)
                is_last_day = day_num == days
                
                schedule = DaySchedule(
                    day=day_num,
                    regions=regions,
                    slots=slots,
                    accommodation_region="" if is_last_day else base_region
                )
                schedules.append(schedule)
            
            # 검증: 요청한 일수만큼 일정이 있는지 확인
            day_nums = [s.day for s in schedules]
            expected_days = set(range(1, days + 1))
            actual_days = set(day_nums)
            missing_days = expected_days - actual_days
            
            if missing_days:
                logger.warning(f"⚠️ LLM이 {missing_days}일차 일정을 생성하지 않음 - 기본 슬롯 추가")
                # 누락된 날짜에 기본 슬롯 추가
                for missing_day in sorted(missing_days):
                    # 기본 슬롯 생성
                    default_slots = [
                        TimeSlot(name="오전 활동", start_time="09:00", end_time="12:00", place_type="관광지", duration_hours=3.0),
                        TimeSlot(name="점심", start_time="12:00", end_time="14:00", place_type="맛집", duration_hours=2.0),
                        TimeSlot(name="오후 활동", start_time="14:00", end_time="17:00", place_type="관광지", duration_hours=3.0),
                        TimeSlot(name="저녁", start_time="18:00", end_time="20:00", place_type="맛집", duration_hours=2.0)
                    ]
                    
                    schedule = DaySchedule(
                        day=missing_day,
                        regions=[base_region],
                        slots=default_slots,
                        accommodation_region="" if missing_day == days else base_region
                    )
                    schedules.append(schedule)
                    logger.info(f"   ➕ Day {missing_day} 기본 슬롯 추가")
            
            # 일정 정렬 (day 순서대로)
            schedules.sort(key=lambda x: x.day)
            
            logger.info(f"🎨 LLM 일정 설계 완료: {len(schedules)}일")
            for s in schedules:
                slot_names = [slot.name for slot in s.slots]
                logger.info(f"   Day {s.day} ({s.regions[0]}): {' → '.join(slot_names)} ({len(s.slots)}개 슬롯)")
            
            return schedules
            
        except Exception as e:
            logger.warning(f"⚠️ LLM 일정 설계 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _search_place_by_name(self, place_name: str) -> Optional[Dict[str, Any]]:
        """장소명으로 DB 검색 (PostgreSQL + Elasticsearch)"""
        
        # 1. PostgreSQL 검색
        try:
            query = text("""
                SELECT id, name, category, rating, region, lat, lng, parking, kid_friendly
                FROM places
                WHERE name ILIKE :search_name
                ORDER BY rating DESC NULLS LAST
                LIMIT 1
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"search_name": f"%{place_name}%"}).fetchone()
                
                if result:
                    logger.info(f"✅ PostgreSQL에서 '{place_name}' 발견")
                    return {
                        "id": result[0],
                        "name": result[1],
                        "category": result[2],
                        "rating": float(result[3]) if result[3] else None,
                        "region": result[4],
                        "lat": float(result[5]) if result[5] else None,
                        "lng": float(result[6]) if result[6] else None,
                        "parking": result[7],
                        "kid_friendly": result[8],
                        "source": "postgresql"
                    }
        except Exception as e:
            logger.warning(f"PostgreSQL 검색 오류: {e}")
        
        # 2. Elasticsearch 검색
        try:
            retriever = get_retriever()
            results, _ = await retriever.retrieve(query=place_name, num_results=5)
            
            for result in results:
                metadata = result.metadata or {}
                title = metadata.get("title", "")
                
                # 이름 유사도 체크
                if place_name.lower() in title.lower() or title.lower() in place_name.lower():
                    logger.info(f"✅ Elasticsearch에서 '{place_name}' 발견: {title}")
                    return {
                        "id": result.document_id,
                        "name": title,
                        "category": "관광지",
                        "rating": metadata.get("rating"),
                        "region": metadata.get("region", "제주시"),
                        "lat": metadata.get("lat"),
                        "lng": metadata.get("lng"),
                        "parking": None,
                        "kid_friendly": None,
                        "source": "elasticsearch"
                    }
        except Exception as e:
            logger.warning(f"Elasticsearch 검색 오류: {e}")
        
        logger.warning(f"⚠️ '{place_name}'을 찾을 수 없음")
        return None
    
    def _weighted_random_select(
        self, 
        candidates: List[Dict[str, Any]], 
        diversity_penalty: bool = True
    ) -> Optional[Dict[str, Any]]:
        """가중 랜덤 선택 (다양성 확보)
        
        - rating 높을수록 선택 확률 높음 (rating^2)
        - 이미 사용된 카테고리는 가중치 30%로 감소
        
        Args:
            candidates: 후보 장소 리스트 (dict with 'rating', 'category')
            diversity_penalty: 카테고리 다양성 패널티 적용 여부
        
        Returns:
            선택된 장소 dict 또는 None
        """
        if not candidates:
            return None
        
        # rating 기반 가중치 계산 (rating^2로 높은 평점에 더 큰 가중치)
        weights = []
        for c in candidates:
            rating = c.get('rating') or 3.0  # 평점 없으면 3.0 기본값
            weight = float(rating) ** 2
            
            # 다양성 패널티: 이미 사용된 세부 카테고리는 가중치 감소
            if diversity_penalty:
                category = c.get('category', '')
                # 세부 카테고리 추출 (예: "돼지고기구이" → "돼지고기구이")
                sub_category = category.split(',')[0].strip() if category else ''
                if sub_category in self._used_categories:
                    weight *= 0.3  # 70% 패널티
            
            weights.append(max(weight, 0.1))  # 최소 0.1 보장
        
        # 가중 랜덤 선택
        selected = random.choices(candidates, weights=weights, k=1)[0]
        
        # 선택된 카테고리 기록
        category = selected.get('category', '')
        sub_category = category.split(',')[0].strip() if category else ''
        if sub_category:
            self._used_categories.add(sub_category)
        
        return selected
    
    async def create_itinerary(
        self,
        user_query: str,
        preferences: Dict[str, Any] = None
    ) -> Tuple[List[DayItinerary], Optional[List[Dict[str, Any]]]]:
        """
        사용자 요청을 분석하여 일정 생성 (비동기)
        
        Args:
            user_query: 사용자 요청 텍스트
            preferences: 추가 선호도 (kid_friendly, parking 등)
        
        Returns:
            (일정 리스트, 경로 데이터 리스트) 튜플
            경로 데이터: [{"day": 1, "routes": [{"from_place": {...}, "to_place": {...}, "path": [...], ...}]}]
        """
        logger.info(f"📅 일정 생성 시작: {user_query}")
        
        # 1. LLM으로 상세 조건 추출
        conditions = await self._extract_conditions_with_llm(user_query)
        
        duration = conditions.duration
        style = conditions.style
        
        logger.info(f"   기간: {duration}, 스타일: {style}")
        logger.info(f"   필수 방문: {conditions.must_visit_places}")
        logger.info(f"   관심사: {conditions.interests}")
        
        # 2. 필수 방문 장소 검색
        must_visit_data = []
        for place_name in conditions.must_visit_places:
            place_data = await self._search_place_by_name(place_name)
            if place_data:
                must_visit_data.append(place_data)
                logger.info(f"   ✅ 필수 방문 장소 확인: {place_data['name']} ({place_data['region']})")
        
        # 2.5. 감성 키워드 추출 (규칙 기반)
        subjective_patterns = [
            r"예쁜", r"분위기", r"감성", r"힙한", r"인스타",
            r"바다.*(보이|뷰)", r"오션\s*뷰", r"바다\s*뷰", r"뷰\s*맛집", r"뷰\s*카페",
            r"루프탑", r"야경", r"노을", r"일출",
            r"조용한", r"한적한", r"숨은", r"로컬"
        ]
        for pattern in subjective_patterns:
            if re.search(pattern, user_query):
                match = re.search(pattern, user_query)
                if match:
                    conditions.subjective_keywords.append(match.group())
        
        if conditions.subjective_keywords:
            logger.info(f"   🎨 감성 키워드: {conditions.subjective_keywords}")
        
        # 3. 선호도 업데이트
        if preferences is None:
            preferences = {}
        
        if conditions.group_type == "가족":
            preferences["kid_friendly"] = True
        if conditions.interests:
            preferences["interests"] = conditions.interests
        if conditions.subjective_keywords:
            preferences["subjective_keywords"] = conditions.subjective_keywords
            preferences["use_elasticsearch_for_food"] = True  # 카페/맛집도 ES 사용
        
        # 4. 🆕 LLM으로 유연한 일정 구조 설계 시도
        template = None
        if self._llm:
            logger.info("   🎨 LLM으로 유연한 일정 설계 시도...")
            template = await self._design_schedule_with_llm(user_query, conditions)
        
        # LLM 설계 실패 시 기존 템플릿 사용
        if not template:
            logger.info("   📋 기존 템플릿 사용")
            template = get_template(duration, style)
        
        if not template:
            logger.warning("   템플릿을 찾을 수 없음, 기본 2박3일 사용")
            template = get_template("2박3일", "기본")
        
        # 5. 각 Day별로 장소 채우기 (비동기)
        itinerary: List[DayItinerary] = []
        all_routes_data: List[Dict[str, Any]] = []  # 🆕 모든 일차의 경로 데이터
        used_place_ids = set()  # PostgreSQL 중복 방지
        self._used_es_doc_ids = set()  # Elasticsearch 중복 방지 (매번 초기화)
        self._used_place_names = set()  # 장소명 중복 방지 (매번 초기화)
        self._used_categories = set()  # 카테고리 다양성 (매번 초기화)
        
        # 필수 방문 장소 사용 추적
        must_visit_remaining = list(must_visit_data)
        
        for day_schedule in template:
            day_itinerary, routes_data = await self._fill_day_schedule(
                day_schedule, 
                used_place_ids,
                preferences or {},
                must_visit_remaining  # 필수 방문 장소 전달
            )
            
            # 3일차 이상에서 장소가 없으면 경고 및 재시도
            if day_itinerary.day >= 3 and len(day_itinerary.places) == 0:
                logger.warning(f"⚠️ Day {day_itinerary.day}에 장소가 없음 - 재시도...")
                # 재시도: 조건 완화
                relaxed_preferences = preferences.copy() if preferences else {}
                relaxed_preferences.pop("min_rating", None)  # 평점 조건 제거
                
                # 재검색 시도
                day_itinerary, routes_data = await self._fill_day_schedule(
                    day_schedule,
                    used_place_ids,
                    relaxed_preferences,
                    must_visit_remaining
                )
                
                if len(day_itinerary.places) == 0:
                    logger.error(f"❌ Day {day_itinerary.day} 재시도 후에도 장소 없음 - 강제 장소 할당 시도")
                    # 🔥 강제 장소 할당: 지역 조건 완화 + 모든 조건 제거
                    day_itinerary, routes_data = await self._force_fill_day_schedule(
                        day_schedule,
                        used_place_ids
                    )
            
            itinerary.append(day_itinerary)
            
            # 🆕 경로 데이터 수집
            if routes_data:
                all_routes_data.append({
                    "day": day_itinerary.day,
                    "routes": routes_data
                })
        
        # 최종 검증: 모든 날짜에 장소가 있는지 확인 및 강제 할당
        for i, day_itinerary in enumerate(itinerary):
            if len(day_itinerary.places) == 0:
                logger.error(f"❌ Day {day_itinerary.day}에 장소가 없습니다! - 강제 장소 할당")
                # 해당 날짜의 day_schedule 찾기
                day_schedule = template[i] if i < len(template) else None
                if day_schedule:
                    new_day_itinerary, routes_data = await self._force_fill_day_schedule(
                        day_schedule,
                        used_place_ids
                    )
                    itinerary[i] = new_day_itinerary
                    
                    # 🆕 경로 데이터도 업데이트
                    if routes_data:
                        # 기존 해당 day의 경로 데이터 교체
                        for j, rd in enumerate(all_routes_data):
                            if rd["day"] == new_day_itinerary.day:
                                all_routes_data[j] = {"day": new_day_itinerary.day, "routes": routes_data}
                                break
                        else:
                            all_routes_data.append({"day": new_day_itinerary.day, "routes": routes_data})
        
        logger.info(f"✅ 일정 생성 완료: {len(itinerary)}일, {len(all_routes_data)}개 경로 데이터")
        return itinerary, all_routes_data if all_routes_data else None
    
    async def _fill_day_schedule(
        self,
        day_schedule: DaySchedule,
        used_place_ids: set,
        preferences: Dict[str, Any],
        must_visit_remaining: List[Dict[str, Any]] = None
    ) -> Tuple[DayItinerary, Optional[List[Dict[str, Any]]]]:
        """하루 일정에 장소 채우기 (비동기) + 경로 최적화 + 필수 방문 장소 포함"""
        places: List[ScheduledPlace] = []
        must_visit_remaining = must_visit_remaining or []
        
        # 1. 필수 방문 장소 중 이 Day의 지역과 맞는 것 먼저 배치
        must_visit_for_today = []
        for place_data in must_visit_remaining[:]:  # 복사본 순회
            place_region = place_data.get("region", "")
            
            # 지역 매칭 (동부, 서귀포시 등)
            if any(r in place_region or place_region in r for r in day_schedule.regions):
                must_visit_for_today.append(place_data)
                must_visit_remaining.remove(place_data)
                logger.info(f"   🎯 필수 방문 '{place_data['name']}'을 Day {day_schedule.day}에 배치")
        
        # 2. 각 슬롯에 장소 채우기
        slot_index = 0
        for slot in day_schedule.slots:
            place = None
            
            # 필수 방문 장소가 있고 슬롯 유형과 맞으면 우선 배치
            if must_visit_for_today:
                for mv_place in must_visit_for_today[:]:
                    # 카페는 카페 슬롯에, 맛집은 맛집 슬롯에
                    category = (mv_place.get("category") or "").lower()
                    
                    can_place = False
                    if slot.place_type == "카페" and "카페" in category:
                        can_place = True
                    elif slot.place_type == "맛집" and any(kw in category for kw in ["고기", "한식", "회", "음식"]):
                        can_place = True
                    elif slot.place_type == "관광지":
                        # 관광지 슬롯에는 맛집/카페가 아닌 것들 배치
                        if "카페" not in category and not any(kw in category for kw in ["고기", "한식", "회", "음식"]):
                            can_place = True
                        # 또는 첫 번째 관광지 슬롯에 강제 배치
                        elif slot_index == 0:
                            can_place = True
                    
                    if can_place:
                        place = ScheduledPlace(
                            id=mv_place["id"],
                            name=mv_place["name"],
                            category=mv_place.get("category", ""),
                            rating=mv_place.get("rating"),
                            region=mv_place.get("region", day_schedule.regions[0]),
                            time_slot=slot.name,
                            start_time=slot.start_time,
                            end_time=slot.end_time,
                            lat=mv_place.get("lat"),
                            lng=mv_place.get("lng"),
                            parking=mv_place.get("parking"),
                            kid_friendly=mv_place.get("kid_friendly"),
                            source=mv_place.get("source", "postgresql")
                        )
                        must_visit_for_today.remove(mv_place)
                        logger.info(f"   ✅ 필수 방문 '{mv_place['name']}' → {slot.name} 슬롯에 배치")
                        break
            
            # 필수 방문 장소가 없으면 일반 검색
            if not place:
                place = await self._find_place_for_slot(
                    slot=slot,
                    regions=day_schedule.regions,
                    used_ids=used_place_ids,
                    preferences=preferences
                )
            
            if place:
                places.append(place)
                # 소스에 따라 다른 집합에 추가
                if place.source == "postgresql":
                    used_place_ids.add(place.id)
                else:
                    self._used_es_doc_ids.add(place.id)
            
            slot_index += 1
        
        # 남은 필수 방문 장소가 있으면 마지막 Day에 추가 (다음 Day로 전달)
        if must_visit_for_today:
            logger.warning(f"   ⚠️ 미배치 필수 방문 장소: {[p['name'] for p in must_visit_for_today]}")
            must_visit_remaining.extend(must_visit_for_today)
        
        # 🚀 경로 최적화: lat/lng가 있는 장소들의 방문 순서 최적화
        places, routes_data = self._optimize_route(places, day_schedule.day)
        
        # 숙소 (선택적)
        accommodation = None
        if day_schedule.accommodation_region:
            accommodation = self._find_accommodation(
                day_schedule.accommodation_region,
                used_place_ids
            )
        
        day_itinerary = DayItinerary(
            day=day_schedule.day,
            date_label=f"Day {day_schedule.day}",
            regions=day_schedule.regions,
            places=places,
            accommodation=accommodation
        )
        
        return day_itinerary, routes_data
    
    async def _force_fill_day_schedule(
        self,
        day_schedule: DaySchedule,
        used_place_ids: set
    ) -> Tuple[DayItinerary, Optional[List[Dict[str, Any]]]]:
        """강제로 장소 할당 (모든 조건 제거, 지역 확대)"""
        logger.warning(f"🔥 Day {day_schedule.day} 강제 장소 할당 시작")
        places: List[ScheduledPlace] = []
        
        # 모든 조건 제거된 preferences
        empty_preferences = {}
        
        # 지역 확대: 원래 지역 + 인근 지역들
        expanded_regions = list(day_schedule.regions)
        # 제주시 관련 지역 추가
        if any(r in ["제주시", "애월", "한림"] for r in expanded_regions):
            expanded_regions.extend(["제주시", "애월", "한림", "동부", "서부"])
        # 서귀포 관련 지역 추가
        if any(r in ["서귀포시", "중문", "안덕"] for r in expanded_regions):
            expanded_regions.extend(["서귀포시", "중문", "안덕", "동부", "서부"])
        # 동부 관련 지역 추가
        if any(r in ["동부", "성산", "표선", "구좌"] for r in expanded_regions):
            expanded_regions.extend(["동부", "성산", "표선", "구좌", "제주시", "서귀포시"])
        # 서부 관련 지역 추가
        if "서부" in expanded_regions:
            expanded_regions.extend(["서부", "제주시", "애월", "한림"])
        
        expanded_regions = list(dict.fromkeys(expanded_regions))  # 중복 제거
        logger.info(f"   📍 확대된 지역: {expanded_regions}")
        
        # 각 슬롯에 장소 찾기
        for slot in day_schedule.slots:
            place = None
            
            # 1차 시도: 확대된 지역에서 검색
            place = await self._find_place_for_slot(
                slot=slot,
                regions=expanded_regions,
                used_ids=used_place_ids,
                preferences=empty_preferences
            )
            
            # 2차 시도: 지역 조건 완전히 제거 (전체 제주도)
            if not place:
                logger.warning(f"   ⚠️ {slot.name} 슬롯에서 지역 조건 제거하여 재검색")
                place = await self._find_place_for_slot(
                    slot=slot,
                    regions=["제주시", "서귀포시", "동부", "서부"],  # 전체 제주도
                    used_ids=used_place_ids,
                    preferences=empty_preferences
            )
            
            # 3차 시도: place_type도 무시하고 아무 장소나 (최후의 수단)
            if not place:
                logger.warning(f"   ⚠️ {slot.name} 슬롯에서 타입 조건도 완화하여 재검색")
                # 슬롯 타입을 무시하고 맛집/카페/관광지 중 아무거나
                fallback_types = ["맛집", "카페", "관광지"]
                for fallback_type in fallback_types:
                    fallback_slot = TimeSlot(
                        name=slot.name,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        place_type=fallback_type,
                        duration_hours=slot.duration_hours
                    )
                    place = await self._find_place_for_slot(
                        slot=fallback_slot,
                        regions=["제주시", "서귀포시", "동부", "서부"],
                        used_ids=used_place_ids,
                        preferences=empty_preferences
                    )
                    if place:
                        break
            
            if place:
                places.append(place)
                if place.source == "postgresql":
                    used_place_ids.add(place.id)
                else:
                    self._used_es_doc_ids.add(place.id)
                logger.info(f"   ✅ {slot.name} → {place.name} ({place.region})")
            else:
                logger.error(f"   ❌ {slot.name} 슬롯에 장소를 찾을 수 없음")
        
        # 경로 최적화
        routes_data = None
        if places:
            places, routes_data = self._optimize_route(places, day_schedule.day)
        
        # 숙소
        accommodation = None
        if day_schedule.accommodation_region:
            accommodation = self._find_accommodation(
                day_schedule.accommodation_region,
                used_place_ids
            )
        
        logger.info(f"   ✅ Day {day_schedule.day} 강제 할당 완료: {len(places)}개 장소")
        day_itinerary = DayItinerary(
            day=day_schedule.day,
            date_label=f"Day {day_schedule.day}",
            regions=day_schedule.regions,
            places=places,
            accommodation=accommodation
        )
        
        return day_itinerary, routes_data
    
    async def _find_place_for_slot(
        self,
        slot: TimeSlot,
        regions: List[str],
        used_ids: set,
        preferences: Dict[str, Any]
    ) -> Optional[ScheduledPlace]:
        """시간대에 맞는 장소 찾기 (하이브리드)"""
        
        use_es_for_food = preferences.get("use_elasticsearch_for_food", False)
        subjective_keywords = preferences.get("subjective_keywords", [])
        
        # 관광지인 경우 Elasticsearch에서 검색
        if slot.place_type == "관광지":
            place = await self._find_attraction_from_elasticsearch(
                slot=slot,
                regions=regions
            )
            if place:
                return place
            # Elasticsearch에서 못 찾으면 PostgreSQL fallback
            logger.warning(f"   ⚠️ ES에서 관광지 못 찾음, PostgreSQL fallback")
            place = self._find_place_from_postgresql(
                slot=slot,
                regions=regions,
                used_ids=used_ids,
                preferences=preferences
            )
            if place:
                # 검증: 관광지 슬롯에 맛집이 할당되었는지 체크
                category_lower = (place.category or "").lower()
                food_keywords = ["맛집", "음식", "식당", "고기", "해물", "회", "해장국", "국수", "돈가스", "생선", "돼지", "한식", "중식", "일식", "양식"]
                if any(kw in category_lower for kw in food_keywords):
                    logger.error(f"   ❌ 관광지 슬롯에 맛집이 할당됨: {place.name} ({place.category}) - 재검색 시도")
                    return None  # 재검색 유도
                return place
            return None  # 관광지를 찾을 수 없음
        
        # 🆕 감성 조건이 있고 카페인 경우 → Elasticsearch에서 먼저 검색
        if use_es_for_food and slot.place_type in ["카페", "맛집"]:
            logger.info(f"   🎨 감성 검색: {subjective_keywords} → ES 사용")
            place = await self._find_food_from_elasticsearch(
                slot=slot,
                regions=regions,
                subjective_keywords=subjective_keywords
            )
            if place:
                return place
            logger.warning(f"   ⚠️ ES에서 {slot.place_type} 못 찾음, PostgreSQL fallback")
        
        # 맛집, 카페는 PostgreSQL에서 검색 (기본)
        return self._find_place_from_postgresql(
            slot=slot,
            regions=regions,
            used_ids=used_ids,
            preferences=preferences
        )
    
    async def _find_attraction_from_elasticsearch(
        self,
        slot: TimeSlot,
        regions: List[str]
    ) -> Optional[ScheduledPlace]:
        """Elasticsearch에서 관광지 검색 (가중 랜덤 선택으로 다양성 확보)"""
        try:
            retriever = get_retriever()
            
            # 지역 + 슬롯 hint 기반 쿼리 생성
            region_query = " ".join(regions)
            slot_hint = slot.name if slot.name else "관광지"
            query = f"{region_query} {slot_hint} 관광지 명소"
            
            logger.info(f"   🔍 ES 검색 (hint: {slot_hint}): '{query}'")
            
            # retrieve 메서드 호출 (더 많은 후보 가져오기)
            results, _ = await retriever.retrieve(query=query, num_results=30)
            
            logger.info(f"   📊 ES 결과: {len(results)}개")
            
            # 유효한 후보 필터링
            valid_candidates = []
            for result in results:
                doc_id = result.document_id
                if doc_id in self._used_es_doc_ids:
                    continue
                
                # 메타데이터에서 source_type 확인 (관광지만 허용)
                metadata = result.metadata or {}
                source_type = metadata.get("source_type", "")
                
                # 관광지 관련 타입만 허용 (맛집/카페, 숙박 제외)
                if source_type not in ["관광지", "축제/행사", "체험", "문화"]:
                    continue
                
                # 이상한 데이터 필터: 삭제요청, (중특), 폐업 등 제외
                title = metadata.get("title", "관광지")
                
                # 강화된 필터링: 이상한 데이터 제외
                bad_keywords = [
                    "삭제요청", "삭제", "(중특)", "테스트", "임시", "폐업", 
                    "펫플러스", "도그앤캣", "준비중", "공사중", "휴업",
                    "미운영", "폐점", "이전", "확인필요"
                ]
                if any(bad in title for bad in bad_keywords):
                    continue
                
                # 이름이 너무 짧거나 이상한 경우 제외
                if len(title) < 2 or title.count("삭제") > 0:
                    continue
                
                # 숫자로만 이루어진 이름 제외
                if title.replace(" ", "").isdigit():
                    continue
                
                # 이름 중복 체크
                if title in self._used_place_names:
                    continue
                
                # 유효한 후보로 추가
                valid_candidates.append({
                    "doc_id": doc_id,
                    "title": title,
                    "rating": metadata.get("rating") or 3.0,
                    "category": "관광지",
                    "lat": metadata.get("lat"),
                    "lng": metadata.get("lng"),
                    "metadata": metadata
                })
            
            if not valid_candidates:
                logger.warning(f"   ⚠️ ES에서 유효한 관광지 없음")
                return None
            
            logger.info(f"   📊 유효한 ES 후보: {len(valid_candidates)}개")
            
            # 가중 랜덤 선택 (다양성 확보, 관광지는 카테고리 패널티 없음)
            selected = self._weighted_random_select(valid_candidates, diversity_penalty=False)
            
            if not selected:
                return None
            
            title = selected["title"]
            logger.info(f"   ✅ ES 선택 (가중 랜덤): {title}")
            self._used_place_names.add(title)
            
            # 좌표가 없으면 카카오 키워드 검색으로 보정
            lat = selected.get("lat")
            lng = selected.get("lng")
            if not lat or not lng:
                from src.tool_agents.route_optimizer_agent.utils import search_kakao_place_coord
                lat, lng = search_kakao_place_coord(title, 33.4, 126.5)  # 제주 중심 좌표 fallback
                if lat != 33.4 or lng != 126.5:
                    logger.info(f"   📍 카카오에서 좌표 획득: {title} → ({lat:.4f}, {lng:.4f})")
            
            return ScheduledPlace(
                id=selected["doc_id"],
                name=title,
                category="관광지",
                rating=selected.get("rating"),
                region=regions[0],
                time_slot=slot.name,
                start_time=slot.start_time,
                end_time=slot.end_time,
                lat=lat,
                lng=lng,
                parking=None,
                kid_friendly=None,
                source="elasticsearch"
            )
            
        except Exception as e:
            logger.error(f"   ❌ ES 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _find_food_from_elasticsearch(
        self,
        slot: TimeSlot,
        regions: List[str],
        subjective_keywords: List[str]
    ) -> Optional[ScheduledPlace]:
        """Elasticsearch에서 카페/맛집 검색 (감성 조건 기반)"""
        try:
            retriever = get_retriever()
            
            # 쿼리 생성: 지역 + 슬롯 hint + 장소 유형 + 감성 키워드
            region_query = " ".join(regions)
            slot_hint = slot.name if slot.name else slot.place_type
            keywords_str = " ".join(subjective_keywords) if subjective_keywords else ""
            query = f"{region_query} {slot_hint} {slot.place_type} {keywords_str}".strip()
            
            logger.info(f"   🔍 ES 음식점 검색 (hint: {slot_hint}): '{query}'")
            
            # 검색 실행 (더 많은 후보)
            results, _ = await retriever.retrieve(query=query, num_results=30)
            
            logger.info(f"   📊 ES 결과: {len(results)}개")
            
            # 유효한 후보 필터링
            valid_candidates = []
            for result in results:
                doc_id = result.document_id
                
                # 중복 체크
                if doc_id in self._used_es_doc_ids:
                    continue
                
                metadata = result.metadata or {}
                title = metadata.get("title", "")
                category = metadata.get("category", "")
                
                # 카페/맛집 필터링 (food_ prefix로 시작하는 문서)
                if not doc_id.startswith("food_"):
                    continue
                
                # 타입 필터링 강화
                category_lower = category.lower()
                if slot.place_type == "카페":
                    # 카페 슬롯: 카페만 허용
                    if "카페" not in category_lower:
                        continue
                elif slot.place_type == "맛집":
                    # 맛집 슬롯: 카페만 있는 것은 제외 (맛집/카페는 허용)
                    if "카페" in category_lower and "맛집" not in category_lower and "음식" not in category_lower:
                        continue
                
                # 이상한 데이터 필터
                bad_keywords = ["삭제", "폐업", "준비중", "공사중", "휴업", "미운영"]
                if any(bad in title for bad in bad_keywords):
                    continue
                
                if len(title) < 2:
                    continue
                
                if title in self._used_place_names:
                    continue
                
                # 유효한 후보로 추가
                valid_candidates.append({
                    "doc_id": doc_id,
                    "title": title,
                    "rating": metadata.get("rating") or 4.0,
                    "category": category or slot.place_type,
                    "lat": metadata.get("lat"),
                    "lng": metadata.get("lng"),
                    "metadata": metadata
                })
            
            if not valid_candidates:
                logger.warning(f"   ⚠️ ES에서 유효한 {slot.place_type} 없음")
                return None
            
            logger.info(f"   📊 유효한 ES 후보: {len(valid_candidates)}개")
            
            # 가중 랜덤 선택
            selected = self._weighted_random_select(valid_candidates, diversity_penalty=True)
            
            if not selected:
                return None
            
            title = selected["title"]
            logger.info(f"   ✅ ES 음식점 선택: {title}")
            self._used_es_doc_ids.add(selected["doc_id"])
            self._used_place_names.add(title)
            
            return ScheduledPlace(
                id=selected["doc_id"],
                name=title,
                category=selected.get("category", slot.place_type),
                rating=selected.get("rating"),
                region=regions[0] if regions else "제주시",
                time_slot=slot.name,
                start_time=slot.start_time,
                end_time=slot.end_time,
                lat=selected.get("lat"),
                lng=selected.get("lng"),
                parking=None,
                kid_friendly=None,
                source="elasticsearch"
            )
            
        except Exception as e:
            logger.error(f"   ❌ ES 음식점 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _find_place_from_postgresql(
        self,
        slot: TimeSlot,
        regions: List[str],
        used_ids: set,
        preferences: Dict[str, Any]
    ) -> Optional[ScheduledPlace]:
        """PostgreSQL에서 장소 검색 (맛집, 카페) - 가중 랜덤 선택으로 다양성 확보"""
        
        # 장소 유형에 따른 카테고리 필터
        category_filter = self._get_category_filter(slot.place_type)
        
        # 지역 필터
        region_filter = " OR ".join([f"region = '{r}'" for r in regions])
        
        # 슬롯 hint 키워드 필터 (타입 강화)
        hint_filter = ""
        if slot.name and slot.name != slot.place_type:
            # hint에서 의미있는 키워드 추출
            hint_lower = slot.name.lower()
            
            # 타입 확인: 카페 슬롯에는 카페만, 맛집 슬롯에는 맛집만
            if slot.place_type == "카페":
                # 카페가 아닌 것 제외 (카테고리 필터로 이미 필터링되지만 추가 검증)
                hint_filter = " AND category ILIKE '%카페%'"
            elif slot.place_type == "맛집":
                # 카페가 아닌 것만 (카페는 맛집 슬롯에 배치 안 됨)
                hint_filter = " AND category NOT ILIKE '%카페%'"
        
        # 이미 사용된 장소 제외 (int만)
        exclude_filter = ""
        if used_ids:
            int_ids = [str(id) for id in used_ids if isinstance(id, int)]
            if int_ids:
                exclude_filter = f"AND id NOT IN ({','.join(int_ids)})"
        
        # 추가 조건 (아이 동반, 주차 등)
        pref_filter = ""
        if preferences.get("kid_friendly"):
            pref_filter += " AND kid_friendly = true"
        if preferences.get("parking"):
            pref_filter += " AND parking = true"
        
        # 더 많은 후보 가져오기 (다양성 확보를 위해 20개)
        query = text(f"""
            SELECT id, name, category, rating, region, parking, kid_friendly, lat, lng
            FROM places
            WHERE ({region_filter})
            AND ({category_filter})
            {hint_filter}
            {exclude_filter}
            {pref_filter}
            AND name NOT ILIKE '%호텔%'
            AND name NOT ILIKE '%리조트%'
            AND name NOT ILIKE '%펜션%'
            ORDER BY rating DESC NULLS LAST, review_count DESC NULLS LAST
            LIMIT 20
        """)
        
        try:
            with self.engine.connect() as conn:
                results = conn.execute(query).fetchall()
                
                # 유효한 후보 필터링 (이름 중복 제외 + 이상한 데이터 제외)
                valid_candidates = []
                for result in results:
                    name = result[1]
                    if name in self._used_place_names:
                        continue
                    
                    # 이상한 데이터 필터링
                    bad_keywords = [
                        "삭제", "테스트", "임시", "폐업", "준비중", "공사중",
                        "휴업", "미운영", "폐점", "이전", "확인필요"
                    ]
                    if any(bad in name for bad in bad_keywords):
                        continue
                    
                    # 이름이 너무 짧거나 이상한 경우 제외
                    if len(name) < 2:
                        continue
                    
                    valid_candidates.append({
                        "id": result[0],
                        "name": name,
                        "category": result[2],
                        "rating": float(result[3]) if result[3] else None,
                        "region": result[4] or "",
                        "parking": result[5],
                        "kid_friendly": result[6],
                        "lat": float(result[7]) if result[7] else None,
                        "lng": float(result[8]) if result[8] else None,
                    })
                
                if not valid_candidates:
                    logger.warning(f"   ⚠️ PG에서 유효한 {slot.place_type} 없음")
                    return None
                
                logger.info(f"   📊 유효한 PG 후보: {len(valid_candidates)}개 ({slot.place_type})")
                
                # 가중 랜덤 선택 (다양성 확보)
                selected = self._weighted_random_select(valid_candidates, diversity_penalty=True)
                
                if not selected:
                    return None
                
                # 최종 검증: type과 카테고리 일치 여부 확인
                category_lower = (selected.get("category") or "").lower()
                place_type = slot.place_type
                
                # 관광지 슬롯에 맛집이 할당되었는지 체크
                if place_type == "관광지":
                    food_keywords = ["맛집", "음식", "식당", "고기", "해물", "회", "해장국", "국수", "돈가스", "생선", "돼지", "한식", "중식", "일식", "양식", "카페"]
                    if any(kw in category_lower for kw in food_keywords):
                        logger.error(f"   ❌ 관광지 슬롯에 잘못된 타입 할당: {selected['name']} ({selected.get('category')}) - 필터링 실패")
                        # 필터링된 후보 중에서 다시 선택 (맛집 제외)
                        valid_candidates_filtered = [
                            c for c in valid_candidates 
                            if not any(kw in (c.get("category") or "").lower() for kw in food_keywords)
                        ]
                        if valid_candidates_filtered:
                            selected = self._weighted_random_select(valid_candidates_filtered, diversity_penalty=True)
                            if not selected:
                                return None
                        else:
                            logger.warning(f"   ⚠️ 관광지 후보가 모두 필터링됨")
                            return None
                
                # 맛집 슬롯에 카페만 있는 경우 체크
                elif place_type == "맛집":
                    if "카페" in category_lower and "맛집" not in category_lower and "음식" not in category_lower:
                        logger.warning(f"   ⚠️ 맛집 슬롯에 카페만 할당: {selected['name']} - 허용 (혼합 가능)")
                
                name = selected["name"]
                logger.info(f"   ✅ PG 선택 (가중 랜덤): {name} ({slot.place_type}, 카테고리: {selected.get('category')})")
                self._used_place_names.add(name)
                
                return ScheduledPlace(
                    id=selected["id"],
                    name=name,
                    category=selected["category"],
                    rating=selected["rating"],
                    region=selected["region"],
                    time_slot=slot.name,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    lat=selected["lat"],
                    lng=selected["lng"],
                    parking=selected["parking"],
                    kid_friendly=selected["kid_friendly"],
                    source="postgresql"
                )
                
        except Exception as e:
            logger.error(f"   ❌ PG 검색 오류: {e}")
        
        return None
    
    def _get_category_filter(self, place_type: str) -> str:
        """장소 유형에 따른 카테고리 필터 생성"""
        
        if place_type == "맛집":
            return """
                (category ILIKE '%고기%' OR category ILIKE '%한식%' OR 
                 category ILIKE '%중식%' OR category ILIKE '%일식%' OR 
                 category ILIKE '%양식%' OR category ILIKE '%회%' OR 
                 category ILIKE '%국수%' OR category ILIKE '%해물%' OR
                 category ILIKE '%해장국%' OR category ILIKE '%돈가스%' OR
                 category ILIKE '%생선%' OR category ILIKE '%분식%' OR
                 category ILIKE '%라면%' OR category ILIKE '%햄버거%')
            """
        elif place_type == "카페":
            return "category ILIKE '%카페%'"
        elif place_type == "관광지":
            return """
                (category ILIKE '%관광%' OR category ILIKE '%명소%' OR 
                 category ILIKE '%박물관%' OR category ILIKE '%해변%' OR
                 category ILIKE '%공원%' OR category ILIKE '%체험%' OR
                 category ILIKE '%테마파크%' OR category ILIKE '%오름%' OR
                 category ILIKE '%전망대%' OR category ILIKE '%동굴%' OR
                 category ILIKE '%폭포%' OR category ILIKE '%박물관%')
                AND category NOT ILIKE '%카페%'
                AND category NOT ILIKE '%맛집%'
                AND category NOT ILIKE '%음식%'
                AND category NOT ILIKE '%식당%'
                AND category NOT ILIKE '%고기%'
                AND category NOT ILIKE '%해물%'
                AND category NOT ILIKE '%회%'
                AND category NOT ILIKE '%해장국%'
                AND category NOT ILIKE '%국수%'
                AND category NOT ILIKE '%돈가스%'
                AND category NOT ILIKE '%생선%'
                AND category NOT ILIKE '%돼지%'
                AND category NOT ILIKE '%한식%'
                AND category NOT ILIKE '%중식%'
                AND category NOT ILIKE '%일식%'
                AND category NOT ILIKE '%양식%'
            """
        else:
            return "1=1"  # 모든 카테고리
    
    def _optimize_route(
        self,
        places: List[ScheduledPlace],
        day: int,
        use_road_distance: bool = True
    ) -> Tuple[List[ScheduledPlace], Optional[List[Dict[str, Any]]]]:
        """
        시간대별 장소 유형을 유지하면서 실제 도로 거리 기반 TSP 최적화
        
        카카오맵 API를 사용하여 자동차 도로 거리 기준으로 경로를 최적화합니다.
        API 호출 실패 시 직선 거리로 fallback합니다.
        
        시간대-장소유형 매핑:
        - 오전/오후: 관광지
        - 점심/저녁: 맛집
        - 카페: 카페
        
        ⚠️ 중요: 시간대별 장소 유형은 변경하지 않음!
        
        Returns:
            (최적화된 장소 리스트, 경로 데이터 리스트)
        """
        if len(places) < 2:
            return places, None
        
        # 좌표가 있는 장소만 필터링
        valid_places = [p for p in places if p.lat and p.lng]
        invalid_places = [p for p in places if not p.lat or not p.lng]
        
        if len(valid_places) < 2:
            logger.info(f"   🗺️ Day {day}: 좌표가 있는 장소가 부족하여 시간대 순서로 정렬")
            return self._sort_by_time_slot(places), None
        
        try:
            # 좌표 리스트 생성
            locations = [{"lat": p.lat, "lng": p.lng} for p in valid_places]
            
            # 카카오맵 API로 실제 도로 거리 행렬 생성
            logger.info(f"   🗺️ Day {day}: 카카오맵 API로 도로 거리 기반 경로 최적화 중...")
            distance_matrix = build_distance_matrix(locations, use_road_distance=use_road_distance)
            
            # TSP로 최적 순서 계산 (첫 번째 장소 고정)
            optimized_order, total_distance = nearest_neighbor_tsp(distance_matrix, start_index=0)
            
            # 최적화된 순서로 장소 재배열
            optimized_places = [valid_places[idx] for idx in optimized_order]
            
            # 시간대 재배정: 장소 유형에 맞는 time_slot 배정
            # 사용 가능한 슬롯 분류
            attraction_slots = []  # 관광지용 (오전, 오후)
            food_slots = []        # 맛집용 (점심, 저녁, 아침)
            cafe_slots = []        # 카페용 (카페, 간식)
            
            for p in valid_places:
                ts = p.time_slot
                if ts in ["오전", "오후"]:
                    if ts not in attraction_slots:
                        attraction_slots.append(ts)
                elif ts in ["점심", "저녁", "아침"]:
                    if ts not in food_slots:
                        food_slots.append(ts)
                elif ts in ["카페", "간식"]:
                    if ts not in cafe_slots:
                        cafe_slots.append(ts)
            
            # 슬롯 정렬
            slot_order = {"오전": 0, "아침": 0, "점심": 1, "오후": 2, "카페": 3, "간식": 3, "저녁": 4}
            attraction_slots.sort(key=lambda x: slot_order.get(x, 99))
            food_slots.sort(key=lambda x: slot_order.get(x, 99))
            cafe_slots.sort(key=lambda x: slot_order.get(x, 99))
            
            # 장소 유형별로 적절한 슬롯 배정
            attraction_idx = 0
            food_idx = 0
            cafe_idx = 0
            
            for place in optimized_places:
                category = (place.category or "").lower()
                
                # 카페인지 확인
                if "카페" in category or "디저트" in category or "베이커리" in category:
                    if cafe_idx < len(cafe_slots):
                        place.time_slot = cafe_slots[cafe_idx]
                        cafe_idx += 1
                    elif food_idx < len(food_slots):
                        place.time_slot = food_slots[food_idx]
                        food_idx += 1
                # 맛집인지 확인
                elif any(kw in category for kw in ["한식", "일식", "중식", "양식", "고기", "해물", "생선", "회", "국수", "돼지", "버거", "육류"]):
                    if food_idx < len(food_slots):
                        place.time_slot = food_slots[food_idx]
                        food_idx += 1
                    elif cafe_idx < len(cafe_slots):
                        place.time_slot = cafe_slots[cafe_idx]
                        cafe_idx += 1
                # 그 외는 관광지
                else:
                    if attraction_idx < len(attraction_slots):
                        place.time_slot = attraction_slots[attraction_idx]
                        attraction_idx += 1
                    elif food_idx < len(food_slots):
                        place.time_slot = food_slots[food_idx]
                        food_idx += 1
            
            # 최종 정렬: time_slot 순서대로
            optimized_places.sort(key=lambda p: slot_order.get(p.time_slot, 99))
            
            # 🆕 경로 정보 생성 (지도 표시용) - 장소명으로 카카오 POI 좌표 검색 후 길찾기
            routes_data = []
            for i in range(len(optimized_places) - 1):
                p1 = optimized_places[i]
                p2 = optimized_places[i + 1]
                
                # 장소명 기반 좌표 보정 후 길찾기 (성공률 향상)
                route_info = get_road_route_kakao_by_name(
                    p1.name, p1.lat, p1.lng,
                    p2.name, p2.lat, p2.lng
                )
                if route_info and route_info.get("path"):
                    routes_data.append({
                        "from_place": {"name": p1.name, "lat": p1.lat, "lng": p1.lng},
                        "to_place": {"name": p2.name, "lat": p2.lat, "lng": p2.lng},
                        "path": route_info["path"],
                        "distance": route_info.get("distance"),
                        "duration": route_info.get("duration")
                    })
                else:
                    # fallback: 직선 경로 + 추정 거리/시간
                    straight_dist = haversine_distance(p1.lat, p1.lng, p2.lat, p2.lng)
                    estimated_dist = straight_dist * 1.35  # 제주도 평균 우회 계수
                    estimated_dur = (estimated_dist / 40) * 60  # 평균 40km/h
                    
                    routes_data.append({
                        "from_place": {"name": p1.name, "lat": p1.lat, "lng": p1.lng},
                        "to_place": {"name": p2.name, "lat": p2.lat, "lng": p2.lng},
                        "path": [[p1.lat, p1.lng], [p2.lat, p2.lng]],
                        "distance": round(estimated_dist, 1),
                        "duration": round(estimated_dur, 0),
                        "is_estimated": True  # 추정치 표시
                    })
            
            logger.info(f"   ✅ Day {day}: 경로 최적화 완료 (총 {total_distance:.1f}km, {len(routes_data)}개 경로)")
            
            # 좌표 없는 장소는 뒤에 추가
            return optimized_places + invalid_places, routes_data
            
        except Exception as e:
            logger.warning(f"   ⚠️ Day {day}: 도로 거리 최적화 실패 ({e}), 시간대 순서로 정렬")
            return self._sort_by_time_slot(places), None
    
    def _sort_by_time_slot(self, places: List[ScheduledPlace]) -> List[ScheduledPlace]:
        """시간대 순서로만 정렬 (fallback)"""
        time_slot_order = {
            "오전": 0, "점심": 1, "오후": 2, "카페": 3, "저녁": 4,
            "아침": 0, "간식": 3
        }
        return sorted(places, key=lambda p: time_slot_order.get(p.time_slot, 99))
    
    def _find_accommodation(
        self,
        region: str,
        used_ids: set
    ) -> Optional[Dict[str, Any]]:
        """숙소 찾기"""
        
        exclude_filter = ""
        if used_ids:
            int_ids = [str(id) for id in used_ids if isinstance(id, int)]
            if int_ids:
                exclude_filter = f"AND id NOT IN ({','.join(int_ids)})"
        
        query = text(f"""
            SELECT id, name, category, rating, region, address, lat, lng
            FROM places
            WHERE region = :region
            AND (category ILIKE '%호텔%' OR category ILIKE '%리조트%' OR 
                 category ILIKE '%펜션%' OR category ILIKE '%게스트하우스%')
            {exclude_filter}
            ORDER BY rating DESC NULLS LAST
            LIMIT 1
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {"region": region}).fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "name": result[1],
                        "category": result[2],
                        "rating": float(result[3]) if result[3] else None,
                        "region": result[4],
                        "address": result[5],
                        "lat": float(result[6]) if result[6] else None,
                        "lng": float(result[7]) if result[7] else None
                    }
        except Exception as e:
            logger.error(f"숙소 검색 오류: {e}")
        
        return None
    
    def to_markdown(self, itinerary: List[DayItinerary]) -> str:
        """일정을 마크다운으로 변환"""
        lines = ["# 🗓️ 제주 여행 일정\n"]
        
        for day in itinerary:
            lines.append(f"\n## {day.date_label} ({', '.join(day.regions)})\n")
            
            for place in day.places:
                rating_str = f"⭐ {place.rating:.1f}" if place.rating else ""
                source_tag = "🔍" if place.source == "elasticsearch" else "🗄️"
                lines.append(
                    f"### {place.time_slot} ({place.start_time}~{place.end_time})\n"
                    f"**{place.name}** {rating_str} {source_tag}\n"
                    f"- 카테고리: {place.category}\n"
                    f"- 지역: {place.region}\n"
                )
            
            if day.accommodation:
                lines.append(
                    f"\n### 🏨 숙소\n"
                    f"**{day.accommodation['name']}**\n"
                    f"- {day.accommodation.get('address', '')}\n"
                )
        
        return "\n".join(lines)
    
    def to_json(self, itinerary: List[DayItinerary]) -> Dict[str, Any]:
        """일정을 JSON으로 변환"""
        return {
            "type": "itinerary",
            "total_days": len(itinerary),
            "days": [
                {
                    "day": day.day,
                    "label": day.date_label,
                    "regions": day.regions,
                    "places": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "category": p.category,
                            "rating": p.rating,
                            "region": p.region,
                            "time_slot": p.time_slot,
                            "start_time": p.start_time,
                            "end_time": p.end_time,
                            "lat": p.lat,
                            "lng": p.lng,
                            "parking": p.parking,
                            "kid_friendly": p.kid_friendly,
                            "source": p.source
                        }
                        for p in day.places
                    ],
                    "accommodation": day.accommodation
                }
                for day in itinerary
            ]
        }

