import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { SidebarProvider, useSidebar } from './contexts/SidebarContext';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import BotPlaygroundPage from './pages/BotPlaygroundPage';
import SchedulePage from './pages/SchedulePage';
import ScheduleDetailPage from './pages/ScheduleDetailPage';
import CourseDetailPage from './pages/CourseDetailPage';
import DataPage from './pages/DataPage';
import AdminPage from './pages/AdminPage';
import CoursesPage from './pages/CoursesPage';
import ExplorePage from './pages/ExplorePage';
import AboutPage from './pages/AboutPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import OAuthCallbackPage from './pages/OAuthCallbackPage';
import DmPage from './pages/DmPage';
import DmListPage from './pages/DmListPage';
import { useAuth } from './contexts/AuthContext';
import { Toaster } from 'sonner';

function AppContent() {
  const location = useLocation();
  const { isAuthenticated, user } = useAuth();
  const { isCollapsed } = useSidebar();
  
  // 로그인/회원가입/비밀번호 찾기 페이지에서는 Sidebar와 Footer 숨김
  const hideLayout = ['/login', '/register', '/forgot-password', '/reset-password', '/auth/callback'].includes(location.pathname);
  
  // 관리자 페이지(/admin)에서만 사이드바 숨김
  const isAdminPage = location.pathname === '/admin';
  const showSidebar = !hideLayout && isAuthenticated && !isAdminPage;
  
  // 사이드바 너비에 따른 margin (접힘: 64px, 펼침: 256px)
  const sidebarMargin = showSidebar ? (isCollapsed ? 'ml-16' : 'ml-64') : '';

  return (
    <div className="flex min-h-screen bg-white dark:bg-gray-900 transition-colors">
      {showSidebar && <Sidebar />}
      <div className={`flex flex-col flex-1 transition-all duration-300 ${sidebarMargin}`}>
        <main className="flex-1">
          <Routes>
            {/* 루트 경로는 로그인 상태와 권한에 따라 분기 */}
            <Route 
              path="/" 
              element={
                isAuthenticated 
                  ? <Navigate to={user?.is_admin ? "/admin" : "/chat"} replace /> 
                  : <Navigate to="/login" replace />
              } 
            />
            
            {/* 공개 페이지 */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/auth/callback" element={<OAuthCallbackPage />} />
            <Route path="/about" element={<AboutPage />} />
            
            {/* 보호된 페이지 (로그인 필요) */}
            <Route path="/home" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
            <Route path="/bots" element={<ProtectedRoute><BotPlaygroundPage /></ProtectedRoute>} />
            <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
            <Route path="/courses" element={<ProtectedRoute><CoursesPage /></ProtectedRoute>} />
            <Route path="/courses/:scheduleId" element={<ProtectedRoute><CourseDetailPage /></ProtectedRoute>} />
            <Route path="/explore" element={<ProtectedRoute><ExplorePage /></ProtectedRoute>} />
            <Route path="/schedule" element={<ProtectedRoute><SchedulePage /></ProtectedRoute>} />
            <Route path="/schedule/:scheduleId" element={<ProtectedRoute><ScheduleDetailPage /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
            <Route path="/dm" element={<ProtectedRoute><DmListPage /></ProtectedRoute>} />
            <Route path="/dm/:conversationId" element={<ProtectedRoute><DmPage /></ProtectedRoute>} />
            
            {/* 관리자 전용 페이지 */}
            <Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />
            <Route path="/data" element={<AdminRoute><DataPage /></AdminRoute>} />
          </Routes>
        </main>
        {showSidebar && <Footer />}
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <SidebarProvider>
            <AppContent />
            <Toaster position="top-right" richColors />
          </SidebarProvider>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
