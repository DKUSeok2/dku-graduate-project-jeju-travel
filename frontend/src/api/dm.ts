/**
 * DM (Direct Message) API
 */
import apiClient from './client';

export interface ConversationSummary {
  id: number;
  partner_id: number;
  partner_name: string;
  last_message: string | null;
  last_message_at: string | null;
}

export interface DmMessage {
  id: number;
  sender_id: number;
  sender_name: string;
  content: string;
  created_at: string;
}

export interface MessageCreate {
  content: string;
  context?: {
    schedule_id?: number;
    comment_id?: number;
    [key: string]: any;
  };
}

/**
 * 내 DM 목록 조회
 */
export const getConversations = async (): Promise<ConversationSummary[]> => {
  const response = await apiClient.get<ConversationSummary[]>('/api/dm/conversations');
  return response.data;
};

/**
 * 특정 사용자와의 DM 방 조회 또는 생성
 */
export const getOrCreateConversation = async (targetUserId: number): Promise<ConversationSummary> => {
  const response = await apiClient.post<ConversationSummary>(`/api/dm/conversations/${targetUserId}`);
  return response.data;
};

/**
 * 특정 DM 방 정보 조회
 */
export const getConversation = async (conversationId: number): Promise<ConversationSummary> => {
  const response = await apiClient.get<ConversationSummary>(`/api/dm/conversations/${conversationId}`);
  return response.data;
};

/**
 * DM 방의 메시지 목록 조회
 */
export const getMessages = async (
  conversationId: number,
  before?: number,
  limit: number = 50
): Promise<DmMessage[]> => {
  const params = new URLSearchParams();
  if (before) params.append('before', before.toString());
  params.append('limit', limit.toString());
  
  const response = await apiClient.get<DmMessage[]>(
    `/api/dm/conversations/${conversationId}/messages?${params.toString()}`
  );
  return response.data;
};

/**
 * DM 방에 메시지 전송
 */
export const sendMessage = async (
  conversationId: number,
  data: MessageCreate
): Promise<DmMessage> => {
  const response = await apiClient.post<DmMessage>(
    `/api/dm/conversations/${conversationId}/messages`,
    data
  );
  return response.data;
};

