#!/usr/bin/env python
"""
VisitJeju JSON → PostgreSQL places 테이블 적재 스크립트

대상 파일:
- visitjeju_food.json (맛집/카페) → places 테이블
- visitjeju_hotel.json (숙박) → places 테이블

Usage:
    python scripts/data/load_visitjeju_to_postgres.py
    python scripts/data/load_visitjeju_to_postgres.py --dry-run
"""
import json
import re
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from sqlalchemy import create_engine, text
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터 디렉토리
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# 지역 추출을 위한 패턴
REGION_PATTERNS = {
    "제주시": ["제주시", "애월", "한림", "조천", "구좌", "우도", "한경", "추자"],
    "서귀포시": ["서귀포시", "중문", "성산", "표선", "남원", "대정", "안덕"],
    "동부": ["성산", "표선", "구좌", "우도"],
    "서부": ["한림", "한경", "대정", "애월"],
}


def extract_region(address: str) -> str:
    """주소에서 지역 추출"""
    if not address:
        return "제주시"
    
    # 동부/서부 우선 체크 (더 구체적인 지역)
    for region in ["동부", "서부"]:
        for keyword in REGION_PATTERNS[region]:
            if keyword in address:
                return region
    
    # 제주시/서귀포시 체크
    if "서귀포" in address:
        return "서귀포시"
    
    return "제주시"


def extract_category_from_tags(tags: str, source_type: str) -> str:
    """태그에서 카테고리 추출"""
    if not tags:
        return "기타"
    
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    
    # 음식점 카테고리
    food_keywords = {
        "한식": ["한식", "백반", "국수", "냉면", "해장국"],
        "중식": ["중식", "짬뽕", "짜장", "탕수육"],
        "일식": ["일식", "초밥", "라멘", "돈가스", "우동"],
        "양식": ["양식", "파스타", "스테이크", "피자", "버거", "햄버거"],
        "해물,생선요리": ["해물", "횟집", "회", "생선", "해산물", "전복", "문어"],
        "고기,구이": ["고기", "구이", "삼겹", "갈비", "불고기", "흑돼지"],
        "치킨": ["치킨", "후라이드"],
        "카페,디저트": ["카페", "디저트", "베이커리", "빵", "커피", "라떼"],
    }
    
    # 숙박 카테고리
    hotel_keywords = {
        "호텔": ["호텔"],
        "리조트": ["리조트"],
        "펜션": ["펜션"],
        "게스트하우스": ["게스트하우스", "게스트"],
        "민박": ["민박"],
    }
    
    keywords = hotel_keywords if source_type == "숙박" else food_keywords
    
    for category, kws in keywords.items():
        for kw in kws:
            for tag in tag_list:
                if kw in tag:
                    return category
    
    # 기본값
    return "숙박" if source_type == "숙박" else "기타"


def convert_to_place_record(item: Dict[str, Any], source_type: str) -> Optional[Dict[str, Any]]:
    """VisitJeju 항목을 places 테이블 레코드로 변환"""
    name = (item.get("이름") or "").strip()
    address = (item.get("주소") or "").strip()
    
    # 유효성 검사
    if not name or len(name) < 2:
        return None
    
    # 이상한 데이터 필터링
    bad_keywords = ["삭제", "준비중", "공사중", "폐업", "테스트", "샘플"]
    if any(kw in name for kw in bad_keywords):
        return None
    
    tags = item.get("태그") or ""
    category = extract_category_from_tags(tags, source_type)
    region = extract_region(address)
    
    # 전화번호 정리
    phone = item.get("전화번호") or ""
    if phone in ["--", "-", "null"]:
        phone = None
    elif phone:
        # 첫 번째 번호만 추출
        phone = phone.split(",")[0].strip()[:20]
    
    return {
        "naver_id": f"visitjeju_{hash(name + address) % 10**9}",
        "name": name[:255],
        "category": category[:100] if category else None,
        "address": address or None,
        "phone": phone,
        "rating": None,  # VisitJeju에는 평점 없음
        "review_count": 0,
        "region": region[:50] if region else None,
        "lat": None,  # 좌표 없음 (나중에 Geocoding 가능)
        "lng": None,
        "parking": None,
        "kid_friendly": None,
    }


def load_and_insert(filename: str, source_type: str, engine, dry_run: bool = False) -> int:
    """JSON 파일 로드 및 PostgreSQL 삽입"""
    filepath = DATA_DIR / filename
    
    if not filepath.exists():
        logger.warning(f"⚠️ 파일 없음: {filename}")
        return 0
    
    logger.info(f"📂 로딩: {filename}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"   원본 건수: {len(data)}")
    
    records = []
    skipped = 0
    
    for item in data:
        record = convert_to_place_record(item, source_type)
        if record:
            records.append(record)
        else:
            skipped += 1
    
    logger.info(f"   변환 완료: {len(records)}건 (스킵: {skipped}건)")
    
    if dry_run:
        logger.info(f"   [DRY RUN] 삽입 생략")
        return len(records)
    
    # PostgreSQL 삽입
    inserted = 0
    duplicates = 0
    
    with engine.connect() as conn:
        for record in records:
            try:
                # 중복 체크 (이름 + 주소)
                check_sql = text("""
                    SELECT id FROM places 
                    WHERE name = :name AND address = :address
                    LIMIT 1
                """)
                existing = conn.execute(check_sql, {
                    "name": record["name"],
                    "address": record["address"]
                }).fetchone()
                
                if existing:
                    duplicates += 1
                    continue
                
                # 삽입
                insert_sql = text("""
                    INSERT INTO places (naver_id, name, category, address, phone, rating, review_count, region, lat, lng, parking, kid_friendly)
                    VALUES (:naver_id, :name, :category, :address, :phone, :rating, :review_count, :region, :lat, :lng, :parking, :kid_friendly)
                """)
                conn.execute(insert_sql, record)
                inserted += 1
                
            except Exception as e:
                logger.warning(f"   삽입 실패 ({record['name']}): {e}")
        
        conn.commit()
    
    logger.info(f"   ✅ 삽입 완료: {inserted}건 (중복 스킵: {duplicates}건)")
    return inserted


def main(dry_run: bool = False):
    """메인 실행 함수"""
    logger.info("🚀 VisitJeju → PostgreSQL 적재 시작")
    
    if dry_run:
        logger.info("🔍 [DRY RUN 모드] 실제 삽입 없음")
    
    engine = create_engine(settings.database_url)
    
    total_inserted = 0
    
    # 맛집/카페
    total_inserted += load_and_insert("visitjeju_food.json", "맛집", engine, dry_run)
    
    # 숙박
    total_inserted += load_and_insert("visitjeju_hotel.json", "숙박", engine, dry_run)
    
    logger.info(f"\n📊 총 {total_inserted}건 삽입 완료!")
    
    # 현재 테이블 상태 확인
    if not dry_run:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM places"))
            total = result.scalar()
            logger.info(f"📈 places 테이블 총 건수: {total}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load VisitJeju to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="변환만 하고 삽입 안 함")
    args = parser.parse_args()
    
    main(dry_run=args.dry_run)




