"""
places 테이블에 region 컬럼 추가 및 데이터 업데이트
주소 기반으로 지역을 분류합니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.config import settings


def add_region_column():
    """places 테이블에 region 컬럼 추가"""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # 1. region 컬럼이 이미 있는지 확인
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'places' AND column_name = 'region'
        """)
        result = conn.execute(check_query).fetchone()
        
        if result:
            print("✅ region 컬럼이 이미 존재합니다.")
        else:
            # 2. region 컬럼 추가
            print("📝 region 컬럼 추가 중...")
            conn.execute(text("ALTER TABLE places ADD COLUMN region VARCHAR(50)"))
            conn.commit()
            print("✅ region 컬럼 추가 완료")
        
        # 3. 주소 기반 지역 분류 업데이트
        print("📝 지역 데이터 업데이트 중...")
        update_query = text("""
            UPDATE places SET region = CASE
                -- 제주시권 (북부)
                WHEN address ILIKE '%제주시%' THEN '제주시'
                WHEN address ILIKE '%애월%' THEN '제주시'
                WHEN address ILIKE '%한림%' THEN '제주시'
                WHEN address ILIKE '%조천%' THEN '제주시'
                WHEN address ILIKE '%구좌%' THEN '동부'
                
                -- 서귀포시권 (남부)
                WHEN address ILIKE '%서귀포%' THEN '서귀포시'
                WHEN address ILIKE '%중문%' THEN '서귀포시'
                WHEN address ILIKE '%대정%' THEN '서부'
                WHEN address ILIKE '%안덕%' THEN '서부'
                WHEN address ILIKE '%남원%' THEN '서귀포시'
                
                -- 동부
                WHEN address ILIKE '%성산%' THEN '동부'
                WHEN address ILIKE '%표선%' THEN '동부'
                WHEN address ILIKE '%우도%' THEN '동부'
                
                -- 서부
                WHEN address ILIKE '%한경%' THEN '서부'
                WHEN address ILIKE '%대정%' THEN '서부'
                
                ELSE '기타'
            END
            WHERE region IS NULL OR region = '기타'
        """)
        conn.execute(update_query)
        conn.commit()
        print("✅ 지역 데이터 업데이트 완료")
        
        # 4. 결과 확인
        stats_query = text("""
            SELECT region, COUNT(*) as count 
            FROM places 
            GROUP BY region 
            ORDER BY count DESC
        """)
        result = conn.execute(stats_query)
        
        print("\n📊 지역별 장소 수:")
        print("-" * 30)
        for row in result:
            print(f"  {row[0] or '미분류'}: {row[1]}개")
    
    engine.dispose()
    print("\n✅ 모든 작업 완료!")


def verify_region_data():
    """region 데이터 검증"""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # 샘플 데이터 확인
        sample_query = text("""
            SELECT name, address, region, category 
            FROM places 
            WHERE region IS NOT NULL 
            ORDER BY region, rating DESC NULLS LAST
            LIMIT 20
        """)
        result = conn.execute(sample_query)
        
        print("\n📋 샘플 데이터 (상위 20개):")
        print("-" * 80)
        for row in result:
            print(f"  [{row[2]}] {row[0]} - {row[3]}")
            print(f"       주소: {row[1][:50] if row[1] else 'N/A'}...")
    
    engine.dispose()


if __name__ == "__main__":
    add_region_column()
    verify_region_data()

