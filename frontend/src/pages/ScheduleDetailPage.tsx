/**
 * Schedule Detail Page - 일정 상세 보기
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Calendar, Clock, MapPin, Users, Heart, Bookmark, Eye, 
  Share2, ArrowLeft, Edit, Loader2,
  MessageCircle, Map, Lightbulb, ChevronDown, ChevronUp, Send, Plus, X,
  Search, GripVertical  // 검색 및 드래그 아이콘
} from 'lucide-react';
import { 
  getSchedule, 
  likeSchedule, 
  bookmarkSchedule, 
  recordView, 
  getScheduleStats,
  updateSchedule
} from '../api/schedules';
import type { Schedule, ScheduleStats } from '../api/schedules';
import { format, differenceInDays } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useAuth } from '../contexts/AuthContext';
import KakaoMap from '../components/KakaoMap';
import { getAttractionsList } from '../api/attractions';
import type { Attraction } from '../api/attractions';
import { apiClient } from '../api/client';
import CommentSection from '../components/CommentSection';
import PhotoGallery from '../components/PhotoGallery';

// 카테고리별 이모지 매핑
const categoryEmojis: Record<string, string> = {
  '자연': '🌳',
  '문화': '🏛️',
  '해변': '🏖️',
  '맛집': '🍖',
  '카페': '☕',
  '숙소': '🏨',
  '액티비티': '🎯',
  '관광지': '🗺️',
};

const ScheduleDetailPage: React.FC = () => {
  const { scheduleId } = useParams<{ scheduleId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState<'like' | 'bookmark' | null>(null);
  
  // 통계 상태
  const [stats, setStats] = useState<ScheduleStats | null>(null);
  
  // 섹션 토글 상태
  const [showMap, setShowMap] = useState(true);
  
  // 편집 모드 상태
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedSchedule, setEditedSchedule] = useState<Partial<Schedule>>({});
  const [saveLoading, setSaveLoading] = useState(false);
  
  // 관광지 추가 모달 상태
  const [showAttractionModal, setShowAttractionModal] = useState(false);
  const [selectedDay, setSelectedDay] = useState<string>('day1');
  const [modalSearchTerm, setModalSearchTerm] = useState('');
  const [modalCategory, setModalCategory] = useState('전체');
  
  // 드래그 상태
  const [draggedItem, setDraggedItem] = useState<{day: string; index: number} | null>(null);
  
  // 관광지 목록 (API에서 가져옴)
  const [availableAttractions, setAvailableAttractions] = useState<Attraction[]>([]);
  const [attractionsLoading, setAttractionsLoading] = useState(false);
  

  // 카테고리 목록
  const categories = [
    { name: '전체', emoji: '🏝️' },
    { name: '자연', emoji: '🌳' },
    { name: '문화', emoji: '🏛️' },
    { name: '해변', emoji: '🏖️' },
    { name: '맛집', emoji: '🍖' },
    { name: '카페', emoji: '☕' },
    { name: '숙소', emoji: '🏨' },
    { name: '액티비티', emoji: '🎯' },
  ];

  // 관광지 목록 로드 (카테고리, 검색어 반영)
  const fetchAttractions = async () => {
    try {
      setAttractionsLoading(true);
      const data = await getAttractionsList(
        modalCategory !== '전체' ? modalCategory : undefined,
        modalSearchTerm || undefined,
        200  // 더 많은 데이터 로드
      );
      setAvailableAttractions(data);
    } catch (err) {
      console.error('Failed to fetch attractions:', err);
    } finally {
      setAttractionsLoading(false);
    }
  };

  // 모달 열릴 때, 카테고리 변경 시 API 재호출
  useEffect(() => {
    if (showAttractionModal) {
      fetchAttractions();
    }
  }, [showAttractionModal, modalCategory]);

  // 검색어 입력 시 debounce 적용
  useEffect(() => {
    if (!showAttractionModal) return;
    
    const timer = setTimeout(() => {
      fetchAttractions();
    }, 500);

    return () => clearTimeout(timer);
  }, [modalSearchTerm]);

  // 관광지 목록 로드
  useEffect(() => {
    fetchAttractions();
  }, []);

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
      
      console.log('🔍 디버깅 정보:');
      console.log('현재 사용자 ID:', user?.id, typeof user?.id);
      console.log('일정 소유자 ID:', data.user_id, typeof data.user_id);
      console.log('일치 여부 (===):', user?.id === data.user_id);
      console.log('일치 여부 (==):', user?.id == data.user_id);
      console.log('일치 여부 (Number):', Number(user?.id) === Number(data.user_id));
      console.log('AI 대화 내역 있음:', !!data.chat_history);
      console.log('AI 추천 이유 있음:', !!data.ai_reasoning);
      
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
    // TODO: 공유 기능 구현
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

  const handleGoToChat = () => {
    if (schedule?.chat_session_id) {
      // chat_session_id가 있으면 해당 세션으로 이동
      navigate('/chat', { state: { sessionId: schedule.chat_session_id } });
    } else {
      // 없으면 일반 채팅 페이지로 이동
      alert('이 일정은 채팅으로 생성되지 않아 연결된 대화가 없습니다.');
    }
  };

  const handleEdit = () => {
    if (!schedule) return;
    setEditedSchedule({
      title: schedule.title,
      memo: schedule.memo || '',
      start_date: schedule.start_date,
      end_date: schedule.end_date,
      attractions: schedule.attractions,
    });
    setIsEditMode(true);
  };

  const handleCancelEdit = () => {
    setIsEditMode(false);
    setEditedSchedule({});
  };

  const handleSaveEdit = async () => {
    if (!scheduleId || !editedSchedule) return;
    
    setSaveLoading(true);
    try {
      // 수정된 attractions에서 map_data 생성
      const newMapData = getEditedMapData();
      
      await updateSchedule(parseInt(scheduleId), {
        title: editedSchedule.title,
        memo: editedSchedule.memo ?? undefined,
        start_date: editedSchedule.start_date,
        end_date: editedSchedule.end_date,
        attractions: editedSchedule.attractions,
        map_data: newMapData,  // 지도 데이터도 함께 저장
      });
      
      // 저장 성공 후 페이지 새로고침해서 DB 데이터로 다시 렌더링
      alert('일정이 성공적으로 수정되었습니다!');
      window.location.reload();
    } catch (error: any) {
      console.error('일정 수정 실패:', error);
      alert(error.response?.data?.detail || '일정 수정에 실패했습니다');
    } finally {
      setSaveLoading(false);
    }
  };
  
  // 관광지 추가 모달 열기
  const handleOpenAttractionModal = (day: string) => {
    setSelectedDay(day);
    setShowAttractionModal(true);
  };
  
  
  // 편집된 일정에서 지도 데이터 생성
  const getEditedMapData = () => {
    if (!editedSchedule.attractions) return null;
    
    const markers: Array<{
      lat: number;
      lng: number;
      name: string;
      category?: string;
      day: number;
      order: number;
      rating?: number;
      address?: string;
      description?: string;
      phone?: string;
      price?: string;
    }> = [];
    
    Object.entries(editedSchedule.attractions).forEach(([dayKey, dayAttractions]: [string, any]) => {
      if (Array.isArray(dayAttractions)) {
        const dayNum = parseInt(dayKey.replace('day', ''));
        dayAttractions.forEach((attr: any, idx: number) => {
          if (attr.lat && attr.lng) {
            markers.push({
              lat: Number(attr.lat),
              lng: Number(attr.lng),
              name: attr.name,
              category: attr.category,
              day: dayNum,
              order: idx + 1,
              rating: attr.rating,
              address: attr.address,
              description: attr.description,
              phone: attr.phone,
              price: attr.price,
            });
          }
        });
      }
    });
    
    if (markers.length === 0) return null;
    
    // 경로 정보 추가 (최적화된 경로가 있는 경우)
    const routes: any[] = [];
    if ((editedSchedule as any)._routeData) {
      Object.entries((editedSchedule as any)._routeData).forEach(([dayKey, dayRoutes]: [string, any]) => {
        const dayNum = parseInt(dayKey.replace('day', ''));
        if (Array.isArray(dayRoutes)) {
          routes.push({
            day: dayNum,
            routes: dayRoutes.map((r: any) => ({
              from: r.from_place,
              to: r.to_place,
              path: r.path,
              distance: r.distance,
              duration: r.duration
            }))
          });
        }
      });
    }
    
    return {
      markers,
      routes: routes.length > 0 ? routes : undefined,
      center: { lat: markers[0].lat, lng: markers[0].lng },
    };
  };
  
  // 관광지 추가 (최적 위치에 삽입)
  const handleAddAttraction = async (attraction: any) => {
    if (!editedSchedule.attractions) return;
    
    const attractions = { ...editedSchedule.attractions };
    if (!attractions[selectedDay]) {
      attractions[selectedDay] = [];
    }
    
    // 중복 체크
    const exists = attractions[selectedDay].some((a: any) => a.name === attraction.name);
    if (exists) {
      alert('이미 추가된 관광지입니다!');
      return;
    }
    
    const currentDayPlaces = attractions[selectedDay];
    
    // lat/lng가 있는 장소만 최적화 대상
    const validPlaces = currentDayPlaces.filter((p: any) => p.lat && p.lng);
    
    if (validPlaces.length >= 2 && attraction.lat && attraction.lng) {
      // TSP로 최적 삽입 위치 계산
      try {
        const response = await apiClient.post('/api/attractions/find-optimal-position', {
          current_places: validPlaces.map((p: any) => ({
            name: p.name,
            category: p.category || '관광지',
            lat: Number(p.lat),
            lng: Number(p.lng),
          })),
          new_place: {
            name: attraction.name,
            category: attraction.category || '관광지',
            lat: Number(attraction.lat),
            lng: Number(attraction.lng),
          }
        });
        
        if (response.status === 200) {
          const result = response.data;
          // 최적 위치에 삽입
          attractions[selectedDay].splice(result.optimal_index, 0, attraction);
          setEditedSchedule({ ...editedSchedule, attractions });
          setShowAttractionModal(false);
          
          // 사용자에게 알림
          const message = result.distance_increase > 0 
            ? `✨ "${attraction.name}"을(를) 최적 위치에 추가했습니다! (이동거리 +${result.distance_increase.toFixed(1)}km)`
            : `✨ "${attraction.name}"을(를) 최적 위치에 추가했습니다!`;
          alert(message);
          return;
        }
      } catch (err) {
        console.error('최적 위치 계산 실패, 기본 위치에 추가:', err);
      }
    }
    
    // fallback: 끝에 추가
    attractions[selectedDay].push(attraction);
    setEditedSchedule({ ...editedSchedule, attractions });
    setShowAttractionModal(false);
  };
  
  // 전체 경로 최적화
  // 관광지 삭제
  const handleRemoveAttraction = (day: string, attractionName: string) => {
    if (!editedSchedule.attractions) return;
    
    const attractions = { ...editedSchedule.attractions };
    attractions[day] = attractions[day].filter((a: any) => a.name !== attractionName);
    
    // 빈 배열이면 day 자체를 삭제
    if (attractions[day].length === 0) {
      delete attractions[day];
    }
    
    setEditedSchedule({ ...editedSchedule, attractions });
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
    return differenceInDays(new Date(schedule.end_date), new Date(schedule.start_date)) + 1;
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
      {/* 관광지 추가 모달 */}
      {showAttractionModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl border-2 border-gray-200 dark:border-gray-700">
            {/* 헤더 */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-black text-gray-900 dark:text-white flex items-center gap-2">
                <MapPin className="text-blue-500" size={28} />
                관광지 추가 (Day {selectedDay.replace('day', '')})
              </h2>
              <button
                onClick={() => {
                  setShowAttractionModal(false);
                  setModalSearchTerm('');
                  setModalCategory('전체');
                }}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* 검색창 */}
            <div className="relative mb-4">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={modalSearchTerm}
                onChange={(e) => setModalSearchTerm(e.target.value)}
                placeholder="장소명으로 검색..."
                className="w-full pl-12 pr-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 transition-colors"
              />
              {modalSearchTerm && (
                <button
                  onClick={() => setModalSearchTerm('')}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X size={18} />
                </button>
              )}
            </div>

            {/* 카테고리 필터 */}
            <div className="flex flex-wrap gap-2 mb-4">
              {categories.map((cat) => (
                <button
                  key={cat.name}
                  onClick={() => setModalCategory(cat.name)}
                  className={`px-4 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
                    modalCategory === cat.name
                      ? 'bg-blue-500 text-white shadow-lg'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  <span>{cat.emoji}</span>
                  <span>{cat.name}</span>
                </button>
              ))}
            </div>

            {/* 결과 개수 */}
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              {attractionsLoading ? '검색 중...' : `${availableAttractions.length}개 장소`}
            </div>

            {/* 장소 목록 */}
            <div className="flex-1 overflow-y-auto space-y-2">
              {attractionsLoading ? (
                <div className="text-center py-12">
                  <Loader2 className="animate-spin mx-auto text-blue-500 mb-3" size={40} />
                  <p className="text-gray-500">장소 검색 중...</p>
                </div>
              ) : availableAttractions.length === 0 ? (
                <div className="text-center py-12">
                  <MapPin className="mx-auto text-gray-300 mb-3" size={48} />
                  <p className="text-gray-500">검색 결과가 없습니다</p>
                  <p className="text-sm text-gray-400 mt-1">다른 키워드로 검색해보세요</p>
                </div>
              ) : (
                availableAttractions.map((attraction) => (
                  <button
                    key={`${attraction.source}-${attraction.id}`}
                    onClick={() => {
                      handleAddAttraction({
                        name: attraction.name,
                        category: attraction.category,
                        time: '2시간',
                        price: attraction.price || '무료',
                        emoji: categoryEmojis[attraction.category] || '📍',
                        lat: attraction.lat,
                        lng: attraction.lng,
                      });
                      setShowAttractionModal(false);
                      setModalSearchTerm('');
                      setModalCategory('전체');
                    }}
                    className="w-full flex items-center justify-between bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-600 rounded-xl p-4 hover:shadow-lg hover:scale-[1.01] transition-all border border-gray-200 dark:border-gray-600 text-left"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{categoryEmojis[attraction.category] || '📍'}</span>
                      <div>
                        <h4 className="font-bold text-gray-900 dark:text-white">{attraction.name}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {attraction.category}
                          {attraction.rating && attraction.rating > 0 && ` · ⭐${attraction.rating.toFixed(1)}`}
                          {attraction.price && ` · ${attraction.price}`}
                        </p>
                      </div>
                    </div>
                    <Plus size={24} className="text-blue-600 dark:text-blue-400 flex-shrink-0" />
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 상단 네비게이션 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-orange-600 dark:hover:text-orange-400 font-medium transition-colors"
            >
              <ArrowLeft size={20} />
              뒤로 가기
            </button>
            
            <div className="flex items-center gap-2">
              <button
                onClick={handleShare}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="공유하기"
              >
                <Share2 size={20} className="text-gray-600 dark:text-gray-400" />
              </button>
              
              {/* 본인 일정일 경우 편집 버튼 표시 */}
              {user && schedule && Number(user.id) === Number(schedule.user_id) && !isEditMode && (
                <button
                  onClick={handleEdit}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
                >
                  <Edit size={18} />
                  수정
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 헤더 */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border-2 border-gray-100 dark:border-gray-700 mb-8">
          {isEditMode ? (
            /* 편집 모드 UI */
            <>
              <div className="mb-6">
                <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                  제목
                </label>
                <input
                  type="text"
                  value={editedSchedule.title || ''}
                  onChange={(e) => setEditedSchedule({ ...editedSchedule, title: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-bold text-2xl focus:outline-none focus:border-orange-500 transition-colors"
                  placeholder="일정 제목"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                    시작일
                  </label>
                  <input
                    type="date"
                    value={editedSchedule.start_date || ''}
                    onChange={(e) => setEditedSchedule({ ...editedSchedule, start_date: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-orange-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                    종료일
                  </label>
                  <input
                    type="date"
                    value={editedSchedule.end_date || ''}
                    onChange={(e) => setEditedSchedule({ ...editedSchedule, end_date: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-orange-500 transition-colors"
                  />
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                  메모
                </label>
                <textarea
                  value={editedSchedule.memo || ''}
                  onChange={(e) => setEditedSchedule({ ...editedSchedule, memo: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-orange-500 transition-colors resize-none"
                  placeholder="여행 메모를 입력하세요..."
                />
              </div>

              {/* 관광지 편집 섹션 */}
              <div className="mb-6 border-t-2 border-gray-200 dark:border-gray-700 pt-6">
                <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-4">
                  관광지 ({getAttractionCount(editedSchedule.attractions)}곳)
                </label>
                
                {editedSchedule.attractions && typeof editedSchedule.attractions === 'object' && (
                  <div className="space-y-4">
                    {Object.entries(editedSchedule.attractions).map(([day, attractions]: [string, any]) => (
                      <div key={day} className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-bold text-gray-900 dark:text-white">
                            Day {day.replace('day', '')}
                          </h3>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleOpenAttractionModal(day)}
                              type="button"
                              className="inline-flex items-center gap-1 px-3 py-1 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
                            >
                              <Plus size={16} />
                              추가
                            </button>
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          {Array.isArray(attractions) && attractions.map((attraction: any, idx: number) => (
                            <div
                              key={`${day}-${idx}`}
                              draggable
                              onDragStart={(e) => {
                                setDraggedItem({ day, index: idx });
                                e.currentTarget.classList.add('opacity-50');
                              }}
                              onDragEnd={(e) => {
                                setDraggedItem(null);
                                e.currentTarget.classList.remove('opacity-50');
                              }}
                              onDragOver={(e) => {
                                e.preventDefault();
                                e.currentTarget.classList.add('border-blue-500', 'border-2');
                              }}
                              onDragLeave={(e) => {
                                e.currentTarget.classList.remove('border-blue-500', 'border-2');
                              }}
                              onDrop={(e) => {
                                e.preventDefault();
                                e.currentTarget.classList.remove('border-blue-500', 'border-2');
                                
                                if (!draggedItem || draggedItem.day !== day) return;
                                
                                const fromIndex = draggedItem.index;
                                const toIndex = idx;
                                
                                if (fromIndex === toIndex) return;
                                
                                // 순서 변경
                                const updatedAttractions = { ...editedSchedule.attractions };
                                const dayAttractions = [...(updatedAttractions as any)[day]];
                                const [movedItem] = dayAttractions.splice(fromIndex, 1);
                                dayAttractions.splice(toIndex, 0, movedItem);
                                (updatedAttractions as any)[day] = dayAttractions;
                                
                                setEditedSchedule({ ...editedSchedule, attractions: updatedAttractions });
                                setDraggedItem(null);
                              }}
                              className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-3 cursor-grab active:cursor-grabbing transition-all hover:shadow-md border border-transparent"
                            >
                              <div className="flex items-center gap-2">
                                {/* 드래그 핸들 */}
                                <div className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600">
                                  <GripVertical size={18} />
                                </div>
                                <span className="text-2xl">{attraction.emoji || '📍'}</span>
                                <div>
                                  <p className="font-medium text-gray-900 dark:text-white">{attraction.name}</p>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">
                                    {attraction.category} · {attraction.time}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                {/* 삭제 버튼 */}
                                <button
                                  onClick={() => handleRemoveAttraction(day, attraction.name)}
                                  type="button"
                                  className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
                                  title="삭제"
                                >
                                  <X size={18} className="text-red-600" />
                                </button>
                              </div>
                            </div>
                          ))}
                          
                          {(!Array.isArray(attractions) || attractions.length === 0) && (
                            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-2">
                              관광지를 추가해보세요
                            </p>
                          )}
                          
                          {Array.isArray(attractions) && attractions.length > 1 && (
                            <p className="text-xs text-gray-400 dark:text-gray-500 text-center pt-2">
                              💡 드래그하여 순서를 변경할 수 있습니다
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={handleSaveEdit}
                  disabled={saveLoading}
                  className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50"
                >
                  {saveLoading ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      저장 중...
                    </>
                  ) : (
                    '저장하기'
                  )}
                </button>
                <button
                  onClick={handleCancelEdit}
                  disabled={saveLoading}
                  className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl font-bold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                  취소
                </button>
              </div>
            </>
          ) : (
            /* 일반 보기 모드 UI */
            <>
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <h1 className="text-4xl font-black text-gray-900 dark:text-white mb-4">
                    {schedule.title}
                  </h1>
                  
                  <div className="flex items-center gap-6 text-gray-600 dark:text-gray-400 mb-6">
                    <div className="flex items-center gap-2">
                      <Users size={18} />
                      <span className="font-medium">{schedule.user_name}</span>
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
            </>
          )}
        </div>

        {/* AI 채팅으로 이동 버튼 - 본인 일정이고 채팅 세션이 있을 때만 표시 */}
        {user && schedule && Number(user.id) === Number(schedule.user_id) && schedule.chat_session_id && (
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-2xl p-6 border border-purple-200 dark:border-purple-800 mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <MessageCircle className="text-white" size={24} />
                        </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white">AI와의 대화</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    이 일정은 AI 여행 가이드와의 대화로 생성되었습니다
                  </p>
                      </div>
                    </div>
                    <button
                      onClick={handleGoToChat}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-xl font-bold shadow-md hover:shadow-lg transition-all"
                    >
                <Send size={18} />
                채팅으로 이동
                    </button>
                  </div>
          </div>
        )}

        {/* AI 추천 이유 섹션 - 본인 일정일 때만 표시 */}
        {user && schedule && Number(user.id) === Number(schedule.user_id) && schedule.ai_reasoning && (
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-gray-800 dark:to-gray-700 rounded-3xl p-8 shadow-xl border-2 border-yellow-200 dark:border-yellow-900 mb-8">
            <h2 className="text-2xl font-black text-gray-900 dark:text-white flex items-center gap-3 mb-4">
              <Lightbulb className="text-yellow-500" size={28} />
              AI 추천 이유
            </h2>
            <p className="text-gray-800 dark:text-gray-200 text-lg leading-relaxed whitespace-pre-wrap">
              {schedule.ai_reasoning}
            </p>
          </div>
        )}

        {/* 지도 시각화 섹션 */}
        {schedule.map_data && (
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border-2 border-gray-100 dark:border-gray-700 mb-8">
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
                  // 편집 모드면 editedSchedule에서 동적 생성, 아니면 원본 사용
                  const mapData = isEditMode ? getEditedMapData() : schedule.map_data;
                  
                  if (mapData && mapData.markers && mapData.markers.length > 0) {
                    return <KakaoMap mapData={mapData} className="w-full" style={{ height: '500px' }} />;
                  }
                  
                  return (
                    <div className="aspect-video flex items-center justify-center">
                      <div className="text-center">
                        <Map className="mx-auto text-gray-400 mb-4" size={64} />
                        <p className="text-gray-600 dark:text-gray-400 font-medium">
                          {isEditMode ? '위치 정보가 있는 장소를 추가하면 지도가 표시됩니다' : '지도 데이터가 없습니다'}
                        </p>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        )}

        {/* 관광지 리스트 */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border-2 border-gray-100 dark:border-gray-700">
          <h2 className="text-2xl font-black text-gray-900 dark:text-white mb-6 flex items-center gap-3">
            <MapPin className="text-orange-500" size={28} />
            관광지 ({getAttractionCount(schedule.attractions)}곳)
          </h2>

          {schedule.attractions && typeof schedule.attractions === 'object' && (
            <div className="space-y-6">
              {Object.entries(schedule.attractions).map(([day, attractions]: [string, any], idx) => (
                <div key={idx} className="border-l-4 border-orange-500 pl-6">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                    Day {day.replace('day', '')}
                  </h3>
                  <div className="space-y-3">
                    {Array.isArray(attractions) && attractions.map((attraction: any, aIdx: number) => (
                      <div
                        key={aIdx}
                        className="bg-gradient-to-br from-orange-50 to-blue-50 dark:from-gray-700 dark:to-gray-600 rounded-xl p-4 border border-gray-200 dark:border-gray-600"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-3xl">{attraction.emoji || '📍'}</span>
                          <div className="flex-1">
                            <h4 className="font-bold text-gray-900 dark:text-white">{attraction.name}</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{attraction.time}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 여행 사진 갤러리 */}
        <div className="mt-8">
          <PhotoGallery 
            scheduleId={parseInt(scheduleId!)} 
            scheduleOwnerId={schedule.user_id}
            days={getTotalDays()}
          />
        </div>

        {/* 댓글 섹션 - 공개 일정일 때만 표시 */}
        {schedule.is_public && (
          <div className="mt-8">
            <CommentSection 
              scheduleId={parseInt(scheduleId!)} 
              onStartChat={handleStartChat}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ScheduleDetailPage;

