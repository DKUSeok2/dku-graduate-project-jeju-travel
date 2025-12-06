/**
 * Schedule Photos API
 */
import apiClient from './client';

export interface SchedulePhoto {
  id: number;
  schedule_id: number;
  user_id: number;
  url: string;
  caption: string | null;
  day: number | null;
  order_in_day: number | null;
  created_at: string;
}

/**
 * 일정의 사진 목록 조회
 */
export const getSchedulePhotos = async (scheduleId: number): Promise<SchedulePhoto[]> => {
  const response = await apiClient.get<SchedulePhoto[]>(`/api/schedules/${scheduleId}/photos`);
  return response.data;
};

/**
 * 사진 업로드
 */
export const uploadSchedulePhoto = async (
  scheduleId: number,
  file: File,
  caption?: string,
  day?: number,
  orderInDay?: number
): Promise<SchedulePhoto> => {
  const formData = new FormData();
  formData.append('file', file);
  if (caption) formData.append('caption', caption);
  if (day !== undefined) formData.append('day', day.toString());
  if (orderInDay !== undefined) formData.append('order_in_day', orderInDay.toString());

  const response = await apiClient.post<SchedulePhoto>(
    `/api/schedules/${scheduleId}/photos`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

/**
 * 사진 삭제
 */
export const deleteSchedulePhoto = async (scheduleId: number, photoId: number): Promise<void> => {
  await apiClient.delete(`/api/schedules/${scheduleId}/photos/${photoId}`);
};

