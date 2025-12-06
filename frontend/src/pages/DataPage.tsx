import React, { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, MapPin, Users, Loader2, MessageCircle, Heart, Eye } from 'lucide-react';
import { 
  getDataStats, 
  getPopularAttractions, 
  getCategoryDistribution,
  type DataStats,
  type PopularAttraction,
  type CategoryDistribution
} from '../api/adminData';

const DataPage: React.FC = () => {
  const [stats, setStats] = useState<DataStats | null>(null);
  const [popularAttractions, setPopularAttractions] = useState<PopularAttraction[]>([]);
  const [categories, setCategories] = useState<CategoryDistribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [statsData, attractionsData, categoriesData] = await Promise.all([
          getDataStats(),
          getPopularAttractions(8),
          getCategoryDistribution()
        ]);
        
        setStats(statsData);
        setPopularAttractions(attractionsData);
        setCategories(categoriesData);
        setError(null);
      } catch (err: any) {
        console.error('데이터 로드 실패:', err);
        setError(err.response?.data?.detail || '데이터를 불러오는데 실패했습니다');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto text-orange-500 mb-4" size={48} />
          <p className="text-gray-600 dark:text-gray-400">데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">⚠️ {error}</p>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 제주 관광 데이터</h1>
          <p className="text-gray-600">수집된 데이터와 통계를 확인하세요</p>
        </div>

        {/* 통계 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6 mb-8">
          <div className="card-jeju p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 text-sm">전체 사용자</span>
              <Users className="text-jeju-green-500" size={20} />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_users}명</div>
            <div className="text-xs text-gray-500 mt-1">가입 회원</div>
          </div>

          <div className="card-jeju p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 text-sm">생성된 일정</span>
              <BarChart3 className="text-jeju-orange-500" size={20} />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_schedules}개</div>
            <div className="text-xs text-gray-500 mt-1">누적 통계</div>
          </div>

          <div className="card-jeju p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 text-sm">채팅 세션</span>
              <MessageCircle className="text-purple-500" size={20} />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_chat_sessions}개</div>
            <div className="text-xs text-gray-500 mt-1">AI 대화</div>
          </div>

          <div className="card-jeju p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 text-sm">좋아요</span>
              <Heart className="text-red-500" size={20} />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_likes}개</div>
            <div className="text-xs text-gray-500 mt-1">누적</div>
          </div>

          <div className="card-jeju p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 text-sm">북마크</span>
              <TrendingUp className="text-blue-500" size={20} />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_bookmarks}개</div>
            <div className="text-xs text-gray-500 mt-1">누적</div>
          </div>

          <div className="card-jeju p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 text-sm">조회수</span>
              <Eye className="text-indigo-500" size={20} />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_views}회</div>
            <div className="text-xs text-gray-500 mt-1">누적</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 왼쪽: 인기 관광지 */}
          <div className="lg:col-span-2">
            <div className="card-jeju p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">🔥 인기 관광지 TOP {popularAttractions.length}</h2>
              
              {popularAttractions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <MapPin size={48} className="mx-auto mb-3 text-gray-400" />
                  <p>아직 데이터가 없습니다</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {popularAttractions.map((attraction) => (
                    <div
                      key={attraction.rank}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center space-x-4">
                        {/* 순위 */}
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                          attraction.rank === 1
                            ? 'bg-yellow-500'
                            : attraction.rank === 2
                            ? 'bg-gray-400'
                            : attraction.rank === 3
                            ? 'bg-orange-600'
                            : 'bg-gray-300'
                        }`}>
                          {attraction.rank}
                        </div>

                        {/* 정보 */}
                        <div className="flex items-center space-x-3">
                          <span className="text-3xl">{attraction.emoji}</span>
                          <div>
                            <h3 className="font-bold text-gray-900">{attraction.name}</h3>
                            <span className="text-sm text-gray-500">{attraction.category}</span>
                          </div>
                        </div>
                      </div>

                      {/* 통계 */}
                      <div className="text-right">
                        <div className="text-xl font-bold text-gray-900">
                          {attraction.count.toLocaleString()}회
                        </div>
                        <div className="text-xs text-gray-500">
                          일정 포함
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6 p-4 bg-jeju-blue-50 rounded-xl border border-jeju-blue-200">
                <div className="text-sm text-jeju-blue-800">
                  💡 <span className="font-semibold">실시간 집계:</span> 사용자들이 생성한 일정에서 가장 많이 선택된 관광지입니다
                </div>
              </div>
            </div>
          </div>

          {/* 오른쪽: 카테고리 & 기타 통계 */}
          <div className="space-y-6">
            {/* 카테고리 분포 */}
            <div className="card-jeju p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-6">📂 카테고리 분포</h3>
              
              {categories.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-sm">아직 데이터가 없습니다</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {categories.map((category) => {
                    // 카테고리별 색상 매핑
                    const colorMap: Record<string, string> = {
                      '자연': 'bg-jeju-green-500',
                      '해변': 'bg-jeju-blue-500',
                      '문화': 'bg-jeju-orange-500',
                      '맛집': 'bg-yellow-500',
                      '카페': 'bg-orange-400',
                      '액티비티': 'bg-purple-500',
                    };
                    const color = colorMap[category.name] || 'bg-gray-500';
                    
                    return (
                      <div key={category.name}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">{category.name}</span>
                          <span className="text-sm font-bold text-gray-900">
                            {category.count}개 ({category.percentage}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className={`${color} h-3 rounded-full transition-all duration-500`}
                            style={{ width: `${category.percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* 데이터베이스 현황 */}
            <div className="card-jeju p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">🗄️ 데이터베이스 현황</h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">사용자</span>
                  <span className="font-semibold text-gray-900">{stats.total_users}명</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">일정</span>
                  <span className="font-semibold text-gray-900">{stats.total_schedules}개</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">채팅 세션</span>
                  <span className="font-semibold text-gray-900">{stats.total_chat_sessions}개</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">PostgreSQL</span>
                  <span className="font-semibold text-jeju-blue-600">✓ 연결됨</span>
                </div>
              </div>
            </div>

            {/* 사용자 활동 통계 */}
            <div className="card-jeju p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">📈 사용자 활동</h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">좋아요</span>
                  <span className="font-semibold text-red-600">❤️ {stats.total_likes}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">북마크</span>
                  <span className="font-semibold text-blue-600">🔖 {stats.total_bookmarks}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">조회수</span>
                  <span className="font-semibold text-indigo-600">👁️ {stats.total_views}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">평균 일정당 조회</span>
                  <span className="font-semibold text-gray-900">
                    {stats.total_schedules > 0 
                      ? Math.round(stats.total_views / stats.total_schedules) 
                      : 0}회
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 요약 정보 */}
        <div className="mt-8 card-jeju p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📝 데이터 요약</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="bg-gradient-to-br from-orange-50 to-blue-50 rounded-xl p-4">
              <div className="font-bold text-gray-900 mb-2">💬 대화 효율성</div>
              <p className="text-gray-700">
                {stats.total_chat_sessions > 0 && stats.total_schedules > 0
                  ? `평균 ${Math.round((stats.total_chat_sessions / stats.total_schedules) * 100)}%의 채팅 세션이 일정으로 변환되었습니다`
                  : '아직 데이터가 부족합니다'}
              </p>
            </div>
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-4">
              <div className="font-bold text-gray-900 mb-2">🎯 사용자 참여도</div>
              <p className="text-gray-700">
                {stats.total_schedules > 0
                  ? `일정당 평균 ${((stats.total_likes + stats.total_bookmarks) / stats.total_schedules).toFixed(1)}개의 상호작용이 발생했습니다`
                  : '아직 데이터가 부족합니다'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataPage;



