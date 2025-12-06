"""
실제 도로 거리 계산 테스트 스크립트
"""
import asyncio
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tool_agents.route_optimizer_agent.utils import (
    haversine_distance,
    get_road_distance_kakao,
    build_distance_matrix,
    solve_tsp,
    get_kakao_api_key
)


def test_haversine_vs_road_distance():
    """직선 거리 vs 실제 도로 거리 비교 테스트"""
    
    # 제주도 주요 관광지 좌표 (실제 도로가 있는 좌표 사용)
    test_cases = [
        {
            "name1": "제주시청",
            "lat1": 33.4996,
            "lng1": 126.5311,
            "name2": "제주공항",
            "lat2": 33.5100,
            "lng2": 126.5189
        },
        {
            "name1": "제주시청",
            "lat1": 33.4996,
            "lng1": 126.5311,
            "name2": "서귀포시청",
            "lat2": 33.2541,
            "lng2": 126.5600
        },
        {
            "name1": "제주공항",
            "lat1": 33.5100,
            "lng1": 126.5189,
            "name2": "서귀포시청",
            "lat2": 33.2541,
            "lng2": 126.5600
        }
    ]
    
    print("=" * 60)
    print("직선 거리 vs 실제 도로 거리 비교 테스트")
    print("=" * 60)
    
    api_key = get_kakao_api_key()
    if api_key:
        print(f"✅ 카카오 API 키 확인됨")
    else:
        print(f"⚠️ 카카오 API 키 없음 - 직선 거리만 테스트")
    
    print()
    
    for i, case in enumerate(test_cases, 1):
        print(f"[테스트 {i}] {case['name1']} → {case['name2']}")
        
        # 직선 거리
        straight_dist = haversine_distance(
            case['lat1'], case['lng1'],
            case['lat2'], case['lng2']
        )
        print(f"  📏 직선 거리: {straight_dist:.2f}km")
        
        # 실제 도로 거리
        if api_key:
            road_dist = get_road_distance_kakao(
                case['lat1'], case['lng1'],
                case['lat2'], case['lng2']
            )
            if road_dist:
                print(f"  🛣️  실제 도로 거리: {road_dist:.2f}km")
                diff = road_dist - straight_dist
                diff_pct = (diff / straight_dist) * 100
                print(f"  📊 차이: {diff:+.2f}km ({diff_pct:+.1f}%)")
            else:
                print(f"  ⚠️  도로 거리 계산 실패 (직선 거리 사용)")
        else:
            print(f"  ⚠️  API 키 없어서 도로 거리 계산 불가")
        
        print()


def test_distance_matrix():
    """거리 행렬 생성 테스트"""
    
    print("=" * 60)
    print("거리 행렬 생성 테스트")
    print("=" * 60)
    
    # 제주도 주요 관광지 4곳
    locations = [
        {"name": "제주공항", "lat": 33.5113, "lng": 126.4930},
        {"name": "성산일출봉", "lat": 33.4581, "lng": 126.9425},
        {"name": "한라산", "lat": 33.3617, "lng": 126.5292},
        {"name": "천지연폭포", "lat": 33.2386, "lng": 126.5703}
    ]
    
    api_key = get_kakao_api_key()
    use_road = api_key is not None
    
    print(f"장소 수: {len(locations)}개")
    print(f"도로 거리 사용: {'예' if use_road else '아니오 (직선 거리)'}")
    print()
    
    # 직선 거리 행렬
    print("📍 직선 거리 행렬:")
    straight_matrix = build_distance_matrix(locations, use_road_distance=False)
    for i, loc1 in enumerate(locations):
        for j, loc2 in enumerate(locations):
            if i < j:
                print(f"  {loc1['name']} → {loc2['name']}: {straight_matrix[i][j]:.2f}km")
    print()
    
    # 실제 도로 거리 행렬 (API 키가 있는 경우)
    if use_road:
        print("🛣️  실제 도로 거리 행렬 (카카오맵 API):")
        road_matrix = build_distance_matrix(locations, use_road_distance=True)
        for i, loc1 in enumerate(locations):
            for j, loc2 in enumerate(locations):
                if i < j:
                    print(f"  {loc1['name']} → {loc2['name']}: {road_matrix[i][j]:.2f}km")
        print()


def test_tsp_optimization():
    """TSP 경로 최적화 테스트"""
    
    print("=" * 60)
    print("TSP 경로 최적화 테스트")
    print("=" * 60)
    
    # 제주도 주요 관광지 5곳
    locations = [
        {"name": "제주공항", "lat": 33.5113, "lng": 126.4930},
        {"name": "성산일출봉", "lat": 33.4581, "lng": 126.9425},
        {"name": "한라산", "lat": 33.3617, "lng": 126.5292},
        {"name": "천지연폭포", "lat": 33.2386, "lng": 126.5703},
        {"name": "협재해수욕장", "lat": 33.3938, "lng": 126.2400}
    ]
    
    api_key = get_kakao_api_key()
    use_road = api_key is not None
    
    print(f"장소 수: {len(locations)}개")
    print(f"도로 거리 사용: {'예' if use_road else '아니오 (직선 거리)'}")
    print()
    
    # 거리 행렬 생성
    distance_matrix = build_distance_matrix(locations, use_road_distance=use_road)
    
    # 원래 순서 (0 → 1 → 2 → 3 → 4)
    original_order = list(range(len(locations)))
    original_distance = sum(
        distance_matrix[original_order[i]][original_order[i+1]]
        for i in range(len(original_order) - 1)
    )
    
    print(f"📍 원래 순서:")
    for i, idx in enumerate(original_order):
        print(f"  {i+1}. {locations[idx]['name']}")
    print(f"  총 거리: {original_distance:.2f}km")
    print()
    
    # TSP 최적화
    optimized_order, optimized_distance = solve_tsp(distance_matrix, start_index=0)
    
    print(f"🚀 최적화된 순서:")
    for i, idx in enumerate(optimized_order):
        print(f"  {i+1}. {locations[idx]['name']}")
    print(f"  총 거리: {optimized_distance:.2f}km")
    print()
    
    saved = original_distance - optimized_distance
    saved_pct = (saved / original_distance) * 100 if original_distance > 0 else 0
    print(f"✅ 절약: {saved:.2f}km ({saved_pct:.1f}% 단축)")


if __name__ == "__main__":
    print("\n🧪 실제 도로 거리 계산 기능 테스트\n")
    
    try:
        # 1. 직선 거리 vs 실제 도로 거리 비교
        test_haversine_vs_road_distance()
        print("\n")
        
        # 2. 거리 행렬 생성 테스트
        test_distance_matrix()
        print("\n")
        
        # 3. TSP 최적화 테스트
        test_tsp_optimization()
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

