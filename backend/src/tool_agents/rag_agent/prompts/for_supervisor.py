"""
RAG Agent - Supervisor용 프롬프트 (klid-aicb 패턴)
"""

SUPERVISOR_PROMPT = """
### search_jeju_attractions (자연어 관광지 검색) 🔍

**자연어로 관광지를 검색합니다. (시맨틱 검색)**

**🚨 반드시 사용해야 하는 경우:**
- 느낌/분위기로 검색 (예: "일몰이 아름다운 해변", "힐링되는 곳")
- 특정 목적으로 검색 (예: "아이들과 함께 갈 수 있는 체험 시설")
- 추상적인 요구사항 (예: "사진 찍기 좋은 곳", "데이트 장소")
- 복합 조건 검색 (예: "가족 친화적이고 무료인 자연 명소")

**✅ 올바른 예:**
- 사용자: "일몰이 아름다운 해변 추천해줘"
  → `search_jeju_attractions(query="일몰이 아름다운 해변")`
- 사용자: "아이랑 갈만한 체험 장소"
  → `search_jeju_attractions(query="아이와 함께 갈 수 있는 체험 시설")`
- 사용자: "사진 찍기 좋은 곳"
  → `search_jeju_attractions(query="사진 찍기 좋은 곳")`
- 사용자: "힐링 여행"
  → `search_jeju_attractions(query="힐링되는 자연 명소")`

**❌ 잘못된 예:**
- 사용자: "성산일출봉 정보"
  → search_jeju_attractions (X) - 구체적인 이름은 query_jeju_database 사용!
- 사용자: "해변 카테고리 관광지"
  → search_jeju_attractions (X) - 카테고리 조회는 query_jeju_database 사용!

**⚠️ 주의사항:**
- 구체적인 관광지 이름이나 카테고리로 검색할 때는 query_jeju_database를 사용하세요
- 자연어로 느낌이나 특징을 검색할 때는 search_jeju_attractions를 사용하세요
""".strip()




