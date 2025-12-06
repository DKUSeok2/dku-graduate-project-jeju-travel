# Jeju Travel Chatbot Backend Scripts

## 스크립트 목록

### 데이터베이스 초기화
```bash
python scripts/init_database.py
```

### Elasticsearch 인덱싱
```bash
python scripts/embedding/index_elasticsearch.py
```

### 데이터 수집 (추후 구현)
```bash
python scripts/data/crawl_attractions.py
```

## 데이터 폴더 구조

```
data/
├── attractions.csv        # 관광지 데이터
├── accommodations.csv     # 숙박 데이터
├── restaurants.csv        # 음식점 데이터
└── reviews/              # 후기 데이터 (RAG용)
```

## 진행 상황

- [x] 데이터베이스 스키마 정의
- [x] Elasticsearch 매핑 정의
- [ ] 데이터 수집 스크립트
- [ ] 임베딩 인덱싱 스크립트





