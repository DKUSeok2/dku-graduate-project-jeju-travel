/**
 * OAuth Callback Page - Google 로그인 콜백 처리
 */
import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { safeLocalStorage } from '../utils/storage';

const OAuthCallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { updateUser } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token');
      const error = searchParams.get('error');

      if (error) {
        alert(`로그인 실패: ${error}`);
        navigate('/login');
        return;
      }

      if (token) {
        try {
          // 토큰을 localStorage에 저장
          safeLocalStorage.setItem('access_token', token);
          
          // 사용자 정보 가져오기
          const response = await api.get('/api/auth/me');
          updateUser(response.data);
          
          console.log('✅ Google 로그인 성공:', response.data);
          navigate('/home');
        } catch (err) {
          console.error('❌ 로그인 처리 실패:', err);
          safeLocalStorage.removeItem('access_token');
          alert('로그인에 실패했습니다. 다시 시도해주세요.');
          navigate('/login');
        }
      } else {
        navigate('/login');
      }
    };

    handleCallback();
  }, [searchParams, navigate, updateUser]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
      <div className="text-center">
        <Loader2 className="animate-spin mx-auto text-orange-500 mb-4" size={48} />
        <p className="text-gray-600 dark:text-gray-400">로그인 처리 중...</p>
      </div>
    </div>
  );
};

export default OAuthCallbackPage;

