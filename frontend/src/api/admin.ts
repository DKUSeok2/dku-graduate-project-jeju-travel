import axios from 'axios';
import { safeLocalStorage } from '../utils/storage';

const API_BASE_URL = import.meta.env.PROD 
  ? 'https://jeju-travel-chatbot-production.up.railway.app'
  : 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 토큰 추가 인터셉터
api.interceptors.request.use((config) => {
  const token = safeLocalStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 대시보드 통계
export const getDashboard = async () => {
  const response = await api.get('/api/admin/dashboard');
  return response.data;
};

// 사용자 목록
export const getUsers = async (skip = 0, limit = 20) => {
  const response = await api.get(`/api/admin/users?skip=${skip}&limit=${limit}`);
  return response.data;
};

// LLM 사용량
export const getLLMUsage = async (days = 7, userId?: number) => {
  let url = `/api/admin/llm-usage?days=${days}`;
  if (userId) {
    url += `&user_id=${userId}`;
  }
  const response = await api.get(url);
  return response.data;
};

// API 로그
export const getAPILogs = async (skip = 0, limit = 50) => {
  const response = await api.get(`/api/admin/api-logs?skip=${skip}&limit=${limit}`);
  return response.data;
};

// 시스템 상태
export const getSystemStatus = async () => {
  const response = await api.get('/api/admin/system-status');
  return response.data;
};

// 사용자 권한 변경
export const updateUserRole = async (userId: number, isAdmin: boolean) => {
  const response = await api.put(`/api/admin/users/${userId}/role?is_admin=${isAdmin}`);
  return response.data;
};

// 사용자 활성화/비활성화
export const updateUserStatus = async (userId: number, isActive: boolean) => {
  const response = await api.put(`/api/admin/users/${userId}/status?is_active=${isActive}`);
  return response.data;
};

// 현재 LLM 모델 조회
export const getCurrentModel = async () => {
  const response = await api.get('/api/admin/settings/model');
  return response.data;
};

// LLM 모델 변경
export const updateModel = async (modelId: string) => {
  const response = await api.put(`/api/admin/settings/model?model_id=${modelId}`);
  return response.data;
};

// 도구 사용 통계
export const getToolUsage = async (days = 30) => {
  const response = await api.get(`/api/admin/tool-usage?days=${days}`);
  return response.data;
};
