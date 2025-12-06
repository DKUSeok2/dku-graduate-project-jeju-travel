/**
 * Login Page - KLID Style
 */
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { login as apiLogin } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await apiLogin({ email, password });
      login(response.access_token, response.user);
      // 관리자는 /admin, 일반 사용자는 /home
      navigate(response.user.is_admin ? '/admin' : '/home');
    } catch (err: any) {
      setError(err.response?.data?.detail || '로그인에 실패했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-jeju-orange-50 via-white to-jeju-blue-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* 로그인 카드 */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl p-10">
          {/* 로고 & 타이틀 */}
          <div className="text-center mb-8">
            <div className="text-5xl mb-4">🏝️</div>
            <h1 className="text-3xl font-bold text-jeju-orange-500 dark:text-jeju-orange-400 mb-2">
              제주 여행 플래너
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              AI와 함께하는 완벽한 제주 여행
            </p>
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          {/* 로그인 폼 */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 이메일 */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                이메일
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="이메일을 입력해주세요."
                required
                className="w-full px-4 py-3.5 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-jeju-orange-500 focus:border-transparent transition-all"
              />
            </div>

            {/* 비밀번호 */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                비밀번호
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="비밀번호를 입력해주세요."
                  required
                  className="w-full px-4 py-3.5 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-jeju-orange-500 focus:border-transparent transition-all pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            {/* 비밀번호 찾기 링크 */}
            <div className="text-right">
              <Link
                to="/forgot-password"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-jeju-orange-600 dark:hover:text-jeju-orange-400 hover:underline"
              >
                비밀번호를 잊으셨나요?
              </Link>
            </div>

            {/* 로그인 버튼 */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-jeju-orange-500 to-jeju-orange-600 hover:from-jeju-orange-600 hover:to-jeju-orange-700 text-white font-semibold py-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed mt-6"
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>로그인 중...</span>
                </div>
              ) : (
                '로그인'
              )}
            </button>
          </form>

          {/* 구분선 */}
          <div className="my-8 flex items-center">
            <div className="flex-1 border-t border-gray-200 dark:border-gray-700"></div>
            <span className="px-4 text-sm text-gray-500 dark:text-gray-400">또는</span>
            <div className="flex-1 border-t border-gray-200 dark:border-gray-700"></div>
          </div>

          {/* Google 로그인 */}
          <a
            href={`${import.meta.env.PROD ? 'https://jeju-travel-chatbot-production.up.railway.app' : 'http://localhost:8000'}/api/auth/google/login`}
            className="w-full flex items-center justify-center gap-3 px-6 py-3.5 bg-white dark:bg-gray-700 border-2 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 rounded-xl font-semibold text-gray-700 dark:text-gray-200 transition-all shadow-sm hover:shadow-md"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Google로 계속하기
          </a>

          {/* 구분선 */}
          <div className="my-8 flex items-center">
            <div className="flex-1 border-t border-gray-200 dark:border-gray-700"></div>
          </div>

          {/* 회원가입 링크 */}
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              아직 계정이 없으신가요?
            </p>
            <Link
              to="/register"
              className="inline-block text-jeju-orange-600 dark:text-jeju-orange-400 font-semibold hover:underline text-lg"
            >
              회원가입하기
            </Link>
          </div>
        </div>

        {/* 하단 텍스트 */}
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-8">
          © 2024 제주 여행 플래너. All rights reserved.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;

