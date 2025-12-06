"""
카카오 API로 places 테이블의 좌표 채우기
"""
import requests
import time
from sqlalchemy import create_engine, text
from tqdm import tqdm
import sys
sys.path.insert(0, '/Users/ohyooseok/PAI_SQL/jeju-travel-chatbot/backend')
from src.config import settings

KAKAO_API_KEY = '29b88d36376b65d78516805b0ee8ff3b'

engine = create_engine(settings.database_url)

def get_coords_from_address(address):
    """주소로 좌표 검색"""
    url = 'https://dapi.kakao.com/v2/local/search/address.json'
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    params = {'query': address}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data.get('documents'):
            doc = data['documents'][0]
            return float(doc['y']), float(doc['x'])  # 위도, 경도
    except:
        pass
    
    return None, None

def get_coords_from_keyword(name):
    """키워드로 좌표 검색 (주소 검색 실패 시)"""
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    
    # 제주도 범위로 제한
    params = {
        'query': f'{name} 제주',
        'x': '126.5312',
        'y': '33.4996',
        'radius': 50000  # 50km
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data.get('documents'):
            doc = data['documents'][0]
            return float(doc['y']), float(doc['x'])
    except:
        pass
    
    return None, None

def main():
    # 좌표 없는 장소 조회
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT id, name, address FROM places 
            WHERE lat IS NULL OR lng IS NULL
        '''))
        places = result.fetchall()
    
    if not places:
        print("✅ 모든 장소에 좌표가 있습니다!")
        return
    
    print(f"🗺️ {len(places)}개 장소 좌표 변환 시작...")
    
    success = 0
    fail = 0
    
    with engine.connect() as conn:
        for place_id, name, address in tqdm(places, desc="좌표 변환"):
            lat, lng = None, None
            
            # 1. 주소로 검색
            if address:
                lat, lng = get_coords_from_address(address)
            
            # 2. 실패하면 키워드로 검색
            if lat is None:
                lat, lng = get_coords_from_keyword(name)
            
            if lat and lng:
                conn.execute(text('''
                    UPDATE places SET lat = :lat, lng = :lng WHERE id = :id
                '''), {'lat': lat, 'lng': lng, 'id': place_id})
                success += 1
            else:
                fail += 1
            
            # API 제한 방지 (초당 10회)
            time.sleep(0.1)
        
        conn.commit()
    
    print(f"\n📊 결과:")
    print(f"  ✅ 성공: {success}개")
    print(f"  ❌ 실패: {fail}개")
    print(f"  📍 성공률: {success/(success+fail)*100:.1f}%")

if __name__ == "__main__":
    main()

