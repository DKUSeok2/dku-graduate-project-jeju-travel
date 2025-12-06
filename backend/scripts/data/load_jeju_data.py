#!/usr/bin/env python
"""
제주관광공사 CSV 데이터 파싱 및 정제 스크립트
4개 CSV 파일을 파싱하여 Elasticsearch 적재용 데이터로 변환
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터 디렉토리
DATA_DIR = Path(__file__).parent.parent.parent / "data"


@dataclass
class JejuContent:
    """제주 콘텐츠 데이터 클래스"""
    content_id: str
    title: str
    category: str
    address: str
    lat: Optional[float]
    lng: Optional[float]
    rating: Optional[float]
    
    # 상세 정보 (조인된 데이터)
    weekday_open: Optional[str] = None
    weekday_close: Optional[str] = None
    weekend_open: Optional[str] = None
    weekend_close: Optional[str] = None
    
    # 추가 정보
    kid_friendly: bool = False
    parking: bool = False
    wheelchair: bool = False
    
    # 음식점 전용
    no_kids_zone: bool = False
    reservation: bool = False
    has_room: bool = False
    
    def to_document(self) -> str:
        """Elasticsearch document 형태로 변환"""
        lines = [
            f"# {self.title}",
            f"카테고리: {self.category}",
        ]
        
        if self.address:
            lines.append(f"주소: {self.address}")
        
        if self.rating and self.rating > 0:
            lines.append(f"평점: {self.rating}")
        
        # 영업시간
        if self.weekday_open and self.weekday_close:
            lines.append(f"평일 영업시간: {self.weekday_open} - {self.weekday_close}")
        if self.weekend_open and self.weekend_close:
            lines.append(f"주말 영업시간: {self.weekend_open} - {self.weekend_close}")
        
        # 시설 정보
        facilities = []
        if self.kid_friendly:
            facilities.append("유아 친화")
        if self.parking:
            facilities.append("주차 가능")
        if self.wheelchair:
            facilities.append("휠체어 접근 가능")
        if self.no_kids_zone:
            facilities.append("노키즈존")
        if self.reservation:
            facilities.append("예약 가능")
        if self.has_room:
            facilities.append("룸 보유")
        
        if facilities:
            lines.append(f"시설: {', '.join(facilities)}")
        
        return "\n".join(lines)
    
    def to_metadata(self) -> Dict[str, Any]:
        """메타데이터 반환"""
        return {
            "content_id": self.content_id,
            "title": self.title,
            "category": self.category,
            "lat": self.lat,
            "lng": self.lng,
            "rating": self.rating,
            "address": self.address,
        }


def load_main_content() -> pd.DataFrame:
    """메인 콘텐츠 CSV 로드 (위도, 경도, 카테고리 등)"""
    file_path = DATA_DIR / "제주관광공사_제주관광정보시스템(VISIT JEJU)_콘텐츠_20250307.CSV"
    
    logger.info(f"Loading main content from {file_path}")
    df = pd.read_csv(file_path, encoding='cp949')
    
    # 필요한 컬럼만 선택
    columns_map = {
        '콘텐츠아이디': 'content_id',
        '콘텐츠분류': 'category',
        '제목': 'title',
        '도로명주소': 'address',
        '위도': 'lat',
        '경도': 'lng',
        '평점': 'rating',
    }
    
    df = df.rename(columns=columns_map)
    df = df[list(columns_map.values())]
    
    # 결측값 처리
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    df['address'] = df['address'].fillna('')
    
    logger.info(f"Loaded {len(df)} main contents")
    return df


def load_attraction_details() -> pd.DataFrame:
    """관광콘텐츠 상세 정보 로드"""
    file_path = DATA_DIR / "제주관광공사_제주관광정보시스템(VISIT JEJU)_관광콘텐츠_20250307.CSV"
    
    logger.info(f"Loading attraction details from {file_path}")
    df = pd.read_csv(file_path, encoding='cp949')
    
    columns_map = {
        '콘텐츠명': 'title',
        '평일오픈시간': 'weekday_open',
        '평일클로즈시간': 'weekday_close',
        '주말오픈시간': 'weekend_open',
        '주말클로즈시간': 'weekend_close',
        '장애인주차구역': 'parking',
        '장애인화장실': 'wheelchair',
        '영유아돌봄시설': 'kid_friendly',
    }
    
    available_columns = {k: v for k, v in columns_map.items() if k in df.columns}
    df = df.rename(columns=available_columns)
    df = df[list(available_columns.values())]
    
    # boolean 변환
    for col in ['parking', 'wheelchair', 'kid_friendly']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).lower() == 'y' if pd.notna(x) else False)
    
    logger.info(f"Loaded {len(df)} attraction details")
    return df


def load_restaurant_details() -> pd.DataFrame:
    """음식점콘텐츠 상세 정보 로드"""
    file_path = DATA_DIR / "제주관광공사_제주관광정보시스템(VISIT JEJU)_음식점콘텐츠_20250307.CSV"
    
    logger.info(f"Loading restaurant details from {file_path}")
    df = pd.read_csv(file_path, encoding='cp949')
    
    columns_map = {
        '콘텐츠명': 'title',
        '노키즈존': 'no_kids_zone',
        '예약가능여부': 'reservation',
        '룸보유여부': 'has_room',
        '평일오픈시간': 'weekday_open',
        '평일클로즈시간': 'weekday_close',
        '주말오픈시간': 'weekend_open',
        '주말클로즈시간': 'weekend_close',
    }
    
    available_columns = {k: v for k, v in columns_map.items() if k in df.columns}
    df = df.rename(columns=available_columns)
    df = df[list(available_columns.values())]
    
    # boolean 변환
    for col in ['no_kids_zone', 'reservation', 'has_room']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).lower() == 'y' if pd.notna(x) else False)
    
    logger.info(f"Loaded {len(df)} restaurant details")
    return df


def load_accommodation_details() -> pd.DataFrame:
    """숙박콘텐츠 상세 정보 로드"""
    file_path = DATA_DIR / "제주관광공사_제주관광정보시스템(VISIT JEJU)_숙박콘텐츠_20250307.CSV"
    
    logger.info(f"Loading accommodation details from {file_path}")
    df = pd.read_csv(file_path, encoding='cp949')
    
    # 숙박의 경우 컬럼명 확인 필요
    logger.info(f"Accommodation columns: {df.columns.tolist()[:10]}")
    
    # title 컬럼 찾기
    title_col = None
    for col in df.columns:
        if '콘텐츠명' in col or '제목' in col or '이름' in col:
            title_col = col
            break
    
    if title_col:
        df = df.rename(columns={title_col: 'title'})
        df = df[['title']]
    else:
        df = pd.DataFrame(columns=['title'])
    
    logger.info(f"Loaded {len(df)} accommodation details")
    return df


def merge_all_data() -> List[JejuContent]:
    """모든 데이터를 조인하여 JejuContent 리스트로 반환"""
    # 메인 데이터 로드
    main_df = load_main_content()
    
    # 상세 데이터 로드
    attraction_df = load_attraction_details()
    restaurant_df = load_restaurant_details()
    accommodation_df = load_accommodation_details()
    
    # 조인을 위해 상세 데이터에 타입 태그 추가
    attraction_df['detail_type'] = 'attraction'
    restaurant_df['detail_type'] = 'restaurant'
    accommodation_df['detail_type'] = 'accommodation'
    
    # 모든 상세 데이터 합치기
    all_details = pd.concat([attraction_df, restaurant_df, accommodation_df], ignore_index=True)
    
    # 메인 데이터와 조인 (title 기준)
    merged_df = main_df.merge(all_details, on='title', how='left')
    
    # JejuContent 객체로 변환
    contents = []
    for _, row in merged_df.iterrows():
        # 위도/경도가 없는 경우 스킵
        if pd.isna(row.get('lat')) or pd.isna(row.get('lng')):
            continue
        
        content = JejuContent(
            content_id=str(row.get('content_id', '')),
            title=str(row.get('title', '')),
            category=str(row.get('category', '')),
            address=str(row.get('address', '')),
            lat=float(row['lat']) if pd.notna(row.get('lat')) else None,
            lng=float(row['lng']) if pd.notna(row.get('lng')) else None,
            rating=float(row['rating']) if pd.notna(row.get('rating')) else None,
            weekday_open=str(row.get('weekday_open', '')) if pd.notna(row.get('weekday_open')) else None,
            weekday_close=str(row.get('weekday_close', '')) if pd.notna(row.get('weekday_close')) else None,
            weekend_open=str(row.get('weekend_open', '')) if pd.notna(row.get('weekend_open')) else None,
            weekend_close=str(row.get('weekend_close', '')) if pd.notna(row.get('weekend_close')) else None,
            kid_friendly=bool(row.get('kid_friendly', False)),
            parking=bool(row.get('parking', False)),
            wheelchair=bool(row.get('wheelchair', False)),
            no_kids_zone=bool(row.get('no_kids_zone', False)),
            reservation=bool(row.get('reservation', False)),
            has_room=bool(row.get('has_room', False)),
        )
        contents.append(content)
    
    logger.info(f"Merged {len(contents)} contents with valid coordinates")
    return contents


def get_category_stats(contents: List[JejuContent]) -> Dict[str, int]:
    """카테고리별 통계 반환"""
    stats = {}
    for content in contents:
        category = content.category
        stats[category] = stats.get(category, 0) + 1
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))


# ============================================
# Query 자동 생성 로직
# ============================================

# 카테고리별 기본 질의 템플릿
CATEGORY_QUERIES = {
    "관광지": [
        "제주 관광지 추천",
        "제주도 가볼만한 곳",
        "제주 명소 추천",
    ],
    "음식점": [
        "제주 맛집 추천",
        "제주도 음식점 추천",
        "제주 맛있는 식당",
    ],
    "숙박": [
        "제주 숙소 추천",
        "제주도 호텔 추천",
        "제주 펜션 추천",
    ],
    "축제/행사": [
        "제주 축제 정보",
        "제주도 행사",
        "제주 이벤트",
    ],
    "쇼핑": [
        "제주 쇼핑 추천",
        "제주도 기념품",
        "제주 특산품",
    ],
    "테마여행": [
        "제주 테마여행",
        "제주도 여행 코스",
    ],
}

# 키워드 기반 질의 매핑
KEYWORD_QUERIES = {
    # 자연/경관
    "해변": ["해변 추천", "바다 볼 수 있는 곳", "해수욕장 추천"],
    "해수욕장": ["해수욕장 추천", "수영할 수 있는 곳"],
    "일출": ["일출 명소", "일출 볼 수 있는 곳", "새벽에 가기 좋은 곳"],
    "일몰": ["일몰 명소", "노을 보기 좋은 곳", "석양 명소"],
    "오름": ["오름 추천", "등산하기 좋은 곳", "트레킹 코스"],
    "폭포": ["폭포 추천", "물놀이 할 수 있는 곳"],
    "동굴": ["동굴 추천", "용암동굴"],
    "숲": ["숲 산책", "힐링 장소", "자연 속 산책"],
    "공원": ["공원 추천", "산책하기 좋은 곳"],
    
    # 체험/활동
    "박물관": ["박물관 추천", "실내 관광지", "비 오는 날 가기 좋은 곳"],
    "미술관": ["미술관 추천", "전시 볼 곳"],
    "체험": ["체험 프로그램", "체험 활동"],
    "카페": ["카페 추천", "뷰 좋은 카페", "분위기 좋은 카페"],
    "테마파크": ["테마파크 추천", "놀이공원"],
    "수족관": ["수족관", "아쿠아리움"],
    "골프": ["골프장 추천", "골프 칠 곳"],
    "스파": ["스파 추천", "온천", "찜질방"],
    
    # 음식
    "흑돼지": ["흑돼지 맛집", "제주 흑돼지"],
    "해산물": ["해산물 맛집", "회 맛집", "해물 맛집"],
    "국수": ["국수 맛집", "제주 국수"],
    "고기국수": ["고기국수 맛집"],
    "갈치": ["갈치 맛집", "갈치조림 맛집"],
    "전복": ["전복 맛집", "전복죽 맛집"],
    "횟집": ["횟집 추천", "회 맛집"],
    "브런치": ["브런치 맛집", "브런치 카페"],
    "디저트": ["디저트 맛집", "케이크 맛집"],
    
    # 가족/동반
    "가족": ["가족 여행", "가족과 가기 좋은 곳"],
    "아이": ["아이와 가기 좋은 곳", "키즈 프렌들리", "어린이 동반"],
    "데이트": ["데이트 코스", "커플 여행"],
    "반려동물": ["반려동물 동반", "펫 프렌들리"],
    
    # 지역
    "제주시": ["제주시 근처", "제주시 주변"],
    "서귀포": ["서귀포 근처", "서귀포 주변"],
    "애월": ["애월 근처", "애월 맛집", "애월 카페"],
    "성산": ["성산 근처", "성산 주변"],
    "중문": ["중문 근처", "중문 주변"],
    "협재": ["협재 근처", "협재 해변"],
    "우도": ["우도 추천", "우도 가볼곳"],
}


@dataclass
class RAGDocument:
    """Elasticsearch에 적재할 RAG 문서"""
    document_id: str
    query: str
    document: str
    metadata: Dict[str, Any]
    embedding: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "query": self.query,
            "document": self.document,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }


def generate_document_id(query: str, document: str) -> str:
    """query + document 기반 고유 ID 생성"""
    import hashlib
    key = (query + document).encode('utf-8')
    return hashlib.sha256(key).hexdigest()[:32]


def generate_queries_for_content(content: JejuContent) -> List[str]:
    """콘텐츠에 대한 검색 질의 생성"""
    queries = []
    
    # 1. 직접 검색 (이름 기반)
    queries.append(f"{content.title} 정보")
    queries.append(f"{content.title} 위치")
    queries.append(f"{content.title}")
    
    # 2. 카테고리 기반 질의
    category_queries = CATEGORY_QUERIES.get(content.category, [])
    queries.extend(category_queries[:2])  # 최대 2개
    
    # 3. 키워드 기반 질의 (제목에서 키워드 추출)
    title_lower = content.title.lower()
    for keyword, keyword_queries in KEYWORD_QUERIES.items():
        if keyword in title_lower or keyword in content.address:
            queries.extend(keyword_queries[:2])  # 최대 2개
            break  # 첫 번째 매칭만
    
    # 4. 시설 기반 질의
    if content.kid_friendly:
        queries.append("아이와 함께 가기 좋은 곳")
    if content.no_kids_zone:
        queries.append("조용한 분위기")
    if content.reservation:
        queries.append("예약 가능한 곳")
    
    # 중복 제거
    return list(dict.fromkeys(queries))


def create_rag_documents(contents: List[JejuContent]) -> List[RAGDocument]:
    """JejuContent 리스트를 RAGDocument 리스트로 변환"""
    rag_docs = []
    
    for content in contents:
        # document 텍스트 생성
        document_text = content.to_document()
        metadata = content.to_metadata()
        
        # 여러 query 생성
        queries = generate_queries_for_content(content)
        
        for query in queries:
            doc_id = generate_document_id(query, document_text)
            rag_doc = RAGDocument(
                document_id=doc_id,
                query=query,
                document=document_text,
                metadata=metadata,
            )
            rag_docs.append(rag_doc)
    
    logger.info(f"Generated {len(rag_docs)} RAG documents from {len(contents)} contents")
    return rag_docs


def save_rag_documents_to_json(rag_docs: List[RAGDocument], output_path: Path):
    """RAG 문서를 JSON 파일로 저장 (임베딩 생성 전)"""
    data = [doc.to_dict() for doc in rag_docs]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(rag_docs)} documents to {output_path}")


if __name__ == "__main__":
    # 테스트 실행
    contents = merge_all_data()
    
    print(f"\n총 {len(contents)}개 콘텐츠 로드됨")
    print("\n카테고리별 통계:")
    stats = get_category_stats(contents)
    for category, count in stats.items():
        print(f"  {category}: {count}개")
    
    # RAG 문서 생성
    print("\n" + "="*60)
    print("RAG 문서 생성 중...")
    rag_docs = create_rag_documents(contents)
    
    print(f"\n총 {len(rag_docs)}개 RAG 문서 생성됨")
    print(f"평균 {len(rag_docs) / len(contents):.1f}개 질의/콘텐츠")
    
    print("\n샘플 RAG 문서:")
    for doc in rag_docs[:5]:
        print(f"\n{'='*50}")
        print(f"Query: {doc.query}")
        print(f"Document ID: {doc.document_id[:16]}...")
        print(f"Document (first 100 chars): {doc.document[:100]}...")
    
    # JSON 저장 (테스트)
    output_path = DATA_DIR / "rag_documents_preview.json"
    save_rag_documents_to_json(rag_docs[:100], output_path)
    print(f"\n미리보기 저장: {output_path}")

