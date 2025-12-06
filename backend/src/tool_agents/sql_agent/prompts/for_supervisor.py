"""
SQL Agent - Supervisor용 프롬프트 (klid-aicb 패턴)
"""

SUPERVISOR_PROMPT = """
### query_jeju_database (관광지 DB 조회) 🗄️

**제주도 관광지 데이터베이스를 조회합니다.**

**🚨 반드시 사용해야 하는 경우:**
- 특정 관광지 이름으로 검색 (예: "성산일출봉", "한라산")
- 카테고리별 조회 (예: "해변", "자연", "박물관")
- 평점 필터링 (예: "평점 4.5 이상")
- 가격 조건 (예: "무료 관광지", "5000원 이하")
- 아이 친화적 여부 (예: "아이랑 갈만한 곳")
- 기본 정보 조회 (위치, 주소, 좌표)

**✅ 올바른 예:**
- 사용자: "성산일출봉 정보 알려줘"
  → `query_jeju_database(query="성산일출봉 정보")`
- 사용자: "해변 카테고리 관광지 추천해줘"
  → `query_jeju_database(query="해변 카테고리 관광지")`
- 사용자: "평점 4.5 이상인 곳"
  → `query_jeju_database(query="평점 4.5 이상인 관광지")`
- 사용자: "무료로 갈 수 있는 관광지"
  → `query_jeju_database(query="무료 관광지")`

**❌ 잘못된 예:**
- 사용자: "제주도 맛집 추천해줘"
  → query_jeju_database (X) - 맛집 추천은 웹 검색(search_realtime_info)이 적합!
- 사용자: "인기 카페 알려줘"
  → query_jeju_database (X) - 인기/추천은 웹 검색!
- 사용자: "오늘 날씨"
  → query_jeju_database (X) - 실시간 정보는 웹 검색!

**⚠️ 주의사항:**
- SQL 쿼리문은 응답에 포함하지 마세요
- [ATTRACTIONS_DATA], [SQL_QUERY_RESULT] 같은 마커는 응답에 포함하지 마세요
- 자연스러운 대화체로 답변하세요
- 조회 결과를 바탕으로 친절하게 안내하세요
""".strip()




