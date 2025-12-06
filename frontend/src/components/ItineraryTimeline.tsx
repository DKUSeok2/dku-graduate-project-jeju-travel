import { useState } from 'react';
import { 
  Calendar, 
  MapPin, 
  Clock, 
  ChevronDown, 
  ChevronUp, 
  Star,
  Utensils,
  Coffee,
  Hotel,
  Sun,
  Sunset,
  Moon,
  Map,
  X,
  Plus,
  Check
} from 'lucide-react';
import KakaoMap from './KakaoMap';
import apiClient from '../api/client';

interface ScheduledPlace {
  id: number;
  name: string;
  category: string;
  rating: number | null;
  region: string;
  time_slot: string;
  start_time: string;
  end_time: string;
  parking?: boolean;
  kid_friendly?: boolean;
  lat?: number | null;
  lng?: number | null;
}

interface DayItinerary {
  day: number;
  label: string;
  regions: string[];
  places: ScheduledPlace[];
  accommodation?: {
    id: number;
    name: string;
    category: string;
    rating?: number;
    region: string;
    address?: string;
    lat?: number | null;
    lng?: number | null;
  };
}

interface RoutePathData {
  from_place?: { name: string; lat: number; lng: number };
  to_place?: { name: string; lat: number; lng: number };
  path: number[][];
  distance?: number;
  duration?: number;
}

interface DayRouteData {
  day: number;
  routes: RoutePathData[];
}

interface MapDataInfo {
  markers?: any[];
  center?: { lat: number; lng: number };
  zoom?: number;
  routes?: DayRouteData[]; // 실제 도로 경로 정보
}

interface ItineraryData {
  type: string;
  total_days: number;
  days: DayItinerary[];
  map_data?: MapDataInfo; // 지도 데이터 (경로 정보 포함)
}

// 내 일정에 추가할 장소 데이터 형식
export interface ScheduleAttraction {
  id?: number;
  name: string;
  category: string;
  lat: number | null;
  lng: number | null;
  rating?: number | null;
  emoji?: string;
  time?: string;
  day: number;
  order: number;
}

interface ItineraryTimelineProps {
  data: ItineraryData;
  onAddToSchedule?: (attractions: ScheduleAttraction[], mapData?: any) => void;
  onAddPlace?: (place: ScheduleAttraction) => void;
  onEditItinerary?: (updatedData: ItineraryData) => void; // 일정 수정 콜백
  hideOptimizeButton?: boolean; // 경로 최적화 버튼 숨기기
  hideMapButton?: boolean; // 지도에서 보기 버튼 숨기기
}

// 시간대별 아이콘
const getTimeIcon = (timeSlot: string) => {
  const slot = timeSlot.toLowerCase();
  if (slot.includes('오전') || slot.includes('아침')) return <Sun className="h-4 w-4 text-yellow-500" />;
  if (slot.includes('점심')) return <Utensils className="h-4 w-4 text-orange-500" />;
  if (slot.includes('오후')) return <Sunset className="h-4 w-4 text-orange-400" />;
  if (slot.includes('카페')) return <Coffee className="h-4 w-4 text-amber-600" />;
  if (slot.includes('저녁') || slot.includes('간식')) return <Moon className="h-4 w-4 text-indigo-500" />;
  return <Clock className="h-4 w-4 text-gray-500" />;
};

// 카테고리별 색상
const getCategoryColor = (category: string) => {
  if (category.includes('카페') || category.includes('디저트')) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300';
  if (category.includes('고기') || category.includes('돼지')) return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300';
  if (category.includes('회') || category.includes('해물') || category.includes('생선')) return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
  if (category.includes('한식') || category.includes('국수')) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300';
  if (category.includes('관광') || category.includes('박물관')) return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300';
  return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
};

// Day별 색상
const getDayColor = (day: number) => {
  const colors = [
    'from-blue-500 to-cyan-500',
    'from-purple-500 to-pink-500',
    'from-orange-500 to-red-500',
    'from-green-500 to-teal-500',
  ];
  return colors[(day - 1) % colors.length];
};

