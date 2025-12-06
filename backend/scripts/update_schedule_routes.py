"""
기존 일정들에 실제 도로 경로 데이터 추가
- 카카오 모빌리티 API로 도로 경로 가져오기
- map_data.routes 업데이트
"""
import asyncio
import json
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.config import settings
from src.tool_agents.route_optimizer_agent.utils import get_road_route_kakao_by_name, get_kakao_api_key, search_kakao_place_coord


def get_road_routes_for_day(places: list) -> list:
    """
    하루 일정의 장소들에 대해 도로 경로 가져오기
    
    Args:
        places: [{"name": str, "lat": float, "lng": float, ...}, ...]
    
    Returns:
        [{"from_place": {...}, "to_place": {...}, "path": [[lat, lng], ...], "distance": float, "duration": float}, ...]
    """
    routes = []
    
    for i in range(len(places) - 1):
        from_place = places[i]
        to_place = places[i + 1]
        
        # 좌표 확인 (없으면 카카오 검색)
        from_lat = from_place.get('lat') or from_place.get('position', {}).get('lat')
        from_lng = from_place.get('lng') or from_place.get('position', {}).get('lng')
        to_lat = to_place.get('lat') or to_place.get('position', {}).get('lat')
        to_lng = to_place.get('lng') or to_place.get('position', {}).get('lng')
        
        from_name = from_place.get('name', '')
        to_name = to_place.get('name', '')
        
        # 좌표가 없거나 기본값(33.4, 126.5 근처)이면 카카오 검색
        DEFAULT_LAT, DEFAULT_LNG = 33.4, 126.5
        
        if not from_lat or not from_lng or (abs(from_lat - DEFAULT_LAT) < 0.01 and abs(from_lng - DEFAULT_LNG) < 0.01):
            searched_lat, searched_lng = search_kakao_place_coord(from_name, 0, 0)
            if searched_lat and searched_lng:
                from_lat, from_lng = searched_lat, searched_lng
                print(f"   🔍 좌표 검색: {from_name} → ({from_lat:.4f}, {from_lng:.4f})")
        
        if not to_lat or not to_lng or (abs(to_lat - DEFAULT_LAT) < 0.01 and abs(to_lng - DEFAULT_LNG) < 0.01):
            searched_lat, searched_lng = search_kakao_place_coord(to_name, 0, 0)
            if searched_lat and searched_lng:
                to_lat, to_lng = searched_lat, searched_lng
                print(f"   🔍 좌표 검색: {to_name} → ({to_lat:.4f}, {to_lng:.4f})")
        
        if not all([from_lat, from_lng, to_lat, to_lng]):
            print(f"   ⚠️ 좌표 검색 실패: {from_name} → {to_name}")
            continue
        
        # 카카오 API로 도로 경로 가져오기
        route_info = get_road_route_kakao_by_name(
            from_place.get('name', ''), float(from_lat), float(from_lng),
            to_place.get('name', ''), float(to_lat), float(to_lng)
        )
        
        if route_info and route_info.get('path'):
            routes.append({
                "from_place": {"name": from_place.get('name'), "lat": float(from_lat), "lng": float(from_lng)},
                "to_place": {"name": to_place.get('name'), "lat": float(to_lat), "lng": float(to_lng)},
                "path": route_info["path"],
                "distance": route_info.get("distance", 0),
                "duration": route_info.get("duration", 0)
            })
            print(f"   ✅ {from_place.get('name')} → {to_place.get('name')}: {route_info['distance']:.1f}km")
        else:
            # fallback: 직선 경로
            routes.append({
                "from_place": {"name": from_place.get('name'), "lat": float(from_lat), "lng": float(from_lng)},
                "to_place": {"name": to_place.get('name'), "lat": float(to_lat), "lng": float(to_lng)},
                "path": [[float(from_lat), float(from_lng)], [float(to_lat), float(to_lng)]],
                "distance": 0,
                "duration": 0
            })
            print(f"   📍 {from_place.get('name')} → {to_place.get('name')}: 직선 (API 실패)")
    
    return routes


