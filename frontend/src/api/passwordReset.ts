/**
 * Password Reset API
 */
import apiClient from './client';

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface MessageResponse {
  message: string;
}

export interface TokenValidationResponse {
  valid: boolean;
  message: string;
}

// 비밀번호 재설정 요청 (이메일 발송)
export const forgotPassword = async (data: ForgotPasswordRequest): Promise<MessageResponse> => {
  const response = await apiClient.post<MessageResponse>('/api/auth/forgot-password', data);
  return response.data;
};

// 비밀번호 재설정 (새 비밀번호 설정)
export const resetPassword = async (data: ResetPasswordRequest): Promise<MessageResponse> => {
  const response = await apiClient.post<MessageResponse>('/api/auth/reset-password', data);
  return response.data;
};

// 토큰 유효성 검증
export const validateResetToken = async (token: string): Promise<TokenValidationResponse> => {
  const response = await apiClient.get<TokenValidationResponse>(`/api/auth/validate-reset-token/${token}`);
  return response.data;
};


