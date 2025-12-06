# Poetry 사용 가이드

> 제주 AI 여행 플래너는 Poetry를 사용하여 Python 의존성을 관리합니다.

---

## 🔧 Poetry 설치

### macOS/Linux
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Windows (PowerShell)
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### 설치 확인
```bash
poetry --version
```

---

## 🚀 프로젝트 설정

### 1. 의존성 설치

```bash
cd jeju-travel-chatbot/backend
poetry install
```

이 명령어는 `pyproject.toml`에 정의된 모든 의존성을 설치하고 `poetry.lock` 파일을 생성합니다.

### 2. 가상환경 활성화

```bash
# 가상환경 활성화
poetry shell

# 또는 명령어 앞에 poetry run 사용
poetry run python script.py
poetry run uvicorn src.api.app:app --reload
```

### 3. 가상환경 정보 확인

```bash
# 가상환경 경로 확인
poetry env info

# 설치된 패키지 목록
poetry show

# 의존성 트리
poetry show --tree
```

---

## 📦 의존성 관리

### 패키지 추가

```bash
# 프로덕션 의존성 추가
poetry add fastapi
poetry add "langchain>=0.1.0"

# 개발 의존성 추가
poetry add --group dev pytest
poetry add --group dev black

# 특정 버전 지정
poetry add "numpy>=1.26.0,<2.0.0"
```

### 패키지 제거

```bash
poetry remove package-name
poetry remove --group dev pytest
```

### 패키지 업데이트

```bash
# 모든 패키지 업데이트
poetry update

# 특정 패키지만 업데이트
poetry update langchain

# 업데이트 가능한 패키지 확인 (실제 업데이트는 안 함)
poetry show --outdated
```

---

## 🔒 Lock 파일 관리

### poetry.lock 생성/업데이트

```bash
# pyproject.toml 변경 후 lock 파일 업데이트
poetry lock

# 의존성 재설치 (lock 파일 기준)
poetry install
```

### Lock 파일의 중요성

- ✅ **일관성**: 모든 환경에서 동일한 버전 사용
- ✅ **재현성**: 배포 시 정확한 버전 복원
- ✅ **Git에 커밋**: `poetry.lock`은 반드시 Git에 포함

---

## 🏃 개발 워크플로우

### 일반적인 개발 순서

```bash
# 1. 프로젝트 클론 후 의존성 설치
git clone <repository>
cd jeju-travel-chatbot/backend
poetry install

# 2. 가상환경 활성화
poetry shell

# 3. 개발 서버 실행
uvicorn src.api.app:app --reload

# 4. 새로운 패키지 필요 시
poetry add new-package

# 5. 테스트 실행
pytest tests/

# 6. 코드 포맷팅
black src/ tests/
isort src/ tests/
```

### 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 환경변수 자동 로드 (python-dotenv)
poetry add python-dotenv
```

---

## 🐳 Docker와 함께 사용

### Dockerfile에서 Poetry 사용

현재 `backend/Dockerfile`은 이미 Poetry를 사용하도록 설정되어 있습니다:

```dockerfile
# Poetry 설치
RUN pip install poetry==1.7.1

# 의존성 파일 복사
COPY pyproject.toml poetry.lock* ./

# 의존성 설치 (가상환경 없이)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# 애플리케이션 코드 복사
COPY . .

# 애플리케이션 설치
RUN poetry install --no-interaction --no-ansi
```

### Docker Compose에서 개발

```bash
# Docker 빌드 및 실행
docker-compose up --build

# Docker 내부에서 poetry 명령 실행
docker-compose exec backend poetry show
docker-compose exec backend poetry add new-package
```

---

## 🧪 테스트 및 품질 관리

### 테스트 실행

```bash
# pytest 실행
poetry run pytest

# 커버리지 포함
poetry run pytest --cov=src --cov-report=html

# 특정 테스트만 실행
poetry run pytest tests/tool_agents/test_rag_agent.py
```

### 코드 포맷팅

```bash
# Black (코드 포맷터)
poetry run black src/ tests/

# isort (import 정렬)
poetry run isort src/ tests/

# Ruff (린터)
poetry run ruff check src/ tests/
```

### 타입 체크

```bash
# mypy
poetry run mypy src/
```

---

## 📝 pyproject.toml 구조

### 현재 프로젝트 설정

```toml
[tool.poetry]
name = "jeju-travel-chatbot-backend"
version = "0.1.0"
description = "Jeju AI Travel Planner Backend"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
langchain = "^0.1.0"
langgraph = "^0.0.20"
# ... 기타 의존성

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
black = "^23.12.0"
# ... 기타 개발 의존성

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 의존성 그룹

- **main**: 프로덕션 의존성
- **dev**: 개발/테스트용 의존성

```bash
# 개발 의존성 제외하고 설치 (배포 시)
poetry install --without dev
```

---

## 🚨 문제 해결

### 가상환경 재생성

```bash
# 기존 가상환경 삭제
poetry env remove python

# 새로 생성
poetry install
```

### 캐시 초기화

```bash
# Poetry 캐시 삭제
poetry cache clear pypi --all

# 재설치
poetry install
```

### Lock 파일 충돌 해결

```bash
# Lock 파일 재생성
poetry lock --no-update

# 또는 의존성 업데이트 포함
poetry lock
```

### Python 버전 변경

```bash
# 특정 Python 버전으로 가상환경 생성
poetry env use python3.11
poetry install
```

---

## 💡 유용한 팁

### 1. 자동완성 설정

```bash
# Bash
poetry completions bash >> ~/.bash_completion

# Zsh
poetry completions zsh > ~/.zfunc/_poetry

# Fish
poetry completions fish > ~/.config/fish/completions/poetry.fish
```

### 2. Poetry 설정 변경

```bash
# 프로젝트 내 가상환경 생성 (.venv 폴더)
poetry config virtualenvs.in-project true

# 가상환경 경로 확인
poetry config virtualenvs.path
```

### 3. 스크립트 등록

`pyproject.toml`에 스크립트 추가:

```toml
[tool.poetry.scripts]
start = "uvicorn src.api.app:app --reload"
test = "pytest tests/"
format = "black src/ tests/ && isort src/ tests/"
```

사용:
```bash
poetry run start
poetry run test
poetry run format
```

---

## 📚 추가 자료

- [Poetry 공식 문서](https://python-poetry.org/docs/)
- [Poetry GitHub](https://github.com/python-poetry/poetry)
- [Dependency Groups](https://python-poetry.org/docs/managing-dependencies/#dependency-groups)
- [Scripts](https://python-poetry.org/docs/pyproject/#scripts)

---

## ✅ 체크리스트

### 초기 설정
- [ ] Poetry 설치 확인 (`poetry --version`)
- [ ] Python 3.11 설치 확인 (`python --version`)
- [ ] 프로젝트 의존성 설치 (`poetry install`)
- [ ] 가상환경 활성화 (`poetry shell`)
- [ ] 환경변수 설정 (`.env` 파일)

### 개발 중
- [ ] 새 패키지 추가 시 `poetry add` 사용
- [ ] `poetry.lock` 파일 Git에 커밋
- [ ] 테스트 실행 (`poetry run pytest`)
- [ ] 코드 포맷팅 (`poetry run black`)

### 배포 전
- [ ] 의존성 업데이트 확인 (`poetry show --outdated`)
- [ ] Lock 파일 최신화 (`poetry lock`)
- [ ] 테스트 통과 확인
- [ ] 프로덕션 의존성만 설치 (`poetry install --without dev`)

---

**마지막 업데이트**: 2025-10-26





