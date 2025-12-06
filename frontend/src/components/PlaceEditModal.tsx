/**
 * PlaceEditModal - 장소 수정 모달 (OR-Tools 기반 동선 최적화 대안 추천)
 */
import { useState, useEffect } from 'react';
import { 
  X, 
  MapPin, 
  Star, 
  Route,
  Check,
  RefreshCw,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import apiClient from '../api/client';

interface PlaceInfo {
  id?: number;
  name: string;
  category: string;
  lat: number;
  lng: number;
  rating?: number;
}

interface AlternativePlace {
  id: number;
  name: string;
  category: string;
  lat: number;
  lng: number;
  rating: number;
  address: string;
  source: string;
  distance_impact: number;
  total_route_distance: number;
}

interface PlaceEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPlaces: PlaceInfo[];
  replaceIndex: number;
  originalPlace: PlaceInfo;
  onSelectPlace: (newPlace: PlaceInfo) => void;
}

// 카테고리 한글 매핑
const categoryOptions = [
  { value: '자연', label: '🏔️ 자연' },
  { value: '문화', label: '🏛️ 문화' },
  { value: '해변', label: '🏖️ 해변' },
  { value: '맛집', label: '🍽️ 맛집' },
  { value: '카페', label: '☕ 카페' },
  { value: '액티비티', label: '🎢 액티비티' },
];

