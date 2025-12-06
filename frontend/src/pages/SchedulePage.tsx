/**
 * Schedule Page - 내 일정 관리
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, MapPin, Clock, Plus, Trash2, Share2, Eye, EyeOff } from 'lucide-react';
import { getUserSchedules, deleteSchedule, updateSchedule } from '../api/schedules';
import type { Schedule } from '../api/schedules';
import { format, differenceInDays } from 'date-fns';
import { ko } from 'date-fns/locale';

const SchedulePage: React.FC = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
    try {
      setLoading(true);
      const data = await getUserSchedules();
      setSchedules(data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || '일정을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (scheduleId: number) => {
    if (!window.confirm('정말로 이 일정을 삭제하시겠습니까?')) {
      return;
    }

    try {
      setDeletingId(scheduleId);
      await deleteSchedule(scheduleId);
      setSchedules(schedules.filter(s => s.id !== scheduleId));
    } catch (err: any) {
      alert(err.response?.data?.detail || '일정 삭제에 실패했습니다');
    } finally {
      setDeletingId(null);
    }
  };

  const handleTogglePublic = async (schedule: Schedule) => {
    try {
      setTogglingId(schedule.id);
      const updated = await updateSchedule(schedule.id, {
        is_public: !schedule.is_public
      });
      setSchedules(schedules.map(s => s.id === schedule.id ? updated : s));
      
      if (updated.is_public) {
        alert('일정이 공개되었습니다! 다른 사용자들이 추천 코스에서 볼 수 있습니다.');
      } else {
        alert('일정이 비공개로 변경되었습니다.');
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || '공유 설정 변경에 실패했습니다');
    } finally {
      setTogglingId(null);
    }
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
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-jeju-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-orange-400 via-orange-500 to-orange-600 text-white py-16">
        {/* 배경 장식 */}
        <div className="absolute top-5 right-10 text-6xl opacity-20 animate-pulse">📅</div>
        <div className="absolute bottom-5 left-10 text-5xl opacity-20 animate-bounce">✨</div>
        
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="flex items-center justify-between">
            <div>
              <div className="inline-block mb-4 px-6 py-2 bg-white/20 backdrop-blur-sm rounded-full">
                <span className="text-white font-medium text-sm">
                  🗺️ 나의 여행 계획
                </span>
              </div>
              
              <h1 className="text-5xl md:text-6xl font-black mb-4">
                내 일정
              </h1>
              
              <p className="text-xl md:text-2xl text-white/90">
                총 <span className="font-black">{schedules.length}개</span>의 멋진 여행 계획 🎉
              </p>
            </div>
            
            <Link
              to="/chat"
              className="hidden md:inline-flex items-center gap-3 bg-white text-orange-600 px-8 py-4 rounded-2xl font-bold hover:shadow-2xl hover:scale-105 transition-all"
            >
              <Plus size={24} />
              새 일정 만들기
            </Link>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/30 border-2 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-6 py-4 rounded-2xl shadow-lg">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚠️</span>
              <span className="font-bold">{error}</span>
            </div>
          </div>
        </div>
      )}

      {/* Schedules List */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {schedules.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-block p-12 bg-white dark:bg-gray-800 rounded-3xl shadow-2xl">
              <Calendar className="mx-auto h-24 w-24 text-orange-400 mb-6 animate-bounce" />
              <p className="text-gray-600 dark:text-gray-400 text-2xl font-bold mb-6">
                아직 생성된 일정이 없어요
              </p>
              <p className="text-gray-500 dark:text-gray-500 mb-8">
                AI와 함께 나만의 제주 여행을 계획해보세요!
              </p>
              <Link
                to="/chat"
                className="inline-flex items-center gap-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white px-10 py-4 rounded-2xl font-bold hover:shadow-xl hover:scale-105 transition-all"
              >
                <Plus size={24} />
                첫 여행 일정 만들기
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {schedules.map((schedule) => (
              <div
                key={schedule.id}
                className="group bg-white dark:bg-gray-800 rounded-3xl shadow-lg hover:shadow-2xl transition-all overflow-hidden border-2 border-gray-100 dark:border-gray-700 hover:border-orange-300 dark:hover:border-orange-500"
              >
                {/* Header */}
                <div className="relative bg-gradient-to-br from-orange-100 via-orange-50 to-blue-50 dark:from-gray-700 dark:to-gray-600 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">
                        {schedule.title.includes('힐링') ? '🌊' :
                         schedule.title.includes('맛집') ? '🍊' :
                         schedule.title.includes('가족') ? '👨‍👩‍👧‍👦' :
                         schedule.title.includes('감성') ? '📸' : '🏝️'}
                      </span>
                      <div>
                        <h3 className="text-xl font-black text-gray-900 dark:text-white mb-1">
                          {schedule.title}
                        </h3>
                        <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm">
                          <Calendar size={14} />
                          <span className="font-medium">{getDuration(schedule.start_date, schedule.end_date)}</span>
                        </div>
                      </div>
                    </div>
                    {schedule.is_public && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-green-400 to-emerald-500 text-white text-xs rounded-full font-bold shadow-lg shrink-0">
                        <Eye size={12} />
                        공개
                      </span>
                    )}
                  </div>
                </div>

                {/* Info */}
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 text-sm">
                      <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                        <Clock size={16} className="text-blue-600 dark:text-blue-400" />
                      </div>
                      <span className="font-medium">{format(new Date(schedule.start_date), 'M월 d일', { locale: ko })}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 text-sm">
                      <div className="p-2 bg-orange-50 dark:bg-orange-900/30 rounded-lg">
                        <MapPin size={16} className="text-orange-600 dark:text-orange-400" />
                      </div>
                      <span className="font-medium">{getAttractionCount(schedule.attractions)}곳</span>
                    </div>
                  </div>

                  {schedule.memo && (
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-6 line-clamp-2 leading-relaxed">
                      {schedule.memo}
                    </p>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleTogglePublic(schedule)}
                      disabled={togglingId === schedule.id}
                      className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-bold transition-all ${
                        schedule.is_public
                          ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                          : 'bg-gradient-to-r from-green-400 to-emerald-500 text-white hover:shadow-lg'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                      title={schedule.is_public ? '공유 취소' : '일정 공유하기'}
                    >
                      {togglingId === schedule.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-current"></div>
                      ) : schedule.is_public ? (
                        <>
                          <EyeOff size={16} />
                          <span className="text-sm">비공개</span>
                        </>
                      ) : (
                        <>
                          <Share2 size={16} />
                          <span className="text-sm">공유</span>
                        </>
                      )}
                    </button>

                    <Link
                      to={`/schedule/${schedule.id}`}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-xl font-bold transition-all hover:shadow-lg"
                    >
                      <Eye size={16} />
                      <span className="text-sm">상세보기</span>
                    </Link>

                    <button
                      onClick={() => handleDelete(schedule.id)}
                      disabled={deletingId === schedule.id}
                      className="p-3 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="삭제"
                    >
                      {deletingId === schedule.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-red-600"></div>
                      ) : (
                        <Trash2 size={18} />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SchedulePage;
