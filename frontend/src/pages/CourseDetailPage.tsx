/**
 * Course Detail Page - 추천 코스 상세 보기 (AI 대화 내역 없음)
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Calendar, Clock, MapPin, Users, Heart, Bookmark, Eye, 
  Share2, ArrowLeft, Loader2, Map, ChevronDown, ChevronUp
} from 'lucide-react';
import { 
  getSchedule, 
  likeSchedule, 
  bookmarkSchedule, 
  recordView, 
  getScheduleStats
} from '../api/schedules';
import type { Schedule, ScheduleStats } from '../api/schedules';
import { format, differenceInDays } from 'date-fns';
import { ko } from 'date-fns/locale';
import KakaoMap from '../components/KakaoMap';
import CommentSection from '../components/CommentSection';
import PhotoGallery from '../components/PhotoGallery';
import apiClient from '../api/client';
import { differenceInDays as diffDays } from 'date-fns';

const CourseDetailPage: React.FC = () => {
  const { scheduleId } = useParams<{ scheduleId: string }>();
  const navigate = useNavigate();
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState<'like' | 'bookmark' | null>(null);
  
  // 통계 상태
  const [stats, setStats] = useState<ScheduleStats | null>(null);
  
  // 섹션 토글 상태
  const [showMap, setShowMap] = useState(true);

  useEffect(() => {
    if (scheduleId) {
      fetchSchedule(parseInt(scheduleId));
    }
  }, [scheduleId]);

  const fetchSchedule = async (id: number) => {
    try {
      setLoading(true);
      const data = await getSchedule(id);
      setSchedule(data);
      
      // 조회수 기록
      await recordView(id).catch(err => console.error('조회수 기록 실패:', err));
      
      // 통계 조회
      const statsData = await getScheduleStats(id);
      setStats(statsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || '일정을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
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

  const handleLike = async () => {
    if (!scheduleId || actionLoading) return;
    
    setActionLoading('like');
    try {
      const result = await likeSchedule(parseInt(scheduleId));
      if (stats) {
        setStats({
          ...stats,
          is_liked: result.is_active,
          likes_count: result.total_count
        });
      }
    } catch (error) {
      console.error('좋아요 실패:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleBookmark = async () => {
    if (!scheduleId || actionLoading) return;
    
    setActionLoading('bookmark');
    try {
      const result = await bookmarkSchedule(parseInt(scheduleId));
      if (stats) {
        setStats({
          ...stats,
          is_bookmarked: result.is_active,
          bookmarks_count: result.total_count
        });
      }
    } catch (error) {
      console.error('북마크 실패:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: schedule?.title,
        text: '제주 여행 일정을 공유합니다',
        url: window.location.href
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('링크가 복사되었습니다!');
    }
  };

  // 작성자/댓글 작성자와 채팅 시작
  const handleStartChat = async (targetUserId: number, _targetUserName: string) => {
    try {
      const response = await apiClient.post(`/api/dm/conversations/${targetUserId}`);
      const conversationId = response.data.id;
      navigate(`/dm/${conversationId}`);
    } catch (error) {
      console.error('DM 시작 실패:', error);
      alert('채팅을 시작할 수 없습니다. 로그인이 필요합니다.');
    }
  };

  // 일정 기간 계산
  const getTotalDays = () => {
    if (!schedule) return 1;
    return diffDays(new Date(schedule.end_date), new Date(schedule.start_date)) + 1;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">📅</div>
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400 font-medium">일정 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error || !schedule) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
        <div className="text-center bg-white dark:bg-gray-800 rounded-3xl p-12 shadow-xl">
          <div className="text-6xl mb-4">😢</div>
          <p className="text-gray-600 dark:text-gray-400 text-xl font-bold mb-6">{error || '일정을 찾을 수 없습니다'}</p>
          <button
            onClick={() => navigate('/courses')}
            className="inline-flex items-center gap-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white px-8 py-3 rounded-xl font-bold hover:shadow-lg transition-all"
          >
            <ArrowLeft size={20} />
            목록으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* 상단 네비게이션 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/courses')}
              className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-orange-600 dark:hover:text-orange-400 font-medium transition-colors"
            >
              <ArrowLeft size={20} />
              추천 코스 목록
            </button>
            
            <div className="flex items-center gap-2">
              <button
                onClick={handleShare}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="공유하기"
              >
                <Share2 size={20} className="text-gray-600 dark:text-gray-400" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 헤더 */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border-2 border-gray-100 dark:border-gray-700 mb-8">
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
              <h1 className="text-4xl font-black text-gray-900 dark:text-white mb-4">
                {schedule.title}
              </h1>
              
              <div className="flex items-center gap-6 text-gray-600 dark:text-gray-400 mb-6">
                <div className="flex items-center gap-2">
                  <Users size={18} />
                  <span className="font-medium">{schedule.user_name}</span>
                  <button
                    onClick={() => handleStartChat(schedule.user_id, schedule.user_name)}
                    className="ml-2 inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors"
                  >
                    💬 채팅하기
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar size={18} />
                  <span className="font-medium">
                    {format(new Date(schedule.start_date), 'M월 d일', { locale: ko })} ~{' '}
                    {format(new Date(schedule.end_date), 'M월 d일', { locale: ko })}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={18} />
                  <span className="font-medium">{getDuration(schedule.start_date, schedule.end_date)}</span>
                </div>
              </div>

              {schedule.memo && (
                <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
                  {schedule.memo}
                </p>
              )}
            </div>
          </div>

          {/* 통계 및 액션 버튼 */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                <Eye size={18} />
                <span className="font-medium">{stats?.views_count || 0}회</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                <Heart size={18} />
                <span className="font-medium">{stats?.likes_count || 0}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                <Bookmark size={18} />
                <span className="font-medium">{stats?.bookmarks_count || 0}</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleLike}
                disabled={actionLoading !== null}
                className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all disabled:opacity-50 ${
                  stats?.is_liked
                    ? 'bg-red-500 text-white hover:bg-red-600'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-red-50 dark:hover:bg-red-900/30'
                }`}
              >
                {actionLoading === 'like' ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Heart size={20} fill={stats?.is_liked ? 'currentColor' : 'none'} />
                )}
                좋아요
              </button>
              <button
                onClick={handleBookmark}
                disabled={actionLoading !== null}
                className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all disabled:opacity-50 ${
                  stats?.is_bookmarked
                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/30'
                }`}
              >
                {actionLoading === 'bookmark' ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Bookmark size={20} fill={stats?.is_bookmarked ? 'currentColor' : 'none'} />
                )}
                북마크
              </button>
            </div>
          </div>
        </div>

        {/* 관광지 리스트 (일차별) */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border-2 border-gray-100 dark:border-gray-700 mb-8">
          <h2 className="text-2xl font-black text-gray-900 dark:text-white mb-6 flex items-center gap-3">
            <MapPin className="text-orange-500" size={28} />
            여행 일정 ({getAttractionCount(schedule.attractions)}곳)
          </h2>

          {schedule.attractions && (
            <div className="space-y-8">
              {(() => {
                // attractions가 객체(day별)인지 배열인지 확인
                const isObjectByDay = typeof schedule.attractions === 'object' && !Array.isArray(schedule.attractions);
                
                if (isObjectByDay) {
                  // day1, day2 형식의 객체
                  const sortedDays = Object.entries(schedule.attractions)
                    .sort(([a], [b]) => {
                      const numA = parseInt(a.replace('day', '')) || 0;
                      const numB = parseInt(b.replace('day', '')) || 0;
                      return numA - numB;
                    });
                  
                  return sortedDays.map(([dayKey, attractions]: [string, any], idx) => {
                    const dayNum = parseInt(dayKey.replace('day', '')) || idx + 1;
                    const dayColors = [
                      { bg: 'from-red-50 to-red-100', border: 'border-red-400', text: 'text-red-600' },
                      { bg: 'from-cyan-50 to-cyan-100', border: 'border-cyan-400', text: 'text-cyan-600' },
                      { bg: 'from-blue-50 to-blue-100', border: 'border-blue-400', text: 'text-blue-600' },
                      { bg: 'from-green-50 to-green-100', border: 'border-green-400', text: 'text-green-600' },
                      { bg: 'from-yellow-50 to-yellow-100', border: 'border-yellow-400', text: 'text-yellow-600' },
                      { bg: 'from-purple-50 to-purple-100', border: 'border-purple-400', text: 'text-purple-600' },
                      { bg: 'from-pink-50 to-pink-100', border: 'border-pink-400', text: 'text-pink-600' },
                    ];
                    const color = dayColors[(dayNum - 1) % dayColors.length];
                    
                    return (
                      <div key={idx} className={`border-l-4 ${color.border} pl-6`}>
                        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r ${color.bg} mb-4`}>
                          <span className={`font-black text-lg ${color.text}`}>Day {dayNum}</span>
                          <span className="text-gray-500 text-sm">
                            ({Array.isArray(attractions) ? attractions.length : 0}곳)
                          </span>
                        </div>
                        <div className="space-y-3">
                          {Array.isArray(attractions) && attractions.map((attraction: any, aIdx: number) => (
                            <div
                              key={aIdx}
                              className={`bg-gradient-to-br ${color.bg} dark:from-gray-700 dark:to-gray-600 rounded-xl p-4 border-2 ${color.border} dark:border-gray-600`}
                            >
                              <div className="flex items-center gap-4">
                                <div className={`flex items-center justify-center w-10 h-10 rounded-full bg-white dark:bg-gray-800 ${color.text} font-bold text-lg shadow-md`}>
                                  {aIdx + 1}
                                </div>
                                <span className="text-3xl">{attraction.emoji || '📍'}</span>
                                <div className="flex-1">
                                  <h4 className="font-bold text-gray-900 dark:text-white text-lg">{attraction.name}</h4>
                                  <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                                    {attraction.time && <span>⏱️ {attraction.time}</span>}
                                    {attraction.category && <span>📍 {attraction.category}</span>}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  });
                } else if (Array.isArray(schedule.attractions)) {
                  // 단순 배열인 경우 - 모든 관광지를 하나의 목록으로
                  return (
                    <div className="border-l-4 border-orange-400 pl-6">
                      <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-orange-50 to-orange-100 mb-4">
                        <span className="font-black text-lg text-orange-600">전체 일정</span>
                        <span className="text-gray-500 text-sm">
                          ({schedule.attractions.length}곳)
                        </span>
                      </div>
                      <div className="space-y-3">
                        {schedule.attractions.map((attraction: any, aIdx: number) => (
                          <div
                            key={aIdx}
                            className="bg-gradient-to-br from-orange-50 to-blue-50 dark:from-gray-700 dark:to-gray-600 rounded-xl p-4 border-2 border-orange-300 dark:border-gray-600"
                          >
                            <div className="flex items-center gap-4">
                              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-orange-500 text-white font-bold text-lg shadow-md">
                                {aIdx + 1}
                              </div>
                              <span className="text-3xl">{attraction.emoji || '📍'}</span>
                              <div className="flex-1">
                                <h4 className="font-bold text-gray-900 dark:text-white text-lg">{attraction.name}</h4>
                                <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                                  {attraction.time && <span>⏱️ {attraction.time}</span>}
                                  {attraction.category && <span>📍 {attraction.category}</span>}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                }
                return null;
              })()}
            </div>
          )}
        </div>

        {/* 지도 시각화 섹션 */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border-2 border-gray-100 dark:border-gray-700">
          <button
            onClick={() => setShowMap(!showMap)}
            className="w-full flex items-center justify-between mb-6 hover:opacity-80 transition-opacity"
          >
            <h2 className="text-2xl font-black text-gray-900 dark:text-white flex items-center gap-3">
              <Map className="text-green-500" size={28} />
              여행 경로 지도
            </h2>
            {showMap ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
          </button>

          {showMap && (
            <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl overflow-hidden">
              {(() => {
                // schedule.map_data가 있고 routes가 있으면 그대로 사용 (카카오 자동차 경로 포함)
                if (schedule.map_data && schedule.map_data.markers && schedule.map_data.markers.length > 0) {
                  return <KakaoMap mapData={schedule.map_data} className="w-full" style={{ height: '500px' }} />;
                }
                
                // map_data가 없으면 attractions에서 day 정보를 추출하여 마커 구성 (fallback)
                const mapMarkers: any[] = [];
                
                if (schedule.attractions) {
                  const isObjectByDay = typeof schedule.attractions === 'object' && !Array.isArray(schedule.attractions);
                  
                  if (isObjectByDay) {
                    // day1, day2 형식 - day별로 정렬해서 처리
                    const sortedDays = Object.entries(schedule.attractions)
                      .sort(([a], [b]) => {
                        const numA = parseInt(a.replace('day', '')) || 0;
                        const numB = parseInt(b.replace('day', '')) || 0;
                        return numA - numB;
                      });
                    
                    sortedDays.forEach(([dayKey, attractions]: [string, any]) => {
                      const dayNum = parseInt(dayKey.replace('day', '')) || 1;
                      if (Array.isArray(attractions)) {
                        attractions.forEach((attr: any, idx: number) => {
                          if (attr.lat && attr.lng) {
                            mapMarkers.push({
                              id: mapMarkers.length,
                              position: { lat: attr.lat, lng: attr.lng },
                              name: attr.name,
                              emoji: attr.emoji,
                              category: attr.category,
                              day: dayNum,
                              order: idx + 1,
                              label: String(idx + 1),
                            });
                          }
                        });
                      }
                    });
                  } else if (Array.isArray(schedule.attractions)) {
                    // 단순 배열 - 모두 Day 1
                    schedule.attractions.forEach((attr: any, idx: number) => {
                      if (attr.lat && attr.lng) {
                        mapMarkers.push({
                          id: idx,
                          position: { lat: attr.lat, lng: attr.lng },
                          name: attr.name,
                          emoji: attr.emoji,
                          category: attr.category,
                          day: attr.day || 1,
                          order: idx + 1,
                          label: String(idx + 1),
                        });
                      }
                    });
                  }
                }
                
                if (mapMarkers.length === 0) {
                  return (
                    <div className="aspect-video flex items-center justify-center">
                      <div className="text-center">
                        <Map className="mx-auto text-gray-400 mb-4" size={64} />
                        <p className="text-gray-600 dark:text-gray-400 font-medium">
                          위치 정보가 없습니다
                        </p>
                      </div>
                    </div>
                  );
                }
                
                // 지도 데이터 구성 (attractions에서 생성, 직선 경로 fallback)
                const mapData = {
                  markers: mapMarkers,
                  center: {
                    lat: mapMarkers.reduce((sum, m) => sum + m.position.lat, 0) / mapMarkers.length,
                    lng: mapMarkers.reduce((sum, m) => sum + m.position.lng, 0) / mapMarkers.length,
                  },
                  zoom: 10,
                  showDayColors: Object.keys(
                    mapMarkers.reduce((acc, m) => ({ ...acc, [m.day]: true }), {})
                  ).length > 1, // 2일 이상일 때만 색상 표시
                };
                
                return <KakaoMap mapData={mapData} className="w-full" style={{ height: '500px' }} />;
              })()}
            </div>
          )}
        </div>

        {/* 여행 사진 갤러리 */}
        <div className="mt-8">
          <PhotoGallery 
            scheduleId={parseInt(scheduleId!)} 
            scheduleOwnerId={schedule.user_id}
            days={getTotalDays()}
            canEdit={false}
          />
        </div>

        {/* 댓글 섹션 */}
        <div className="mt-8">
          <CommentSection 
            scheduleId={parseInt(scheduleId!)} 
            onStartChat={handleStartChat}
          />
        </div>
      </div>
    </div>
  );
};

export default CourseDetailPage;