export function ItineraryTimeline({ data, onAddToSchedule, onAddPlace, onEditItinerary, hideOptimizeButton: _hideOptimizeButton = false, hideMapButton = false }: ItineraryTimelineProps) {
  void _hideOptimizeButton; // 향후 사용 예정
  // 데이터 안전성 확인
  if (!data || !data.days || !Array.isArray(data.days) || data.days.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        일정 데이터를 불러올 수 없습니다.
      </div>
    );
  }

  const [expandedDays, setExpandedDays] = useState<number[]>(
    data.days?.map(d => d.day) || [] // 모든 Day 펼침
  );
  const [showMapModal, setShowMapModal] = useState(false);
  const [selectedMapDay, setSelectedMapDay] = useState<number | null>(null);
  const [addedPlaces, setAddedPlaces] = useState<Set<string>>(new Set());
  const [isAllAdded, setIsAllAdded] = useState(false);
  
  // 장소 수정 모달 상태
  const [_showEditModal, setShowEditModal] = useState(false);
  const [editingPlace, setEditingPlace] = useState<{
    dayIndex: number;
    placeIndex: number;
    place: ScheduledPlace;
  } | null>(null);
  
  // 최적화 상태
  const [optimizedData, setOptimizedData] = useState<ItineraryData | null>(null);
  const [_isOptimizing, setIsOptimizing] = useState(false);
  const [optimizedDays, setOptimizedDays] = useState<Set<number>>(new Set());
  
  // 향후 사용 예정 변수들
  void _showEditModal; void _isOptimizing;

  // 카테고리별 이모지
  const getCategoryEmoji = (category: string) => {
    if (category.includes('카페') || category.includes('디저트')) return '☕';
    if (category.includes('고기') || category.includes('돼지')) return '🥩';
    if (category.includes('회') || category.includes('해물') || category.includes('생선')) return '🐟';
    if (category.includes('한식') || category.includes('국수')) return '🍜';
    if (category.includes('관광') || category.includes('박물관')) return '🏛️';
    if (category.includes('해변') || category.includes('해수욕')) return '🏖️';
    if (category.includes('산') || category.includes('오름')) return '⛰️';
    if (category.includes('숙소') || category.includes('호텔')) return '🏨';
    return '📍';
  };

  // 경로 최적화 (향후 사용 예정)
  const _handleOptimizeRoute = async () => {
    setIsOptimizing(true);
    try {
      const updatedDays = [...data.days];
      const newOptimizedDays = new Set<number>();
      
      // 각 일별로 최적화
      for (const dayData of data.days) {
        const validPlaces = dayData.places.filter(p => p.lat && p.lng);
        
        if (validPlaces.length < 3) {
          continue; // 최적화할 장소가 부족하면 스킵
        }
        
        try {
          const response = await apiClient.post('/api/attractions/optimize-route', {
            places: validPlaces.map(p => ({
              name: p.name,
              category: p.category || '관광지',
              lat: Number(p.lat),
              lng: Number(p.lng),
            })),
            fix_first: true
          });
          
          if (response.status === 200 && response.data.optimized_order) {
            const result = response.data;
            
            // 최적화된 순서로 재배치
            const optimizedPlaces = result.optimized_order.map((idx: number) => validPlaces[idx]);
            const invalidPlaces = dayData.places.filter(p => !p.lat || !p.lng);
            
            // 해당 일의 places 업데이트
            const dayIndex = updatedDays.findIndex(d => d.day === dayData.day);
            if (dayIndex !== -1) {
              updatedDays[dayIndex] = {
                ...updatedDays[dayIndex],
                places: [...optimizedPlaces, ...invalidPlaces]
              };
              newOptimizedDays.add(dayData.day);
            }
          }
        } catch (err) {
          console.error(`Day ${dayData.day} 최적화 실패:`, err);
        }
      }
      
      const newData: ItineraryData = {
        ...data,
        days: updatedDays
      };
      
      setOptimizedData(newData);
      setOptimizedDays(newOptimizedDays);
      
      if (newOptimizedDays.size > 0) {
        alert(`🚀 ${newOptimizedDays.size}일 경로 최적화 완료!\n이제 "전체 일정 추가" 버튼을 눌러 저장하세요.`);
      } else {
        alert('최적화할 수 있는 일정이 없습니다.\n(각 일별로 위치 정보가 있는 장소가 3개 이상 필요합니다)');
      }
    } catch (err) {
      console.error('경로 최적화 실패:', err);
      alert('경로 최적화에 실패했습니다.');
    } finally {
      setIsOptimizing(false);
    }
  };

  // 전체 일정 추가 (최적화된 데이터 사용)
  const handleAddAllToSchedule = () => {
    if (!onAddToSchedule) return;
    
    // 최적화된 데이터가 있으면 사용, 없으면 원본 데이터 사용
    const dataToUse = optimizedData || data;
    
    const attractions: ScheduleAttraction[] = [];
    dataToUse.days.forEach((dayData) => {
      // 장소들 추가
      dayData.places.forEach((place, idx) => {
        attractions.push({
          id: place.id,
          name: place.name,
          category: place.category,
          lat: place.lat || null,
          lng: place.lng || null,
          rating: place.rating,
          emoji: getCategoryEmoji(place.category),
          time: `${place.start_time} - ${place.end_time}`,
          day: dayData.day,
          order: idx + 1,
        });
      });
      
      // 숙소도 추가
      if (dayData.accommodation) {
        attractions.push({
          id: dayData.accommodation.id,
          name: dayData.accommodation.name,
          category: '숙소',
          lat: dayData.accommodation.lat || null,
          lng: dayData.accommodation.lng || null,
          rating: dayData.accommodation.rating,
          emoji: '🏨',
          time: '숙소',
          day: dayData.day,
          order: dayData.places.length + 1,
        });
      }
    });
    
    // map_data (경로 정보 포함)도 함께 전달
    onAddToSchedule(attractions, dataToUse.map_data);
    setIsAllAdded(true);
    
    // 모든 장소를 추가됨으로 표시 (숙소 포함)
    const allPlaceNames = new Set<string>();
    dataToUse.days.forEach(d => {
      d.places.forEach(p => allPlaceNames.add(p.name));
      if (d.accommodation) allPlaceNames.add(d.accommodation.name);
    });
    setAddedPlaces(allPlaceNames);
  };

  // 개별 장소 추가
  const handleAddPlace = (place: ScheduledPlace, dayNum: number, orderInDay: number) => {
    if (!onAddPlace) return;
    
    const attraction: ScheduleAttraction = {
      id: place.id,
      name: place.name,
      category: place.category,
      lat: place.lat || null,
      lng: place.lng || null,
      rating: place.rating,
      emoji: getCategoryEmoji(place.category),
      time: `${place.start_time} - ${place.end_time}`,
      day: dayNum,
      order: orderInDay,
    };
    
    onAddPlace(attraction);
    setAddedPlaces(prev => new Set(prev).add(place.name));
  };

  const toggleDay = (day: number) => {
    setExpandedDays(prev => 
      prev.includes(day) 
        ? prev.filter(d => d !== day)
        : [...prev, day]
    );
  };

  // 장소 수정 모달 열기 (향후 사용 예정)
  const _openEditModal = (dayIndex: number, placeIndex: number, place: ScheduledPlace) => {
    setEditingPlace({ dayIndex, placeIndex, place });
    setShowEditModal(true);
  };

  // 장소 변경 처리 (향후 사용 예정)
  const _handlePlaceChange = (newPlace: {
    id?: number;
    name: string;
    category: string;
    lat: number;
    lng: number;
    rating?: number;
  }) => {
    if (!editingPlace || !onEditItinerary) return;

    // 데이터 복사 및 수정
    const updatedDays = displayData.days.map((day, dIdx) => {
      if (dIdx === editingPlace.dayIndex) {
        const updatedPlaces = day.places.map((place, pIdx) => {
          if (pIdx === editingPlace.placeIndex) {
            return {
              ...place,
              id: newPlace.id || place.id,
              name: newPlace.name,
              category: newPlace.category,
              lat: newPlace.lat,
              lng: newPlace.lng,
              rating: newPlace.rating || null,
            };
          }
          return place;
        });
        return { ...day, places: updatedPlaces };
      }
      return day;
    });

    // 수정된 일정 콜백
    onEditItinerary({
      ...data,
      days: updatedDays,
    });

    // 모달 닫기
    setShowEditModal(false);
    setEditingPlace(null);
  };
  
  // 향후 사용 예정 함수들
  void _handleOptimizeRoute; void _openEditModal; void _handlePlaceChange;

  // 선택된 Day의 지도 데이터 생성 (요일별 색상 지원)
  const getMapData = () => {
    const currentData = displayData;
    const daysToShow = selectedMapDay 
      ? currentData.days.filter(d => d.day === selectedMapDay)
      : currentData.days;
    
    const markers: Array<{
      id: number;
      position: { lat: number; lng: number };
      label: string;
      name: string;
      category: string;
      rating?: number;
      day: number; // 요일 정보 추가
      order: number; // 해당 요일 내 순서
    }> = [];
    
    daysToShow.forEach((dayData) => {
      let orderInDay = 1;
      dayData.places.forEach((place) => {
        if (place.lat && place.lng) {
          markers.push({
            id: place.id,
            position: { lat: place.lat, lng: place.lng },
            label: `${orderInDay}`,
            name: place.name,
            category: place.category,
            rating: place.rating || undefined,
            day: dayData.day, // 요일 정보
            order: orderInDay, // 순서
          });
          orderInDay++;
        }
      });
      // 숙소 추가
      if (dayData.accommodation?.lat && dayData.accommodation?.lng) {
        markers.push({
          id: dayData.accommodation.id,
          position: { lat: dayData.accommodation.lat, lng: dayData.accommodation.lng },
          label: '🏨',
          name: dayData.accommodation.name,
          category: '숙소',
          rating: dayData.accommodation.rating,
          day: dayData.day,
          order: orderInDay,
        });
      }
    });
    
    // 제주도 중심 좌표
    const defaultCenter = { lat: 33.3846, lng: 126.5534 };
    
    // 마커가 있으면 중심점 계산
    let center = defaultCenter;
    if (markers.length > 0) {
      const lats = markers.map(m => m.position.lat);
      const lngs = markers.map(m => m.position.lng);
      center = {
        lat: (Math.max(...lats) + Math.min(...lats)) / 2,
        lng: (Math.max(...lngs) + Math.min(...lngs)) / 2,
      };
    }
    
    // 경로 정보 (map_data에서 가져오기)
    let routes = currentData.map_data?.routes;
    
    // 선택된 일자만 필터링
    if (selectedMapDay && routes) {
      routes = routes.filter(r => r.day === selectedMapDay);
    }
    
    return {
      type: 'route_map',
      markers,
      center,
      zoom: 10,
      showDayColors: !selectedMapDay, // 전체 보기일 때만 요일별 색상 표시
      routes: routes, // 실제 도로 경로 정보 포함
    };
  };

  // 지도 모달 열기
  const openMapModal = (dayNum?: number) => {
    setSelectedMapDay(dayNum || null);
    setShowMapModal(true);
  };

  // 표시할 데이터 (최적화된 데이터가 있으면 사용)
  const displayData = optimizedData || data;

  return (
    <div className="mt-4 space-y-4">
      {/* 전체 일정 추가 버튼 */}
      {onAddToSchedule && (
        <div className="flex items-center justify-between bg-gradient-to-r from-orange-50 to-blue-50 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-4 border-2 border-orange-200 dark:border-gray-600">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500 rounded-xl">
              <Calendar className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-gray-900 dark:text-white">
                {displayData.total_days}일 일정 • {displayData.days.reduce((sum, d) => sum + d.places.length, 0)}곳
                {optimizedDays.size > 0 && (
                  <span className="ml-2 text-sm text-green-600 dark:text-green-400">
                    (최적화됨)
                  </span>
                )}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                이 일정을 내 여행에 추가하세요
              </p>
            </div>
          </div>
          <button
            onClick={handleAddAllToSchedule}
            disabled={isAllAdded}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${
              isAllAdded
                ? 'bg-green-500 text-white cursor-default'
                : 'bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white shadow-lg hover:shadow-xl hover:scale-105'
            }`}
          >
            {isAllAdded ? (
              <>
                <Check className="h-5 w-5" />
                추가됨
              </>
            ) : (
              <>
                <Plus className="h-5 w-5" />
                전체 일정 추가
              </>
            )}
          </button>
        </div>
      )}

      {/* 지도 모달 */}
      {showMapModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
              <div className="flex items-center gap-3">
                <Map className="h-6 w-6" />
                <div>
                  <h2 className="text-lg font-bold">
                    🗺️ {selectedMapDay ? `Day ${selectedMapDay}` : '전체'} 여행 경로
                  </h2>
                  <p className="text-sm opacity-90">
                    {selectedMapDay 
                      ? displayData.days.find(d => d.day === selectedMapDay)?.regions.join(' → ')
                      : `${data.total_days}일 전체 코스`
                    }
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowMapModal(false)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Day 탭 */}
            <div className="flex gap-2 p-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
              <button
                onClick={() => setSelectedMapDay(null)}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors whitespace-nowrap ${
                  selectedMapDay === null
                    ? 'bg-indigo-500 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
                }`}
              >
                전체 보기
              </button>
              {displayData.days.map((day) => (
                <button
                  key={day.day}
                  onClick={() => setSelectedMapDay(day.day)}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors whitespace-nowrap ${
                    selectedMapDay === day.day
                      ? `bg-gradient-to-r ${getDayColor(day.day)} text-white`
                      : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
                  }`}
                >
                  Day {day.day}
                </button>
              ))}
            </div>

            {/* 지도 */}
            <div className="h-[60vh]">
              <KakaoMap 
                mapData={getMapData()} 
                className="w-full h-full"
              />
            </div>

            {/* 범례 */}
            <div className="p-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
              <div className="flex flex-wrap gap-3 text-sm text-gray-600 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <span className="w-5 h-5 rounded-full bg-indigo-500 text-white text-xs flex items-center justify-center">1</span>
                  방문 순서
                </span>
                <span className="flex items-center gap-1">
                  <span className="text-lg">🏨</span>
                  숙소
                </span>
                <span className="text-gray-400">|</span>
                <span>마커를 클릭하면 장소 정보를 볼 수 있습니다</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl text-white">
        <div className="flex items-center gap-3">
          <Calendar className="h-6 w-6" />
          <div>
            <h2 className="text-lg font-bold">🗓️ 제주 여행 일정</h2>
            <p className="text-sm opacity-90">{data.total_days}일 코스</p>
          </div>
        </div>
        
        {/* 지도에서 보기 버튼 */}
        {!hideMapButton && (
          <button
            onClick={() => openMapModal()}
            className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg font-medium text-sm transition-colors"
          >
            <Map className="h-5 w-5" />
            지도에서 보기
          </button>
        )}
      </div>

      {/* Day별 타임라인 */}
      {data.days.map((day) => (
        <div 
          key={day.day}
          className="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden bg-white dark:bg-gray-900 shadow-sm"
        >
          {/* Day 헤더 */}
          <div
            className={`p-4 flex items-center justify-between bg-gradient-to-r ${getDayColor(day.day)} text-white`}
          >
            <button
              onClick={() => toggleDay(day.day)}
              className="flex items-center gap-3 flex-1"
            >
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold">
                D{day.day}
              </div>
              <div className="text-left">
                <p className="font-semibold">{day.label}</p>
                <p className="text-sm opacity-90">
                  <MapPin className="h-3 w-3 inline mr-1" />
                  {day.regions.join(' → ')}
                </p>
              </div>
            </button>
            
            <div className="flex items-center gap-2">
              {/* Day별 지도 보기 버튼 */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  openMapModal(day.day);
                }}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title={`Day ${day.day} 지도 보기`}
              >
                <Map className="h-5 w-5" />
              </button>
              
              {/* 펼치기/접기 버튼 */}
              <button
                onClick={() => toggleDay(day.day)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                {expandedDays.includes(day.day) ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>

          {/* 일정 내용 */}
          {expandedDays.includes(day.day) && (
            <div className="p-4">
              {/* 타임라인 - 시간순 정렬 */}
              <div className="relative pl-6 border-l-2 border-gray-200 dark:border-gray-700 space-y-4">
                {[...day.places].sort((a, b) => {
                  // start_time 기준 정렬 (예: "10:00", "12:30")
                  const timeToMinutes = (time: string) => {
                    if (!time) return 0;
                    const [h, m] = time.split(':').map(Number);
                    return (h || 0) * 60 + (m || 0);
                  };
                  return timeToMinutes(a.start_time) - timeToMinutes(b.start_time);
                }).map((place, idx) => (
                  <div key={`${place.id}-${idx}`} className="relative">
                    {/* 타임라인 점 */}
                    <div className="absolute -left-[25px] w-4 h-4 rounded-full bg-white dark:bg-gray-900 border-2 border-indigo-500 flex items-center justify-center">
                      <div className="w-2 h-2 rounded-full bg-indigo-500" />
                    </div>

                    {/* 장소 카드 */}
                    <div className="ml-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors group">
                      {/* 시간대 */}
                      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-2">
                        {getTimeIcon(place.time_slot)}
                        <span className="font-medium">{place.time_slot}</span>
                        <span className="text-xs">({place.start_time} ~ {place.end_time})</span>
                      </div>

                      {/* 장소 정보 */}
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 dark:text-white">
                            {place.name}
                          </h4>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            <span className={`px-2 py-0.5 rounded-full text-xs ${getCategoryColor(place.category)}`}>
                              {place.category}
                            </span>
                            {place.region && (
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                <MapPin className="h-3 w-3 inline" /> {place.region}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {/* 평점 */}
                          {place.rating && (
                            <div className="flex items-center gap-1 px-2 py-1 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                              <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                              <span className="text-sm font-bold text-yellow-600 dark:text-yellow-400">
                                {place.rating.toFixed(1)}
                              </span>
                            </div>
                          )}
                          
                          {/* 개별 추가 버튼 */}
                          {onAddPlace && (
                            <button
                              onClick={() => handleAddPlace(place, day.day, idx + 1)}
                              disabled={addedPlaces.has(place.name)}
                              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                                addedPlaces.has(place.name)
                                  ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                                  : 'bg-orange-100 text-orange-600 hover:bg-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:hover:bg-orange-900/50 opacity-0 group-hover:opacity-100'
                              }`}
                            >
                              {addedPlaces.has(place.name) ? (
                                <>
                                  <Check className="h-4 w-4" />
                                  추가됨
                                </>
                              ) : (
                                <>
                                  <Plus className="h-4 w-4" />
                                  추가
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* 숙소 */}
                {day.accommodation && (
                  <div className="relative">
                    <div className="absolute -left-[25px] w-4 h-4 rounded-full bg-white dark:bg-gray-900 border-2 border-purple-500 flex items-center justify-center">
                      <Hotel className="h-2 w-2 text-purple-500" />
                    </div>
                    <div className="ml-4 p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
                      <div className="flex items-center gap-2 text-sm text-purple-600 dark:text-purple-400 mb-1">
                        <Hotel className="h-4 w-4" />
                        <span className="font-medium">숙소</span>
                      </div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">
                        {day.accommodation.name}
                      </h4>
                      {day.accommodation.address && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {day.accommodation.address}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}

      {/* 하단 팁 */}
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-blue-700 dark:text-blue-300">
        💡 <strong>팁:</strong> 각 장소에서 1~2시간 정도 여유를 두고 이동하세요!
      </div>

    </div>
  );
}

