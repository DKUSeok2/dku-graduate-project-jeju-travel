/**
 * Reset Password Page - 비밀번호 재설정
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Lock, Eye, EyeOff, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { resetPassword, validateResetToken } from '../api/passwordReset';

const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [tokenMessage, setTokenMessage] = useState('');
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 토큰 유효성 검증
  useEffect(() => {
    const checkToken = async () => {
      if (!token) {
        setTokenValid(false);
        setTokenMessage('유효하지 않은 링크입니다');
        setValidating(false);
        return;
      }

      try {
        const result = await validateResetToken(token);
        setTokenValid(result.valid);
        setTokenMessage(result.message);
      } catch (err) {
        setTokenValid(false);
        setTokenMessage('토큰 검증에 실패했습니다');
      } finally {
        setValidating(false);
      }
    };

    checkToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // 유효성 검사
    if (!newPassword) {
      setError('새 비밀번호를 입력해주세요');
      return;
    }

    if (newPassword.length < 6) {
      setError('비밀번호는 최소 6자 이상이어야 합니다');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다');
      return;
    }

    setLoading(true);

    try {
      await resetPassword({ token, new_password: newPassword });
      setSuccess(true);
      
      // 3초 후 로그인 페이지로 이동
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      console.error('비밀번호 재설정 실패:', err);
      setError(err.response?.data?.detail || '비밀번호 재설정에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 토큰 검증 중
  if (validating) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto text-orange-500 mb-4" size={48} />
          <p className="text-gray-600 dark:text-gray-400">토큰 확인 중...</p>
        </div>
      </div>
    );
  }

  // 토큰 무효
  if (!tokenValid) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-2xl border-2 border-gray-100 dark:border-gray-700">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
                <AlertCircle className="text-red-600 dark:text-red-400" size={32} />
              </div>
              <h1 className="text-2xl font-black text-gray-900 dark:text-white mb-2">
                링크가 유효하지 않습니다
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {tokenMessage}
              </p>
              <button
                onClick={() => navigate('/forgot-password')}
                className="w-full px-6 py-3 bg-gradient-to-r from-orange-500 to-blue-500 hover:from-orange-600 hover:to-blue-600 text-white rounded-xl font-bold transition-all shadow-lg"
              >
                다시 시도하기
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 재설정 성공
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-2xl border-2 border-gray-100 dark:border-gray-700">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
                <CheckCircle className="text-green-600 dark:text-green-400" size={32} />
              </div>
              <h1 className="text-2xl font-black text-gray-900 dark:text-white mb-2">
                비밀번호가 변경되었습니다! 🎉
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                새로운 비밀번호로 로그인할 수 있습니다.<br />
                잠시 후 로그인 페이지로 이동합니다...
              </p>
              <Loader2 className="animate-spin mx-auto text-orange-500" size={24} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 비밀번호 입력 폼
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-2xl border-2 border-gray-100 dark:border-gray-700">
          {/* 헤더 */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-orange-400 to-orange-500 rounded-full mb-4">
              <span className="text-3xl">🔐</span>
            </div>
            <h1 className="text-3xl font-black text-gray-900 dark:text-white mb-2">
              새 비밀번호 설정
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              새로운 비밀번호를 입력해주세요
            </p>
          </div>

          {/* 폼 */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                새 비밀번호
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full pl-12 pr-12 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-orange-500 transition-colors"
                  placeholder="최소 6자 이상"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                비밀번호 확인
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-orange-500 transition-colors"
                  placeholder="비밀번호 재입력"
                  disabled={loading}
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl p-4">
                <p className="text-sm text-red-600 dark:text-red-400">⚠️ {error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-orange-500 to-blue-500 hover:from-orange-600 hover:to-blue-600 text-white rounded-xl font-bold transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  변경 중...
                </>
              ) : (
                <>
                  <CheckCircle size={20} />
                  비밀번호 변경하기
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;


