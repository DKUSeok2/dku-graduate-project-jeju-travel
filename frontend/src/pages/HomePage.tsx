import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Calendar } from 'lucide-react';
import { getStats } from '../api/stats';
import { getDashboard, getLLMUsage } from '../api/admin';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    attractions: 0,
    schedules: 0,
    users: 0,
  });
  const [adminStats, setAdminStats] = useState<any>(null);
  const [llmUsage, setLlmUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await fetchStats();
      if (user?.is_admin) {
        await fetchAdminStats();
      }
      setLoading(false);
    };
    fetchData();
  }, [user?.is_admin]);

  const fetchStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.error('통계 조회 실패:', error);
    }
  };

  const fetchAdminStats = async () => {
    try {
      const [dashboardData, llmData] = await Promise.all([
        getDashboard(),
        getLLMUsage(7),
      ]);
      setAdminStats(dashboardData);
      setLlmUsage(llmData);
    } catch (error) {
      console.error('관리자 통계 조회 실패:', error);
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 10000) {
      return `${(num / 10000).toFixed(1)}만`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}천`;
    }
    return num.toString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* 관리자는 모니터링만 표시 */}
      {user?.is_admin ? (
        <>
          {/* 페이지 헤더 */}
          <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex h-24 items-center justify-between gap-4 px-8">
              <div className="flex flex-col items-start justify-center gap-1">
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">대시보드</h1>
                <p className="text-gray-600 dark:text-gray-400 text-xs">핵심 지표를 빠르게 확인하세요</p>
              </div>
            </div>
          </div>

          {/* 관리자 모니터링 섹션 */}
          {loading ? (
            <div className="flex items-center justify-center p-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-jeju-orange-500 mx-auto mb-4"></div>
                <p className="text-gray-600 dark:text-gray-400">데이터 로딩 중...</p>
              </div>
            </div>
          ) : adminStats ? (
            <div className="space-y-6 p-8">
              {/* 상단 통계 카드 */}
              <div className="rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm bg-white dark:bg-gray-800 h-24">
                <div className="grid grid-cols-4 gap-0 h-full">
                  <div className="flex flex-col items-center justify-center border-r border-gray-200 dark:border-gray-700">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">전체 회원 수</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatNumber(adminStats.users.total)}
                    </div>
                  </div>
                  <div className="flex flex-col items-center justify-center border-r border-gray-200 dark:border-gray-700">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">생성된 일정</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatNumber(adminStats.schedules.total)}
                    </div>
                  </div>
                  <div className="flex flex-col items-center justify-center border-r border-gray-200 dark:border-gray-700">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">오늘 사용 토큰</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {adminStats.llm_usage.today_tokens > 0 
                        ? `${(adminStats.llm_usage.today_tokens / 1000).toFixed(1)}K`
                        : '0'
                      }
                    </div>
                  </div>
                  <div className="flex flex-col items-center justify-center">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">오늘 API 비용</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      ${adminStats.llm_usage.today_cost.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
              {/* LLM 사용량 차트 */}
              <div className="grid grid-cols-12 gap-6">
                {/* 일별 토큰 사용량 */}
                <div className="col-span-8">
                  <div className="rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm bg-white dark:bg-gray-800 p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">최근 7일 토큰 사용량</h3>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">일별 LLM API 사용 현황</p>
                      </div>
                    </div>
                    {llmUsage && llmUsage.daily_usage.length > 0 ? (
                      <div className="space-y-4">
                        {llmUsage.daily_usage.slice(-7).map((day: any, idx: number) => {
                          const maxTokens = Math.max(...llmUsage.daily_usage.map((d: any) => d.total_tokens), 1000);
                          const percentage = Math.max((day.total_tokens / maxTokens) * 100, 2);
                          
                          return (
                            <div key={idx}>
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-600 dark:text-gray-400 w-28">{day.date}</span>
                                <div className="flex items-center gap-4">
                                  <span className="text-sm font-bold text-gray-900 dark:text-white">
                                    {day.total_tokens > 0 ? `${(day.total_tokens / 1000).toFixed(1)}K` : '0'}
                                  </span>
                                  <span className="text-sm font-semibold text-jeju-orange-600">
                                    ${day.cost.toFixed(2)}
                                  </span>
                                </div>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                                <div
                                  className="bg-jeju-orange-500 h-2.5 rounded-full transition-all duration-500"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="text-center py-12 text-gray-600 dark:text-gray-400">
                        아직 사용 기록이 없습니다
                      </div>
                    )}
                  </div>
                </div>

                {/* 모델별 사용량 */}
                <div className="col-span-4">
                  <div className="rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm bg-white dark:bg-gray-800 p-6">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">모델별 사용</h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-6">AI 모델 호출 통계</p>
                    <div className="space-y-3">
                      {llmUsage && llmUsage.model_usage && llmUsage.model_usage.length > 0 ? (
                        llmUsage.model_usage.map((model: any, idx: number) => (
                          <div key={idx} className="p-4 bg-gray-100 dark:bg-gray-700 rounded-xl border border-gray-200 dark:border-gray-600 hover:border-jeju-orange-300 transition-all">
                            <div>
                              <div className="font-bold text-gray-900 dark:text-white text-sm mb-1">{model.model}</div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">호출 {model.count}회</div>
                            </div>
                            <div className="flex items-center justify-between text-sm mt-2">
                              <span className="text-gray-600 dark:text-gray-400">
                                {(model.total_tokens / 1000).toFixed(1)}K 토큰
                              </span>
                              <span className="font-bold text-jeju-orange-600">
                                ${model.cost.toFixed(2)}
                              </span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-8 text-gray-600 dark:text-gray-400 text-sm">
                          아직 LLM 사용 기록이 없습니다
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center p-12">
              <div className="text-center bg-white dark:bg-gray-800 rounded-2xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm">
                <p className="text-red-600 dark:text-red-400 text-xl font-semibold mb-4">데이터를 불러올 수 없습니다</p>
                <button
                  onClick={() => window.location.reload()}
                  className="px-6 py-3 bg-jeju-orange-500 text-white rounded-lg hover:bg-jeju-orange-600 transition-colors"
                >
                  다시 시도
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <>
          {/* 일반 사용자용 콘텐츠 */}
          {/* Hero Section - 귀여운 감귤 테마 */}
          <section className="relative overflow-hidden pt-20 pb-16">
            {/* 배경 장식 */}
            <div className="absolute top-10 right-10 text-8xl opacity-10 animate-bounce">🍊</div>
            <div className="absolute bottom-20 left-10 text-6xl opacity-10 animate-pulse">🏝️</div>
            <div className="absolute top-40 left-1/4 text-5xl opacity-10">🌺</div>
            
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="text-center">
                {/* 귀여운 인사말 */}
                <div className="inline-block mb-6 px-6 py-2 bg-orange-100 dark:bg-orange-900/30 rounded-full">
                  <span className="text-orange-600 dark:text-orange-400 font-medium text-sm">
                    ✨ 제주도 여행의 모든 것
                  </span>
                </div>
                
                <h1 className="text-5xl md:text-7xl font-black text-gray-900 dark:text-white mb-6 leading-tight">
                  제주 여행, 이제는 <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-orange-600">
                    쉽게
                  </span>
                </h1>
                
                <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
                  감귤처럼 상큼한 AI 추천으로 <br />
                  나만의 특별한 제주 여행을 만들어보세요 🍊
                </p>

                <div className="flex flex-wrap justify-center gap-4 mb-12">
                  <Link 
                    to="/chat" 
                    className="group inline-flex items-center gap-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white px-8 py-4 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all"
                  >
                    <MessageCircle size={24} className="group-hover:rotate-12 transition-transform" />
                    AI 여행 상담 시작
                  </Link>
                  <Link 
                    to="/schedule" 
                    className="inline-flex items-center gap-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-8 py-4 rounded-2xl font-bold text-lg border-2 border-gray-200 dark:border-gray-700 hover:border-orange-300 dark:hover:border-orange-500 hover:scale-105 transition-all shadow-md"
                  >
                    <Calendar size={24} />
                    내 일정 보기
                  </Link>
                </div>

                {/* 통계 카드 - 귀여운 스타일 */}
                <div className="grid grid-cols-3 gap-6 max-w-4xl mx-auto">
                  <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow border border-gray-100 dark:border-gray-700">
                    <div className="text-4xl mb-3">🏖️</div>
                    <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                      {stats.attractions.toLocaleString()}
                    </div>
                    <div className="text-gray-600 dark:text-gray-400 text-sm font-medium">관광지</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow border border-gray-100 dark:border-gray-700">
                    <div className="text-4xl mb-3">📅</div>
                    <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                      {stats.schedules.toLocaleString()}
                    </div>
                    <div className="text-gray-600 dark:text-gray-400 text-sm font-medium">생성된 일정</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow border border-gray-100 dark:border-gray-700">
                    <div className="text-4xl mb-3">👥</div>
                    <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                      {stats.users.toLocaleString()}
                    </div>
                    <div className="text-gray-600 dark:text-gray-400 text-sm font-medium">행복한 여행자</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Features Section - 카드 스타일 */}
          <section className="py-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-16">
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                  왜 제주 여행 플래너일까요?
                </h2>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                  AI가 만드는 맞춤형 제주 여행
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Feature 1 */}
                <div className="group bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all hover:-translate-y-2 border border-gray-100 dark:border-gray-700">
                  <div className="text-6xl mb-6 group-hover:scale-110 transition-transform">💬</div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">대화형 추천</h3>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                    원하는 여행 스타일을 말하면 <br />
                    딱 맞는 장소를 찾아드려요
                  </p>
                </div>

                {/* Feature 2 */}
                <div className="group bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all hover:-translate-y-2 border border-gray-100 dark:border-gray-700">
                  <div className="text-6xl mb-6 group-hover:scale-110 transition-transform">🗺️</div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">최적 경로</h3>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                    이동 시간을 최소화하는 <br />
                    효율적인 동선을 계산해요
                  </p>
                </div>

                {/* Feature 3 */}
                <div className="group bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all hover:-translate-y-2 border border-gray-100 dark:border-gray-700">
                  <div className="text-6xl mb-6 group-hover:scale-110 transition-transform">⭐</div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">실시간 정보</h3>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                    날씨, 운영시간 등 <br />
                    최신 정보를 확인할 수 있어요
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Popular Destinations - 귀여운 카드 */}
          <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-orange-50 to-white dark:from-gray-800 dark:to-gray-900">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                  인기 여행지 🔥
                </h2>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                  제주에서 가장 많이 찾는 명소
                </p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {[
                  { name: '한라산', emoji: '🏔️', tag: '등산', color: 'from-green-400 to-green-500' },
                  { name: '협재해수욕장', emoji: '🏖️', tag: '해변', color: 'from-blue-400 to-blue-500' },
                  { name: '성산일출봉', emoji: '🌋', tag: '명소', color: 'from-orange-400 to-orange-500' },
                  { name: '섭지코지', emoji: '🌊', tag: '경관', color: 'from-cyan-400 to-cyan-500' },
                ].map((place, idx) => (
                  <div key={idx} className="group bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-lg hover:shadow-2xl transition-all cursor-pointer hover:-translate-y-2 border border-gray-100 dark:border-gray-700">
                    <div className={`text-6xl mb-4 bg-gradient-to-br ${place.color} w-20 h-20 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg`}>
                      {place.emoji}
                    </div>
                    <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-2">{place.name}</h3>
                    <span className="inline-block px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded-full font-medium">
                      #{place.tag}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default HomePage;
