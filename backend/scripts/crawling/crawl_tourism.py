#!/usr/bin/env python3
"""
🏞️ 네이버 플레이스 관광 데이터 크롤링 스크립트

제주도 자연, 문화, 해변, 액티비티, 숙박 데이터를 네이버 플레이스에서 크롤링합니다.

Usage:
    python crawl_tourism.py                    # 전체 크롤링
    python crawl_tourism.py --test             # 테스트 (5개 키워드만)
    python crawl_tourism.py --skip-details     # 상세정보 수집 건너뛰기
    nohup python crawl_tourism.py > crawl.log 2>&1 &  # 백그라운드 실행
"""

import asyncio
import argparse
import random
import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import quote

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️ tqdm 없음 - 진행률 표시 비활성화")

from playwright.async_api import async_playwright, Page

# ============================================================================
# 설정
# ============================================================================

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5433"),
    "database": os.getenv("DB_NAME", "jeju_travel"),
    "user": os.getenv("DB_USER", "jeju_user"),
    "password": os.getenv("DB_PASSWORD", "jeju_password"),
}

CONFIG = {
    "delay_min": 2.0,
    "delay_max": 4.0,
    "timeout": 60000,  # 60초
    "headless": True,  # 백그라운드 실행용
    "max_retries": 2,
}

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

# ============================================================================
# 키워드
# ============================================================================

TOURISM_KEYWORDS = [
    # 🌿 자연
    "제주 오름", "제주 오름 추천", "제주 등산", "제주 트레킹",
    "제주 숲길", "제주 자연", "제주 계곡", "제주 폭포",
    "제주 한라산", "제주 곶자왈", "제주 올레길",
    "제주 용두암", "제주 산방산",
    "제주 천지연폭포", "제주 정방폭포", "제주 천제연폭포",
    "제주 성산일출봉", "제주 만장굴",
    "제주 비자림", "제주 사려니숲길",
    
    # 🏛️ 문화
    "제주 박물관", "제주 미술관",
    "제주 민속촌", "제주 테마파크", "제주 아쿠아리움",
    "제주 체험", "제주 공방",
    "제주 전통시장", "제주 오일장",
    
    # 🏖️ 해변
    "제주 해변", "제주 해수욕장", "제주 바다",
    "제주 협재해수욕장", "제주 함덕해수욕장",
    "제주 월정리해변", "제주 중문해수욕장",
    "제주 우도 해변",
    "제주 해안도로", "제주 일출 명소",
    
    # 🎯 액티비티
    "제주 액티비티", "제주 레저",
    "제주 스쿠버다이빙", "제주 서핑",
    "제주 카약", "제주 요트", "제주 낚시",
    "제주 승마", "제주 ATV",
    "제주 패러글라이딩", "제주 짚라인",
    "제주 골프장",
    "제주 자전거",
    
    # 🏨 숙박
    "제주 호텔", "제주 특급호텔",
    "서귀포 호텔", "중문 호텔",
    "제주 리조트", "제주 풀빌라",
    "제주 펜션", "서귀포 펜션", "애월 펜션",
    "제주 게스트하우스",
]

# ============================================================================
# 유틸리티 함수
# ============================================================================

def log(msg: str):
    """타임스탬프와 함께 로그 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


async def random_delay():
    delay = random.uniform(CONFIG["delay_min"], CONFIG["delay_max"])
    await asyncio.sleep(delay)


async def create_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=CONFIG["headless"])
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1920, "height": 1080},
    )
    page = await context.new_page()
    return playwright, browser, page


async def close_browser(playwright, browser):
    await browser.close()
    await playwright.stop()


def save_data(data: List[Dict], prefix: str = "naver_tourism"):
    """데이터 저장 (JSON + CSV)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON 저장
    json_path = DATA_DIR / f"{prefix}_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"💾 JSON 저장: {json_path}")
    
    # CSV 저장
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        csv_path = DATA_DIR / f"{prefix}_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        log(f"💾 CSV 저장: {csv_path}")
    except ImportError:
        log("⚠️ pandas 없음 - CSV 저장 건너뜀")
    
    return json_path


