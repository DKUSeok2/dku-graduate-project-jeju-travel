"""
places 테이블 데이터 재분류
- 관광지/액티비티 → attractions 테이블로 이동
- 숙박 → place_type = 'accommodation'으로 수정
- 음식점/카페 → place_type = 'restaurant' 유지
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.config import settings

# 카테고리 분류 기준
ATTRACTION_CATEGORIES = [
    # 자연
    '오름', '숲', '숲길', '숲,숲길', '폭포', '계곡', '해변', '해수욕장', '동굴',
    '자연명소', '휴양림', '산림욕장', '휴양림,산림욕장', '산책로',
    # 문화
    '박물관', '미술관', '전시관', '기념관', '유적지', '사찰', '절',
    '갤러리', '화랑', '갤러리,화랑',
    # 액티비티
    '테마파크', '스킨스쿠버', '서핑', '윈드서핑', '서핑,윈드서핑', '스노클링',
    '승마장', '승마', '요트', '배낚시', '낚시', '수상', '해양레저', '수상,해양레저',
    '자전거', '등산', '아웃도어', '등산,아웃도어', '트레킹', '도보코스',
    '골프장', '퍼블릭골프장', '골프', '카트', '카트체험', 'ATV',
    '행글라이딩', '패러글라이딩', '행글라이딩,패러글라이딩', '레포츠시설', '레포츠',
    # 체험
    '관람', '체험', '관람,체험', '공방', '만들기체험', '관광농원', '팜스테이', '관광농원,팜스테이',
    # 기타 관광
    '전망대', '공원', '정원', '수목원', '식물원', '동물원', '거리', '골목', '거리,골목',
]

ACCOMMODATION_CATEGORIES = [
    '펜션', '호텔', '모텔', '게스트하우스', '민박', '리조트', '콘도',
    '콘도,리조트', '숙박', '풀빌라', '한옥스테이', '캠핑장',
]

RESTAURANT_CATEGORIES = [
    '카페', '디저트', '카페,디저트', '한식', '양식', '일식', '중식',
    '해물', '생선요리', '해물,생선요리', '고기', '구이', '고기,구이',
    '돼지고기구이', '육류', '고기요리', '육류,고기요리', '생선회',
    '베이커리', '빵', '국수', '칼국수', '만두', '분식', '종합분식',
    '치킨', '피자', '햄버거', '패스트푸드', '술집', '바', '주점',
    # 추가 카테고리
    '샤브샤브', '향토음식', '해장국', '돈가스', '김밥', '쌈밥',
    '멕시코', '남미음식', '멕시코,남미음식', '태국음식', '베트남음식', '아시아음식',
    '브런치', '샐러드', '죽', '찌개', '전골', '백반', '정식',
    '닭요리', '닭갈비', '삼계탕', '오리', '족발', '보쌈', '곱창',
    '냉면', '막국수', '우동', '라멘', '떡볶이', '순대', '튀김',
    '아이스크림', '빙수', '와플', '토스트', '샌드위치',
]


def classify_category(category: str) -> str:
    """카테고리를 기반으로 타입 분류"""
    if not category:
        return 'unknown'
    
    category_lower = category.lower()
    
    # 관광지 체크
    for kw in ATTRACTION_CATEGORIES:
        if kw in category_lower or category_lower in kw:
            return 'attraction'
    
    # 숙박 체크
    for kw in ACCOMMODATION_CATEGORIES:
        if kw in category_lower or category_lower in kw:
            return 'accommodation'
    
    # 음식점 체크
    for kw in RESTAURANT_CATEGORIES:
        if kw in category_lower or category_lower in kw:
            return 'restaurant'
    
    return 'unknown'


def reclassify_places():
    """places 테이블 데이터 재분류"""
    
    print("🔄 places 테이블 데이터 재분류 시작")
    print("=" * 60)
    
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # 1. 모든 places 데이터 조회
        result = conn.execute(text("""
            SELECT id, name, category, address, phone, rating, 
                   lat, lng, place_type, kid_friendly
            FROM places
        """))
        places = result.fetchall()
        print(f"📋 총 {len(places)}개 데이터 조회\n")
        
        # 2. 카테고리 기반 분류
        attractions_data = []
        accommodation_updates = []
        restaurant_updates = []
        unknown_data = []
        
        for place in places:
            place_id = place[0]
            name = place[1]
            category = place[2]
            address = place[3]
            phone = place[4]
            rating = place[5]
            lat = place[6]
            lng = place[7]
            current_type = place[8]
            kid_friendly = place[9]
            
            new_type = classify_category(category)
            
            if new_type == 'attraction':
                attractions_data.append({
                    'name': name,
                    'category': category,
                    'address': address,
                    'phone': phone,
                    'rating': rating,
                    'lat': lat,
                    'lng': lng,
                    'kid_friendly': kid_friendly,
                    'place_id': place_id,  # 원본 ID (나중에 삭제용)
                })
            elif new_type == 'accommodation':
                if current_type != 'accommodation':
                    accommodation_updates.append(place_id)
            elif new_type == 'restaurant':
                if current_type != 'restaurant':
                    restaurant_updates.append(place_id)
            else:
                unknown_data.append((place_id, name, category))
        
        print(f"📊 분류 결과:")
        print(f"   - attractions로 이동: {len(attractions_data)}개")
        print(f"   - accommodation으로 수정: {len(accommodation_updates)}개")
        print(f"   - restaurant으로 수정: {len(restaurant_updates)}개")
        print(f"   - 분류 불가: {len(unknown_data)}개")
        print()
        
        # 3. attractions 테이블에 삽입
        if attractions_data:
            print(f"🏞️ attractions 테이블에 {len(attractions_data)}개 삽입 중...")
            
            # 카테고리 매핑 (프론트엔드 UI용)
            category_map = {
                '오름': '자연', '숲': '자연', '숲길': '자연', '폭포': '자연', '계곡': '자연',
                '해변': '해변', '해수욕장': '해변',
                '박물관': '문화', '미술관': '문화', '전시관': '문화', '기념관': '문화',
                '테마파크': '액티비티', '스킨스쿠버': '액티비티', '서핑': '액티비티',
                '승마': '액티비티', '요트': '액티비티', '골프': '액티비티',
                '체험': '체험', '공방': '체험',
            }
            
            inserted = 0
            skipped = 0
            for item in attractions_data:
                # 카테고리 변환
                original_cat = item['category'] or ''
                mapped_cat = '기타'
                for key, val in category_map.items():
                    if key in original_cat:
                        mapped_cat = val
                        break
                
                try:
                    # 이미 존재하는지 확인
                    exists = conn.execute(text("""
                        SELECT id FROM attractions WHERE name = :name
                    """), {'name': item['name']}).fetchone()
                    
                    if exists:
                        # 이미 있으면 업데이트
                        conn.execute(text("""
                            UPDATE attractions 
                            SET category = :category,
                                lat = COALESCE(:lat, lat),
                                lng = COALESCE(:lng, lng),
                                address = COALESCE(:address, address)
                            WHERE name = :name
                        """), {
                            'name': item['name'],
                            'category': mapped_cat,
                            'address': item['address'],
                            'lat': float(item['lat']) if item['lat'] else None,
                            'lng': float(item['lng']) if item['lng'] else None,
                        })
                        skipped += 1
                    else:
                        # 없으면 삽입
                        conn.execute(text("""
                            INSERT INTO attractions (name, category, address, phone, avg_rating, lat, lng, kid_friendly)
                            VALUES (:name, :category, :address, :phone, :rating, :lat, :lng, :kid_friendly)
                        """), {
                            'name': item['name'],
                            'category': mapped_cat,
                            'address': item['address'],
                            'phone': item['phone'],
                            'rating': item['rating'],
                            'lat': float(item['lat']) if item['lat'] else None,
                            'lng': float(item['lng']) if item['lng'] else None,
                            'kid_friendly': item['kid_friendly'] or False,
                        })
                        inserted += 1
                except Exception as e:
                    print(f"   ⚠️ 삽입 실패 ({item['name']}): {e}")
            
            conn.commit()
            print(f"   ✅ {inserted}개 삽입, {skipped}개 업데이트 완료")
        
        # 4. place_type 수정
        if accommodation_updates:
            print(f"\n🏨 accommodation으로 {len(accommodation_updates)}개 수정 중...")
            conn.execute(text("""
                UPDATE places SET place_type = 'accommodation'
                WHERE id = ANY(:ids)
            """), {'ids': accommodation_updates})
            conn.commit()
            print("   ✅ 완료")
        
        if restaurant_updates:
            print(f"\n🍽️ restaurant으로 {len(restaurant_updates)}개 수정 중...")
            conn.execute(text("""
                UPDATE places SET place_type = 'restaurant'
                WHERE id = ANY(:ids)
            """), {'ids': restaurant_updates})
            conn.commit()
            print("   ✅ 완료")
        
        # 5. attractions로 이동한 데이터는 places에서 삭제 (선택)
        if attractions_data:
            place_ids_to_delete = [item['place_id'] for item in attractions_data]
            print(f"\n🗑️ places에서 {len(place_ids_to_delete)}개 삭제 중...")
            conn.execute(text("""
                DELETE FROM places WHERE id = ANY(:ids)
            """), {'ids': place_ids_to_delete})
            conn.commit()
            print("   ✅ 완료")
        
        # 6. 최종 통계
        print("\n" + "=" * 60)
        print("📊 최종 결과:")
        
        result = conn.execute(text("SELECT COUNT(*) FROM attractions"))
        print(f"   attractions: {result.scalar()}개")
        
        result = conn.execute(text("SELECT place_type, COUNT(*) FROM places GROUP BY place_type"))
        print("   places:")
        for row in result:
            print(f"      - {row[0]}: {row[1]}개")
        
        # 분류 불가 목록 (상위 10개)
        if unknown_data:
            print(f"\n⚠️ 분류 불가 데이터 (상위 10개):")
            for pid, name, cat in unknown_data[:10]:
                print(f"   - [{pid}] {name} ({cat})")


if __name__ == "__main__":
    reclassify_places()