def update_schedule_routes():
    """모든 일정의 도로 경로 업데이트"""
    
    # API 키 확인
    api_key = get_kakao_api_key()
    if not api_key:
        print("❌ 카카오 API 키가 설정되지 않았습니다!")
        print("   .env 파일에 KAKAO_API_KEY를 설정해주세요.")
        return
    
    print("🚀 기존 일정 도로 경로 업데이트 시작")
    print(f"   카카오 API 키: {api_key[:10]}...")
    print()
    
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # 모든 일정 조회
        result = conn.execute(text("""
            SELECT id, title, attractions, map_data 
            FROM schedules 
            ORDER BY created_at DESC
        """))
        
        schedules = result.fetchall()
        print(f"📋 총 {len(schedules)}개 일정 발견\n")
        
        updated_count = 0
        skipped_count = 0
        
        for schedule in schedules:
            schedule_id = schedule[0]
            title = schedule[1]
            attractions = schedule[2]  # JSON
            map_data = schedule[3]  # JSON
            
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📅 [{schedule_id}] {title}")
            
            if not attractions:
                print("   ⏭️ attractions 없음, 스킵")
                skipped_count += 1
                continue
            
            # attractions가 문자열이면 JSON 파싱
            if isinstance(attractions, str):
                try:
                    attractions = json.loads(attractions)
                except:
                    print("   ⏭️ attractions 파싱 실패, 스킵")
                    skipped_count += 1
                    continue
            
            # map_data가 문자열이면 JSON 파싱
            if isinstance(map_data, str):
                try:
                    map_data = json.loads(map_data)
                except:
                    map_data = {}
            
            if not map_data:
                map_data = {}
            
            # 이미 routes가 있어도 직선 경로가 있으면 재생성
            has_straight_lines = False
            if map_data.get('routes'):
                for day_route in map_data['routes']:
                    for route in day_route.get('routes', []):
                        if len(route.get('path', [])) <= 2:
                            has_straight_lines = True
                            break
                    if has_straight_lines:
                        break
            
            if map_data.get('routes') and not has_straight_lines:
                print("   ⏭️ 이미 완전한 routes 있음, 스킵")
                skipped_count += 1
                continue
            
            if has_straight_lines:
                print("   ⚠️ 직선 경로 발견, 재생성 시도")
            
            # 일별 경로 생성
            all_routes = []
            
            for day_key, day_places in attractions.items():
                if not isinstance(day_places, list) or len(day_places) < 2:
                    continue
                
                day_num = int(day_key.replace('day', ''))
                print(f"\n   📆 Day {day_num}: {len(day_places)}개 장소")
                
                routes = get_road_routes_for_day(day_places)
                
                if routes:
                    all_routes.append({
                        "day": day_num,
                        "routes": routes
                    })
            
            if not all_routes:
                print("\n   ⏭️ 경로 생성 실패, 스킵")
                skipped_count += 1
                continue
            
            # map_data 업데이트
            map_data['routes'] = all_routes
            
            # markers가 없으면 생성
            if not map_data.get('markers'):
                markers = []
                for day_key, day_places in attractions.items():
                    if not isinstance(day_places, list):
                        continue
                    day_num = int(day_key.replace('day', ''))
                    for idx, place in enumerate(day_places):
                        lat = place.get('lat') or place.get('position', {}).get('lat')
                        lng = place.get('lng') or place.get('position', {}).get('lng')
                        if lat and lng:
                            markers.append({
                                "name": place.get('name'),
                                "lat": float(lat),
                                "lng": float(lng),
                                "day": day_num,
                                "order": idx + 1,
                                "category": place.get('category', '')
                            })
                map_data['markers'] = markers
                
                # center 계산
                if markers:
                    map_data['center'] = {
                        "lat": sum(m['lat'] for m in markers) / len(markers),
                        "lng": sum(m['lng'] for m in markers) / len(markers)
                    }
            
            # DB 업데이트
            conn.execute(text("""
                UPDATE schedules 
                SET map_data = :map_data 
                WHERE id = :id
            """), {"map_data": json.dumps(map_data, ensure_ascii=False), "id": schedule_id})
            conn.commit()
            
            print(f"\n   ✅ 업데이트 완료! ({len(all_routes)}일 경로)")
            updated_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎉 완료!")
    print(f"   - 업데이트: {updated_count}개")
    print(f"   - 스킵: {skipped_count}개")


if __name__ == "__main__":
    update_schedule_routes()

