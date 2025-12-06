import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, MessageCircle, Calendar, BarChart3, LogIn, LogOut, User, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { logout as apiLogout } from '../api/auth';

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 드롭다운 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  // 관리자는 홈만, 일반 사용자는 모든 메뉴
  const allNavItems = [
    { path: '/home', label: '홈', icon: Home },
    // AI 채팅은 이제 여러 챗봇을 고를 수 있는 플레이그라운드로 이동
    { path: '/bots', label: 'AI 채팅', icon: MessageCircle },
    { path: '/schedule', label: '내 일정', icon: Calendar },
    { path: '/data', label: '데이터', icon: BarChart3 },
  ];

  const navItems = user?.is_admin 
    ? [{ path: '/home', label: '홈', icon: Home }]
    : allNavItems;

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

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* 로고 */}
          <Link to={isAuthenticated ? "/home" : "/login"} className="flex items-center space-x-2">
            <div className="text-2xl">🏝️</div>
            <div>
              <span className="text-xl font-bold text-gradient-jeju">
                제주 여행 플래너
              </span>
            </div>
          </Link>

          {/* 네비게이션 메뉴 */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={isActive ? 'nav-link-active' : 'nav-link'}
                >
                  <div className="flex items-center space-x-2">
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </div>
                </Link>
              );
            })}
            
            {/* 로그인/로그아웃 */}
            <div className="ml-4 border-l border-gray-200 pl-4">
              {isAuthenticated ? (
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                  >
                    <User size={18} />
                    <span className="font-medium">{user?.name}</span>
                    <ChevronDown size={16} className={`transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {/* 드롭다운 메뉴 */}
                  {dropdownOpen && (
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-gray-200 py-2 z-50">
                      <div className="px-4 py-3 border-b border-gray-100">
                        <div className="text-sm font-semibold text-gray-900">{user?.name}</div>
                        <div className="text-xs text-gray-500">{user?.email}</div>
                        {user?.is_admin && (
                          <div className="mt-1 inline-block px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-semibold rounded">
                            관리자
                          </div>
                        )}
                      </div>
                      
                      <Link
                        to="/profile"
                        onClick={() => setDropdownOpen(false)}
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        <Settings size={16} />
                        <span>프로필 설정</span>
                      </Link>
                      
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          handleLogout();
                        }}
                        className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <LogOut size={16} />
                        <span>로그아웃</span>
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  to="/login"
                  className="flex items-center space-x-2 px-4 py-2 bg-jeju-orange-400 text-white rounded-lg font-medium hover:bg-jeju-orange-500 transition-colors"
                >
                  <LogIn size={18} />
                  <span>로그인</span>
                </Link>
              )}
            </div>
          </div>

          {/* 모바일 메뉴 버튼 */}
          <div className="md:hidden">
            <button className="text-gray-700 p-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

