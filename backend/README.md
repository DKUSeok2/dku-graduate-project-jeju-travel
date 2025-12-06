# 제주 AI 여행 플래너 백엔드

> Poetry로 관리되는 LangGraph 기반 멀티 에이전트 시스템

---

## 🚀 빠른 시작

### 1. Poetry 설치

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# 설치 확인
poetry --version
```

### 2. 의존성 설치

```bash
cd backend
poetry install
```

### 3. 가상환경 활성화

```bash
poetry shell
```

### 4. 환경변수 설정

```bash
# 프로젝트 루트로 이동
cd ..

# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (API 키 입력)
# - OPENAI_API_KEY
# - TAVILY_API_KEY
```

### 5. 개발 서버 실행

```bash
# 백엔드 디렉토리로 돌아가기
cd backend

# FastAPI 서버 시작
poetry run uvicorn src.api.app:app --reload
```

또는 가상환경 활성화 후:

```bash
poetry shell
uvicorn src.api.app:app --reload
```

### 6. API 문서 확인

브라우저에서 http://localhost:8000/docs 접속

---

## 📦 Poetry 명령어

### 패키지 추가/제거

```bash
# 패키지 추가
poetry add package-name

# 개발 의존성 추가
poetry add --group dev package-name

# 패키지 제거
poetry remove package-name
```

### 의존성 관리

```bash
# 모든 패키지 업데이트
poetry update

# 특정 패키지만 업데이트
poetry update langchain

# 설치된 패키지 목록
poetry show

# 의존성 트리
poetry show --tree
```

### 가상환경 관리

```bash
# 가상환경 정보
poetry env info

# 가상환경 재생성
poetry env remove python
poetry install
```

---

## 🧪 테스트

```bash
# 모든 테스트 실행
poetry run pytest

# 커버리지 포함
poetry run pytest --cov=src --cov-report=html

# 특정 테스트만 실행
poetry run pytest tests/tool_agents/test_rag_agent.py
```

---

## 🎨 코드 품질

### 포맷팅

```bash
# Black (코드 포맷터)
poetry run black src/ tests/

# isort (import 정렬)
poetry run isort src/ tests/
```

### 린팅

```bash
# Ruff
poetry run ruff check src/ tests/

# mypy (타입 체크)
poetry run mypy src/
```

---

## 📁 프로젝트 구조

```
backend/
├── src/
│   ├── api/                      # FastAPI 애플리케이션
│   │   └── app.py
│   ├── supervisor_agent/         # Supervisor Agent
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   ├── state.py
│   │   ├── prompt.py
│   │   ├── service.py
│   │   └── settings.py
│   ├── tool_agents/              # Tool Agents
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── domains.py
│   │   ├── rag_agent/
│   │   ├── sql_agent/
│   │   ├── web_search_agent/
│   │   ├── route_optimizer_agent/
│   │   └── map_visualization_agent/
│   ├── model/                    # LLM 실행 서비스
│   ├── storage/                  # 데이터베이스
│   ├── database.py
│   └── config.py
├── scripts/                      # 스크립트
│   ├── init_database.py
│   └── embedding/
├── tests/                        # 테스트
├── data/                         # 데이터 (CSV 등)
├── pyproject.toml               # Poetry 설정
├── poetry.lock                  # 의존성 Lock
├── Dockerfile
└── README.md
```

---

## 🐳 Docker 사용

### Docker Compose로 전체 시스템 실행

```bash
# 프로젝트 루트로 이동
cd ..

# Docker Compose 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 서비스 중지
docker-compose down
```

### Docker 내부에서 Poetry 사용

```bash
# Backend 컨테이너 접속
docker-compose exec backend bash

# Poetry 명령어 실행
poetry show
poetry add new-package
```

---

## 🛠️ 개발 워크플로우

### 1. 새 기능 개발

```bash
# 1. 브랜치 생성
git checkout -b feature/new-feature

# 2. 가상환경 활성화
poetry shell

# 3. 필요한 패키지 추가
poetry add new-package

# 4. 코드 작성
# ...

# 5. 테스트 작성 및 실행
poetry run pytest

# 6. 포맷팅
poetry run black src/ tests/
poetry run isort src/ tests/

# 7. 커밋
git add .
git commit -m "feat: add new feature"

# 8. Push
git push origin feature/new-feature
```

### 2. 의존성 추가 시

```bash
# 패키지 추가
poetry add package-name

# poetry.lock 파일이 자동으로 업데이트됨
# pyproject.toml과 poetry.lock 모두 커밋
git add pyproject.toml poetry.lock
git commit -m "chore: add package-name"
```

---

## 📊 데이터베이스

### 초기화

```bash
# Docker로 PostgreSQL 실행
cd ..
docker-compose up -d postgres

# 데이터베이스 초기화 스크립트 실행
cd backend
poetry run python scripts/init_database.py
```

### 연결 확인

```bash
# PostgreSQL 접속
docker-compose exec postgres psql -U jeju_user -d jeju_travel

# 테이블 확인
\dt

# 종료
\q
```

---

## 🔍 Elasticsearch

### 인덱싱

```bash
# Elasticsearch 실행
docker-compose up -d elasticsearch

# 임베딩 및 인덱싱
poetry run python scripts/embedding/index_elasticsearch.py
```

### 상태 확인

```bash
# 클러스터 상태
curl http://localhost:9200/_cluster/health

# 인덱스 목록
curl http://localhost:9200/_cat/indices
```

---

## 🚨 문제 해결

### Poetry 가상환경 문제

```bash
# 가상환경 삭제 후 재생성
poetry env remove python
poetry install
```

### 의존성 충돌

```bash
# Lock 파일 재생성
poetry lock --no-update
poetry install
```

### Docker 빌드 오류

```bash
# 캐시 없이 재빌드
docker-compose build --no-cache backend
docker-compose up -d
```

---

## 📚 참고 문서

- **Poetry 가이드**: [POETRY_GUIDE.md](./POETRY_GUIDE.md)
- **다음 단계**: [../NEXT_STEPS.md](../NEXT_STEPS.md)
- **프로젝트 구조**: [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)

### 외부 링크
- [Poetry 공식 문서](https://python-poetry.org/docs/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [LangChain 문서](https://python.langchain.com/)

---

## ✅ 개발 체크리스트

### 초기 설정
- [ ] Poetry 설치
- [ ] Python 3.11 설치
- [ ] `poetry install` 실행
- [ ] `.env` 파일 설정
- [ ] Docker 서비스 시작
- [ ] 데이터베이스 초기화

### 개발 중
- [ ] `poetry shell`로 가상환경 활성화
- [ ] 새 패키지는 `poetry add`로 추가
- [ ] 테스트 작성 및 실행
- [ ] 코드 포맷팅 (Black, isort)
- [ ] `poetry.lock` 파일 커밋

### 커밋 전
- [ ] 테스트 통과 확인
- [ ] 린터 에러 없음
- [ ] 불필요한 print 제거
- [ ] TODO 주석 정리

---

**마지막 업데이트**: 2025-10-26
