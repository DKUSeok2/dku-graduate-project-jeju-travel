/**
 * Photo Gallery - 일정 사진 갤러리 컴포넌트
 */
import React, { useState, useEffect, useRef } from 'react';
import { Camera, Plus, X, Loader2, Image as ImageIcon, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { getSchedulePhotos, uploadSchedulePhoto, deleteSchedulePhoto } from '../api/photos';
import type { SchedulePhoto } from '../api/photos';
import { useAuth } from '../contexts/AuthContext';

interface PhotoGalleryProps {
  scheduleId: number;
  scheduleOwnerId: number;
  days?: number; // 일정 일수 (Day별 분류용)
  canEdit?: boolean; // 편집 가능 여부 (기본값: true, 공유 코스에서는 false)
}

const PhotoGallery: React.FC<PhotoGalleryProps> = ({ scheduleId, scheduleOwnerId, canEdit = true }) => {
  const { user } = useAuth();
  const [photos, setPhotos] = useState<SchedulePhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedPhoto, setSelectedPhoto] = useState<SchedulePhoto | null>(null);
  const [uploadDay, setUploadDay] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // canEdit이 false면 owner여도 편집 불가
  const isOwner = canEdit && user?.id === scheduleOwnerId;

  useEffect(() => {
    fetchPhotos();
  }, [scheduleId]);

  const fetchPhotos = async () => {
    try {
      setLoading(true);
      const data = await getSchedulePhotos(scheduleId);
      setPhotos(data);
    } catch (error) {
      console.error('사진 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 파일 크기 체크 (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('파일 크기는 5MB 이하여야 합니다.');
      return;
    }

    // 파일 타입 체크
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      alert('JPG, PNG, WebP, GIF 파일만 업로드 가능합니다.');
      return;
    }

    setUploading(true);
    try {
      const photo = await uploadSchedulePhoto(
        scheduleId,
        file,
        undefined,
        uploadDay ?? undefined
      );
      setPhotos([...photos, photo]);
      setUploadDay(null);
    } catch (error: any) {
      console.error('사진 업로드 실패:', error);
      alert(error.response?.data?.detail || '사진 업로드에 실패했습니다.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (photo: SchedulePhoto) => {
    if (!confirm('사진을 삭제하시겠습니까?')) return;

    try {
      await deleteSchedulePhoto(scheduleId, photo.id);
      setPhotos(photos.filter(p => p.id !== photo.id));
      if (selectedPhoto?.id === photo.id) {
        setSelectedPhoto(null);
      }
    } catch (error) {
      console.error('사진 삭제 실패:', error);
      alert('사진 삭제에 실패했습니다.');
    }
  };

  const openUploadDialog = (day?: number) => {
    setUploadDay(day ?? null);
    fileInputRef.current?.click();
  };

  const navigatePhoto = (direction: 'prev' | 'next') => {
    if (!selectedPhoto) return;
    const currentIndex = photos.findIndex(p => p.id === selectedPhoto.id);
    const newIndex = direction === 'prev' 
      ? (currentIndex - 1 + photos.length) % photos.length
      : (currentIndex + 1) % photos.length;
    setSelectedPhoto(photos[newIndex]);
  };

  // API URL 처리
  const getPhotoUrl = (url: string) => {
    if (url.startsWith('http')) return url;
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return `${baseUrl}${url}`;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border-2 border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-black text-gray-900 dark:text-white flex items-center gap-3">
          <Camera className="text-pink-500" size={28} />
          여행 사진 ({photos.length})
        </h2>
        
        {isOwner && (
          <button
            onClick={() => openUploadDialog()}
            disabled={uploading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-pink-500 to-pink-600 text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50"
          >
            {uploading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Plus size={18} />
            )}
            사진 추가
          </button>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        onChange={handleFileSelect}
        className="hidden"
      />

      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="animate-spin mx-auto text-pink-500 mb-2" size={32} />
          <p className="text-gray-500">사진 로딩 중...</p>
        </div>
      ) : photos.length === 0 ? (
        <div className="text-center py-12">
          <ImageIcon className="mx-auto text-gray-300 dark:text-gray-600 mb-4" size={48} />
          <p className="text-gray-500 dark:text-gray-400 mb-4">아직 사진이 없습니다.</p>
          {isOwner && (
            <button
              onClick={() => openUploadDialog()}
              className="inline-flex items-center gap-2 px-6 py-3 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 rounded-xl font-semibold hover:bg-pink-200 dark:hover:bg-pink-900/50 transition-colors"
            >
              <Plus size={20} />
              첫 여행 사진 추가하기
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {photos.map(photo => (
            <div
              key={photo.id}
              className="relative group aspect-square rounded-xl overflow-hidden cursor-pointer"
              onClick={() => setSelectedPhoto(photo)}
            >
              <img
                src={getPhotoUrl(photo.url)}
                alt={photo.caption || '여행 사진'}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform"
              />
              {isOwner && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(photo);
                  }}
                  className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 사진 라이트박스 */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedPhoto(null)}
        >
          <button
            onClick={() => setSelectedPhoto(null)}
            className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
          >
            <X size={24} />
          </button>

          {photos.length > 1 && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigatePhoto('prev');
                }}
                className="absolute left-4 p-2 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
              >
                <ChevronLeft size={32} />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigatePhoto('next');
                }}
                className="absolute right-4 p-2 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
              >
                <ChevronRight size={32} />
              </button>
            </>
          )}

          <img
            src={getPhotoUrl(selectedPhoto.url)}
            alt={selectedPhoto.caption || '여행 사진'}
            className="max-w-full max-h-[90vh] object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />

          {selectedPhoto.caption && (
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 px-6 py-3 bg-black/60 text-white rounded-xl max-w-lg text-center">
              {selectedPhoto.caption}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PhotoGallery;

