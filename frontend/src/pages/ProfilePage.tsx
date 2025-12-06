import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { updateProfile, updatePassword } from '../api/auth';
import { User, Lock, Shield, Mail, Calendar, Sparkles } from 'lucide-react';

const ProfilePage: React.FC = () => {
  const { user, updateUser } = useAuth();
  const [isEditingName, setIsEditingName] = useState(false);
  const [isEditingPassword, setIsEditingPassword] = useState(false);
  
  const [name, setName] = useState(user?.name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpdateName = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setMessage({ type: 'error', text: '이름을 입력해주세요' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const updatedUser = await updateProfile({ name });
      updateUser(updatedUser);
      setMessage({ type: 'success', text: '이름이 변경되었습니다 ✨' });
      setIsEditingName(false);
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || '이름 변경에 실패했습니다' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!currentPassword || !newPassword || !confirmPassword) {
      setMessage({ type: 'error', text: '모든 필드를 입력해주세요' });
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: '새 비밀번호가 일치하지 않습니다' });
      return;
    }

    if (newPassword.length < 6) {
      setMessage({ type: 'error', text: '비밀번호는 최소 6자 이상이어야 합니다' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      await updatePassword({ current_password: currentPassword, new_password: newPassword });
      setMessage({ type: 'success', text: '비밀번호가 변경되었습니다 🔒' });
      setIsEditingPassword(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || '비밀번호 변경에 실패했습니다' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Header */}
        <div className="text-center mb-12">
          <div className="inline-block mb-4">
            <div className="w-24 h-24 bg-gradient-to-br from-orange-400 to-orange-500 rounded-full flex items-center justify-center text-5xl shadow-2xl animate-bounce">
              🍊
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-gray-900 dark:text-white mb-3">
            프로필 설정
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            내 정보를 관리하고 업데이트하세요 ✨
          </p>
        </div>

        {/* 메시지 */}
        {message && (
          <div
            className={`mb-8 p-5 rounded-2xl shadow-lg animate-in slide-in-from-top ${
              message.type === 'success'
                ? 'bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/30 text-green-800 dark:text-green-400 border-2 border-green-200 dark:border-green-700'
                : 'bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/30 text-red-800 dark:text-red-400 border-2 border-red-200 dark:border-red-700'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">
                {message.type === 'success' ? '✅' : '⚠️'}
              </span>
              <span className="font-bold text-lg">{message.text}</span>
            </div>
          </div>
        )}

        <div className="grid gap-8">
          {/* 사용자 정보 카드 */}
          <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8 border-2 border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between mb-8 pb-6 border-b-2 border-gray-100 dark:border-gray-700">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-orange-500 rounded-full flex items-center justify-center text-white text-2xl shadow-lg">
                  <User size={32} />
                </div>
                <div>
                  <h2 className="text-2xl font-black text-gray-900 dark:text-white">내 정보</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">기본 프로필 정보</p>
                </div>
              </div>
              {user?.is_admin && (
                <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-100 to-purple-200 dark:from-purple-900/30 dark:to-purple-800/30 text-purple-700 dark:text-purple-400 rounded-full border-2 border-purple-200 dark:border-purple-700">
                  <Shield size={18} />
                  <span className="font-bold text-sm">관리자</span>
                </div>
              )}
            </div>

            <div className="space-y-6">
              {/* 이메일 */}
              <div className="flex items-center gap-4 p-5 bg-gray-50 dark:bg-gray-700/50 rounded-2xl">
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
                  <Mail size={24} className="text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500 dark:text-gray-400 font-medium mb-1">이메일</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{user?.email}</p>
                </div>
              </div>

              {/* 이름 */}
              <div className="flex items-center gap-4 p-5 bg-gray-50 dark:bg-gray-700/50 rounded-2xl">
                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-xl">
                  <User size={24} className="text-orange-600 dark:text-orange-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500 dark:text-gray-400 font-medium mb-1">이름</p>
                  {isEditingName ? (
                    <form onSubmit={handleUpdateName} className="flex items-center gap-3 mt-2">
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="flex-1 px-4 py-2 border-2 border-orange-300 dark:border-orange-600 rounded-xl focus:outline-none focus:ring-4 focus:ring-orange-200 dark:focus:ring-orange-800 bg-white dark:bg-gray-600 text-gray-900 dark:text-white font-bold"
                        placeholder="이름 입력"
                      />
                      <button
                        type="submit"
                        disabled={loading}
                        className="px-6 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50"
                      >
                        {loading ? '저장중...' : '저장'}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setIsEditingName(false);
                          setName(user?.name || '');
                        }}
                        className="px-6 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-xl font-bold hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
                      >
                        취소
                      </button>
                    </form>
                  ) : (
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-lg font-bold text-gray-900 dark:text-white">{user?.name}</p>
                      <button
                        onClick={() => setIsEditingName(true)}
                        className="px-4 py-2 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/30 rounded-xl font-bold transition-colors"
                      >
                        수정
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* 가입일 */}
              <div className="flex items-center gap-4 p-5 bg-gray-50 dark:bg-gray-700/50 rounded-2xl">
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-xl">
                  <Calendar size={24} className="text-green-600 dark:text-green-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500 dark:text-gray-400 font-medium mb-1">가입일</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {new Date(user?.created_at || '').toLocaleDateString('ko-KR')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 비밀번호 변경 카드 (로컬 계정만) */}
          {user?.provider === 'local' && (
            <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8 border-2 border-gray-100 dark:border-gray-700">
              <div className="flex items-center space-x-4 mb-8 pb-6 border-b-2 border-gray-100 dark:border-gray-700">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-500 rounded-full flex items-center justify-center text-white shadow-lg">
                  <Lock size={32} />
                </div>
                <div>
                  <h2 className="text-2xl font-black text-gray-900 dark:text-white">비밀번호 변경</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">보안을 위해 주기적으로 변경하세요</p>
                </div>
              </div>

              {!isEditingPassword ? (
                <button
                  onClick={() => setIsEditingPassword(true)}
                  className="w-full px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-2xl font-bold text-lg hover:shadow-2xl hover:scale-105 transition-all"
                >
                  비밀번호 변경하기
                </button>
              ) : (
                <form onSubmit={handleUpdatePassword} className="space-y-5">
                  <div>
                    <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                      현재 비밀번호
                    </label>
                    <input
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-200 dark:focus:ring-blue-800 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="현재 비밀번호 입력"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                      새 비밀번호
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-200 dark:focus:ring-blue-800 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="새 비밀번호 입력 (최소 6자)"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                      새 비밀번호 확인
                    </label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-200 dark:focus:ring-blue-800 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="새 비밀번호 다시 입력"
                    />
                  </div>

                  <div className="flex gap-3 pt-4">
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-2xl font-bold hover:shadow-xl transition-all disabled:opacity-50"
                    >
                      {loading ? '변경 중...' : '비밀번호 변경'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setIsEditingPassword(false);
                        setCurrentPassword('');
                        setNewPassword('');
                        setConfirmPassword('');
                      }}
                      className="px-8 py-4 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-2xl font-bold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                    >
                      취소
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>

        {/* 하단 CTA */}
        <div className="mt-12 text-center">
          <div className="inline-block p-8 bg-gradient-to-r from-orange-100 to-blue-100 dark:from-orange-900/30 dark:to-blue-900/30 rounded-3xl border-2 border-orange-200 dark:border-orange-700">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              더 많은 기능이 궁금하신가요?
            </p>
            <a
              href="/chat"
              className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-2xl font-bold hover:shadow-xl hover:scale-105 transition-all"
            >
              <Sparkles size={20} />
              AI 여행 계획하기
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
