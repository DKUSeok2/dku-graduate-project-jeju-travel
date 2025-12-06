#!/usr/bin/env python3
"""
🍽️ 네이버 플레이스 맛집/카페 데이터 크롤링 스크립트

제주도 맛집, 카페 데이터를 네이버 플레이스에서 크롤링합니다.

Usage:
    python crawl_food.py                    # 전체 크롤링
    python crawl_food.py --test             # 테스트 (5개 키워드만)
    python crawl_food.py --skip-details     # 상세정보 수집 건너뛰기
    nohup python crawl_food.py > crawl_food.log 2>&1 &  # 백그라운드 실행
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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

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
    "timeout": 60000,
    "headless": True,
    "max_retries": 2,
}

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

# ============================================================================
# 키워드
# ============================================================================

FOOD_KEYWORDS = [
    # 지역별 맛집
    "제주시 맛집", "서귀포 맛집", "애월 맛집", "함덕 맛집",
    "중문 맛집", "성산 맛집", "한림 맛집", "조천 맛집",
    "우도 맛집", "협재 맛집",
    
    # 음식 종류별
    "제주 흑돼지", "제주 횟집", "제주 고기국수", "제주 갈치조림",
    "제주 해물탕", "제주 전복죽", "제주 삼겹살", "제주 회",
    "제주 해산물", "제주 한식", "제주 분식",
    
    # 지역별 카페
    "제주시 카페", "서귀포 카페", "애월 카페", "함덕 카페",
    "중문 카페", "성산 카페", "협재 카페", "한림 카페",
    "제주 오션뷰 카페", "제주 감성카페",
]

# ============================================================================
# 유틸리티
# ============================================================================

def log(msg: str):
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


def save_data(data: List[Dict], prefix: str = "naver_food"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_path = DATA_DIR / f"{prefix}_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"💾 JSON 저장: {json_path}")
    
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        csv_path = DATA_DIR / f"{prefix}_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        log(f"💾 CSV 저장: {csv_path}")
    except ImportError:
        pass
    
    return json_path


# ============================================================================
# 크롤링 함수
# ============================================================================

async def get_details(page: Page, place_id: str) -> Dict:
    """음식점 상세 정보 수집"""
    details = {
        "rating": None,
        "review_count": 0,
        "address": "",
        "business_hours": "",
        "lat": None,
        "lng": None,
        "phone": "",
        "min_price": None,
        "max_price": None,
        "price_range": "",
        "menus": [],
        "parking": False,
        "kid_friendly": False,
        "pet_friendly": False,
        "wifi": False,
    }
    
    if not place_id:
        return details
    
    detail_url = f"https://m.place.naver.com/restaurant/{place_id}/home"
    
    # 재시도 로직
    for attempt in range(CONFIG["max_retries"] + 1):
        try:
            await page.goto(detail_url, timeout=CONFIG["timeout"], wait_until="domcontentloaded")
            await asyncio.sleep(2)
            break
        except:
            if attempt < CONFIG["max_retries"]:
                await asyncio.sleep(3)
                continue
            else:
                return details
    
    try:
        # 평점
        try:
            rating_elem = await page.query_selector('.PXMot, .LXIwF')
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
            addr_elem = await page.query_selector('.LDgIH, .IH7VW')
            if addr_elem:
                details["address"] = await addr_elem.inner_text()
        except:
            pass
        
        # 영업시간
        try:
            hours_elem = await page.query_selector('.A_cdD, .MxgIj')
            if hours_elem:
                details["business_hours"] = await hours_elem.inner_text()
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
        
        # 편의시설
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
            if '와이파이' in full_text.lower() or 'wifi' in full_text.lower():
                details["wifi"] = True
        except:
            pass
            
    except:
        pass
    
    # 메뉴 정보 수집
    try:
        menu_url = f"https://m.place.naver.com/restaurant/{place_id}/menu/list"
        await page.goto(menu_url, timeout=CONFIG["timeout"], wait_until="domcontentloaded")
        await asyncio.sleep(1)
        
        menu_items = await page.query_selector_all('.E2jtL, .menu_item, [class*="MenuItem"]')
        prices = []
        
        for item in menu_items[:10]:
            try:
                name_elem = await item.query_selector('.lPzHi, .menu_name, [class*="name"]')
                name = await name_elem.inner_text() if name_elem else ""
                
                price_elem = await item.query_selector('.GXS1X, .menu_price, [class*="price"]')
                price_text = await price_elem.inner_text() if price_elem else ""
                
                price_match = re.search(r'(\d[\d,]*)', price_text)
                price = int(price_match.group(1).replace(',', '')) if price_match else None
                
                if name and price:
                    details["menus"].append({"name": name.strip(), "price": price})
                    prices.append(price)
            except:
                continue
        
        if prices:
            details["min_price"] = min(prices)
            details["max_price"] = max(prices)
            
            main_prices = [p for p in prices if p >= 10000]
            avg = sum(main_prices) // len(main_prices) if main_prices else sum(prices) // len(prices)
            
            if avg < 12000:
                details["price_range"] = "저렴"
            elif avg < 25000:
                details["price_range"] = "보통"
            elif avg < 50000:
                details["price_range"] = "비쌈"
            else:
                details["price_range"] = "고급"
    except:
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
                
                naver_id = None
                link_elem = await item.query_selector('a[href*="place.naver.com"]')
                if link_elem:
                    href = await link_elem.get_attribute('href')
                    id_match = re.search(r'/(?:place|restaurant)/(\d+)', href)
                    if id_match:
                        naver_id = id_match.group(1)
                
                if not naver_id or naver_id in seen_ids:
                    continue
                seen_ids.add(naver_id)
                
                category = keyword
                try:
                    cat_elem = await item.query_selector('em[class*="_item_category"]')
                    if cat_elem:
                        category = (await cat_elem.inner_text()).strip()
                except:
                    pass
                
                address = ""
                try:
                    addr_elem = await item.query_selector('button[class*="_item_address"]')
                    if addr_elem:
                        address = (await addr_elem.inner_text()).replace("주소보기", "").strip()
                except:
                    pass
                
                results.append({
                    "naver_id": naver_id,
                    "name": name,
                    "category": category,
                    "address": address,
                    "keyword": keyword,
                    "place_type": "restaurant",
                    "url": f"https://m.place.naver.com/restaurant/{naver_id}/home",
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
        save_data(all_results, "naver_food_search")
        
        if not skip_details and all_results:
            log("📌 2단계: 상세 정보 수집")
            
            iterator = tqdm(all_results, desc="상세정보") if HAS_TQDM else all_results
            save_interval = 100
            
            for i, place in enumerate(iterator):
                place_id = place.get("naver_id")
                
                if place_id:
                    details = await get_details(page, place_id)
                    place.update(details)
                
                await random_delay()
                
                if (i + 1) % save_interval == 0:
                    save_data(all_results, f"naver_food_checkpoint_{i+1}")
            
            log(f"✅ 상세 정보 수집 완료")
        
        save_data(all_results, "naver_food_final")
        
    finally:
        await close_browser(playwright, browser)
    
    return all_results


def load_to_postgres(data: List[Dict]):
    """PostgreSQL에 적재"""
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        log("❌ sqlalchemy 없음")
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
                        min_price, max_price, price_range,
                        parking, kid_friendly, pet_friendly, wifi,
                        business_hours, url
                    ) VALUES (
                        :naver_id, :name, :category, :address, :phone,
                        :rating, :review_count, :lat, :lng, :place_type,
                        :min_price, :max_price, :price_range,
                        :parking, :kid_friendly, :pet_friendly, :wifi,
                        :business_hours, :url
                    )
                    ON CONFLICT (naver_id) DO UPDATE SET
                        rating = EXCLUDED.rating,
                        review_count = EXCLUDED.review_count,
                        lat = EXCLUDED.lat,
                        lng = EXCLUDED.lng,
                        min_price = EXCLUDED.min_price,
                        max_price = EXCLUDED.max_price,
                        price_range = EXCLUDED.price_range,
                        address = EXCLUDED.address
                    RETURNING id
                """)
                
                try:
                    result = conn.execute(place_sql, {
                        "naver_id": item.get("naver_id"),
                        "name": item.get("name"),
                        "category": item.get("category"),
                        "address": item.get("address"),
                        "phone": item.get("phone", ""),
                        "rating": rating,
                        "review_count": review_count,
                        "lat": item.get("lat"),
                        "lng": item.get("lng"),
                        "place_type": "restaurant",
                        "min_price": item.get("min_price"),
                        "max_price": item.get("max_price"),
                        "price_range": item.get("price_range", ""),
                        "parking": item.get("parking", False),
                        "kid_friendly": item.get("kid_friendly", False),
                        "pet_friendly": item.get("pet_friendly", False),
                        "wifi": item.get("wifi", False),
                        "business_hours": item.get("business_hours", ""),
                        "url": item.get("url", ""),
                    })
                    
                    # 메뉴 저장
                    place_id = result.fetchone()[0]
                    menus = item.get("menus", [])
                    if menus and place_id:
                        conn.execute(text("DELETE FROM menus WHERE place_id = :place_id"), {"place_id": place_id})
                        for menu in menus:
                            conn.execute(text("""
                                INSERT INTO menus (place_id, name, price)
                                VALUES (:place_id, :name, :price)
                            """), {
                                "place_id": place_id,
                                "name": menu.get("name"),
                                "price": menu.get("price"),
                            })
                except Exception as e:
                    log(f"⚠️ 저장 실패 ({item.get('name')}): {e}")
            
            conn.commit()
        
        log(f"✅ {len(data)}개 장소 PostgreSQL 적재 완료!")
        
    except Exception as e:
        log(f"❌ DB 연결 실패: {e}")


def main():
    parser = argparse.ArgumentParser(description="네이버 플레이스 맛집/카페 크롤링")
    parser.add_argument("--test", action="store_true", help="테스트 모드")
    parser.add_argument("--skip-details", action="store_true", help="상세정보 건너뛰기")
    parser.add_argument("--no-db", action="store_true", help="DB 적재 건너뛰기")
    parser.add_argument("--max-per-keyword", type=int, default=30)
    args = parser.parse_args()
    
    log("=" * 60)
    log("🍽️ 네이버 플레이스 맛집/카페 크롤링")
    log("=" * 60)
    
    keywords = FOOD_KEYWORDS[:5] if args.test else FOOD_KEYWORDS
    log(f"📋 키워드: {len(keywords)}개")
    
    data = asyncio.run(crawl_all(
        keywords=keywords,
        max_per_keyword=args.max_per_keyword,
        skip_details=args.skip_details,
    ))
    
    log(f"\n📊 결과: {len(data)}개 장소")
    
    if not args.no_db and data:
        log("\n💾 PostgreSQL 적재 중...")
        load_to_postgres(data)
    
    log("\n✅ 완료!")


if __name__ == "__main__":
    main()


