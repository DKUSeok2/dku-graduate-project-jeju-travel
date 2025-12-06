"""
Map Visualization Agent - Supervisor용 프롬프트 (klid-aicb 패턴)
"""

SUPERVISOR_PROMPT = """
### visualize_attractions_on_map (지도 시각화) 🗺️

**관광지를 지도에 표시합니다.**

**🚨 반드시 사용해야 하는 경우:**
- "지도에 표시해줘"
- "위치 보여줘"
- "어디에 있어?"
- "지도로 보고싶어"
- "어디 있는지 알려줘"

**✅ 올바른 예:**
- 사용자: "해변 관광지 지도에 표시해줘"
  → `visualize_attractions_on_map(query="해변 관광지")`
- 사용자: "평점 높은 곳 위치 보여줘"
  → `visualize_attractions_on_map(query="평점 높은 관광지")`
- 사용자: "제주시 동쪽 관광지 어디 있어?"
  → `visualize_attractions_on_map(query="제주시 동쪽 관광지")`

**❌ 잘못된 예:**
- 사용자가 단순히 정보만 요청 (X) - 지도 관련 키워드가 있을 때만
- "성산일출봉 정보 알려줘" (X) - 단순 정보는 query_jeju_database 사용

**⚠️ 주의사항:**
- 지도 시각화는 관광지 조회와 **별도로** 호출됩니다
- 사용자가 명시적으로 "지도", "위치" 요청 시에만 사용하세요
- [MAP_DATA] 같은 마커는 응답에 포함하지 마세요
""".strip()




