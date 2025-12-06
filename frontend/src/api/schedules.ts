/**
 * Schedules API
 */
import apiClient from './client';

export interface Schedule {
  id: number;
  user_id: number;
  user_name: string;
  title: string;
  start_date: string;
  end_date: string;
  attractions: any;
  route_data: any;
  memo: string | null;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  likes_count?: number;  // 좋아요 수 추가
  bookmarks_count?: number;  // 북마크 수 추가
  chat_history?: ChatMessage[];  // AI 대화 내역
  ai_reasoning?: string;  // AI 추천 이유
  map_data?: any;  // 지도 데이터
  chat_session_id?: string;  // 채팅 세션 ID
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ScheduleCreate {
  title: string;
  start_date: string;
  end_date: string;
  attractions?: any;
  route_data?: any;
  memo?: string;
  chat_history?: ChatMessage[];  // AI 대화 내역
  ai_reasoning?: string;  // AI 추천 이유
  map_data?: any;  // 지도 데이터
  chat_session_id?: string;  // 채팅 세션 ID
}

export interface ScheduleUpdate {
  title?: string;
  start_date?: string;
  end_date?: string;
  attractions?: any;
  route_data?: any;
  memo?: string;
  is_public?: boolean;
  chat_history?: ChatMessage[];  // AI 대화 내역
  ai_reasoning?: string;  // AI 추천 이유
  map_data?: any;  // 지도 데이터
}

// ===== 인터랙션 관련 인터페이스 =====

export interface InteractionResponse {
  success: boolean;
  is_active: boolean;
  total_count: number;
}

export interface ScheduleStats {
  schedule_id: number;
  likes_count: number;
  bookmarks_count: number;
  views_count: number;
  is_liked: boolean;
  is_bookmarked: boolean;
}

/**
 * 내 일정 목록 조회
 */
export const getUserSchedules = async (): Promise<Schedule[]> => {
  const response = await apiClient.get<Schedule[]>('/api/schedules/my');
  return response.data;
};

/**
 * 공개된 일정 목록 조회 (추천 코스)
 */
export const getPublicSchedules = async (skip = 0, limit = 20): Promise<Schedule[]> => {
  const response = await apiClient.get<Schedule[]>(`/api/schedules/public?skip=${skip}&limit=${limit}`);
  return response.data;
};

/**
 * 특정 일정 조회
 */
export const getSchedule = async (scheduleId: number): Promise<Schedule> => {
  const response = await apiClient.get<Schedule>(`/api/schedules/${scheduleId}`);
  return response.data;
};

/**
 * 일정 생성
 */
export const createSchedule = async (data: ScheduleCreate): Promise<Schedule> => {
  const response = await apiClient.post<Schedule>('/api/schedules', data);
  return response.data;
};

/**
 * 일정 수정 (공유하기 포함)
 */
export const updateSchedule = async (scheduleId: number, data: ScheduleUpdate): Promise<Schedule> => {
  const response = await apiClient.put<Schedule>(`/api/schedules/${scheduleId}`, data);
  return response.data;
};

/**
 * 일정 삭제
 */
export const deleteSchedule = async (scheduleId: number): Promise<void> => {
  await apiClient.delete(`/api/schedules/${scheduleId}`);
};

/**
 * 일정 공유하기 토글
 */
export const toggleSchedulePublic = async (scheduleId: number, isPublic: boolean): Promise<Schedule> => {
  return updateSchedule(scheduleId, { is_public: isPublic });
};

// ===== 인터랙션 API =====

/**
 * 일정 좋아요 토글
 */
export const likeSchedule = async (scheduleId: number): Promise<InteractionResponse> => {
  const response = await apiClient.post<InteractionResponse>(`/api/schedules/${scheduleId}/like`);
  return response.data;
};

/**
 * 일정 북마크 토글
 */
export const bookmarkSchedule = async (scheduleId: number): Promise<InteractionResponse> => {
  const response = await apiClient.post<InteractionResponse>(`/api/schedules/${scheduleId}/bookmark`);
  return response.data;
};

/**
 * 일정 조회수 기록
 */
export const recordView = async (scheduleId: number): Promise<void> => {
  await apiClient.post(`/api/schedules/${scheduleId}/view`);
};

/**
 * 일정 통계 조회 (좋아요, 북마크, 조회수)
 */
export const getScheduleStats = async (scheduleId: number): Promise<ScheduleStats> => {
  const response = await apiClient.get<ScheduleStats>(`/api/schedules/${scheduleId}/stats`);
  return response.data;
};

/**
 * 내 북마크 목록 조회
 */
export const getMyBookmarks = async (): Promise<Schedule[]> => {
  const response = await apiClient.get<Schedule[]>('/api/schedules/bookmarks/my');
  return response.data;
};

