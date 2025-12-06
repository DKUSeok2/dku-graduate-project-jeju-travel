import { useNavigate } from 'react-router-dom';

interface BotCard {
  id: string;
  title: string;
  subtitle: string;
  gradient: string;
  badge: string;
  examples: string[];
}

const bots: BotCard[] = [
  {
    id: 'itinerary',
    title: '✈️ 일정 짜기',
    subtitle: '여행 일정 뚝딱 만들어드려요',
    gradient: 'from-orange-500 to-pink-500',
    badge: '일정 생성',
    examples: [
      '2박3일 가족여행 일정 짜줘',
      '혼자 여행 3박4일 코스 추천',
      '맛집 중심 1박2일 일정',
      '우도 포함 2박3일 계획 세워줘',
      '커플 여행 2박3일 럭셔리 코스',
      '아이와 함께 3박4일 체험 일정',
    ],
  },
  {
    id: 'sql',
    title: '🍽️ 맛집·카페 검색',
    subtitle: '제주 맛집, 카페, 숙소 찾아드려요',
    gradient: 'from-sky-500 to-indigo-500',
    badge: '장소 검색',
    examples: [
      '애월 맛집 5개 추천해줘',
      '평점 4.5 이상 카페 알려줘',
      '주차 가능한 흑돼지 맛집',
      '서귀포 중문 해산물 맛집',
      '제주시 근처 조식 맛집',
      '오션뷰 카페 추천해줘',
    ],
  },
  {
    id: 'rag',
    title: '🏝️ 관광지 안내',
    subtitle: '제주 관광지 정보 알려드려요',
    gradient: 'from-violet-500 to-purple-500',
    badge: '관광 정보',
    examples: [
      '성산일출봉은 어떤 곳이야?',
      '우도에서 뭐 하면 좋을까?',
      '한라산 등반 코스 알려줘',
      '제주 동쪽 볼거리 추천해줘',
      '협재해수욕장 주변 관광지',
      '천지연폭포 가는 방법',
    ],
  },
  {
    id: 'web',
    title: '🔍 실시간 검색',
    subtitle: '날씨, 뉴스, 최신 정보 검색해요',
    gradient: 'from-emerald-500 to-lime-500',
    badge: '실시간',
    examples: [
      '제주도 이번주 날씨 예보',
      '제주 공항 실시간 상황',
      '제주도 12월 축제 행사',
      '제주 맛집 블로그 후기',
      '제주도 렌트카 가격 비교',
      '제주 올레길 최신 정보',
    ],
  },
];

const BotPlaygroundPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        <div className="space-y-3">
          <p className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-white/70 text-orange-600 shadow-sm">
            🧪 플레이그라운드
          </p>
          <h1 className="text-3xl md:text-4xl font-black text-gray-900 dark:text-white">
            어떤 챗봇으로 시작할까요?
          </h1>
          <p className="text-gray-600 dark:text-gray-300 text-sm md:text-base">
            여행 일정부터 데이터 분석, 정보검색까지 목적에 맞는 챗봇을 골라 대화를 시작하세요.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {bots.map((bot) => (
            <div
              key={bot.id}
              className={`relative overflow-hidden rounded-3xl p-6 md:p-7 shadow-lg bg-gradient-to-br ${bot.gradient}`}
            >
              <div className="absolute inset-0 bg-white/10 mix-blend-overlay pointer-events-none" />
              <div className="relative space-y-4">
                {/* 헤더 - 클릭하면 기본 채팅 시작 */}
                <button
                  onClick={() => navigate(`/chat?botId=${bot.id}`)}
                  className="w-full text-left space-y-2 hover:opacity-90 transition-opacity"
                >
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-white/20 text-white/90">
                    {bot.badge}
                  </span>
                  <h2 className="text-xl md:text-2xl font-black text-white drop-shadow-sm">
                    {bot.title}
                  </h2>
                  <p className="text-sm md:text-base text-white/90 leading-relaxed">
                    {bot.subtitle}
                  </p>
                </button>
                
                {/* 예시 질의 버튼들 */}
                <div className="pt-2 border-t border-white/20">
                  <p className="text-xs text-white/70 mb-2">💡 예시 질의</p>
                  <div className="flex flex-wrap gap-2">
                    {bot.examples.map((example, idx) => (
                      <button
                        key={idx}
                        onClick={() => navigate(`/chat?botId=${bot.id}&query=${encodeURIComponent(example)}`)}
                        className="px-3 py-1.5 text-xs font-medium bg-white/20 hover:bg-white/30 text-white rounded-full transition-all hover:scale-105"
                      >
                        {example}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BotPlaygroundPage;


