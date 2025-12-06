/**
 * Token Usage API - 토큰 사용량 조회
 */
import apiClient from './client';

export interface DailyUsage {
  date: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost: number;
  request_count: number;
}

export interface HourlyUsage {
  hour: string;
  total_tokens: number;
  cost: number;
  request_count: number;
}

export interface ModelUsage {
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost: number;
  request_count: number;
}

export interface UsageSummary {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost: number;
  total_requests: number;
  avg_tokens_per_request: number;
}

/**
 * 일별 토큰 사용량 조회 (모델별 필터링 가능)
 */
export async function getDailyUsage(days: number = 7, model?: string | null): Promise<DailyUsage[]> {
  const params: { days: number; model?: string } = { days };
  if (model) {
    params.model = model;
  }
  const response = await apiClient.get('/api/admin/token-usage/daily', { params });
  return response.data;
}

/**
 * 시간별 토큰 사용량 조회
 */
export async function getHourlyUsage(hours: number = 24): Promise<HourlyUsage[]> {
  const response = await apiClient.get('/api/admin/token-usage/hourly', {
    params: { hours }
  });
  return response.data;
}

/**
 * 모델별 토큰 사용량 조회
 */
export async function getModelUsage(days: number = 7): Promise<ModelUsage[]> {
  const response = await apiClient.get('/api/admin/token-usage/by-model', {
    params: { days }
  });
  return response.data;
}

/**
 * 토큰 사용량 요약 조회
 */
export async function getUsageSummary(days: number = 30): Promise<UsageSummary> {
  const response = await apiClient.get('/api/admin/token-usage/summary', {
    params: { days }
  });
  return response.data;
}

