# 제주 AI 여행 플래너 - 프론트엔드

React + TypeScript + Tailwind CSS로 구현된 제주도 여행 추천 AI 챗봇 프론트엔드입니다.

## 🎨 디자인 컨셉

- **제주도 테마**: 감귤 오렌지, 바다 블루, 자연 그린 색상
- **참고 스타일**: 여기어때, 야놀자 스타일의 밝고 친근한 UI
- **카드 기반 레이아웃**: 모던하고 직관적인 사용자 경험

## 🚀 시작하기

### 설치

\`\`\`bash
npm install
\`\`\`

### 개발 서버 실행

\`\`\`bash
npm run dev
\`\`\`

개발 서버가 http://localhost:5173 에서 실행됩니다.

### 빌드

\`\`\`bash
npm run build
\`\`\`

### 미리보기

\`\`\`bash
npm run preview
\`\`\`

## 📁 프로젝트 구조

\`\`\`
frontend/
├── src/
│   ├── components/          # 공통 컴포넌트
│   │   ├── Navbar.tsx      # 네비게이션 바
│   │   └── Footer.tsx      # 푸터
│   │
│   ├── pages/              # 페이지 컴포넌트
│   │   ├── HomePage.tsx    # 메인 랜딩 페이지
│   │   ├── ChatPage.tsx    # AI 채팅 페이지
│   │   ├── SchedulePage.tsx # 내 일정 페이지
│   │   ├── DataPage.tsx    # 데이터 통계 페이지
│   │   └── AboutPage.tsx   # 프로젝트 소개 페이지
│   │
│   ├── App.tsx             # 메인 앱 (라우팅)
│   ├── main.tsx            # 엔트리 포인트
│   └── index.css           # Tailwind CSS 설정
│
├── tailwind.config.js      # Tailwind 설정
├── package.json
└── README.md
\`\`\`

## 🎯 주요 페이지

### 1. 홈 페이지 (\`/\`)
- 프로젝트 소개
- 주요 기능 설명
- 인기 관광지 미리보기
- CTA 버튼

### 2. AI 채팅 (\`/chat\`)
- 실시간 AI 대화
- 에이전트 상태 모니터링
- 관광지 추천 카드
- 지도 통합 (예정)

### 3. 내 일정 (\`/schedule\`)
- 일정 타임라인
- 경로 최적화 기능
- 일정 공유/다운로드
- 예상 비용 계산

### 4. 데이터 (\`/data\`)
- 인기 관광지 통계
- 카테고리별 분포
- 시스템 성능 지표

### 5. 소개 (\`/about\`)
- AI 에이전트 시스템 구조
- 기술 스택
- 프로젝트 정보

## 🎨 커스텀 색상 시스템

Tailwind config에 제주도 테마 색상이 정의되어 있습니다:

- **jeju-orange**: 감귤 색상 (메인 액션)
- **jeju-blue**: 바다 색상 (정보, 링크)
- **jeju-green**: 자연 색상 (성공, 완료)

사용 예:
\`\`\`tsx
<button className="bg-jeju-orange-400 hover:bg-jeju-orange-500">
  버튼
</button>
\`\`\`

## 🎭 커스텀 컴포넌트 클래스

\`index.css\`에 정의된 유틸리티 클래스:

- \`.btn-jeju-primary\`: 메인 버튼 (오렌지)
- \`.btn-jeju-secondary\`: 보조 버튼 (블루)
- \`.card-jeju\`: 카드 스타일
- \`.nav-link\`: 네비게이션 링크
- \`.text-gradient-jeju\`: 그라데이션 텍스트

## 🔧 기술 스택

- **React 18**: UI 라이브러리
- **TypeScript**: 타입 안정성
- **Vite**: 빠른 빌드 도구
- **Tailwind CSS**: 유틸리티 CSS 프레임워크
- **React Router**: 클라이언트 라우팅
- **Lucide React**: 아이콘
- **Axios**: HTTP 클라이언트 (예정)

## 📝 TODO

- [ ] 백엔드 API 연동
- [ ] React Leaflet 지도 통합
- [ ] 실시간 채팅 스트리밍 (SSE/WebSocket)
- [ ] 일정 저장 기능
- [ ] 모바일 반응형 최적화
- [ ] 다크 모드 지원

## 🎓 졸업 프로젝트

이 프로젝트는 LangGraph 기반 멀티 에이전트 시스템을 활용한 제주도 여행 추천 AI 챗봇 졸업 프로젝트의 프론트엔드입니다.

## 📞 문의

프로젝트 관련 문의사항은 이슈로 남겨주세요.
