/**
 * Authentication API
 */
import apiClient from './client';

export interface RegisterData {
  email: string;
  password: string;
  name: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface User {
  id: number;
  email: string;
  name: string;
  is_admin: boolean;
  provider: string;
  profile_image: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/**
 * 회원가입
 */
export const register = async (data: RegisterData): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/api/auth/register', data);
  return response.data;
};

/**
 * 로그인
 */
export const login = async (data: LoginData): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/api/auth/login', data);
  return response.data;
};

/**
 * 내 정보 조회
 */
export const getMe = async (): Promise<User> => {
  const response = await apiClient.get<User>('/api/auth/me');
  return response.data;
};

/**
 * 로그아웃
 */
export const logout = async (): Promise<void> => {
  await apiClient.post('/api/auth/logout');
};

/**
 * 프로필 업데이트 (이름 변경)
 */
export const updateProfile = async (data: { name: string }): Promise<User> => {
  const response = await apiClient.put<User>('/api/auth/profile', data);
  return response.data;
};

/**
 * 비밀번호 변경
 */
export const updatePassword = async (data: { current_password: string; new_password: string }): Promise<void> => {
  await apiClient.put('/api/auth/password', data);
};


