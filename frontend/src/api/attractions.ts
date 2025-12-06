/**
 * Attractions API
 * 관광지 정보 조회 API
 */
import apiClient from './client';

export interface Attraction {
  id: number;
  name: string;
  category: string;
  lat: number | null;
  lng: number | null;
  rating: number | null;
  price?: string;
  price_range?: string | null;
  address?: string;
  phone?: string;
  description?: string;
  review_count?: number | null;
  min_price?: number | null;
  max_price?: number | null;
  parking?: boolean | null;
  kid_friendly?: boolean | null;
  wheelchair?: boolean | null;
  pet_friendly?: boolean | null;
  reservation?: boolean | null;
  wifi?: boolean | null;
  business_hours?: string | null;
  source?: 'attraction' | 'place';
}

/**
 * 관광지/맛집/카페 통합 목록 조회
 */
export const getAttractionsList = async (
  category?: string,
  search?: string,
  limit: number = 50
): Promise<Attraction[]> => {
  const params: Record<string, string | number> = { limit };
  if (category && category !== '전체') {
    params.category = category;
  }
  if (search) {
    params.search = search;
  }
  
  const response = await apiClient.get<Attraction[]>('/api/attractions', { params });
  return response.data;
};

/**
 * 관광지 이름으로 위치 정보 조회
 */
export const getAttractionsByNames = async (names: string[]): Promise<Attraction[]> => {
  const namesParam = names.join(',');
  const response = await apiClient.get<Attraction[]>(
    `/api/attractions/by-names?names=${encodeURIComponent(namesParam)}`
  );
  return response.data;
};

/**
 * 관광지 ID로 상세 정보 조회
 */
export const getAttractionById = async (id: number): Promise<Attraction> => {
  const response = await apiClient.get<Attraction>(`/api/attractions/${id}`);
  return response.data;
};

/**
 * Places 테이블 상세 정보 조회
 */
export const getPlaceDetail = async (id: number): Promise<any> => {
  const response = await apiClient.get(`/api/attractions/places/${id}`);
  return response.data;
};

/**
 * AI 응답 텍스트에서 관광지 이름 추출
 */
export const extractAttractionNames = (content: string): string[] => {
  const names = new Set<string>();
  
  // 패턴 1: "1. **한라산**" 형식
  const pattern1 = /\d+\.\s*\*\*([^*]+)\*\*/g;
  let match;
  while ((match = pattern1.exec(content)) !== null) {
    names.add(match[1].trim());
  }
  
  // 패턴 2: "• **한라산**" 형식
  const pattern2 = /[•●]\s*\*\*([^*]+)\*\*/g;
  while ((match = pattern2.exec(content)) !== null) {
    names.add(match[1].trim());
  }
  
  // 패턴 3: "- **한라산**" 형식
  const pattern3 = /-\s*\*\*([^*]+)\*\*/g;
  while ((match = pattern3.exec(content)) !== null) {
    names.add(match[1].trim());
  }
  
  return Array.from(names);
};

