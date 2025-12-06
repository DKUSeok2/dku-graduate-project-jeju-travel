#!/usr/bin/env python
"""
VisitJeju JSON → RAG 문서 형식 변환 스크립트

4개의 VisitJeju JSON 파일을 RAG 문서 형식으로 변환:
- visitjeju_event.json (축제/행사)
- visitjeju_food.json (맛집/카페)
- visitjeju_hotel.json (숙박)
- visitjeju_tour.json (관광지)

Usage:
    python scripts/data/convert_visitjeju.py
    python scripts/data/convert_visitjeju.py --output visitjeju_rag.json
"""
import json
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터 디렉토리
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# 파일별 카테고리 매핑
FILE_CATEGORY_MAP = {
    "visitjeju_event.json": "축제/행사",
    "visitjeju_food.json": "맛집/카페",
    "visitjeju_hotel.json": "숙박",
    "visitjeju_tour.json": "관광지",
}

# Elasticsearch용 (관광지/축제만)
ES_FILES = ["visitjeju_event.json", "visitjeju_tour.json"]

# PostgreSQL용 (맛집/숙박)
PG_FILES = ["visitjeju_food.json", "visitjeju_hotel.json"]

# 지역 추출을 위한 패턴
REGION_PATTERNS = {
    "제주시": ["제주시", "애월", "한림", "조천", "구좌", "우도"],
    "서귀포시": ["서귀포시", "중문", "성산", "표선", "남원", "대정", "안덕"],
}


def extract_region(address: str) -> str:
    """주소에서 지역 추출"""
    if not address:
        return "제주시"  # 기본값
    
    for region, keywords in REGION_PATTERNS.items():
        for keyword in keywords:
            if keyword in address:
                return region
    
    return "제주시"  # 기본값


def generate_document_id(name: str, address: str) -> str:
    """문서 ID 생성 (이름 + 주소 해시)"""
    content = f"{name}_{address}"
    return hashlib.md5(content.encode()).hexdigest()


def extract_category_from_tags(tags: str, default_category: str) -> str:
    """태그에서 세부 카테고리 추출"""
    if not tags:
        return default_category
    
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    # 우선순위 키워드
    priority_keywords = [
        "카페", "디저트", "베이커리",
        "한식", "중식", "일식", "양식", "해물", "고기",
        "오름", "해변", "폭포", "동굴",
        "체험", "액티비티", "레저",
        "호텔", "펜션", "게스트하우스", "리조트",
        "축제", "행사", "공연",
    ]
    
    for keyword in priority_keywords:
        for tag in tag_list:
            if keyword in tag:
                return tag
    
    # 첫 번째 유의미한 태그 반환
    for tag in tag_list:
        if len(tag) > 1 and not tag.isdigit():
            return tag
    
    return default_category


def generate_query(name: str, category: str, tags: str) -> str:
    """검색 쿼리 생성"""
    queries = []
    
    # 기본 쿼리
    queries.append(f"{name} 정보")
    
    # 카테고리 기반 쿼리
    if "맛집" in category or "음식" in category:
        queries.append(f"제주 맛집 {name}")
    elif "카페" in category:
        queries.append(f"제주 카페 {name}")
    elif "숙박" in category or "호텔" in category:
        queries.append(f"제주 숙소 {name}")
    elif "관광" in category or "오름" in category:
        queries.append(f"제주 관광지 {name}")
    elif "축제" in category or "행사" in category:
        queries.append(f"제주 축제 {name}")
    
    # 태그 기반 추가 쿼리
    if tags:
        tag_list = [t.strip() for t in tags.split(",")[:3] if t.strip()]
        if tag_list:
            queries.append(f"제주 {' '.join(tag_list)}")
    
    return " | ".join(queries)


def create_document_text(item: Dict[str, Any], category: str) -> str:
    """RAG 문서 텍스트 생성"""
    lines = [f"# {item.get('이름', '알 수 없음')}"]
    
    # 카테고리
    lines.append(f"\n**카테고리**: {category}")
    
    # 주소
    if item.get("주소"):
        lines.append(f"**주소**: {item['주소']}")
    
    # 전화번호
    phone = item.get("전화번호")
    if phone and phone not in ["--", "-", "null", None]:
        lines.append(f"**전화번호**: {phone}")
    
    # 소개
    if item.get("소개"):
        intro = item["소개"].strip()
        if intro:
            lines.append(f"\n## 소개\n{intro}")
    
    # 태그
    if item.get("태그"):
        tags = item["태그"].replace(",", ", ").strip()
        if tags:
            lines.append(f"\n**태그**: {tags}")
    
    return "\n".join(lines)


