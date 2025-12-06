/**
 * Courses Page - 추천 여행 코스 (사용자 공유 일정)
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, MapPin, Users, Calendar as CalendarIcon, Sparkles, SlidersHorizontal } from 'lucide-react';
import { getPublicSchedules } from '../api/schedules';
import type { Schedule } from '../api/schedules';
import { format, differenceInDays } from 'date-fns';
import { ko } from 'date-fns/locale';

const CoursesPage: React.FC = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [filteredSchedules, setFilteredSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // 필터링/정렬 상태
  const [sortBy, setSortBy] = useState<'latest' | 'popular' | 'oldest'>('latest');
  const [durationFilter, setDurationFilter] = useState<'all' | '1' | '2-3' | '4+'>('all');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchPublicSchedules();
  }, []);

  useEffect(() => {
    applyFiltersAndSort();
  }, [schedules, sortBy, durationFilter]);

  const fetchPublicSchedules = async () => {
    try {
      setLoading(true);
      const data = await getPublicSchedules();
      setSchedules(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || '일정을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const applyFiltersAndSort = () => {
    let result = [...schedules];

    // 기간 필터링
    if (durationFilter !== 'all') {
      result = result.filter((schedule) => {
        const days = differenceInDays(new Date(schedule.end_date), new Date(schedule.start_date)) + 1;
        if (durationFilter === '1') return days === 1;
        if (durationFilter === '2-3') return days >= 2 && days <= 3;
        if (durationFilter === '4+') return days >= 4;
        return true;
      });
    }

    // 정렬
    result.sort((a, b) => {
      if (sortBy === 'latest') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
      if (sortBy === 'oldest') {
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      }
      if (sortBy === 'popular') {
        // 좋아요 수로 정렬
        return (b.likes_count || 0) - (a.likes_count || 0);
      }
      return 0;
    });

    setFilteredSchedules(result);
  };

  const getDuration = (startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days = differenceInDays(end, start) + 1;
    
    if (days === 1) return '당일';
    return `${days - 1}박 ${days}일`;
  };

  const getAttractionCount = (attractions: any) => {
    if (!attractions) return 0;
    if (Array.isArray(attractions)) return attractions.length;
    if (typeof attractions === 'object') return Object.keys(attractions).length;
    return 0;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">🍊</div>
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400 font-medium">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-orange-400 via-orange-500 to-orange-600 text-white py-20">
        {/* 배경 장식 */}
        <div className="absolute top-5 right-10 text-6xl opacity-20 animate-pulse">✨</div>
        <div className="absolute bottom-5 left-10 text-5xl opacity-20 animate-bounce">🏝️</div>
        
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-block mb-4 px-6 py-2 bg-white/20 backdrop-blur-sm rounded-full">
            <span className="text-white font-medium text-sm">
              ✨ 여행자들의 추천 코스
            </span>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-black mb-6">
            추천 여행 코스
          </h1>
          
          <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto">
            다른 여행자들이 직접 다녀온 제주 여행 일정을<br />
            참고해서 나만의 여행을 만들어보세요 🗺️
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-6 py-4 rounded-2xl shadow-lg">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚠️</span>
              <span className="font-medium">{error}</span>
            </div>
          </div>
        </div>
      )}

      {/* Schedules Grid */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {schedules.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-block p-8 bg-white dark:bg-gray-800 rounded-3xl shadow-xl mb-6">
              <CalendarIcon className="mx-auto h-20 w-20 text-orange-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400 text-xl font-medium mb-6">
                아직 공유된 일정이 없어요
              </p>
              <Link
                to="/schedule"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white px-8 py-4 rounded-2xl font-bold hover:shadow-xl hover:scale-105 transition-all"
              >
                <Sparkles size={20} />
                내 일정을 공유해보세요
              </Link>
            </div>
          </div>
        ) : (
          <>
            {/* 필터 & 정렬 바 */}
            <div className="mb-8 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                    총 <span className="text-orange-600 dark:text-orange-400">{filteredSchedules.length}개</span>의 여행 코스
                  </h3>
                </div>
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-orange-50 dark:hover:bg-orange-900/30 text-gray-700 dark:text-gray-300 rounded-lg font-medium transition-all"
                >
                  <SlidersHorizontal size={18} />
                  필터/정렬
                </button>
              </div>

              {/* 필터/정렬 옵션 */}
              {showFilters && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  {/* 정렬 */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      정렬 기준
                    </label>
                    <div className="flex gap-2">
                      {[
                        { value: 'latest', label: '최신순' },
                        { value: 'popular', label: '인기순' },
                        { value: 'oldest', label: '오래된순' }
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setSortBy(option.value as any)}
                          className={`px-4 py-2 rounded-lg font-medium transition-all ${
                            sortBy === option.value
                              ? 'bg-orange-500 text-white'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 기간 필터 */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      여행 기간
                    </label>
                    <div className="flex gap-2">
                      {[
                        { value: 'all', label: '전체' },
                        { value: '1', label: '당일' },
                        { value: '2-3', label: '2-3일' },
                        { value: '4+', label: '4일 이상' }
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setDurationFilter(option.value as any)}
                          className={`px-4 py-2 rounded-lg font-medium transition-all ${
                            durationFilter === option.value
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 상단 정보 */}
            <div className="mb-8">
              <p className="text-gray-600 dark:text-gray-400 text-lg">
                <span className="font-bold text-orange-600 dark:text-orange-400">{schedules.length}개</span>의 
                멋진 여행 코스가 공유되었어요! 🎉
              </p>
            </div>

            {/* 카드 그리드 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {filteredSchedules.map((schedule) => (
                  <Link
                    key={schedule.id}
                    to={`/courses/${schedule.id}`}
                    className="group bg-white dark:bg-gray-800 rounded-3xl shadow-lg hover:shadow-2xl transition-all overflow-hidden border-2 border-gray-100 dark:border-gray-700 hover:border-orange-300 dark:hover:border-orange-500 hover:-translate-y-2 block"
                  >
                  {/* Header - 그라데이션 배경 */}
                  <div className="relative bg-gradient-to-br from-orange-100 via-orange-50 to-blue-50 dark:from-gray-700 dark:to-gray-600 p-6 pb-8">
                    <div className="flex items-start gap-3">
                      <span className="text-3xl">
                        {schedule.title.includes('힐링') ? '🌊' :
                         schedule.title.includes('맛집') ? '🍊' :
                         schedule.title.includes('가족') ? '👨‍👩‍👧‍👦' :
                         schedule.title.includes('감성') ? '📸' : '🏝️'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-black text-gray-900 dark:text-white mb-2 truncate">
                          {schedule.title}
                        </h3>
                        <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm">
                          <div className="flex items-center gap-1.5 bg-white/50 dark:bg-gray-800/50 px-3 py-1.5 rounded-full">
                            <Users size={14} />
                            <span className="font-medium">{schedule.user_name}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Info */}
                  <div className="p-6">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 text-sm">
                        <div className="p-2 bg-orange-50 dark:bg-orange-900/30 rounded-lg">
                          <Clock size={16} className="text-orange-600 dark:text-orange-400" />
                        </div>
                        <span className="font-medium">{getDuration(schedule.start_date, schedule.end_date)}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 text-sm">
                        <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                          <MapPin size={16} className="text-blue-600 dark:text-blue-400" />
                        </div>
                        <span className="font-medium">{getAttractionCount(schedule.attractions)}곳</span>
                      </div>
                    </div>

                    <div className="text-sm text-gray-500 dark:text-gray-400 mb-4 flex items-center gap-2">
                      <CalendarIcon size={14} />
                      <span>
                        {format(new Date(schedule.start_date), 'M월 d일', { locale: ko })} ~{' '}
                        {format(new Date(schedule.end_date), 'M월 d일', { locale: ko })}
                      </span>
                    </div>

                    {schedule.memo && (
                      <p className="text-gray-600 dark:text-gray-400 text-sm mb-6 line-clamp-2 leading-relaxed">
                        {schedule.memo}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default CoursesPage;
