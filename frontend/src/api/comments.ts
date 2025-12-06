/**
 * Schedule Comments API
 */
import apiClient from './client';

export interface ScheduleComment {
  id: number;
  schedule_id: number;
  user_id: number;
  user_name: string;
  content: string;
  parent_id: number | null;
  is_deleted: boolean;
  created_at: string;
}

export interface CommentCreate {
  content: string;
  parent_id?: number | null;
}

/**
 * 일정의 댓글 목록 조회
 */
export const getComments = async (scheduleId: number): Promise<ScheduleComment[]> => {
  const response = await apiClient.get<ScheduleComment[]>(`/api/schedules/${scheduleId}/comments`);
  return response.data;
};

/**
 * 댓글 작성
 */
export const createComment = async (scheduleId: number, data: CommentCreate): Promise<ScheduleComment> => {
  const response = await apiClient.post<ScheduleComment>(`/api/schedules/${scheduleId}/comments`, data);
  return response.data;
};

/**
 * 댓글 삭제 (soft delete)
 */
export const deleteComment = async (commentId: number): Promise<void> => {
  await apiClient.delete(`/api/schedules/comments/${commentId}`);
};

