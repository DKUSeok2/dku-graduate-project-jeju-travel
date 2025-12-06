#!/usr/bin/env python
"""
VisitJeju 관광지 데이터에 좌표(geocoding) 추가

카카오 API를 사용하여 주소/이름으로 좌표를 찾아서 JSON 파일로 저장

Usage:
    python scripts/data/geocode_visitjeju_tour.py
    python scripts/data/geocode_visitjeju_tour.py --limit 100  # 100개만 처리
    python scripts/data/geocode_visitjeju_tour.py --resume     # 이어서 처리

Output:
    data/visitjeju_tour_geocoded.json
"""
import json
import logging
import sys
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from src.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 데이터 디렉토리
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# 카카오 API 키 (환경변수 또는 하드코딩)
KAKAO_API_KEY = settings.kakao_api_key or '29b88d36376b65d78516805b0ee8ff3b'

# ============================================================================
# 카테고리 분류 기준 (load_visitjeju_tour_to_postgres.py와 동일)
# ============================================================================

CATEGORY_KEYWORDS = {
    "해변": [
        "해변", "해수욕장", "해안", "바다", "포구", "등대", "섬", "갯벌",
        "해안도로", "해안절경", "해녀", "바닷가", "물놀이",
    ],
    "자연": [
        "오름", "폭포", "숲", "계곡", "동굴", "용암", "현무암", "습지",
        "자연경관", "자연명소", "휴양림", "산림욕", "수목원", "식물원",
        "공원", "정원", "산책로", "생태", "철새", "곶자왈", "한라산",
        "올레길", "트레킹", "등산", "걷기", "도보", "탐방로",
        "일출", "일몰", "전망대", "경관",
    ],
    "문화": [
        "박물관", "미술관", "전시관", "기념관", "갤러리", "화랑",
        "문화유적", "유적지", "사찰", "절", "역사", "유산",
        "마을", "전통", "민속", "공연", "예술", "문화공간",
        "테마파크", "테마관", "아쿠아리움", "수족관", "동물원",
    ],
    "액티비티": [
        "체험", "액티비티", "레저", "스포츠",
        "스쿠버", "다이빙", "프리다이빙", "스노클링",
        "서핑", "윈드서핑", "카약", "요트", "보트", "낚시", "해양레저",
        "승마", "말", "골프", "카트", "ATV", "짚라인",
        "패러글라이딩", "행글라이딩",
        "원데이클래스", "공방", "만들기", "제작",
        "농장", "목장", "관광농원", "팜",
    ],
}

EXCLUDE_KEYWORDS = [
    "동물병원", "애견미용", "애견유치원", "애견호텔", "반려동물병원",
    "수제간식", "애견", "미용실", "유치원", "호텔", "리조트", "펜션",
    "게스트하우스", "숙박", "민박", "카페", "음식점", "맛집",
    "식당", "레스토랑", "베이커리", "빵집", "커피",
]


def should_exclude(tags: str, name: str) -> bool:
    """제외해야 할 항목인지 확인"""
    text = f"{tags} {name}".lower()
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in text:
            return True
    return False


def classify_category(tags: str, name: str, description: str) -> Optional[str]:
    """태그와 이름에서 카테고리 분류"""
    if not tags:
        return None
    
    text = f"{tags} {name} {description}".lower()
    scores = {"해변": 0, "자연": 0, "문화": 0, "액티비티": 0}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[category] += 1
    
    max_score = max(scores.values())
    if max_score == 0:
        return None
    
    priority = ["해변", "액티비티", "자연", "문화"]
    for cat in priority:
        if scores[cat] == max_score:
            return cat
    
    return None


def extract_region(address: str) -> str:
    """주소에서 지역 추출"""
    if not address:
        return "제주시"
    
    east_keywords = ["성산", "표선", "구좌", "우도", "조천"]
    west_keywords = ["한림", "한경", "대정", "애월", "협재"]
    
    for keyword in east_keywords:
        if keyword in address:
            return "동부"
    for keyword in west_keywords:
        if keyword in address:
            return "서부"
    if "서귀포" in address:
        return "서귀포시"
    
    return "제주시"


