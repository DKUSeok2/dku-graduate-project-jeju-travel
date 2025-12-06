"""
카카오 지오코딩 API를 사용해서 주소에서 정확한 지역명(region) 추출

카카오 로컬 API의 주소 검색 결과에서 행정구역 정보를 추출하여
애월, 한림, 성산 등 구체적인 지역명을 region으로 설정
"""
import asyncio
import sys
import requests
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db_session
from src.config import settings
from sqlalchemy import text

# 카카오 API 키 (환경변수에서 가져오기)
import os
from dotenv import load_dotenv
load_dotenv()

KAKAO_API_KEY = os.getenv('KAKAO_API_KEY') or '29b88d36376b65d78516805b0ee8ff3b'


# 제주도 지역 키워드 매핑 (사용 안 함 - extract_region_from_kakao_response에서 직접 처리)


def extract_region_from_kakao_response(kakao_address_data):
    """
    카카오 API 응답에서 지역명 추출
    
    전략:
    1. 구체적인 읍/면/동이 있으면 구체적으로 설정 (애월, 한림, 중문 등)
    2. 없으면 큰 단위로 분류 (제주시, 서귀포시, 동부, 서부)
    
    Args:
        kakao_address_data: 카카오 주소 검색 API의 document 객체
    
    Returns:
        region (str): 추출된 지역명
    """
    if not kakao_address_data:
        return None
    
    # address_name: 전체 주소 (예: "제주특별자치도 제주시 애월읍 ...")
    address_name = kakao_address_data.get('address_name', '')
    
    if not address_name:
        return None
    
    import re
    
    # 1. 구체적인 읍/면 패턴 찾기 (우선순위: 구체적 지역명)
    # ⚠️ 순서 중요: 더 구체적인 패턴(협재, 함덕 등)을 먼저 체크
    specific_patterns = [
        (r'협재', '협재'),  # 한림읍 협재리 (한림읍보다 먼저!)
        (r'함덕', '함덕'),  # 조천읍 함덕리 (조천읍보다 먼저!)
        (r'중문', '중문'),
        (r'우도면', '우도'),
        (r'애월읍', '애월'),
        (r'한림읍', '한림'),
        (r'성산읍', '성산'),
        (r'표선면', '표선'),
        (r'구좌읍', '구좌'),
        (r'조천읍', '조천'),
        (r'대정읍', '대정'),
        (r'안덕면', '안덕'),
        (r'한경면', '한경'),
        (r'남원읍', '안덕'),  # 남원읍도 안덕면과 같은 지역
        (r'김녕', '김녕'),
        (r'세화', '세화'),
    ]
    
    for pattern, region in specific_patterns:
        if re.search(pattern, address_name):
            return region
    
    # 2. 큰 단위로 분류 (읍/면 정보가 없는 경우)
    # 동부 지역: 성산, 표선, 구좌, 조천, 김녕, 세화 등
    if any(keyword in address_name for keyword in ['성산', '표선', '구좌', '조천', '김녕', '세화', '우도']):
        return "동부"
    
    # 서부 지역: 대정, 한경
    if any(keyword in address_name for keyword in ['대정', '한경', '모슬포', '마라도']):
        return "서부"
    
    # 제주시 vs 서귀포시
    if "서귀포시" in address_name:
        return "서귀포시"
    elif "제주시" in address_name:
        return "제주시"
    
    return None


def get_region_from_kakao_api(address):
    """
    카카오 API를 호출해서 주소에서 region 추출
    
    Args:
        address: 주소 문자열
    
    Returns:
        region (str): 추출된 지역명 또는 None
    """
    if not address:
        return None
    
    url = 'https://dapi.kakao.com/v2/local/search/address.json'
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    params = {'query': address}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data.get('documents') and len(data['documents']) > 0:
            doc = data['documents'][0]
            region = extract_region_from_kakao_response(doc)
            return region
    except Exception as e:
        print(f"  ⚠️ API 오류: {e}")
        pass
    
    return None


async def update_regions_from_kakao_api():
    """모든 장소의 주소를 카카오 API로 검색해서 정확한 region 업데이트"""
    async for db in get_db_session():
        try:
            print("=" * 80)
            print("🔧 카카오 API로 정확한 region 추출 시작")
            print("=" * 80)
            
            # 모든 장소 조회
            result = await db.execute(text("""
                SELECT id, name, address, region
                FROM places
                WHERE address IS NOT NULL
                AND address != ''
                ORDER BY id
            """))
            
            places = list(result)
            print(f"\n📊 총 {len(places)}개 장소 처리 시작...")
            
            updated = 0
            failed = 0
            unchanged = 0
            
            for i, (place_id, name, address, current_region) in enumerate(places, 1):
                if i % 100 == 0:
                    print(f"\n진행: {i}/{len(places)} (업데이트: {updated}, 변경없음: {unchanged}, 실패: {failed})")
                
                # 카카오 API로 region 추출
                new_region = get_region_from_kakao_api(address)
                
                if new_region:
                    if new_region != current_region:
                        # 업데이트
                        await db.execute(text("""
                            UPDATE places
                            SET region = :new_region
                            WHERE id = :place_id
                        """), {"new_region": new_region, "place_id": place_id})
                        updated += 1
                        if updated <= 10:  # 처음 10개만 출력
                            print(f"  ✅ {name[:30]}: '{current_region}' → '{new_region}'")
                    else:
                        unchanged += 1
                else:
                    failed += 1
                
                # API 제한 방지 (초당 10회)
                time.sleep(0.1)
            
            await db.commit()
            
            print("\n" + "=" * 80)
            print("🎉 완료!")
            print("=" * 80)
            print(f"✅ 업데이트: {updated}개")
            print(f"ℹ️  변경없음: {unchanged}개")
            print(f"❌ 실패: {failed}개")
            
            # 최종 region 분포 확인
            print("\n\n📊 최종 region 분포:")
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
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ 오류 발생: {e}")
            raise
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(update_regions_from_kakao_api())

