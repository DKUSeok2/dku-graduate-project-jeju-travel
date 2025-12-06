"""
Route Optimizer Utilities - 거리 계산 및 경로 최적화 (OR-Tools 기반)
+ 실제 도로 거리 계산 (카카오맵 API)
"""
import math
from typing import List, Dict, Tuple, Optional
import logging
import httpx
import os

# OR-Tools 임포트
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logging.warning("OR-Tools not installed. Using fallback nearest neighbor algorithm.")

logger = logging.getLogger(__name__)

# 카카오맵 API 키 (환경변수 또는 설정에서 가져오기)
# config를 lazy import로 가져와서 순환 참조 방지
def get_kakao_api_key() -> Optional[str]:
    """카카오 API 키 가져오기"""
    try:
        from src.config import settings
        settings_key = settings.kakao_api_key
        env_key = os.getenv("KAKAO_API_KEY")
        key = settings_key or env_key
        
        # 🔥 디버깅: print()로 강제 출력
        print(f"🔑🔑🔑 KAKAO API KEY 디버깅:")
        print(f"   - settings.kakao_api_key: {'있음 (' + settings_key[:8] + '...)' if settings_key else 'None'}")
        print(f"   - os.getenv('KAKAO_API_KEY'): {'있음 (' + env_key[:8] + '...)' if env_key else 'None'}")
        print(f"   - 최종 key: {'있음' if key else 'None'}")
        
        return key
    except Exception as e:
        print(f"❌❌❌ 카카오 API 키 로드 실패: {e}")
        key = os.getenv("KAKAO_API_KEY")
        print(f"   - fallback os.getenv: {'있음' if key else 'None'}")
        return key