export default function PlaceEditModal({
  isOpen,
  onClose,
  currentPlaces,
  replaceIndex,
  originalPlace,
  onSelectPlace,
}: PlaceEditModalProps) {
  const [alternatives, setAlternatives] = useState<AlternativePlace[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState(originalPlace.category);
  const [sortBy, setSortBy] = useState<'distance' | 'rating'>('distance');

  // 대안 장소 불러오기
  const fetchAlternatives = async () => {
    setLoading(true);
    setError(null);

    try {
      // 원본 데이터 로깅
      console.log('🔍 원본 currentPlaces:', currentPlaces);
      console.log('🔍 replaceIndex:', replaceIndex);
      console.log('🔍 selectedCategory:', selectedCategory);
      
      // lat/lng가 유효한 장소만 필터링
      const validPlaces = currentPlaces.filter(p => {
        const lat = Number(p.lat);
        const lng = Number(p.lng);
        const isValid = !isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0;
        if (!isValid) {
          console.log('❌ 필터링된 장소:', p.name, 'lat:', p.lat, 'lng:', p.lng);
        }
        return isValid;
      });
      
      console.log('✅ 유효한 장소 수:', validPlaces.length);
      
      if (validPlaces.length < 2) {
        setError('유효한 위치 정보가 있는 장소가 2개 이상 필요합니다');
        setLoading(false);
        return;
      }
      
      const requestBody = {
        current_places: validPlaces.map(p => ({
          // id가 숫자인 경우만 포함 (해시 문자열 제외)
          ...(typeof p.id === 'number' ? { id: p.id } : {}),
          name: p.name,
          category: p.category || '관광지',
          lat: Number(p.lat),
          lng: Number(p.lng),
          rating: Number(p.rating) || 0,
        })),
        replace_index: Math.min(replaceIndex, validPlaces.length - 1),
        category: selectedCategory || '맛집',
        limit: 15,
      };
      
      console.log('📤 API 요청 데이터:', JSON.stringify(requestBody, null, 2));
      
      const response = await apiClient.post<AlternativePlace[]>(
        '/api/attractions/recommend-alternatives',
        requestBody
      );

      setAlternatives(response.data);
    } catch (err: any) {
      console.error('대안 추천 오류:', err);
      console.error('📛 에러 응답 전체:', err.response?.data);
      console.error('📛 에러 상태:', err.response?.status);
      
      // 에러 메시지 처리 (객체일 수 있음)
      let errorMessage = '대안 장소를 불러오는데 실패했습니다';
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (Array.isArray(detail)) {
        // Pydantic 검증 에러
        errorMessage = detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join(', ');
        console.error('📛 Pydantic 에러 상세:', detail);
      } else if (typeof detail === 'object') {
        errorMessage = JSON.stringify(detail);
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 모달 열릴 때 또는 카테고리 변경 시 API 호출
  useEffect(() => {
    if (isOpen) {
      fetchAlternatives();
    }
  }, [isOpen, selectedCategory]);

  // 정렬된 목록
  const sortedAlternatives = [...alternatives].sort((a, b) => {
    if (sortBy === 'distance') {
      return a.distance_impact - b.distance_impact;
    } else {
      return b.rating - a.rating;
    }
  });

  // 장소 선택
  const handleSelect = (alt: AlternativePlace) => {
    onSelectPlace({
      id: alt.id,
      name: alt.name,
      category: alt.category,
      lat: alt.lat,
      lng: alt.lng,
      rating: alt.rating,
    });
    onClose();
  };

  // 거리 영향 표시 아이콘
  const getDistanceImpactIcon = (impact: number) => {
    if (impact < -0.5) return <TrendingDown className="h-4 w-4 text-green-500" />;
    if (impact > 0.5) return <TrendingUp className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-gray-400" />;
  };

  // 거리 영향 색상
  const getDistanceImpactColor = (impact: number) => {
    if (impact < -0.5) return 'text-green-600 bg-green-50 dark:bg-green-900/30 dark:text-green-400';
    if (impact > 0.5) return 'text-red-600 bg-red-50 dark:bg-red-900/30 dark:text-red-400';
    return 'text-gray-600 bg-gray-50 dark:bg-gray-700 dark:text-gray-400';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden shadow-2xl">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
          <div className="flex items-center gap-3">
            <Route className="h-6 w-6" />
            <div>
              <h2 className="text-lg font-bold">장소 변경하기</h2>
              <p className="text-sm opacity-90">
                "{originalPlace.name}" 대신 다른 장소를 선택하세요
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* 필터 & 정렬 */}
        <div className="p-4 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 space-y-3">
          {/* 카테고리 선택 */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {categoryOptions.map((cat) => (
              <button
                key={cat.value}
                onClick={() => setSelectedCategory(cat.value)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  selectedCategory === cat.value
                    ? 'bg-indigo-500 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* 정렬 옵션 */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600 dark:text-gray-400">정렬:</span>
            <button
              onClick={() => setSortBy('distance')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm ${
                sortBy === 'distance'
                  ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Route className="h-4 w-4" />
              동선 효율순
            </button>
            <button
              onClick={() => setSortBy('rating')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm ${
                sortBy === 'rating'
                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Star className="h-4 w-4" />
              평점순
            </button>
            
            <button
              onClick={fetchAlternatives}
              disabled={loading}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              새로고침
            </button>
          </div>
        </div>

        {/* 결과 목록 */}
        <div className="overflow-y-auto max-h-[calc(85vh-220px)]">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 text-indigo-500 animate-spin mb-3" />
              <p className="text-gray-600 dark:text-gray-400">최적 경로 계산 중...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 text-red-500">
              <AlertCircle className="h-8 w-8 mb-3" />
              <p>{error}</p>
              <button
                onClick={fetchAlternatives}
                className="mt-3 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
              >
                다시 시도
              </button>
            </div>
          ) : sortedAlternatives.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <MapPin className="h-8 w-8 mb-3" />
              <p>해당 카테고리의 대안 장소가 없습니다</p>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {/* 동선 효율 안내 */}
              <div className="flex items-center gap-2 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg text-sm text-indigo-700 dark:text-indigo-300">
                <Route className="h-5 w-5 flex-shrink-0" />
                <span>
                  <strong>동선 효율:</strong> 이 장소를 선택하면 총 이동거리가 얼마나 변하는지 보여줍니다.
                  초록색은 더 효율적, 빨간색은 덜 효율적입니다.
                </span>
              </div>

              {/* 장소 카드 목록 */}
              {sortedAlternatives.map((alt, idx) => (
                <div
                  key={alt.id}
                  className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-indigo-300 dark:hover:border-indigo-600 hover:shadow-md transition-all group"
                >
                  <div className="flex items-start justify-between gap-4">
                    {/* 장소 정보 */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-bold text-indigo-500">#{idx + 1}</span>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {alt.name}
                        </h3>
                      </div>
                      
                      <div className="flex items-center gap-2 flex-wrap text-sm">
                        <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                          {alt.category}
                        </span>
                        
                        {alt.rating > 0 && (
                          <span className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
                            <Star className="h-3.5 w-3.5 fill-current" />
                            {alt.rating.toFixed(1)}
                          </span>
                        )}
                        
                        {alt.address && (
                          <span className="text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                            <MapPin className="h-3 w-3 inline" /> {alt.address}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* 동선 효율 & 선택 버튼 */}
                    <div className="flex flex-col items-end gap-2">
                      {/* 동선 효율 표시 */}
                      <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${getDistanceImpactColor(alt.distance_impact)}`}>
                        {getDistanceImpactIcon(alt.distance_impact)}
                        <span>
                          {alt.distance_impact > 0 ? '+' : ''}{alt.distance_impact.toFixed(1)}km
                        </span>
                      </div>
                      
                      {/* 총 거리 */}
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        총 {alt.total_route_distance.toFixed(1)}km
                      </span>
                      
                      {/* 선택 버튼 */}
                      <button
                        onClick={() => handleSelect(alt)}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white font-medium text-sm transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <Check className="h-4 w-4" />
                        선택
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 하단 안내 */}
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-600 dark:text-gray-400">
          💡 <strong>팁:</strong> 동선 효율이 높은 장소를 선택하면 전체 이동시간이 줄어듭니다!
        </div>
      </div>
    </div>
  );
}

