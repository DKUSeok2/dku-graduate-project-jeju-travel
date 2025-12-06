/**
 * Kakao Map Component - 제주 여행 지도
 * 요일별 색상 마커 + 순서 번호 + 예쁜 경로선
 */
import React, { useEffect, useState } from 'react';
import { Map, CustomOverlayMap, Polyline } from 'react-kakao-maps-sdk';

// 요일별 색상 팔레트 (7일까지)
const DAY_COLORS = [
  { bg: '#FF6B6B', border: '#E85555', name: 'Day 1' }, // 코랄 레드
  { bg: '#4ECDC4', border: '#3DBDB5', name: 'Day 2' }, // 청록
  { bg: '#45B7D1', border: '#35A7C1', name: 'Day 3' }, // 스카이 블루
  { bg: '#96CEB4', border: '#86BEA4', name: 'Day 4' }, // 민트 그린
  { bg: '#FFEAA7', border: '#FFD93D', name: 'Day 5' }, // 옐로우
  { bg: '#DDA0DD', border: '#CD90CD', name: 'Day 6' }, // 플럼
  { bg: '#98D8C8', border: '#88C8B8', name: 'Day 7' }, // 씨폼
];

interface MapMarkerData {
  name?: string;  // 장소명 (우선)
  title?: string; // 장소명 (fallback)
  lat?: number;
  lng?: number;
  position?: {
    lat: number;
    lng: number;
  };
  emoji?: string;
  id?: number;
  label?: string;
  category?: string;
  rating?: number;
  price?: string;
  day?: number; // 요일 (1, 2, 3...)
  order?: number; // 해당 요일 내 순서
  address?: string; // 주소
  description?: string; // 설명
  phone?: string; // 전화번호
  image?: string; // 이미지 URL
  openingHours?: string; // 영업시간
}

interface RoutePathData {
  from_place?: { name: string; lat: number; lng: number };
  to_place?: { name: string; lat: number; lng: number };
  path: number[][]; // [[lat, lng], [lat, lng], ...]
  distance?: number;
  duration?: number;
}

interface DayRouteData {
  day: number;
  routes: RoutePathData[];
}

interface MapData {
  markers: MapMarkerData[];
  center?: {
    lat: number;
    lng: number;
  };
  zoom?: number;
  showDayColors?: boolean; // 요일별 색상 사용 여부
  routes?: DayRouteData[]; // 실제 도로 경로 정보
}

interface KakaoMapProps {
  mapData: MapData;
  className?: string;
  style?: React.CSSProperties;
  hideRoutes?: boolean; // true면 경로(선) 숨김, 마커만 표시
}

// 마커에서 좌표 추출 헬퍼 함수
const getMarkerCoords = (marker: MapMarkerData): { lat: number; lng: number } => {
  if (marker.position) {
    return { lat: marker.position.lat, lng: marker.position.lng };
  }
  return { lat: marker.lat || 33.45, lng: marker.lng || 126.57 };
};

// 요일별 색상 가져오기
const getDayColor = (day: number) => {
  return DAY_COLORS[(day - 1) % DAY_COLORS.length];
};

// 두 점 사이의 중간점 계산
const getMidpoint = (
  p1: { lat: number; lng: number },
  p2: { lat: number; lng: number }
) => ({
  lat: (p1.lat + p2.lat) / 2,
  lng: (p1.lng + p2.lng) / 2,
});

// 두 점 사이의 각도 계산 (화살표 방향용)
const getAngle = (
  p1: { lat: number; lng: number },
  p2: { lat: number; lng: number }
) => {
  const dx = p2.lng - p1.lng;
  const dy = p2.lat - p1.lat;
  return Math.atan2(dy, dx) * (180 / Math.PI);
};