def detect_place_type(keyword: str, category: str = "") -> str:
    """장소 타입 감지"""
    keyword_lower = keyword.lower()
    category_lower = category.lower() if category else ""
    
    if any(w in keyword_lower or w in category_lower for w in 
           ['호텔', '펜션', '리조트', '게스트하우스', '민박', '숙소', '풀빌라']):
        return 'accommodation'
    
    if any(w in keyword_lower or w in category_lower for w in 
           ['맛집', '음식', '식당', '카페', '커피', '흑돼지', '횟집']):
        return 'restaurant'
    
    return 'place'


def get_naver_place_url(place_id: str, place_type: str) -> str:
    if place_type == 'accommodation':
        return f"https://m.place.naver.com/accommodation/{place_id}/home"
    elif place_type == 'restaurant':
        return f"https://m.place.naver.com/restaurant/{place_id}/home"
    else:
        return f"https://m.place.naver.com/place/{place_id}/home"


# ============================================================================
# 크롤링 함수
# ============================================================================

async def get_details(page: Page, place_id: str, place_type: str = 'place') -> Dict:
    """상세 정보 수집 (재시도 포함)"""
    details = {
        "rating": None,
        "review_count": 0,
        "address": "",
        "business_hours": "",
        "lat": None,
        "lng": None,
        "phone": "",
        "place_type": place_type,
        "parking": False,
        "kid_friendly": False,
        "pet_friendly": False,
    }
    
    if not place_id:
        return details
    
    detail_url = get_naver_place_url(place_id, place_type)
    
    # 재시도 로직
    for attempt in range(CONFIG["max_retries"] + 1):
        try:
            await page.goto(detail_url, timeout=CONFIG["timeout"], wait_until="domcontentloaded")
            await asyncio.sleep(2)
            break
        except Exception as e:
            if attempt < CONFIG["max_retries"]:
                await asyncio.sleep(3)
                continue
            else:
                return details
    
    try:
        # 평점
        try:
            rating_elem = await page.query_selector('.PXMot, .LXIwF, [class*="rating"]')
            if rating_elem:
                rating_text = await rating_elem.inner_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    details["rating"] = float(rating_match.group(1))
        except:
            pass
        
        # 리뷰 수
        try:
            full_text = await page.inner_text('body')
            for pattern in [r'방문자리뷰\s*(\d[\d,]*)', r'리뷰\s*(\d[\d,]*)', r'(\d[\d,]*)\s*리뷰']:
                match = re.search(pattern, full_text)
                if match:
                    count_str = match.group(1).replace(',', '')
                    if count_str.isdigit():
                        details["review_count"] = int(count_str)
                        break
        except:
            pass
        
        # 주소
        try:
            addr_elem = await page.query_selector('.LDgIH, .IH7VW, [class*="address"]')
            if addr_elem:
                details["address"] = await addr_elem.inner_text()
        except:
            pass
        
        # 위경도
        try:
            html = await page.content()
            coord_match = re.search(r'"y"\s*:\s*(33\.\d+)\s*,\s*"x"\s*:\s*(126\.\d+)', html)
            if coord_match:
                details["lat"] = float(coord_match.group(1))
                details["lng"] = float(coord_match.group(2))
        except:
            pass
        
        # 전화번호 & 편의시설
        try:
            full_text = await page.inner_text('body')
            phone_match = re.search(r'(0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4})', full_text)
            if phone_match:
                details["phone"] = phone_match.group(1)
            
            if '주차' in full_text:
                details["parking"] = True
            if '유아' in full_text or '키즈' in full_text:
                details["kid_friendly"] = True
            if '반려' in full_text or '애견' in full_text:
                details["pet_friendly"] = True
        except:
            pass
            
    except Exception as e:
        pass
    
    return details


