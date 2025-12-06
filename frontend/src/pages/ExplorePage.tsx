/**
 * Explore Page - 관광지 탐색
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Search, MapPin, Star, Info, Loader2, X, Phone, Clock, ParkingSquare, Baby, Accessibility, Dog, CalendarCheck, Wifi, ExternalLink } from 'lucide-react';
import { getAttractionsList, getPlaceDetail } from '../api/attractions';
import type { Attraction } from '../api/attractions';

// 상세 정보 타입
interface PlaceDetail {
  id: number;
  name: string;
  category: string;
  address: string;
  phone: string;
  rating: number;
  review_count: number;
  min_price: number;
  max_price: number;
  price_range: string;
  parking: boolean;
  kid_friendly: boolean;
  wheelchair: boolean;
  pet_friendly: boolean;
  reservation: boolean;
  wifi: boolean;
  business_hours: string;
  lat: number;
  lng: number;
  region: string;
  url: string;
  description?: string;
}

// 카테고리별 이모지 매핑
const categoryEmojis: Record<string, string> = {
  '전체': '🏝️',
  '자연': '🌳',
  '문화': '🏛️',
  '해변': '🏖️',
  '맛집': '🍖',
  '카페': '☕',
  '숙박': '🏨',
  '액티비티': '🎯',
  '관광지': '🗺️',
};

const ExplorePage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('전체');
  const [attractions, setAttractions] = useState<Attraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // 상세 모달 상태
  const [selectedPlace, setSelectedPlace] = useState<PlaceDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  
  // 카드 클릭 핸들러
  const handleCardClick = async (attraction: Attraction) => {
    if (attraction.source !== 'place') {
      // attractions 테이블 데이터는 이미 가지고 있는 정보로 모달 표시
      const attractionDetail: PlaceDetail = {
        id: attraction.id,
        name: attraction.name,
        category: attraction.category,
        address: attraction.address || '',
        phone: attraction.phone || '',
        rating: attraction.rating || 0,
        review_count: 0,
        min_price: 0,
        max_price: 0,
        price_range: attraction.price || attraction.price_range || '',
        parking: attraction.parking || false,
        kid_friendly: attraction.kid_friendly || false,
        wheelchair: attraction.wheelchair || false,
        pet_friendly: attraction.pet_friendly || false,
        reservation: attraction.reservation || false,
        wifi: attraction.wifi || false,
        business_hours: attraction.business_hours || '',
        lat: attraction.lat || 0,
        lng: attraction.lng || 0,
        region: '',
        url: '',
        description: attraction.description || '',
      };
      setSelectedPlace(attractionDetail);
      return;
    }
    
    try {
      setDetailLoading(true);
      const detail = await getPlaceDetail(attraction.id);
      setSelectedPlace(detail);
    } catch (err) {
      console.error('Failed to fetch detail:', err);
      alert('상세 정보를 불러오는데 실패했습니다.');
    } finally {
      setDetailLoading(false);
    }
  };

  const categories = [
    { name: '전체', emoji: '🏝️' },
    { name: '자연', emoji: '🌳' },
    { name: '문화', emoji: '🏛️' },
    { name: '해변', emoji: '🏖️' },
    { name: '맛집', emoji: '🍖' },
    { name: '카페', emoji: '☕' },
    { name: '숙박', emoji: '🏨' },
    { name: '액티비티', emoji: '🎯' },
  ];

  // API에서 데이터 로드
  const fetchAttractions = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getAttractionsList(
        selectedCategory !== '전체' ? selectedCategory : undefined,
        searchTerm || undefined,
        5000  // 전체 데이터 조회
      );
      setAttractions(data);
    } catch (err: any) {
      console.error('Failed to fetch attractions:', err);
      setError('데이터를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchTerm]);

  // 카테고리 변경 시 API 재호출
  useEffect(() => {
    fetchAttractions();
  }, [selectedCategory]);

  // 검색어 입력 시 debounce 적용
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchTerm !== '') {
        fetchAttractions();
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // 초기 로드
  useEffect(() => {
    fetchAttractions();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-orange-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-blue-400 via-blue-500 to-cyan-500 text-white py-20">
        {/* 배경 장식 */}
        <div className="absolute top-5 right-10 text-6xl opacity-20 animate-pulse">🏖️</div>
        <div className="absolute bottom-5 left-10 text-5xl opacity-20 animate-bounce">🌺</div>
        
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-block mb-4 px-6 py-2 bg-white/20 backdrop-blur-sm rounded-full">
            <span className="text-white font-medium text-sm">
              🗺️ 제주의 모든 것
            </span>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-black mb-6">
            관광지 탐색
          </h1>
          
          <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto">
            제주도의 숨은 명소부터 인기 관광지까지<br />
            모든 것을 한눈에 찾아보세요 ✨
          </p>
        </div>
      </div>

      {/* Search Bar - 헤더 외부로 이동 */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-sm -mt-8 relative z-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="max-w-2xl mx-auto">
            <div className="relative">
              <Search className="absolute left-5 top-1/2 transform -translate-y-1/2 text-gray-400" size={24} />
              <input
                type="text"
                placeholder="관광지 이름, 설명으로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-14 pr-6 py-4 rounded-2xl bg-white dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600 text-gray-800 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-blue-200 dark:focus:ring-blue-800 focus:border-blue-400 dark:focus:border-blue-500 shadow-lg text-lg"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Categories - 귀여운 칩 스타일 */}
      <div className="sticky top-0 z-40 bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex gap-3 overflow-x-auto hide-scrollbar pb-2">
            {categories.map((category) => (
              <button
                key={category.name}
                onClick={() => setSelectedCategory(category.name)}
                className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-bold whitespace-nowrap transition-all shadow-md ${
                  selectedCategory === category.name
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-110 shadow-lg'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 hover:scale-105'
                }`}
              >
                <span className="text-xl">{category.emoji}</span>
                <span>{category.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border-2 border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-xl">
                <Info className="text-blue-600 dark:text-blue-400" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">검색 결과</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {loading ? '로딩 중...' : `${attractions.length}개의 장소`}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600 dark:text-gray-400">카테고리</p>
              <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                {selectedCategory}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-4">
          <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-6 py-4 rounded-2xl">
            {error}
          </div>
        </div>
      )}

      {/* Attractions Grid */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block p-8 bg-white dark:bg-gray-800 rounded-3xl shadow-xl">
              <Loader2 className="animate-spin mx-auto h-12 w-12 text-blue-500 mb-4" />
              <p className="text-gray-600 dark:text-gray-400 text-xl font-medium">
                로딩 중...
              </p>
            </div>
          </div>
        ) : attractions.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-block p-8 bg-white dark:bg-gray-800 rounded-3xl shadow-xl">
              <div className="text-6xl mb-4">🔍</div>
              <p className="text-gray-600 dark:text-gray-400 text-xl font-medium mb-4">
                검색 결과가 없어요
              </p>
              <p className="text-gray-500 dark:text-gray-500 text-sm">
                다른 키워드로 검색해보세요
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {attractions.map((attraction) => (
              <div
                key={`${attraction.source}-${attraction.id}`}
                onClick={() => handleCardClick(attraction)}
                className="group bg-white dark:bg-gray-800 rounded-3xl shadow-lg hover:shadow-2xl transition-all overflow-hidden border-2 border-gray-100 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-500 cursor-pointer hover:-translate-y-2"
              >
                {/* Image - 카테고리별 이모지 배경 */}
                <div className="relative bg-gradient-to-br from-blue-50 via-cyan-50 to-blue-100 dark:from-gray-700 dark:to-gray-600 h-52 flex items-center justify-center overflow-hidden">
                  <div className="text-9xl group-hover:scale-110 transition-transform">
                    {categoryEmojis[attraction.category] || '🗺️'}
                  </div>
                  {/* 평점 배지 - rating이 0.1 이상일 때만 표시 */}
                  {attraction.rating != null && Number(attraction.rating) >= 0.1 && (
                    <div className="absolute top-4 right-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm px-3 py-2 rounded-full flex items-center gap-2 shadow-lg">
                      <Star size={16} className="text-yellow-500" fill="currentColor" />
                      <span className="text-sm font-bold text-gray-700 dark:text-gray-300">
                        {Number(attraction.rating).toFixed(1)}
                      </span>
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`px-4 py-1.5 rounded-full text-xs font-bold ${
                      attraction.category === '맛집' 
                        ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                        : attraction.category === '카페'
                        ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                    }`}>
                      {attraction.category}
                    </span>
                    {attraction.price && (
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {attraction.price}
                      </span>
                    )}
                  </div>

                  <h3 className="text-2xl font-black text-gray-900 dark:text-white mb-3 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-1">
                    {attraction.name}
                  </h3>

                  <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm">
                    <MapPin size={16} className="text-blue-500 flex-shrink-0" />
                    <span className="line-clamp-1">{attraction.address || '제주도'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 상세 정보 모달 */}
      {selectedPlace && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedPlace(null)}>
          <div 
            className="bg-white dark:bg-gray-800 rounded-3xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 헤더 */}
            <div className="relative bg-gradient-to-r from-blue-500 to-cyan-500 p-6 text-white">
              <button 
                onClick={() => setSelectedPlace(null)}
                className="absolute top-4 right-4 p-2 hover:bg-white/20 rounded-full transition"
              >
                <X size={24} />
              </button>
              <div className="pr-10">
                <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-sm mb-2">
                  {selectedPlace.category}
                </span>
                <h2 className="text-2xl font-bold">{selectedPlace.name}</h2>
                <div className="flex items-center gap-2 mt-2">
                  <Star className="text-yellow-300 fill-yellow-300" size={18} />
                  <span className="font-bold">{selectedPlace.rating?.toFixed(1) || 'N/A'}</span>
                  <span className="text-white/70">({selectedPlace.review_count || 0} 리뷰)</span>
                </div>
              </div>
            </div>

            {/* 정보 */}
            <div className="p-6 space-y-4">
              {/* 소개 */}
              {selectedPlace.description && (
                <div className="flex items-start gap-3">
                  <Info className="text-purple-500 flex-shrink-0 mt-1" size={20} />
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">소개</p>
                    <p className="text-gray-900 dark:text-white leading-relaxed">{selectedPlace.description}</p>
                  </div>
                </div>
              )}

              {/* 주소 */}
              <div className="flex items-start gap-3">
                <MapPin className="text-blue-500 flex-shrink-0 mt-1" size={20} />
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">주소</p>
                  <p className="text-gray-900 dark:text-white">{selectedPlace.address || '-'}</p>
                  {selectedPlace.region && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs rounded">
                      {selectedPlace.region}
                    </span>
                  )}
                </div>
              </div>

              {/* 전화번호 */}
              {selectedPlace.phone && (
                <div className="flex items-start gap-3">
                  <Phone className="text-green-500 flex-shrink-0 mt-1" size={20} />
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">전화번호</p>
                    <a href={`tel:${selectedPlace.phone}`} className="text-blue-600 dark:text-blue-400 hover:underline">
                      {selectedPlace.phone}
                    </a>
                  </div>
                </div>
              )}

              {/* 영업시간 */}
              {selectedPlace.business_hours && (
                <div className="flex items-start gap-3">
                  <Clock className="text-orange-500 flex-shrink-0 mt-1" size={20} />
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">영업시간</p>
                    <p className="text-gray-900 dark:text-white whitespace-pre-line">{selectedPlace.business_hours}</p>
                  </div>
                </div>
              )}

              {/* 가격대 */}
              {(selectedPlace.min_price || selectedPlace.max_price) && (
                <div className="flex items-start gap-3">
                  <span className="text-xl flex-shrink-0">💰</span>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">가격대</p>
                    <p className="text-gray-900 dark:text-white">
                      {selectedPlace.min_price?.toLocaleString()}원 ~ {selectedPlace.max_price?.toLocaleString()}원
                      {selectedPlace.price_range && (
                        <span className="ml-2 text-orange-600 dark:text-orange-400">({selectedPlace.price_range})</span>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* 시설 정보 */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">시설 정보</p>
                <div className="grid grid-cols-3 gap-3">
                  <div className={`flex flex-col items-center p-3 rounded-xl ${selectedPlace.parking ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-400'}`}>
                    <ParkingSquare size={24} />
                    <span className="text-xs mt-1">주차</span>
                  </div>
                  <div className={`flex flex-col items-center p-3 rounded-xl ${selectedPlace.kid_friendly ? 'bg-pink-50 dark:bg-pink-900/20 text-pink-700 dark:text-pink-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-400'}`}>
                    <Baby size={24} />
                    <span className="text-xs mt-1">아이동반</span>
                  </div>
                  <div className={`flex flex-col items-center p-3 rounded-xl ${selectedPlace.wheelchair ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-400'}`}>
                    <Accessibility size={24} />
                    <span className="text-xs mt-1">휠체어</span>
                  </div>
                  <div className={`flex flex-col items-center p-3 rounded-xl ${selectedPlace.pet_friendly ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-400'}`}>
                    <Dog size={24} />
                    <span className="text-xs mt-1">반려동물</span>
                  </div>
                  <div className={`flex flex-col items-center p-3 rounded-xl ${selectedPlace.reservation ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-400'}`}>
                    <CalendarCheck size={24} />
                    <span className="text-xs mt-1">예약</span>
                  </div>
                  <div className={`flex flex-col items-center p-3 rounded-xl ${selectedPlace.wifi ? 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-400'}`}>
                    <Wifi size={24} />
                    <span className="text-xs mt-1">WiFi</span>
                  </div>
                </div>
              </div>

              {/* 네이버 플레이스 링크 */}
              {selectedPlace.url && (
                <a
                  href={selectedPlace.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 bg-green-500 hover:bg-green-600 text-white rounded-xl font-bold transition"
                >
                  <ExternalLink size={18} />
                  네이버 플레이스에서 보기
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 로딩 오버레이 */}
      {detailLoading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-xl">
            <Loader2 className="animate-spin mx-auto h-8 w-8 text-blue-500" />
            <p className="mt-2 text-gray-600 dark:text-gray-400">상세 정보 로딩 중...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplorePage;