const KakaoMap: React.FC<KakaoMapProps> = ({ mapData, className = '', style = {}, hideRoutes = false }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [selectedDay, setSelectedDay] = useState<number | 'all'>(1); // 기본값: 1일차
  const [selectedMarker, setSelectedMarker] = useState<MapMarkerData | null>(null); // 선택된 마커 정보
  const [markerDetails, setMarkerDetails] = useState<any>(null); // API에서 가져온 상세 정보
  const [loadingDetails, setLoadingDetails] = useState(false);
  
  const showDayColors = mapData.showDayColors ?? true;
  
  // 마커 클릭 시 상세 정보 가져오기
  const fetchMarkerDetails = async (marker: MapMarkerData) => {
    setLoadingDetails(true);
    setMarkerDetails(null);
    
    try {
      // 이름으로 attractions에서 검색
      const name = marker.name || marker.title;
      if (name) {
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/attractions?search=${encodeURIComponent(name)}&limit=1`);
        if (response.ok) {
          const data = await response.json();
          // API가 배열을 직접 반환
          if (Array.isArray(data) && data.length > 0) {
            console.log('✅ 상세 정보 로드:', data[0]);
            setMarkerDetails(data[0]);
          } else if (data.attractions && data.attractions.length > 0) {
            // 또는 { attractions: [...] } 형식
            setMarkerDetails(data.attractions[0]);
          }
        }
      }
    } catch (err) {
      console.error('상세 정보 로드 실패:', err);
    } finally {
      setLoadingDetails(false);
    }
  };
  
  // center 계산 (center가 없으면 첫 번째 마커 위치 또는 제주도 중심)
  const getCenter = () => {
    if (mapData.center) return mapData.center;
    if (mapData.markers.length > 0) {
      const coords = getMarkerCoords(mapData.markers[0]);
      return coords;
    }
    return { lat: 33.45, lng: 126.57 }; // 제주도 중심
  };
  
  const center = getCenter();
  
  useEffect(() => {
    // Kakao Maps SDK 로드 확인 (재시도 로직 포함)
    let retryCount = 0;
    const maxRetries = 10;
    const retryDelay = 300; // ms
    
    const loadKakaoMap = () => {
      if (window.kakao && window.kakao.maps) {
        window.kakao.maps.load(() => {
          console.log('✅ Kakao Maps SDK 로드 완료');
          setIsLoaded(true);
        });
      } else if (retryCount < maxRetries) {
        retryCount++;
        console.log(`⏳ Kakao Maps SDK 대기 중... (${retryCount}/${maxRetries})`);
        setTimeout(loadKakaoMap, retryDelay);
      } else {
        console.error('❌ Kakao Maps SDK를 찾을 수 없습니다 (타임아웃)');
      }
    };

    loadKakaoMap();
  }, []);

  if (!isLoaded) {
    return (
      <div 
        className={className || 'w-full h-full'} 
        style={{ 
          ...style, 
          minHeight: '300px',
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          background: '#f3f4f6' 
        }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-600">지도 로딩 중...</p>
        </div>
      </div>
    );
  }
  
  // 요일별 마커 그룹화 (order 순서대로 정렬)
  const markersByDay = mapData.markers.reduce((acc, marker) => {
    const day = marker.day || 1;
    if (!acc[day]) acc[day] = [];
    acc[day].push(marker);
    return acc;
  }, {} as Record<number, MapMarkerData[]>);
  
  // 각 day 내에서 order로 정렬
  Object.keys(markersByDay).forEach(day => {
    markersByDay[parseInt(day)].sort((a, b) => (a.order || 0) - (b.order || 0));
  });
  
  // 사용 가능한 일차 목록
  const availableDays = Object.keys(markersByDay).map(d => parseInt(d)).sort((a, b) => a - b);
  
  // 선택된 일차만 필터링 (all이면 전체)
  const filteredMarkersByDay = selectedDay === 'all' 
    ? markersByDay 
    : { [selectedDay]: markersByDay[selectedDay] || [] };
  
  // 실제 도로 경로 데이터가 있는지 확인
  const hasRoadRoutes = mapData.routes && mapData.routes.length > 0;
  
  // 요일별 경로 데이터 생성 (실제 도로 경로 우선, 없으면 직선)
  const dayPaths: Array<{
    day: number;
    paths: Array<{ lat: number; lng: number }[]>; // 여러 구간의 경로
    color: { bg: string; border: string; name: string };
  }> = [];
  
  if (hasRoadRoutes) {
    // 실제 도로 경로 사용
    const filteredRoutes = selectedDay === 'all'
      ? mapData.routes!
      : mapData.routes!.filter(r => r.day === selectedDay);
    
    filteredRoutes.forEach(dayRoute => {
      const paths: Array<{ lat: number; lng: number }[]> = [];
      dayRoute.routes.forEach(route => {
        if (route.path && route.path.length > 0) {
          // path가 [[lat, lng], [lat, lng], ...] 형식
          const pathCoords = route.path.map(coord => ({
            lat: coord[0],
            lng: coord[1]
          }));
          paths.push(pathCoords);
        }
      });
      if (paths.length > 0) {
        dayPaths.push({
          day: dayRoute.day,
          paths,
          color: getDayColor(dayRoute.day),
        });
      }
    });
  }
  
  // 실제 도로 경로가 없으면 직선 경로 사용 (fallback)
  if (dayPaths.length === 0) {
    Object.entries(filteredMarkersByDay)
      .filter(([_, markers]) => markers && markers.length > 0)
      .sort(([a], [b]) => parseInt(a) - parseInt(b))
      .forEach(([day, markers]) => {
        dayPaths.push({
          day: parseInt(day),
          paths: [markers.map(m => getMarkerCoords(m))], // 단일 직선 경로
          color: getDayColor(parseInt(day)),
        });
      });
  }

  // 경로 중간점 (화살표 표시용)
  const arrowPoints: Array<{
    position: { lat: number; lng: number };
    angle: number;
    day: number;
  }> = [];
  
  dayPaths.forEach(({ day, paths }) => {
    paths.forEach(path => {
      // 경로의 중간 지점에만 화살표 표시 (너무 많으면 복잡해짐)
      if (path.length >= 2) {
        const midIdx = Math.floor(path.length / 2);
        const p1 = path[Math.max(0, midIdx - 1)];
        const p2 = path[Math.min(path.length - 1, midIdx)];
        const midpoint = getMidpoint(p1, p2);
        const angle = getAngle(p1, p2);
        arrowPoints.push({ position: midpoint, angle: angle - 90, day });
      }
    });
  });
  
  console.log('🗺️ 경로 데이터:', { hasRoadRoutes, dayPathsCount: dayPaths.length });

  console.log('🗺️ 지도 렌더링:', { center, markers: mapData.markers.length, days: Object.keys(markersByDay).length });

  // 기본 스타일 (높이가 지정되지 않았으면 기본값 사용)
  const defaultStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    minHeight: '300px',
    ...style
  };

  // 필터링된 마커 목록 (선택된 일차만)
  const filteredMarkers = selectedDay === 'all' 
    ? mapData.markers 
    : mapData.markers.filter(m => (m.day || 1) === selectedDay);
  
  // 전체 순서 계산 (요일 관계없이 전체 순서)
  let globalOrder = 0;
  const markersWithGlobalOrder = filteredMarkers.map(marker => {
    globalOrder++;
    return { ...marker, globalOrder };
  });

  return (
    <div className={className || 'w-full h-full'} style={{ ...defaultStyle, position: 'relative' }}>
      {/* 일차 선택 버튼 */}
      {availableDays.length > 1 && (
        <div 
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            zIndex: 10,
            display: 'flex',
            gap: '6px',
            backgroundColor: 'white',
            padding: '6px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          }}
        >
          {availableDays.map(day => {
            const color = getDayColor(day);
            const isSelected = selectedDay === day;
            return (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: isSelected ? color.bg : '#f3f4f6',
                  color: isSelected ? (day === 5 ? '#333' : 'white') : '#666',
                  boxShadow: isSelected ? '0 2px 4px rgba(0,0,0,0.2)' : 'none',
                }}
              >
                Day {day}
              </button>
            );
          })}
        </div>
      )}
      
      <Map
        center={center}
        style={{ width: '100%', height: '100%', borderRadius: '0.5rem' }}
        level={mapData.zoom || 9}
      >
        {/* 요일별 경로선 표시 (hideRoutes가 false일 때만) */}
        {!hideRoutes && dayPaths.map(({ day, paths, color }) => (
          paths.map((path, pathIdx) => (
            path.length > 1 && (
              <Polyline
                key={`path-${day}-${pathIdx}`}
                path={path}
                strokeWeight={5}
                strokeColor={color.bg}
                strokeOpacity={0.9}
                strokeStyle="solid"
              />
            )
          ))
        ))}
        
        {/* 경로 중간 화살표 표시 (hideRoutes가 false일 때만) */}
        {!hideRoutes && arrowPoints.map((arrow, idx) => (
          <CustomOverlayMap
            key={`arrow-${idx}`}
            position={arrow.position}
            yAnchor={0.5}
            xAnchor={0.5}
          >
            <div
              style={{
                transform: `rotate(${arrow.angle}deg)`,
                color: getDayColor(arrow.day).bg,
                fontSize: '14px',
                fontWeight: 'bold',
                textShadow: '0 0 3px white, 0 0 3px white',
                pointerEvents: 'none',
              }}
            >
              ▼
            </div>
          </CustomOverlayMap>
        ))}
        
        {/* 커스텀 마커 표시 (요일별 색상 + 순서 번호) */}
        {markersWithGlobalOrder.map((marker, index) => {
          const coords = getMarkerCoords(marker);
          const day = marker.day || 1;
          const color = getDayColor(day);
          const displayLabel = marker.order || marker.label || marker.globalOrder;
          
          return (
            <CustomOverlayMap
              key={marker.id || index}
              position={coords}
              yAnchor={1.3}
            >
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  cursor: 'pointer',
                }}
                title={`${marker.name || marker.title || ''}${marker.category ? ` (${marker.category})` : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  const markerName = marker.name || marker.title;
                  if (selectedMarker?.name === markerName || selectedMarker?.title === markerName) {
                    setSelectedMarker(null);
                    setMarkerDetails(null);
                  } else {
                    setSelectedMarker(marker);
                    fetchMarkerDetails(marker);
                  }
                }}
              >
                {/* 마커 원형 */}
                <div
                  style={{
                    backgroundColor: showDayColors ? color.bg : '#FF6B35',
                    color: day === 5 ? '#333' : 'white', // 노란색 배경은 검은 글씨
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 'bold',
                    fontSize: '14px',
                    border: `3px solid ${showDayColors ? color.border : '#E85525'}`,
                    boxShadow: selectedMarker?.name === marker.name ? '0 0 0 4px rgba(99, 102, 241, 0.5)' : '0 3px 8px rgba(0,0,0,0.4)',
                    transition: 'all 0.2s',
                    transform: selectedMarker?.name === marker.name ? 'scale(1.2)' : 'scale(1)',
                  }}
                  onMouseEnter={(e) => {
                    if (selectedMarker?.name !== marker.name) {
                      e.currentTarget.style.transform = 'scale(1.2)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedMarker?.name !== marker.name) {
                      e.currentTarget.style.transform = 'scale(1)';
                    }
                  }}
                >
                  {displayLabel}
                </div>
                
                {/* 마커 꼬리 (삼각형) */}
                <div
                  style={{
                    width: 0,
                    height: 0,
                    borderLeft: '8px solid transparent',
                    borderRight: '8px solid transparent',
                    borderTop: `10px solid ${showDayColors ? color.border : '#E85525'}`,
                    marginTop: '-2px',
                  }}
                />
                
                {/* 장소 이름 라벨 */}
                {(marker.name || (marker as any).title) && (
                  <div
                    style={{
                      backgroundColor: 'white',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                      color: '#333',
                      marginTop: '4px',
                      boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
                      maxWidth: '120px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      border: `2px solid ${showDayColors ? color.bg : '#FF6B35'}`,
                    }}
                  >
                    {marker.name || (marker as any).title}
                  </div>
                )}
              </div>
            </CustomOverlayMap>
          );
        })}
      </Map>
      
      {/* 선택된 마커 정보 팝업 */}
      {selectedMarker && (
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            backgroundColor: 'white',
            padding: '0',
            borderRadius: '16px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
            zIndex: 20,
            width: '280px',
            overflow: 'hidden',
          }}
        >
          {/* 헤더 - Day 색상 배경 */}
          <div style={{
            background: `linear-gradient(135deg, ${getDayColor(selectedMarker.day || 1).bg}, ${getDayColor(selectedMarker.day || 1).border})`,
            padding: '12px 16px',
            color: 'white',
            position: 'relative',
          }}>
            {/* 닫기 버튼 */}
            <button
              onClick={() => setSelectedMarker(null)}
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                background: 'rgba(255,255,255,0.2)',
                border: 'none',
                fontSize: '14px',
                cursor: 'pointer',
                color: 'white',
                padding: '4px 8px',
                borderRadius: '6px',
                lineHeight: 1,
              }}
            >
              ✕
            </button>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{
                backgroundColor: 'rgba(255,255,255,0.3)',
                padding: '2px 10px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 'bold',
              }}>
                Day {selectedMarker.day || 1}
              </span>
              {selectedMarker.order && (
                <span style={{
                  backgroundColor: 'rgba(255,255,255,0.3)',
                  padding: '2px 10px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                }}>
                  #{selectedMarker.order} 코스
                </span>
              )}
            </div>
            
            <h3 style={{ 
              fontSize: '17px', 
              fontWeight: 'bold',
              margin: 0,
              paddingRight: '30px',
            }}>
              {selectedMarker.name || selectedMarker.title}
            </h3>
          </div>
          
          {/* 상세 정보 */}
          <div style={{ padding: '14px 16px' }}>
            {loadingDetails ? (
              <div style={{ textAlign: 'center', padding: '20px', color: '#9ca3af' }}>
                <div style={{ marginBottom: '8px' }}>🔄</div>
                정보 불러오는 중...
              </div>
            ) : (
              <>
                {/* 카테고리 & 평점 */}
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: '12px',
                  flexWrap: 'wrap',
                }}>
                  {(markerDetails?.category || selectedMarker.category) && (
                    <span style={{ 
                      fontSize: '12px', 
                      color: '#4b5563',
                      backgroundColor: '#f3f4f6',
                      padding: '4px 10px',
                      borderRadius: '8px',
                    }}>
                      🏷️ {markerDetails?.category || selectedMarker.category}
                    </span>
                  )}
                  {(markerDetails?.rating || selectedMarker.rating) && (
                    <span style={{ 
                      fontSize: '12px', 
                      color: '#d97706',
                      backgroundColor: '#fef3c7',
                      padding: '4px 10px',
                      borderRadius: '8px',
                      fontWeight: 600,
                    }}>
                      ⭐ {(markerDetails?.rating || selectedMarker.rating)?.toFixed?.(1) || markerDetails?.rating || selectedMarker.rating}
                    </span>
                  )}
                  {(markerDetails?.price || selectedMarker.price) && (
                    <span style={{ 
                      fontSize: '12px', 
                      color: '#059669',
                      backgroundColor: '#d1fae5',
                      padding: '4px 10px',
                      borderRadius: '8px',
                    }}>
                      💰 {markerDetails?.price || selectedMarker.price}
                    </span>
                  )}
                </div>
                
                {/* 주소 */}
                {(markerDetails?.address || selectedMarker.address) && (
                  <div style={{ 
                    fontSize: '12px', 
                    color: '#6b7280',
                    marginBottom: '10px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '6px',
                    lineHeight: 1.4,
                  }}>
                    <span>📍</span>
                    <span>{markerDetails?.address || selectedMarker.address}</span>
                  </div>
                )}
                
                {/* 설명 */}
                {(markerDetails?.description || selectedMarker.description) && (
                  <div style={{ 
                    fontSize: '12px', 
                    color: '#374151',
                    marginBottom: '10px',
                    lineHeight: 1.6,
                    backgroundColor: '#f9fafb',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    borderLeft: '3px solid #e5e7eb',
                  }}>
                    {markerDetails?.description || selectedMarker.description}
                  </div>
                )}
                
                {/* 전화번호 */}
                {(markerDetails?.phone || selectedMarker.phone) && (
                  <div style={{ 
                    fontSize: '12px', 
                    color: '#6b7280',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    marginBottom: '6px',
                  }}>
                    <span>📞</span>
                    <span>{markerDetails?.phone || selectedMarker.phone}</span>
                  </div>
                )}
                
                {/* 정보 없음 안내 */}
                {!markerDetails && !selectedMarker.address && !selectedMarker.description && (
                  <div style={{ 
                    fontSize: '12px', 
                    color: '#9ca3af',
                    textAlign: 'center',
                    padding: '10px',
                  }}>
                    상세 정보가 없습니다
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default KakaoMap;