async def search_places(page: Page, keyword: str, max_items: int = 30) -> List[Dict]:
    """네이버 지도에서 장소 검색"""
    results = []
    
    encoded_keyword = quote(keyword)
    search_url = f"https://m.map.naver.com/search2/search.naver?query={encoded_keyword}&sm=hty&style=v5"
    
    try:
        await page.goto(search_url, timeout=CONFIG["timeout"])
        await asyncio.sleep(3)
        
        # 스크롤
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        
        items = await page.query_selector_all('li[class*="_list_item"]')
        log(f"   {keyword}: {len(items)}개 발견")
        
        seen_ids = set()
        
        for item in items[:max_items]:
            try:
                name_elem = await item.query_selector('strong[class*="_item_name"]')
                if not name_elem:
                    continue
                name = (await name_elem.inner_text()).strip()
                if not name:
                    continue
                
                # place_id 추출
                naver_id = None
                for pattern in ['a[href*="place.naver.com/place/"]', 
                               'a[href*="place.naver.com/restaurant/"]', 
                               'a[href*="place.naver.com/accommodation/"]']:
                    link_elem = await item.query_selector(pattern)
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        id_match = re.search(r'/(?:place|restaurant|accommodation)/(\d+)', href)
                        if id_match:
                            naver_id = id_match.group(1)
                            break
                
                if not naver_id or naver_id in seen_ids:
                    continue
                seen_ids.add(naver_id)
                
                # 카테고리
                category = keyword
                try:
                    cat_elem = await item.query_selector('em[class*="_item_category"]')
                    if cat_elem:
                        category = (await cat_elem.inner_text()).strip()
                except:
                    pass
                
                # 주소
                address = ""
                try:
                    addr_elem = await item.query_selector('button[class*="_item_address"]')
                    if addr_elem:
                        address = (await addr_elem.inner_text()).replace("주소보기", "").strip()
                except:
                    pass
                
                place_type = detect_place_type(keyword, category)
                
                results.append({
                    "naver_id": naver_id,
                    "name": name,
                    "category": category,
                    "address": address,
                    "keyword": keyword,
                    "place_type": place_type,
                    "url": get_naver_place_url(naver_id, place_type),
                })
                
            except:
                continue
                
    except Exception as e:
        log(f"❌ 검색 실패 ({keyword}): {e}")
    
    return results


async def crawl_all(keywords: List[str], max_per_keyword: int = 30, skip_details: bool = False):
    """전체 크롤링"""
    all_results = []
    seen_ids = set()
    
    log(f"🚀 크롤링 시작: {len(keywords)}개 키워드")
    
    playwright, browser, page = await create_browser()
    
    try:
        # 1단계: 검색
        log("📌 1단계: 장소 검색")
        
        iterator = tqdm(keywords, desc="검색") if HAS_TQDM else keywords
        for keyword in iterator:
            results = await search_places(page, keyword, max_items=max_per_keyword)
            
            for item in results:
                if item["naver_id"] not in seen_ids:
                    seen_ids.add(item["naver_id"])
                    all_results.append(item)
            
            await random_delay()
        
        log(f"✅ {len(all_results)}개 장소 수집 완료")
        
        # 중간 저장
        save_data(all_results, "naver_tourism_search")
        
        # 2단계: 상세 정보
        if not skip_details and all_results:
            log("📌 2단계: 상세 정보 수집")
            
            iterator = tqdm(all_results, desc="상세정보") if HAS_TQDM else all_results
            save_interval = 100  # 100개마다 저장
            
            for i, place in enumerate(iterator):
                place_id = place.get("naver_id")
                place_type = place.get("place_type", "place")
                
                if place_id:
                    details = await get_details(page, place_id, place_type)
                    place.update(details)
                
                await random_delay()
                
                # 주기적 저장
                if (i + 1) % save_interval == 0:
                    save_data(all_results, f"naver_tourism_checkpoint_{i+1}")
            
            log(f"✅ 상세 정보 수집 완료")
        
        # 최종 저장
        save_data(all_results, "naver_tourism_final")
        
    finally:
        await close_browser(playwright, browser)
    
    return all_results


