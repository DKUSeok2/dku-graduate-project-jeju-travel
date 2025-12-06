/**
 * Forgot Password Page - 비밀번호 찾기
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Loader2, CheckCircle } from 'lucide-react';
import { forgotPassword } from '../api/passwordReset';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('이메일을 입력해주세요');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await forgotPassword({ email });
      setSuccess(true);
    } catch (err: any) {
      console.error('비밀번호 재설정 요청 실패:', err);
      setError(err.response?.data?.detail || '요청에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-2xl border-2 border-gray-100 dark:border-gray-700">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
                <CheckCircle className="text-green-600 dark:text-green-400" size={32} />
              </div>
              <h1 className="text-2xl font-black text-gray-900 dark:text-white mb-2">
                이메일이 발송되었습니다! 📧
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                <strong>{email}</strong>로<br />
                비밀번호 재설정 링크를 보냈습니다.
              </p>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 mb-6">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                💡 <strong>이메일이 오지 않았나요?</strong>
              </p>
              <ul className="text-sm text-blue-700 dark:text-blue-400 mt-2 space-y-1 list-disc list-inside">
                <li>스팸 메일함을 확인해보세요</li>
                <li>이메일 주소가 올바른지 확인하세요</li>
                <li>몇 분 정도 기다려보세요</li>
              </ul>
            </div>

            <Link
              to="/login"
              className="block w-full text-center px-6 py-3 bg-gradient-to-r from-orange-500 to-blue-500 hover:from-orange-600 hover:to-blue-600 text-white rounded-xl font-bold transition-all shadow-lg"
            >
              로그인으로 돌아가기
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-2xl border-2 border-gray-100 dark:border-gray-700">
          {/* 헤더 */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-orange-400 to-orange-500 rounded-full mb-4">
              <span className="text-3xl">🍊</span>
            </div>
            <h1 className="text-3xl font-black text-gray-900 dark:text-white mb-2">
              비밀번호 찾기
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              가입하신 이메일 주소를 입력해주세요
            </p>
          </div>

          {/* 폼 */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                이메일
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-orange-500 transition-colors"
                  placeholder="your@email.com"
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
                  발송 중...
                </>
              ) : (
                <>
                  <Mail size={20} />
                  재설정 링크 받기
                </>
              )}
            </button>
          </form>

          {/* 안내 */}
          <div className="mt-6 bg-orange-50 dark:bg-orange-900/20 rounded-xl p-4">
            <p className="text-sm text-orange-800 dark:text-orange-300">
              💡 이메일로 비밀번호 재설정 링크가 발송됩니다.<br />
              링크는 <strong>30분 동안</strong> 유효합니다.
            </p>
          </div>

          {/* 로그인으로 돌아가기 */}
          <div className="mt-6">
            <Link
              to="/login"
              className="flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors"
            >
              <ArrowLeft size={18} />
              로그인으로 돌아가기
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;


