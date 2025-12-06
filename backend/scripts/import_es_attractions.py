"""
Elasticsearch 관광지 데이터를 PostgreSQL attractions 테이블로 가져오기
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlalchemy import create_engine, text
from src.config import settings
from collections import Counter

# 카테고리 매핑
CATEGORY_MAP = {
    '오름': '자연', '산': '자연', '숲': '자연', '폭포': '자연', '계곡': '자연',
    '곶자왈': '자연', '습지': '자연', '호수': '자연', '천연기념물': '자연',
    '해수욕장': '해변', '해변': '해변', '바다': '해변',
    '박물관': '문화', '미술관': '문화', '기념관': '문화', '전시관': '문화',
    '유적지': '문화', '문화유적지': '문화', '사찰': '문화', '4.3': '문화',
    '테마파크': '액티비티', '수족관': '액티비티', '동물원': '액티비티',
    '식물원': '액티비티', '정원': '액티비티', '공원': '액티비티',
    '체험': '액티비티', '레저': '액티비티', '골프': '액티비티',
    '승마': '액티비티', '서핑': '액티비티', '스쿠버': '액티비티',
}

EXCLUDE = ['음식점', '카페', '식당', '숙박', '호텔', '펜션', '리조트', '스파']

def map_category(es_cat):
    if not es_cat:
        return '기타'
    for excl in EXCLUDE:
        if excl in es_cat:
            return None
    for key, val in CATEGORY_MAP.items():
        if key in es_cat:
            return val
    return '기타'

def main():
    ES_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9201')
    
    print("🚀 ES → PostgreSQL attractions 가져오기")
    
    # ES에서 데이터 가져오기
    all_docs = []
    resp = httpx.post(f'{ES_URL}/jeju_attractions/_search?scroll=2m',
                      json={'size': 1000, 'query': {'match_all': {}}}, timeout=30)
    result = resp.json()
    all_docs.extend(result.get('hits', {}).get('hits', []))
    scroll_id = result.get('_scroll_id')
    
    while result.get('hits', {}).get('hits', []):
        resp = httpx.post(f'{ES_URL}/_search/scroll',
                          json={'scroll': '2m', 'scroll_id': scroll_id}, timeout=30)
        result = resp.json()
        all_docs.extend(result.get('hits', {}).get('hits', []))
    
    print(f"📥 {len(all_docs)}개 조회")
    
    # 변환
    items = []
    for doc in all_docs:
        meta = doc['_source'].get('metadata', {})
        cat = map_category(meta.get('category', ''))
        if cat is None:
            continue
        items.append({
            'name': meta.get('title', ''),
            'category': cat,
            'address': meta.get('address', ''),
            'lat': float(meta['lat']) if meta.get('lat') else None,
            'lng': float(meta['lng']) if meta.get('lng') else None,
            'phone': meta.get('phone', ''),
            'avg_rating': float(meta['rating']) if meta.get('rating') else None,
        })
    
    print(f"📊 {len(items)}개 관광지")
    for cat, cnt in Counter(i['category'] for i in items).most_common():
        print(f"   {cat}: {cnt}개")
    
    # PostgreSQL에 삽입 (좌표 있는 것만)
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        inserted, updated, skipped = 0, 0, 0
        for item in items:
            exists = conn.execute(text("SELECT id FROM attractions WHERE name = :name"),
                                  {'name': item['name']}).fetchone()
            if exists:
                conn.execute(text("""UPDATE attractions SET category=:category,
                    lat=COALESCE(:lat,lat), lng=COALESCE(:lng,lng) WHERE name=:name"""), item)
                updated += 1
            else:
                # 좌표 없으면 스킵
                if not item['lat'] or not item['lng']:
                    skipped += 1
                    continue
                conn.execute(text("""INSERT INTO attractions (name,category,address,lat,lng,phone,avg_rating)
                    VALUES (:name,:category,:address,:lat,:lng,:phone,:avg_rating)"""), item)
                inserted += 1
        conn.commit()
        print(f"✅ 삽입: {inserted}, 업데이트: {updated}, 좌표없음 스킵: {skipped}")
        
        result = conn.execute(text("SELECT category, COUNT(*) FROM attractions GROUP BY category"))
        print("\n최종 결과:")
        for row in result:
            print(f"   {row[0]}: {row[1]}개")

if __name__ == "__main__":
    main()

