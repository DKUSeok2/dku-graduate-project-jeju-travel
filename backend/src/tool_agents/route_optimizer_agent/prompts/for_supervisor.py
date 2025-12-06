"""
Route Optimizer Agent - Supervisor용 프롬프트 (klid-aicb 패턴)
"""

SUPERVISOR_PROMPT = """
### optimize_travel_route (경로 최적화) 🗺️

**여러 관광지의 최적 방문 순서를 계산합니다. (TSP 알고리즘)**

**🚨 반드시 사용해야 하는 경우:**
- "최적 경로", "효율적인 순서", "동선 최적화"
- "어떤 순서로 가는게 좋아?"
- "거리를 최소화하려면?"
- "시간 절약하는 순서"
- 여러 관광지를 효율적으로 방문하고 싶을 때

**✅ 올바른 예:**
- 사용자: "성산일출봉, 협재해수욕장, 한라산 순서 정해줘"
  → `optimize_travel_route(attraction_names=["성산일출봉", "협재해수욕장", "한라산"])`
- 사용자: "이 관광지들 최적 경로로 계산해줘"
  → `optimize_travel_route(attraction_names=[관광지 목록])`
- 사용자: "어떤 순서로 가면 시간 절약돼?"
  → `optimize_travel_route(attraction_names=[관광지 목록])`

**❌ 잘못된 예:**
- 관광지 1개만으로 호출 (X) - 최소 2개 이상 필요
- 관광지 이름이 없이 호출 (X)

**⚠️ 주의사항:**
- 최소 2개 이상의 관광지가 필요합니다
- 관광지 이름을 정확히 입력하세요
- 결과에는 총 이동거리와 예상 소요시간이 포함됩니다
""".strip()