KAKAO_API_KEY = None  # lazy load


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Haversine 공식을 사용한 두 좌표 간 거리 계산 (km)
    
    Args:
        lat1, lng1: 첫 번째 지점의 위도, 경도
        lat2, lng2: 두 번째 지점의 위도, 경도
    
    Returns:
        두 지점 간의 거리 (km)
    """
    # 지구 반지름 (km)
    R = 6371.0
    
    # 라디안으로 변환
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # 차이 계산
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    # Haversine 공식
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def clean_place_name(name: str) -> str:
    """
    장소 이름에서 검색에 방해되는 텍스트 제거
    
    예: "제주목관아 야간개장" → "제주목관아"
        "협재해수욕장 본점" → "협재해수욕장"
        "그리스신화박물관 / 트릭아이미술관" → "그리스신화박물관"
    """
    import re
    
    # "/" 또는 "&"로 분리된 경우 첫 번째만 사용
    if '/' in name:
        name = name.split('/')[0].strip()
    if '&' in name:
        name = name.split('&')[0].strip()
    
    # 제거할 패턴들
    remove_patterns = [
        r'\s*야간개장\s*',
        r'\s*본점\s*',
        r'\s*지점\s*',
        r'\s*\d+호점\s*',
        r'\s*제주점\s*',
        r'\s*제주공항점\s*',
        r'\s*제주시점\s*',
        r'\s*서귀포점\s*',
        r'\s*애월점\s*',
        r'\s*함덕점\s*',
        r'\s*중문점\s*',
        r'\s*성산점\s*',
        r'\s*\(.*?\)\s*',  # 괄호 안 내용 제거
    ]
    
    cleaned = name
    for pattern in remove_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip() or name  # 빈 문자열이면 원본 반환


def search_kakao_place_coord(name: str, fallback_lat: float, fallback_lng: float) -> Tuple[float, float]:
    """
    카카오 키워드 검색 API로 도로 접근 가능한 좌표 가져오기
    
    카카오맵 앱처럼 장소 이름으로 검색하면 주차장/입구 등 
    도로에서 접근 가능한 좌표를 반환합니다.
    
    Args:
        name: 장소 이름 (예: "성산일출봉")
        fallback_lat: 검색 실패 시 사용할 위도
        fallback_lng: 검색 실패 시 사용할 경도
    
    Returns:
        (위도, 경도) 튜플
    """
    api_key = get_kakao_api_key()
    if not api_key:
        return fallback_lat, fallback_lng
    
    # 장소 이름 정제
    cleaned_name = clean_place_name(name)
    
    try:
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {api_key}"}
        # 제주도 내에서 검색 (더 정확한 결과)
        params = {
            "query": f"제주 {cleaned_name}",
            "size": 1
        }
        
        with httpx.Client(timeout=3.0) as client:
            response = client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                documents = data.get("documents", [])
                if documents:
                    # 카카오 POI 좌표 사용 (도로 접근 가능한 좌표)
                    kakao_lat = float(documents[0]["y"])
                    kakao_lng = float(documents[0]["x"])
                    logger.debug(f"카카오 POI 좌표 획득: {cleaned_name} → ({kakao_lat}, {kakao_lng})")
                    return kakao_lat, kakao_lng
                
                # 정제된 이름으로 실패 시 원본으로 재시도
                if cleaned_name != name:
                    params["query"] = f"제주 {name}"
                    response = client.get(url, headers=headers, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        documents = data.get("documents", [])
                        if documents:
                            kakao_lat = float(documents[0]["y"])
                            kakao_lng = float(documents[0]["x"])
                            logger.debug(f"카카오 POI 좌표 획득 (원본): {name} → ({kakao_lat}, {kakao_lng})")
                            return kakao_lat, kakao_lng
                            
    except Exception as e:
        logger.debug(f"카카오 키워드 검색 실패 ({name}): {e}")
    
    return fallback_lat, fallback_lng


def get_road_route_kakao_by_name(
    from_name: str, from_lat: float, from_lng: float,
    to_name: str, to_lat: float, to_lng: float
) -> Optional[Dict]:
    """
    장소 이름으로 카카오 POI 검색 후 길찾기 (더 정확한 좌표 사용)
    
    DB에 저장된 좌표가 도로에서 멀리 떨어져 있어도,
    카카오맵이 알고 있는 좌표(주차장/입구)로 변환하여 길찾기를 수행합니다.
    
    Args:
        from_name: 출발지 장소명
        from_lat, from_lng: 출발지 좌표 (fallback용)
        to_name: 도착지 장소명
        to_lat, to_lng: 도착지 좌표 (fallback용)
    
    Returns:
        {"distance": km, "duration": 분, "path": [[lat, lng], ...]} 또는 None
    """
    # 1. 카카오 POI 좌표로 변환 시도
    corrected_from_lat, corrected_from_lng = search_kakao_place_coord(from_name, from_lat, from_lng)
    corrected_to_lat, corrected_to_lng = search_kakao_place_coord(to_name, to_lat, to_lng)
    
    # 2. 변환된 좌표로 길찾기
    result = get_road_route_kakao(corrected_from_lat, corrected_from_lng, corrected_to_lat, corrected_to_lng)
    
    # 3. 실패 시 원본 좌표로 재시도 (혹시 모를 경우)
    if result is None and (corrected_from_lat != from_lat or corrected_to_lat != to_lat):
        logger.debug(f"보정 좌표 실패, 원본 좌표로 재시도: {from_name} → {to_name}")
        result = get_road_route_kakao(from_lat, from_lng, to_lat, to_lng)
    
    return result


def get_road_route_kakao(lat1: float, lng1: float, lat2: float, lng2: float) -> Optional[Dict]:
    """
    카카오맵 API를 사용한 실제 도로 경로 정보 가져오기
    
    Args:
        lat1, lng1: 출발지 위도, 경도
        lat2, lng2: 도착지 위도, 경도
    
    Returns:
        {"distance": km, "duration": 분, "path": [[lat, lng], ...]} 또는 None
    """
    api_key = get_kakao_api_key()
    if not api_key:
        logger.warning("❌ 카카오 API 키가 없어 경로 정보 가져오기 실패")
        return None
    
    try:
        url = "https://apis-navi.kakaomobility.com/v1/directions"
        headers = {
            "Authorization": f"KakaoAK {api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "origin": f"{lng1},{lat1}",
            "destination": f"{lng2},{lat2}"
        }
        
        print(f"🚗🚗🚗 카카오 길찾기 API 호출: {lat1},{lng1} → {lat2},{lng2}")
        
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, headers=headers, params=params)
            
            print(f"📡📡📡 카카오 API 응답: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                routes = data.get("routes", [])
                if routes and len(routes) > 0:
                    route = routes[0]
                    result_code = route.get("result_code", 0)
                    if result_code != 0:
                        result_msg = route.get("result_msg", "알 수 없는 오류")
                        print(f"❌❌❌ 카카오맵 경로 탐색 실패 (code: {result_code}): {result_msg}")
                        return None
                    
                    summary = route.get("summary", {})
                    distance_m = summary.get("distance", 0)
                    duration_s = summary.get("duration", 0)
                    
                    if distance_m == 0:
                        logger.debug("카카오맵 거리 정보 없음")
                        return None
                    
                    # 경로 좌표 추출
                    path_coordinates = []
                    sections = route.get("sections", [])
                    for section in sections:
                        roads = section.get("roads", [])
                        for road in roads:
                            # vertexes는 [lng1, lat1, lng2, lat2, ...] 형식의 플랫 리스트
                            vertexes = road.get("vertexes", [])
                            for i in range(0, len(vertexes), 2):
                                if i + 1 < len(vertexes):
                                    path_coordinates.append([vertexes[i+1], vertexes[i]])  # [lat, lng]
                    
                    print(f"✅✅✅ 카카오 길찾기 성공: {distance_m/1000:.1f}km, {len(path_coordinates)}개 좌표")
                    return {
                        "distance": distance_m / 1000.0,  # km
                        "duration": duration_s / 60.0,  # 분
                        "path": path_coordinates  # [[lat, lng], ...]
                    }
            else:
                print(f"❌❌❌ 카카오맵 API HTTP 오류: {response.status_code} - {response.text[:300]}")
                return None
                
    except Exception as e:
        print(f"❌❌❌ 카카오맵 API 예외: {e}")
        return None


def get_road_distance_kakao(lat1: float, lng1: float, lat2: float, lng2: float) -> Optional[float]:
    """
    카카오맵 API를 사용한 실제 도로 거리 계산 (km)
    
    Args:
        lat1, lng1: 출발지 위도, 경도
        lat2, lng2: 도착지 위도, 경도
    
    Returns:
        실제 도로 거리 (km), 실패 시 None
    """
    route_info = get_road_route_kakao(lat1, lng1, lat2, lng2)
    if route_info:
        return route_info["distance"]
    return None
    api_key = get_kakao_api_key()
    if not api_key:
        logger.debug("카카오 API 키가 없어 직선 거리 사용")
        return None
    
    try:
        url = "https://apis-navi.kakaomobility.com/v1/directions"
        headers = {
            "Authorization": f"KakaoAK {api_key}",
            "Content-Type": "application/json"
        }
        
        # 카카오맵 API 형식: origin=경도,위도&destination=경도,위도
        params = {
            "origin": f"{lng1},{lat1}",
            "destination": f"{lng2},{lat2}"
        }
        
        # 동기 요청 (httpx 사용)
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                routes = data.get("routes", [])
                if routes and len(routes) > 0:
                    route = routes[0]
                    # result_code 확인 (0이면 성공)
                    result_code = route.get("result_code", 0)
                    if result_code != 0:
                        # 경로를 찾을 수 없는 경우 (바다 위, 도로 없음 등)
                        result_msg = route.get("result_msg", "알 수 없는 오류")
                        logger.debug(f"카카오맵 경로 탐색 실패 (code: {result_code}): {result_msg}")
                        return None
                    
                    # 첫 번째 경로의 총 거리 (미터 단위)
                    summary = route.get("summary", {})
                    distance_m = summary.get("distance", 0)
                    if distance_m == 0:
                        logger.debug("카카오맵 거리 정보 없음")
                        return None
                    
                    distance_km = distance_m / 1000.0
                    logger.debug(f"카카오맵 도로 거리: {distance_km:.2f}km")
                    return distance_km
            else:
                logger.warning(f"카카오맵 API 오류: {response.status_code} - {response.text[:200]}")
                return None
                
    except Exception as e:
        logger.warning(f"카카오맵 API 호출 실패: {e}, 직선 거리 사용")
        return None


def build_distance_matrix(
    locations: List[Dict[str, float]], 
    use_road_distance: bool = True
) -> List[List[float]]:
    """
    위치 리스트로부터 거리 행렬 생성
    
    Args:
        locations: [{"lat": ..., "lng": ...}, ...] 형태의 위치 리스트
        use_road_distance: True면 실제 도로 거리 사용 (카카오맵 API), False면 직선 거리
    
    Returns:
        거리 행렬 (2D 리스트)
    """
    n = len(locations)
    distance_matrix = [[0.0] * n for _ in range(n)]
    
    # 실제 도로 거리 사용 여부 및 API 키 확인
    use_api = use_road_distance and get_kakao_api_key() is not None
    
    if use_api:
        logger.info(f"🛣️ 실제 도로 거리로 거리 행렬 생성 중... ({n}개 장소, {n*(n-1)//2}개 쌍)")
    else:
        logger.info(f"📍 직선 거리로 거리 행렬 생성 중... ({n}개 장소)")
    
    for i in range(n):
        for j in range(i + 1, n):
            if use_api:
                # 카카오맵 API로 실제 도로 거리 계산
                road_dist = get_road_distance_kakao(
                    locations[i]["lat"], locations[i]["lng"],
                    locations[j]["lat"], locations[j]["lng"]
                )
                
                if road_dist is not None:
                    dist = road_dist
                else:
                    # API 실패 시 직선 거리 fallback
                    dist = haversine_distance(
                        locations[i]["lat"], locations[i]["lng"],
                        locations[j]["lat"], locations[j]["lng"]
                    )
            else:
                # 직선 거리 사용
                dist = haversine_distance(
                    locations[i]["lat"], locations[i]["lng"],
                    locations[j]["lat"], locations[j]["lng"]
                )
            
            distance_matrix[i][j] = dist
            distance_matrix[j][i] = dist
    
    return distance_matrix


def nearest_neighbor_tsp(distance_matrix: List[List[float]], start_index: int = 0) -> Tuple[List[int], float]:
    """
    Nearest Neighbor 알고리즘으로 TSP 해결 (Fallback)
    
    Args:
        distance_matrix: 거리 행렬
        start_index: 시작 지점 인덱스
    
    Returns:
        (방문 순서, 총 거리)
    """
    n = len(distance_matrix)
    visited = [False] * n
    route = [start_index]
    visited[start_index] = True
    total_distance = 0.0
    
    current = start_index
    
    # n-1번 반복 (모든 지점 방문)
    for _ in range(n - 1):
        nearest_dist = float('inf')
        nearest_idx = -1
        
        # 방문하지 않은 지점 중 가장 가까운 곳 찾기
        for j in range(n):
            if not visited[j] and distance_matrix[current][j] < nearest_dist:
                nearest_dist = distance_matrix[current][j]
                nearest_idx = j
        
        if nearest_idx != -1:
            route.append(nearest_idx)
            visited[nearest_idx] = True
            total_distance += nearest_dist
            current = nearest_idx
    
    return route, total_distance


def ortools_tsp(distance_matrix: List[List[float]], start_index: int = 0) -> Tuple[List[int], float]:
    """
    OR-Tools를 사용한 TSP 최적 해결
    
    Args:
        distance_matrix: 거리 행렬 (km 단위)
        start_index: 시작 지점 인덱스
    
    Returns:
        (방문 순서, 총 거리)
    """
    if not ORTOOLS_AVAILABLE:
        logger.warning("OR-Tools not available, falling back to nearest neighbor")
        return nearest_neighbor_tsp(distance_matrix, start_index)
    
    n = len(distance_matrix)
    if n < 2:
        return [0], 0.0
    
    # 거리를 미터 단위 정수로 변환 (OR-Tools는 정수를 선호)
    # km → m (x 1000) 후 정수 변환
    int_matrix = [[int(dist * 1000) for dist in row] for row in distance_matrix]
    
    # OR-Tools 데이터 모델 생성
    def create_data_model():
        data = {}
        data['distance_matrix'] = int_matrix
        data['num_vehicles'] = 1
        data['depot'] = start_index
        return data
    
    data = create_data_model()
    
    # Routing Index Manager 생성
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),
        data['num_vehicles'],
        data['depot']
    )
    
    # Routing Model 생성
    routing = pywrapcp.RoutingModel(manager)
    
    # 거리 콜백 함수
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # 검색 파라미터 설정
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    
    # 더 나은 해를 찾기 위한 전략 설정
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 5  # 최대 5초
    search_parameters.log_search = False
    
    # 문제 해결
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        # 경로 추출
        route = []
        total_distance = 0
        index = routing.Start(0)
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
        
        # 미터 → km 변환
        total_distance_km = total_distance / 1000.0
        
        logger.info(f"✅ OR-Tools TSP 해결: {len(route)}개 노드, {total_distance_km:.2f}km")
        return route, total_distance_km
    else:
        logger.warning("OR-Tools failed to find solution, falling back to nearest neighbor")
        return nearest_neighbor_tsp(distance_matrix, start_index)


def solve_tsp(distance_matrix: List[List[float]], start_index: int = 0) -> Tuple[List[int], float]:
    """
    TSP 해결 - OR-Tools 사용 (가능한 경우), 아니면 Nearest Neighbor
    
    Args:
        distance_matrix: 거리 행렬
        start_index: 시작 지점 인덱스
    
    Returns:
        (방문 순서, 총 거리)
    """
    n = len(distance_matrix)
    
    # 장소가 2개 이하면 그냥 순차적으로
    if n <= 2:
        route = list(range(n))
        total_dist = sum(distance_matrix[i][i+1] for i in range(n-1)) if n > 1 else 0
        return route, total_dist
    
    # OR-Tools 사용 시도
    if ORTOOLS_AVAILABLE:
        logger.info(f"🚀 OR-Tools TSP 솔버 사용 ({n}개 장소)")
        return ortools_tsp(distance_matrix, start_index)
    else:
        logger.info(f"📍 Nearest Neighbor 사용 ({n}개 장소)")
        return nearest_neighbor_tsp(distance_matrix, start_index)


def calculate_travel_time(distance_km: float, avg_speed_kmh: float = 40.0) -> float:
    """
    거리를 기반으로 이동 시간 계산
    
    Args:
        distance_km: 거리 (km)
        avg_speed_kmh: 평균 속도 (km/h, 기본값: 40km/h - 제주도 일반 도로)
    
    Returns:
        이동 시간 (시간)
    """
    return distance_km / avg_speed_kmh


def format_time(hours: float) -> str:
    """
    시간을 "X시간 Y분" 형태로 포맷팅
    
    Args:
        hours: 시간 (float)
    
    Returns:
        포맷된 문자열
    """
    h = int(hours)
    m = int((hours - h) * 60)
    
    if h > 0 and m > 0:
        return f"{h}시간 {m}분"
    elif h > 0:
        return f"{h}시간"
    else:
        return f"{m}분"

