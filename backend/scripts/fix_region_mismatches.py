"""
DB의 주소-region 불일치 수정 스크립트

주소를 기반으로 올바른 region으로 업데이트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db_session
from sqlalchemy import text


# 주소 키워드 → 올바른 region 매핑
REGION_FIX_MAPPING = [
    # 제주시 지역
    ("애월", "제주시"),
    ("한림", "제주시"),
    ("협재", "제주시"),
    # 동부 지역
    ("성산", "동부"),
    ("표선", "동부"),
    # 서귀포시 지역
    ("안덕", "서귀포시"),
    # 서부 지역
    ("대정", "서부"),
]


async def fix_region_mismatches():
    """주소 기반으로 region 불일치 수정"""
    async for db in get_db_session():
        try:
            print("=" * 80)
            print("🔧 주소-region 불일치 수정 시작")
            print("=" * 80)
            
            total_updated = 0
            
            for keyword, correct_region in REGION_FIX_MAPPING:
                # 현재 잘못된 region인 레코드 수 확인
                check_query = text(f"""
                    SELECT COUNT(*) as count
                    FROM places
                    WHERE address ILIKE '%{keyword}%'
                    AND region != :correct_region
                """)
                
                result = await db.execute(check_query, {"correct_region": correct_region})
                count = result.scalar()
                
                if count > 0:
                    print(f"\n📍 {keyword} → {correct_region}: {count}개 수정")
                    
                    # 업데이트 실행
                    update_query = text(f"""
                        UPDATE places
                        SET region = :correct_region
                        WHERE address ILIKE '%{keyword}%'
                        AND region != :correct_region
                    """)
                    
                    await db.execute(update_query, {"correct_region": correct_region})
                    await db.commit()
                    
                    total_updated += count
                    print(f"   ✅ {count}개 레코드 업데이트 완료")
                else:
                    print(f"\n✅ {keyword}: 이미 올바른 region ({correct_region})")
            
            print("\n" + "=" * 80)
            print(f"🎉 수정 완료: 총 {total_updated}개 레코드 업데이트")
            print("=" * 80)
            
            # 검증: 수정 후 결과 확인
            print("\n📊 수정 후 검증")
            print("-" * 80)
            
            for keyword, correct_region in REGION_FIX_MAPPING:
                result = await db.execute(text(f"""
                    SELECT COUNT(*) as count
                    FROM places
                    WHERE address ILIKE '%{keyword}%'
                    AND region != :correct_region
                """), {"correct_region": correct_region})
                
                remaining = result.scalar()
                if remaining > 0:
                    print(f"  ⚠️ {keyword}: 아직 {remaining}개 레코드가 잘못된 region")
                else:
                    print(f"  ✅ {keyword}: 모든 레코드가 올바른 region ({correct_region})")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ 오류 발생: {e}")
            raise
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(fix_region_mismatches())




