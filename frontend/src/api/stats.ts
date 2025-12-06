import axios from 'axios';

const API_BASE_URL = import.meta.env.PROD 
  ? 'https://jeju-travel-chatbot-production.up.railway.app'
  : 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 통계 조회
export const getStats = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};


