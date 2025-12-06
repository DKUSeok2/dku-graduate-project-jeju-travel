"""
DB의 region을 구체적인 지역명으로 업데이트

주소를 분석해서 애월, 한림, 성산, 우도 등의 구체적인 지역명을 region으로 설정
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db_session
from sqlalchemy import text


# 주소 키워드 → 구체적인 region 매핑 (우선순위 순)
# 먼저 매칭되는 것을 사용 (더 구체적인 지역명 먼저)
REGION_KEYWORD_MAPPING = [
    # 동부 지역
    ("우도", "우도"),
    ("섭지코지", "성산"),
    ("성산일출봉", "성산"),
    ("성산", "성산"),
    ("표선", "표선"),
    ("김녕", "김녕"),
    ("세화", "세화"),
    ("구좌", "구좌"),
    
    # 서부 지역
    ("대정", "대정"),
    ("모슬포", "대정"),
    ("마라도", "대정"),
    ("한경", "한경"),
    
    # 제주시 지역
    ("애월", "애월"),
    ("한림", "한림"),
    ("협재", "협재"),
    ("조천", "조천"),
    ("함덕", "함덕"),
    
    # 서귀포시 지역
    ("중문", "중문"),
    ("안덕", "안덕"),
    ("남원", "안덕"),
    ("위미", "안덕"),
    ("화순", "안덕"),
]


async def update_regions_to_detailed():
    """주소를 분석해서 구체적인 지역명으로 region 업데이트"""
    async for db in get_db_session():
        try:
            print("=" * 80)
            print("🔧 구체적인 지역명으로 region 업데이트 시작")
            print("=" * 80)
            
            total_updated = 0
            updates_by_region = {}
            
            # 각 지역 키워드에 대해 업데이트
            for keyword, new_region in REGION_KEYWORD_MAPPING:
                # 현재 다른 region인 레코드 수 확인
                check_query = text(f"""
                    SELECT COUNT(*) as count
                    FROM places
                    WHERE address ILIKE '%{keyword}%'
                    AND region != :new_region
                """)
                
                result = await db.execute(check_query, {"new_region": new_region})
                count = result.scalar()
                
                if count > 0:
                    print(f"\n📍 {keyword} → {new_region}: {count}개 수정")
                    
                    # 업데이트 실행
                    update_query = text(f"""
                        UPDATE places
                        SET region = :new_region
                        WHERE address ILIKE '%{keyword}%'
                        AND region != :new_region
                    """)
                    
                    await db.execute(update_query, {"new_region": new_region})
                    await db.commit()
                    
                    total_updated += count
                    updates_by_region[new_region] = updates_by_region.get(new_region, 0) + count
                    print(f"   ✅ {count}개 레코드 업데이트 완료")
            
            # 제주시 중심 지역 (애월, 한림, 협재, 조천, 함덕 제외)
            print("\n\n📍 제주시 중심 지역 처리")
            print("-" * 80)
            
            check_query = text("""
                SELECT COUNT(*) as count
                FROM places
                WHERE address ILIKE '%제주시%'
                AND address NOT ILIKE '%애월%'
                AND address NOT ILIKE '%한림%'
                AND address NOT ILIKE '%협재%'
                AND address NOT ILIKE '%조천%'
                AND address NOT ILIKE '%함덕%'
                AND region != '제주시'
            """)
            
            result = await db.execute(check_query)
            count = result.scalar()
            
            if count > 0:
                print(f"   제주시 중심: {count}개 수정")
                update_query = text("""
                    UPDATE places
                    SET region = '제주시'
                    WHERE address ILIKE '%제주시%'
                    AND address NOT ILIKE '%애월%'
                    AND address NOT ILIKE '%한림%'
                    AND address NOT ILIKE '%협재%'
                    AND address NOT ILIKE '%조천%'
                    AND address NOT ILIKE '%함덕%'
                    AND region != '제주시'
                """)
                
                await db.execute(update_query)
                await db.commit()
                
                total_updated += count
                updates_by_region['제주시'] = updates_by_region.get('제주시', 0) + count
                print(f"   ✅ {count}개 레코드 업데이트 완료")
            
            # 서귀포시 중심 지역 (중문, 안덕 제외)
            print("\n\n📍 서귀포시 중심 지역 처리")
            print("-" * 80)
            
            check_query = text("""
                SELECT COUNT(*) as count
                FROM places
                WHERE address ILIKE '%서귀포시%'
                AND address NOT ILIKE '%중문%'
                AND address NOT ILIKE '%안덕%'
                AND address NOT ILIKE '%남원%'
                AND address NOT ILIKE '%대정%'
                AND region != '서귀포시'
            """)
            
            result = await db.execute(check_query)
            count = result.scalar()
            
            if count > 0:
                print(f"   서귀포시 중심: {count}개 수정")
                update_query = text("""
                    UPDATE places
                    SET region = '서귀포시'
                    WHERE address ILIKE '%서귀포시%'
                    AND address NOT ILIKE '%중문%'
                    AND address NOT ILIKE '%안덕%'
                    AND address NOT ILIKE '%남원%'
                    AND address NOT ILIKE '%대정%'
                    AND region != '서귀포시'
                """)
                
                await db.execute(update_query)
                await db.commit()
                
                total_updated += count
                updates_by_region['서귀포시'] = updates_by_region.get('서귀포시', 0) + count
                print(f"   ✅ {count}개 레코드 업데이트 완료")
            
            print("\n" + "=" * 80)
            print(f"🎉 수정 완료: 총 {total_updated}개 레코드 업데이트")
            print("=" * 80)
            
            # region별 업데이트 통계
            print("\n📊 Region별 업데이트 통계:")
            for region, count in sorted(updates_by_region.items(), key=lambda x: -x[1]):
                print(f"  - {region}: {count}개")
            
            # 검증: 수정 후 region 분포 확인
            print("\n\n📊 수정 후 region 분포")
            print("-" * 80)
            result = await db.execute(text("""
                SELECT region, COUNT(*) as count
                FROM places
                WHERE region IS NOT NULL
                GROUP BY region
                ORDER BY count DESC
            """))
            
            for row in result:
                print(f"  {row[0]}: {row[1]}개")
            
            # 검증: 주요 지역 확인
            print("\n\n✅ 주요 지역 검증")
            print("-" * 80)
            test_regions = ["애월", "한림", "성산", "우도", "중문", "대정"]
            for test_region in test_regions:
                result = await db.execute(text(f"""
                    SELECT COUNT(*) as count
                    FROM places
                    WHERE address ILIKE '%{test_region}%'
                    AND region = :test_region
                """), {"test_region": test_region})
                
                count = result.scalar()
                total = await db.execute(text(f"""
                    SELECT COUNT(*) as count
                    FROM places
                    WHERE address ILIKE '%{test_region}%'
                """))
                total_count = total.scalar()
                
                if count == total_count:
                    print(f"  ✅ {test_region}: 모든 레코드 올바름 ({count}개)")
                else:
                    print(f"  ⚠️ {test_region}: {count}/{total_count}개 올바름")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ 오류 발생: {e}")
            raise
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(update_regions_to_detailed())




