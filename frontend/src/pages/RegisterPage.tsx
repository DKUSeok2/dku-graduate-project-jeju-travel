/**
 * Register Page - KLID Style
 */
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { register as apiRegister } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';

const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // 비밀번호 확인
    if (password !== passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다');
      return;
    }

    if (password.length < 6) {
      setError('비밀번호는 최소 6자 이상이어야 합니다');
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiRegister({ email, password, name });
      login(response.access_token, response.user);
      navigate('/home');
    } catch (err: any) {
      setError(err.response?.data?.detail || '회원가입에 실패했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-jeju-orange-50 via-white to-jeju-blue-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* 회원가입 카드 */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl p-10">
          {/* 로고 & 타이틀 */}
          <div className="text-center mb-8">
            <div className="text-5xl mb-4">🏝️</div>
            <h1 className="text-3xl font-bold text-jeju-orange-500 dark:text-jeju-orange-400 mb-2">
              회원가입
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              제주 여행의 시작, 지금 바로!
            </p>
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          {/* 회원가입 폼 */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 이름 */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                이름
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="이름을 입력해주세요."
                required
                className="w-full px-4 py-3.5 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-jeju-orange-500 focus:border-transparent transition-all"
              />
            </div>

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
                  placeholder="비밀번호 (최소 6자)"
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

            {/* 비밀번호 확인 */}
            <div>
              <label htmlFor="passwordConfirm" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                비밀번호 확인
              </label>
              <div className="relative">
                <input
                  id="passwordConfirm"
                  type={showPasswordConfirm ? 'text' : 'password'}
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  placeholder="비밀번호를 다시 입력해주세요."
                  required
                  className="w-full px-4 py-3.5 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-jeju-orange-500 focus:border-transparent transition-all pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  {showPasswordConfirm ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            {/* 회원가입 버튼 */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-jeju-orange-500 to-jeju-orange-600 hover:from-jeju-orange-600 hover:to-jeju-orange-700 text-white font-semibold py-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed mt-6"
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>회원가입 중...</span>
                </div>
              ) : (
                '회원가입'
              )}
            </button>
          </form>

          {/* 구분선 */}
          <div className="my-8 flex items-center">
            <div className="flex-1 border-t border-gray-200 dark:border-gray-700"></div>
            <span className="px-4 text-sm text-gray-500 dark:text-gray-400">또는</span>
            <div className="flex-1 border-t border-gray-200 dark:border-gray-700"></div>
          </div>

          {/* 로그인 링크 */}
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              이미 계정이 있으신가요?
            </p>
            <Link
              to="/login"
              className="inline-block text-jeju-orange-600 dark:text-jeju-orange-400 font-semibold hover:underline text-lg"
            >
              로그인하기
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

export default RegisterPage;

