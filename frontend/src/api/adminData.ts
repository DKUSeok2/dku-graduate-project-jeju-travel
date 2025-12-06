/**
 * Admin Data API - 관리자용 데이터 통계 + Places CRUD
 */
import api from './client';

export interface DataStats {
  total_users: number;
  total_schedules: number;
  total_chat_sessions: number;
  total_likes: number;
  total_bookmarks: number;
  total_views: number;
}

export interface PopularAttraction {
  rank: number;
  name: string;
  category: string;
  count: number;
  emoji: string;
}

export interface CategoryDistribution {
  name: string;
  count: number;
  percentage: number;
}

// ==================== Places CRUD ====================

export interface Place {
  id: number;
  naver_id?: string;
  name: string;
  category: string;
  address?: string;
  phone?: string;
  rating?: number;
  review_count?: number;
  min_price?: number;
  max_price?: number;
  price_range?: string;
  parking?: boolean;
  kid_friendly?: boolean;
  wheelchair?: boolean;
  pet_friendly?: boolean;
  reservation?: boolean;
  wifi?: boolean;
  business_hours?: string;
  url?: string;
  region?: string;
  lat?: number;
  lng?: number;
}

export interface PlaceCreate {
  name: string;
  category: string;
  address?: string;
  phone?: string;
  rating?: number;
  review_count?: number;
  min_price?: number;
  max_price?: number;
  price_range?: string;
  parking?: boolean;
  kid_friendly?: boolean;
  wheelchair?: boolean;
  pet_friendly?: boolean;
  reservation?: boolean;
  wifi?: boolean;
  business_hours?: string;
  region?: string;
  lat?: number;
  lng?: number;
  naver_id?: string;
  url?: string;
}

export interface PlacesResponse {
  places: Place[];
  total: number;
  skip: number;
  limit: number;
}

// 전체 데이터 통계
export const getDataStats = async (): Promise<DataStats> => {
  const response = await api.get('/api/admin/data/stats');
  return response.data;
};

// 인기 관광지 TOP N
export const getPopularAttractions = async (limit: number = 10): Promise<PopularAttraction[]> => {
  const response = await api.get(`/api/admin/data/popular-attractions?limit=${limit}`);
  return response.data;
};

// 카테고리별 분포
export const getCategoryDistribution = async (): Promise<CategoryDistribution[]> => {
  const response = await api.get('/api/admin/data/category-distribution');
  return response.data;
};

// ==================== Places CRUD ====================

// Places 목록 조회
export const getPlaces = async (
  skip: number = 0,
  limit: number = 20,
  search?: string,
  category?: string,
  region?: string
): Promise<PlacesResponse> => {
  const params = new URLSearchParams();
  params.append('skip', skip.toString());
  params.append('limit', limit.toString());
  if (search) params.append('search', search);
  if (category) params.append('category', category);
  if (region) params.append('region', region);
  
  const response = await api.get(`/api/admin/data/places?${params.toString()}`);
  return response.data;
};

// Place 상세 조회
export const getPlace = async (id: number): Promise<Place> => {
  const response = await api.get(`/api/admin/data/places/${id}`);
  return response.data;
};

// Place 추가
export const createPlace = async (place: PlaceCreate): Promise<{ id: number; message: string }> => {
  const response = await api.post('/api/admin/data/places', place);
  return response.data;
};

// Place 수정
export const updatePlace = async (id: number, place: PlaceCreate): Promise<{ message: string }> => {
  const response = await api.put(`/api/admin/data/places/${id}`, place);
  return response.data;
};

// Place 삭제
export const deletePlace = async (id: number): Promise<{ message: string }> => {
  const response = await api.delete(`/api/admin/data/places/${id}`);
  return response.data;
};

// ==================== 필터 옵션 ====================

export interface FilterOption {
  name: string;
  count: number;
}

export interface FilterOptions {
  categories: FilterOption[];
  regions: FilterOption[];
}

// 카테고리/지역 필터 옵션 조회
export const getFilterOptions = async (): Promise<FilterOptions> => {
  const response = await api.get('/api/attractions/filters/options');
  return response.data;
};

