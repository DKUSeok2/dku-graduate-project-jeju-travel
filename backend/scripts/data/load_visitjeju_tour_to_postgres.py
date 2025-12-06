#!/usr/bin/env python
"""
Geocoding 완료된 VisitJeju 관광지 데이터 → PostgreSQL attractions 테이블 적재

입력 파일:
- visitjeju_tour_geocoded.json (좌표 포함)

Usage:
    # 1단계: 먼저 geocoding 실행
    python scripts/data/geocode_visitjeju_tour.py
    
    # 2단계: DB에 로드
    python scripts/data/load_visitjeju_tour_to_postgres.py
    python scripts/data/load_visitjeju_tour_to_postgres.py --dry-run
    python scripts/data/load_visitjeju_tour_to_postgres.py --clear  # 기존 데이터 삭제 후 로드
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from sqlalchemy import create_engine, text
from src.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 데이터 디렉토리
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_to_postgres(dry_run: bool = False, clear: bool = False):
    """Geocoded 데이터를 PostgreSQL에 로드"""
    
    input_file = DATA_DIR / "visitjeju_tour_geocoded.json"
    
    if not input_file.exists():
        logger.error(f"❌ 입력 파일 없음: {input_file}")
        logger.info("   먼저 geocoding을 실행하세요:")
        logger.info("   python scripts/data/geocode_visitjeju_tour.py")
        return 0
    
    logger.info(f"📂 입력 파일: {input_file}")
    
    # 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    logger.info(f"   로드된 건수: {len(records)}건")
    
    # 좌표 확인
    valid_records = [r for r in records if r.get("lat") and r.get("lng")]
    logger.info(f"   좌표 있는 건수: {len(valid_records)}건")
    
    if len(valid_records) == 0:
        logger.error("❌ 좌표가 있는 데이터가 없습니다!")
        return 0
    
    # 카테고리별 통계
    category_stats = {}
    for r in valid_records:
        cat = r["category"]
        category_stats[cat] = category_stats.get(cat, 0) + 1
    logger.info(f"   카테고리별: {category_stats}")
    
    if dry_run:
        logger.info("\n🔍 [DRY RUN] 실제 삽입 없음")
        
        # 샘플 출력
        logger.info("\n📋 샘플 데이터 (각 카테고리 3개씩):")
        for cat in ["자연", "문화", "해변", "액티비티"]:
            samples = [r for r in valid_records if r["category"] == cat][:3]
            logger.info(f"\n   [{cat}]")
            for s in samples:
                logger.info(f"      - {s['name']} ({s['region']}) [{s['lat']:.4f}, {s['lng']:.4f}]")
        
        return len(valid_records)
    
    # PostgreSQL 연결
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # 기존 데이터 삭제 (옵션)
        if clear:
            logger.info("\n🗑️ 기존 attractions 데이터 삭제...")
            conn.execute(text("DELETE FROM attractions"))
            conn.commit()
            logger.info("   삭제 완료")
        
        # 삽입
        logger.info(f"\n💾 PostgreSQL 삽입 시작...")
        
        inserted = 0
        updated = 0
        errors = 0
        
        for record in tqdm(valid_records, desc="DB 삽입"):
            try:
                # 이미 존재하는지 확인 (이름으로)
                exists = conn.execute(text("""
                    SELECT id FROM attractions WHERE name = :name
                """), {'name': record["name"]}).fetchone()
                
                # 태그를 PostgreSQL 배열 형식으로 변환
                tags_list = record.get("tags", [])
                tags_sql = "{" + ",".join(f'"{t}"' for t in tags_list) + "}" if tags_list else None
                
                if exists:
                    # 업데이트
                    conn.execute(text("""
                        UPDATE attractions 
                        SET lat = :lat,
                            lng = :lng,
                            category = :category,
                            address = COALESCE(:address, address),
                            description = COALESCE(:description, description),
                            phone = COALESCE(:phone, phone),
                            kid_friendly = :kid_friendly,
                            tags = :tags
                        WHERE name = :name
                    """), {
                        "name": record["name"],
                        "category": record["category"],
                        "address": record.get("address"),
                        "phone": record.get("phone"),
                        "description": record.get("description"),
                        "kid_friendly": record.get("kid_friendly", False),
                        "tags": tags_sql,
                        "lat": record["lat"],
                        "lng": record["lng"],
                    })
                    updated += 1
                else:
                    # 새로 삽입
                    conn.execute(text("""
                        INSERT INTO attractions (
                            name, category, address, phone, avg_rating, 
                            description, tags, kid_friendly, lat, lng
                        ) VALUES (
                            :name, :category, :address, :phone, :avg_rating,
                            :description, :tags, :kid_friendly, :lat, :lng
                        )
                    """), {
                        "name": record["name"],
                        "category": record["category"],
                        "address": record.get("address"),
                        "phone": record.get("phone"),
                        "avg_rating": None,
                        "description": record.get("description"),
                        "tags": tags_sql,
                        "kid_friendly": record.get("kid_friendly", False),
                        "lat": record["lat"],
                        "lng": record["lng"],
                    })
                    inserted += 1
                    
            except Exception as e:
                if errors < 5:
                    logger.warning(f"   오류 ({record['name']}): {e}")
                errors += 1
        
        conn.commit()
    
    logger.info(f"\n✅ 완료!")
    logger.info(f"   새로 삽입: {inserted}건")
    logger.info(f"   업데이트: {updated}건")
    logger.info(f"   오류: {errors}건")
    
    # 최종 통계
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT category, COUNT(*) as cnt 
            FROM attractions 
            GROUP BY category 
            ORDER BY cnt DESC
        """))
        logger.info(f"\n📊 attractions 테이블 현재 상태:")
        for row in result:
            logger.info(f"   - {row[0]}: {row[1]}개")
        
        total = conn.execute(text("SELECT COUNT(*) FROM attractions")).scalar()
        logger.info(f"   총계: {total}개")
        
        with_coords = conn.execute(text("""
            SELECT COUNT(*) FROM attractions WHERE lat IS NOT NULL AND lng IS NOT NULL
        """)).scalar()
        if total > 0:
            logger.info(f"   좌표 있음: {with_coords}개 ({with_coords/total*100:.1f}%)")
    
    return inserted


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Load geocoded VisitJeju Tour to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="실제 삽입 없이 확인만")
    parser.add_argument("--clear", action="store_true", help="기존 데이터 삭제 후 로드")
    args = parser.parse_args()
    
    logger.info("🚀 VisitJeju Tour → PostgreSQL attractions 적재")
    logger.info("=" * 60)
    
    load_to_postgres(dry_run=args.dry_run, clear=args.clear)


if __name__ == "__main__":
    main()
