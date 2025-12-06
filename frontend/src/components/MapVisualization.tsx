import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Leaflet 마커 아이콘 설정 (기본 아이콘 경로 수정)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapMarker {
  id: number;
  position: {
    lat: number;
    lng: number;
  };
  label: string;
  name: string;
  category?: string;
  rating?: number;
  price?: string;
}

interface RoutePath {
  from: { lat: number; lng: number; name: string };
  to: { lat: number; lng: number; name: string };
  path: [number, number][]; // [[lat, lng], ...]
  distance?: number;
  duration?: number;
}

interface DayRoute {
  day: number;
  routes: RoutePath[];
}

interface MapData {
  type: string;
  markers: MapMarker[];
  routes?: DayRoute[]; // 경로 정보
  center: {
    lat: number;
    lng: number;
  };
  zoom: number;
}

interface MapVisualizationProps {
  mapData: MapData;
}

const MapVisualization: React.FC<MapVisualizationProps> = ({ mapData }) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // 지도 초기화
    const map = L.map(mapRef.current).setView(
      [mapData.center.lat, mapData.center.lng],
      mapData.zoom
    );

    // OpenStreetMap 타일 추가
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map);

    mapInstanceRef.current = map;

    // 경로 선 그리기 (마커보다 먼저 그려야 마커가 위에 표시됨)
    if (mapData.routes && mapData.routes.length > 0) {
      const colors = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899']; // 일별 색상
      
      mapData.routes.forEach((dayRoute) => {
        const color = colors[(dayRoute.day - 1) % colors.length];
        
        dayRoute.routes.forEach((route) => {
          if (route.path && route.path.length >= 2) {
            // 경로 좌표를 Leaflet 형식으로 변환 [lat, lng] → [lat, lng]
            const latlngs = route.path.map(([lat, lng]) => [lat, lng] as [number, number]);
            
            // Polyline으로 경로 그리기
            const polyline = L.polyline(latlngs, {
              color: color,
              weight: 4,
              opacity: 0.7,
              smoothFactor: 1
            }).addTo(map);
            
            // 경로 정보를 툴팁으로 표시
            const tooltipText = route.distance 
              ? `${route.from.name} → ${route.to.name}\n${route.distance.toFixed(1)}km`
              : `${route.from.name} → ${route.to.name}`;
            polyline.bindTooltip(tooltipText, { permanent: false });
          }
        });
      });
    }

    // 마커 추가
    mapData.markers.forEach((marker) => {
      const leafletMarker = L.marker([marker.position.lat, marker.position.lng]).addTo(map);
      
      // 팝업 내용 생성
      const popupContent = `
        <div style="font-family: sans-serif;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="background: #f97316; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">
              ${marker.label}
            </span>
            <strong style="font-size: 14px;">${marker.name}</strong>
          </div>
          ${marker.category ? `<div style="color: #666; font-size: 12px; margin-bottom: 2px;">📍 ${marker.category}</div>` : ''}
          ${marker.rating ? `<div style="color: #666; font-size: 12px; margin-bottom: 2px;">⭐ ${marker.rating}</div>` : ''}
          ${marker.price ? `<div style="color: #666; font-size: 12px;">💰 ${marker.price}</div>` : ''}
        </div>
      `;
      
      leafletMarker.bindPopup(popupContent);
    });

    // Cleanup
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [mapData]);

  return (
    <div className="my-4 rounded-lg overflow-hidden border border-orange-200 shadow-md">
      <div className="bg-gradient-to-r from-orange-50 to-yellow-50 px-4 py-2 border-b border-orange-200">
        <div className="flex items-center gap-2">
          <span className="text-lg">🗺️</span>
          <span className="font-semibold text-gray-700">지도</span>
          <span className="text-sm text-gray-500">({mapData.markers.length}개 관광지)</span>
        </div>
      </div>
      <div 
        ref={mapRef} 
        style={{ width: '100%', height: '400px' }}
        className="bg-gray-100"
      />
    </div>
  );
};

export default MapVisualization;