# ============================================================================
# Geocoding (카카오 API)
# ============================================================================

def get_coords_from_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """주소로 좌표 검색"""
    if not address or not KAKAO_API_KEY:
        return None, None
    
    url = 'https://dapi.kakao.com/v2/local/search/address.json'
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    params = {'query': address}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data.get('documents'):
            doc = data['documents'][0]
            return float(doc['y']), float(doc['x'])
    except Exception as e:
        logger.debug(f"주소 검색 실패 ({address}): {e}")
    
    return None, None


def get_coords_from_keyword(name: str) -> Tuple[Optional[float], Optional[float]]:
    """키워드로 좌표 검색"""
    if not name or not KAKAO_API_KEY:
        return None, None
    
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    
    # 제주도 범위로 제한
    params = {
        'query': f'{name} 제주',
        'x': '126.5312',
        'y': '33.4996',
        'radius': 50000
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data.get('documents'):
            doc = data['documents'][0]
            return float(doc['y']), float(doc['x'])
    except Exception as e:
        logger.debug(f"키워드 검색 실패 ({name}): {e}")
    
    return None, None


def geocode_place(name: str, address: str) -> Tuple[Optional[float], Optional[float]]:
    """장소 좌표 찾기 (주소 → 키워드 순서로 시도)"""
    lat, lng = None, None
    
    # 1. 주소로 검색
    if address:
        lat, lng = get_coords_from_address(address)
    
    # 2. 실패하면 키워드로 검색
    if lat is None:
        lat, lng = get_coords_from_keyword(name)
    
    return lat, lng


# ============================================================================
# 메인 처리
# ============================================================================

def process_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """VisitJeju 항목을 처리하여 좌표 포함 레코드 생성"""
    name = (item.get("이름") or "").strip()
    address = (item.get("주소") or "").strip()
    tags = item.get("태그") or ""
    description = (item.get("소개") or "").strip()
    
    # 유효성 검사
    if not name or len(name) < 2:
        return None
    
    # 이상한 데이터 필터링
    bad_keywords = ["삭제", "준비중", "공사중", "폐업", "테스트", "샘플"]
    if any(kw in name for kw in bad_keywords):
        return None
    
    # 제외 대상 체크
    if should_exclude(tags, name):
        return None
    
    # 카테고리 분류
    category = classify_category(tags, name, description)
    if not category:
        return None
    
    # 지역 추출
    region = extract_region(address)
    
    # 전화번호 정리
    phone = item.get("전화번호") or ""
    if phone in ["--", "-", "null", None]:
        phone = None
    elif phone:
        phone = phone.split(",")[0].strip()[:20]
    
    # 아이 동반 여부
    kid_friendly = any(kw in tags.lower() for kw in ["아이", "가족", "어린이", "키즈", "체험"])
    
    # 태그 리스트
    tags_list = [t.strip() for t in tags.split(",") if t.strip()][:10]
    
    return {
        "name": name[:100],
        "category": category,
        "address": address or None,
        "phone": phone,
        "description": description[:1000] if description else None,
        "tags": tags_list,
        "kid_friendly": kid_friendly,
        "region": region,
        "lat": None,
        "lng": None,
    }


def geocode_visitjeju_tour(limit: Optional[int] = None, resume: bool = False):
    """VisitJeju 관광지 데이터에 좌표 추가"""
    
    input_file = DATA_DIR / "visitjeju_tour.json"
    output_file = DATA_DIR / "visitjeju_tour_geocoded.json"
    
    if not input_file.exists():
        logger.error(f"❌ 입력 파일 없음: {input_file}")
        return
    
    logger.info(f"📂 입력 파일: {input_file}")
    
    # 원본 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    logger.info(f"   원본 건수: {len(raw_data)}")
    
    # 기존 결과 로드 (resume 모드)
    existing_data = {}
    if resume and output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            existing_data = {item["name"]: item for item in existing}
        logger.info(f"   기존 결과: {len(existing_data)}건 로드됨")
    
    # 필터링 및 변환
    records = []
    excluded = {"숙박/음식점": 0, "분류불가": 0}
    
    for item in raw_data:
        name = item.get("이름", "")
        tags = item.get("태그", "")
        
        if should_exclude(tags, name):
            excluded["숙박/음식점"] += 1
            continue
        
        record = process_item(item)
        if record:
            records.append(record)
        else:
            excluded["분류불가"] += 1
    
    logger.info(f"   변환 완료: {len(records)}건")
    logger.info(f"   제외됨: {excluded}")
    
    if limit:
        records = records[:limit]
        logger.info(f"   제한 적용: {limit}건")
    
    # 카테고리별 통계
    category_stats = {}
    for r in records:
        cat = r["category"]
        category_stats[cat] = category_stats.get(cat, 0) + 1
    logger.info(f"   카테고리별: {category_stats}")
    
    # Geocoding
    logger.info(f"\n🗺️ Geocoding 시작...")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for record in tqdm(records, desc="좌표 변환"):
        # resume 모드: 이미 좌표가 있으면 건너뛰기
        if record["name"] in existing_data:
            existing = existing_data[record["name"]]
            if existing.get("lat") and existing.get("lng"):
                record["lat"] = existing["lat"]
                record["lng"] = existing["lng"]
                skip_count += 1
                continue
        
        # Geocoding
        lat, lng = geocode_place(record["name"], record["address"])
        
        if lat and lng:
            record["lat"] = lat
            record["lng"] = lng
            success_count += 1
        else:
            fail_count += 1
        
        # API 제한 방지 (초당 10회)
        time.sleep(0.1)
    
    logger.info(f"\n✅ Geocoding 완료!")
    logger.info(f"   성공: {success_count}건")
    logger.info(f"   스킵(기존): {skip_count}건")
    logger.info(f"   실패: {fail_count}건")
    
    # 좌표가 있는 데이터만 필터링
    records_with_coords = [r for r in records if r["lat"] and r["lng"]]
    records_without_coords = [r for r in records if not r["lat"] or not r["lng"]]
    
    logger.info(f"\n📊 결과:")
    logger.info(f"   좌표 있음: {len(records_with_coords)}건")
    logger.info(f"   좌표 없음: {len(records_without_coords)}건")
    
    # 카테고리별 (좌표 있는 것만)
    category_stats_final = {}
    for r in records_with_coords:
        cat = r["category"]
        category_stats_final[cat] = category_stats_final.get(cat, 0) + 1
    logger.info(f"   카테고리별 (좌표 있음): {category_stats_final}")
    
    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records_with_coords, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n💾 저장 완료: {output_file}")
    logger.info(f"   총 {len(records_with_coords)}건 저장됨")
    
    # 좌표 없는 데이터도 별도 저장 (디버깅용)
    if records_without_coords:
        fail_file = DATA_DIR / "visitjeju_tour_no_coords.json"
        with open(fail_file, 'w', encoding='utf-8') as f:
            json.dump(records_without_coords, f, ensure_ascii=False, indent=2)
        logger.info(f"   좌표 없는 데이터: {fail_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Geocode VisitJeju Tour data")
    parser.add_argument("--limit", type=int, default=None, help="처리할 최대 건수")
    parser.add_argument("--resume", action="store_true", help="기존 결과 이어서 처리")
    args = parser.parse_args()
    
    logger.info("🚀 VisitJeju Tour Geocoding 시작")
    logger.info("=" * 60)
    
    if not KAKAO_API_KEY:
        logger.error("❌ KAKAO_API_KEY가 설정되지 않았습니다!")
        return
    
    geocode_visitjeju_tour(limit=args.limit, resume=args.resume)


if __name__ == "__main__":
    main()


