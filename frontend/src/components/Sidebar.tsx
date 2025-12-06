import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, MessageCircle, Calendar, BarChart3, LogOut, User, Settings, ChevronRight, ChevronLeft, Sun, Moon, Map, Sparkles, Mail } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useSidebar } from '../contexts/SidebarContext';
import { logout as apiLogout } from '../api/auth';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const { isDarkMode, toggleDarkMode } = useTheme();
  const { isCollapsed, toggleSidebar } = useSidebar();
  
  const allNavItems = [
    { path: '/home', label: '홈', icon: Home },
    // AI 채팅은 여러 챗봇을 고를 수 있는 플레이그라운드(/bots)로 이동
    { path: '/bots', label: 'AI 채팅', icon: MessageCircle },
    { path: '/courses', label: '추천 코스', icon: Sparkles },
    { path: '/explore', label: '관광지 탐색', icon: Map },
    { path: '/schedule', label: '내 일정', icon: Calendar },
  ];

  const adminNavItems = [
    { path: '/admin', label: '대시보드', icon: BarChart3 },
  ];

  const navItems = user?.is_admin ? adminNavItems : allNavItems;

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      logout();
      navigate('/login');
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <aside 
      className={`fixed left-0 top-0 h-screen bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col z-50 shadow-sm transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* 접기 버튼 */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-7 w-6 h-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-full flex items-center justify-center text-gray-500 hover:text-orange-500 hover:border-orange-300 transition-colors shadow-sm z-10"
      >
        {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {/* 로고 */}
      <div className={`border-b border-gray-200 dark:border-gray-700 ${isCollapsed ? 'p-3' : 'p-6'}`}>
        <Link to="/home" className="flex items-center space-x-3">
          <div className={`bg-gradient-to-br from-orange-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform ${
            isCollapsed ? 'w-10 h-10 text-2xl' : 'w-12 h-12 text-3xl'
          }`}>
            🍊
          </div>
          {!isCollapsed && (
            <div>
              <div className="text-lg font-bold text-gray-900 dark:text-white">제주 여행</div>
              <div className="text-xs text-orange-500 dark:text-orange-400 font-medium">플래너 ✨</div>
            </div>
          )}
        </Link>
      </div>

      {/* 메인 메뉴 */}
      <div className="flex-1 overflow-y-auto py-4">
        <nav className={`space-y-1 ${isCollapsed ? 'px-2' : 'px-3'}`}>
          {!isCollapsed && (
            <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-3 mb-3">
              메뉴
            </div>
          )}
          
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                title={isCollapsed ? item.label : undefined}
                className={`flex items-center rounded-lg transition-all ${
                  isCollapsed 
                    ? 'justify-center p-3' 
                    : 'space-x-3 px-3 py-2.5'
                } ${
                  isActive
                    ? 'bg-orange-500 text-white shadow-md'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Icon size={20} />
                {!isCollapsed && (
                  <>
                    <span className="font-medium">{item.label}</span>
                    {isActive && <ChevronRight size={16} className="ml-auto" />}
                  </>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* 하단 영역 */}
      <div className="border-t border-gray-200 dark:border-gray-700">
        {/* 로그아웃 & 다크모드 */}
        <div className={`border-b border-gray-200 dark:border-gray-700 ${isCollapsed ? 'p-2' : 'p-4'}`}>
          <div className={`flex items-center ${isCollapsed ? 'flex-col gap-2' : 'gap-2'}`}>
            <button
              onClick={handleLogout}
              title="로그아웃"
              className={`flex items-center justify-center rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-red-600 dark:hover:text-red-400 transition-colors ${
                isCollapsed ? 'p-2.5' : 'flex-1 gap-2 px-4 py-2.5'
              }`}
            >
              <LogOut size={18} />
              {!isCollapsed && <span className="font-medium">로그아웃</span>}
            </button>

            <button
              onClick={toggleDarkMode}
              className="p-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title={isDarkMode ? '라이트 모드' : '다크 모드'}
            >
              {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </div>
        </div>

        {/* 사용자 프로필 */}
        <div className={`flex items-center ${isCollapsed ? 'justify-center p-3' : 'gap-3 p-4'}`}>
          <Link
            to="/profile"
            title={isCollapsed ? user?.name : undefined}
            className="group flex items-center gap-3 flex-1 min-w-0"
          >
            <div className={`bg-gradient-to-br from-blue-400 to-orange-400 rounded-full flex items-center justify-center text-white flex-shrink-0 ${
              isCollapsed ? 'w-8 h-8' : 'w-9 h-9'
            }`}>
              <User size={isCollapsed ? 16 : 18} />
            </div>
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-gray-900 dark:text-white truncate">{user?.name}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 truncate">{user?.email}</div>
              </div>
            )}
          </Link>
          {!isCollapsed && (
            <div className="flex items-center gap-1 flex-shrink-0">
              <Link
                to="/dm"
                title="메시지"
                className="p-2 rounded-lg text-gray-400 hover:text-orange-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-all"
              >
                <Mail size={18} />
              </Link>
              <Link
                to="/profile"
                title="설정"
                className="p-2 rounded-lg text-gray-400 hover:text-orange-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-all group"
              >
                <Settings size={18} className="group-hover:rotate-90 transition-transform" />
              </Link>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
