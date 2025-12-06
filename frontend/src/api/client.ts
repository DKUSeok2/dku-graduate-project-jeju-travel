/**
 * Axios HTTP Client Configuration
 */
import axios from 'axios';
import { safeLocalStorage } from '../utils/storage';

// 배포 환경에서는 Railway URL 사용
const API_BASE_URL = import.meta.env.PROD 
  ? 'https://jeju-travel-chatbot-production.up.railway.app'
  : 'http://localhost:8000';

// Axios 인스턴스 생성
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor - 토큰 자동 포함
apiClient.interceptors.request.use(
  (config) => {
    const token = safeLocalStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor - 401 에러 처리
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 토큰 만료 시 로컬스토리지 클리어
      safeLocalStorage.removeItem('access_token');
      safeLocalStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;