def load_to_postgres(data: List[Dict]):
    """PostgreSQL에 적재"""
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        log("❌ sqlalchemy 없음 - DB 적재 건너뜀")
        return
    
    conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    
    try:
        engine = create_engine(conn_str)
        
        with engine.connect() as conn:
            for item in data:
                rating = item.get("rating")
                if rating is not None and (rating > 5.0 or rating < 0):
                    rating = None
                
                review_count = item.get("review_count", 0)
                if not isinstance(review_count, int):
                    try:
                        review_count = int(review_count) if review_count else 0
                    except:
                        review_count = 0
                
                place_sql = text("""
                    INSERT INTO places (
                        naver_id, name, category, address, phone,
                        rating, review_count, lat, lng, place_type,
                        parking, kid_friendly, pet_friendly,
                        business_hours, url
                    ) VALUES (
                        :naver_id, :name, :category, :address, :phone,
                        :rating, :review_count, :lat, :lng, :place_type,
                        :parking, :kid_friendly, :pet_friendly,
                        :business_hours, :url
                    )
                    ON CONFLICT (naver_id) DO UPDATE SET
                        rating = EXCLUDED.rating,
                        review_count = EXCLUDED.review_count,
                        lat = EXCLUDED.lat,
                        lng = EXCLUDED.lng,
                        place_type = EXCLUDED.place_type,
                        address = EXCLUDED.address
                """)
                
                try:
                    conn.execute(place_sql, {
                        "naver_id": item.get("naver_id"),
                        "name": item.get("name"),
                        "category": item.get("category"),
                        "address": item.get("address"),
                        "phone": item.get("phone", ""),
                        "rating": rating,
                        "review_count": review_count,
                        "lat": item.get("lat"),
                        "lng": item.get("lng"),
                        "place_type": item.get("place_type", "place"),
                        "parking": item.get("parking", False),
                        "kid_friendly": item.get("kid_friendly", False),
                        "pet_friendly": item.get("pet_friendly", False),
                        "business_hours": item.get("business_hours", ""),
                        "url": item.get("url", ""),
                    })
                except Exception as e:
                    log(f"⚠️ 저장 실패 ({item.get('name')}): {e}")
            
            conn.commit()
        
        log(f"✅ {len(data)}개 장소 PostgreSQL 적재 완료!")
        
    except Exception as e:
        log(f"❌ DB 연결 실패: {e}")


# ============================================================================
# 메인
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="네이버 플레이스 관광 데이터 크롤링")
    parser.add_argument("--test", action="store_true", help="테스트 모드 (5개 키워드만)")
    parser.add_argument("--skip-details", action="store_true", help="상세정보 수집 건너뛰기")
    parser.add_argument("--no-db", action="store_true", help="DB 적재 건너뛰기")
    parser.add_argument("--max-per-keyword", type=int, default=30, help="키워드당 최대 수집 개수")
    args = parser.parse_args()
    
    log("=" * 60)
    log("🏞️ 네이버 플레이스 관광 데이터 크롤링")
    log("=" * 60)
    
    keywords = TOURISM_KEYWORDS[:5] if args.test else TOURISM_KEYWORDS
    log(f"📋 키워드: {len(keywords)}개")
    log(f"📦 DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    log(f"📁 저장 경로: {DATA_DIR}")
    
    # 크롤링 실행
    data = asyncio.run(crawl_all(
        keywords=keywords,
        max_per_keyword=args.max_per_keyword,
        skip_details=args.skip_details,
    ))
    
    # 통계
    log("\n📊 결과 통계:")
    log(f"   총 장소: {len(data)}개")
    
    from collections import Counter
    type_counts = Counter(d.get('place_type', 'unknown') for d in data)
    for t, cnt in type_counts.items():
        log(f"   - {t}: {cnt}개")
    
    with_coords = sum(1 for d in data if d.get('lat') and d.get('lng'))
    log(f"   위경도 있음: {with_coords}개 ({with_coords/len(data)*100:.1f}%)" if data else "")
    
    # DB 적재
    if not args.no_db and data:
        log("\n💾 PostgreSQL 적재 중...")
        load_to_postgres(data)
    
    log("\n✅ 완료!")


if __name__ == "__main__":
    main()