def convert_visitjeju_item(item: Dict[str, Any], source_file: str) -> Optional[Dict[str, Any]]:
    """단일 VisitJeju 항목을 RAG 문서로 변환"""
    name = (item.get("이름") or "").strip()
    address = (item.get("주소") or "").strip()
    
    # 유효성 검사
    if not name or len(name) < 2:
        return None
    
    # 이상한 데이터 필터링
    bad_keywords = ["삭제", "준비중", "공사중", "폐업", "테스트", "샘플"]
    if any(kw in name for kw in bad_keywords):
        return None
    
    default_category = FILE_CATEGORY_MAP.get(source_file, "기타")
    category = extract_category_from_tags(item.get("태그", ""), default_category)
    
    # 문서 ID 생성
    doc_id = generate_document_id(name, address)
    
    # 쿼리 생성
    query = generate_query(name, category, item.get("태그", ""))
    
    # 문서 텍스트 생성
    document = create_document_text(item, category)
    
    # 지역 추출
    region = extract_region(address)
    
    return {
        "document_id": f"visitjeju_{doc_id}",
        "query": query,
        "document": document,
        "metadata": {
            "content_id": doc_id,
            "title": name,
            "category": category,
            "source_type": default_category,  # 원본 파일 타입
            "address": address,
            "region": region,
            "phone": item.get("전화번호"),
            "tags": item.get("태그", ""),
            "lat": None,  # 나중에 Geocoding으로 추가 가능
            "lng": None,
            "rating": None,  # VisitJeju에는 평점 없음
        }
    }


def load_and_convert_file(filename: str) -> List[Dict[str, Any]]:
    """단일 JSON 파일 로드 및 변환"""
    filepath = DATA_DIR / filename
    
    if not filepath.exists():
        logger.warning(f"⚠️ 파일 없음: {filename}")
        return []
    
    logger.info(f"📂 로딩: {filename}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"   원본 건수: {len(data)}")
    
    documents = []
    skipped = 0
    
    for item in data:
        doc = convert_visitjeju_item(item, filename)
        if doc:
            documents.append(doc)
        else:
            skipped += 1
    
    logger.info(f"   변환 완료: {len(documents)}건 (스킵: {skipped}건)")
    
    return documents


def main(output_file: str = "visitjeju_rag.json", es_only: bool = False):
    """메인 실행 함수
    
    Args:
        output_file: 출력 파일명
        es_only: True면 관광지/축제만 변환 (Elasticsearch용)
    """
    logger.info("🚀 VisitJeju → RAG 변환 시작")
    
    all_documents = []
    
    # 대상 파일 선택
    target_files = ES_FILES if es_only else FILE_CATEGORY_MAP.keys()
    
    if es_only:
        logger.info("📌 Elasticsearch용: 관광지/축제만 변환")
    
    for filename in target_files:
        documents = load_and_convert_file(filename)
        all_documents.extend(documents)
    
    # 중복 제거 (document_id 기준)
    seen_ids = set()
    unique_documents = []
    
    for doc in all_documents:
        if doc["document_id"] not in seen_ids:
            seen_ids.add(doc["document_id"])
            unique_documents.append(doc)
    
    logger.info(f"\n📊 총 {len(unique_documents)}건 (중복 제거: {len(all_documents) - len(unique_documents)}건)")
    
    # JSON 저장
    output_path = DATA_DIR / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique_documents, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 저장 완료: {output_path}")
    
    # 샘플 출력
    if unique_documents:
        logger.info("\n📝 샘플 (첫 번째 문서):")
        sample = unique_documents[0]
        logger.info(f"   ID: {sample['document_id']}")
        logger.info(f"   Query: {sample['query']}")
        logger.info(f"   Category: {sample['metadata']['category']}")
    
    return unique_documents


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert VisitJeju JSON to RAG format")
    parser.add_argument("--output", default="visitjeju_rag.json", help="Output filename")
    parser.add_argument("--es-only", action="store_true", help="관광지/축제만 변환 (Elasticsearch용)")
    args = parser.parse_args()
    
    main(args.output, es_only=args.es_only)

