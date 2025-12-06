/**
 * Chat Session API Client
 * 채팅 세션 관리 API
 */
import apiClient from './client';

// ===== 인터페이스 =====

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  attractions?: any[];
}

export interface ChatSession {
  id: number;
  session_id: string;
  user_id: number;
  title: string | null;
  messages: ChatMessage[];
  context: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionListItem {
  id: number;
  session_id: string;
  title: string | null;
  message_count: number;
  last_message_preview: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateSessionRequest {
  title?: string;
  context?: any;
}

export interface AddMessageRequest {
  message: ChatMessage;
}

export interface UpdateSessionRequest {
  title?: string;
  is_active?: boolean;
}

// ===== API 함수 =====

/**
 * 새 채팅 세션 생성
 */
export const createChatSession = async (data?: CreateSessionRequest): Promise<ChatSession> => {
  const response = await apiClient.post<ChatSession>('/api/chat/sessions', data || {});
  return response.data;
};

/**
 * 내 채팅 세션 목록 조회 (최근순)
 */
export const getChatSessions = async (skip = 0, limit = 100): Promise<ChatSessionListItem[]> => {
  const response = await apiClient.get<ChatSessionListItem[]>(
    `/api/chat/sessions?skip=${skip}&limit=${limit}`
  );
  return response.data;
};

/**
 * 특정 채팅 세션 조회
 */
export const getChatSession = async (sessionId: string): Promise<ChatSession> => {
  const response = await apiClient.get<ChatSession>(`/api/chat/sessions/${sessionId}`);
  return response.data;
};

/**
 * 세션에 메시지 추가
 */
export const addMessageToSession = async (
  sessionId: string,
  message: ChatMessage
): Promise<{ success: boolean; message_count: number }> => {
  const response = await apiClient.post<{ success: boolean; message_count: number }>(
    `/api/chat/sessions/${sessionId}/messages`,
    { message }
  );
  return response.data;
};

/**
 * 세션 정보 업데이트 (제목, 활성 상태)
 */
export const updateChatSession = async (
  sessionId: string,
  data: UpdateSessionRequest
): Promise<ChatSession> => {
  const response = await apiClient.put<ChatSession>(`/api/chat/sessions/${sessionId}`, data);
  return response.data;
};

/**
 * 세션 삭제 (Soft delete)
 */
export const deleteChatSession = async (sessionId: string): Promise<void> => {
  await apiClient.delete(`/api/chat/sessions/${sessionId}`);
};

/**
 * 세션의 컨텍스트 조회
 */
export const getSessionContext = async (sessionId: string): Promise<any> => {
  const response = await apiClient.get(`/api/chat/sessions/${sessionId}/context`);
  return response.data;
};

/**
 * 세션의 컨텍스트 업데이트
 */
export const updateSessionContext = async (
  sessionId: string,
  context: any
): Promise<{ success: boolean; context: any }> => {
  const response = await apiClient.put<{ success: boolean; context: any }>(
    `/api/chat/sessions/${sessionId}/context`,
    context
  );
  return response.data;
};

/**
 * 피드백 저장 (좋아요/싫어요)
 */
export const saveFeedback = async (
  sessionId: string,
  messageId: string,
  isLike: boolean
): Promise<{ success: boolean; message: string; is_like: boolean }> => {
  const response = await apiClient.post<{ success: boolean; message: string; is_like: boolean }>(
    `/api/chat/sessions/${sessionId}/feedback`,
    {
      message_id: messageId,
      is_like: isLike,
    }
  );
  return response.data;
};


