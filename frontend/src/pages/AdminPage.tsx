/**
 * Admin Dashboard Page - 제주도 테마 대시보드 🍊🌊
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Database, RefreshCw, TrendingUp, Clock, Bot, LogOut, Sun, Moon, Plane
} from 'lucide-react';
import { getDashboard, getSystemStatus, getCurrentModel, updateModel, getToolUsage } from '../api/admin';
import { logout as apiLogout } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import TokenUsageChart from '../components/TokenUsageChart';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface DashboardData {
  users: { total: number; today: number };
  schedules: { total: number; today: number };
  llm_usage: { today_tokens: number; today_cost: number };
  api_calls: { today: number };
}

interface SystemStatus {
  database: string;
  elasticsearch: string;
  timestamp: string;
}

// 도구별 색상 (제주 테마)
const TOOL_COLORS = ['#FF6B35', '#0EA5E9', '#10B981', '#F59E0B', '#EC4899'];

const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { isDarkMode, toggleDarkMode } = useTheme();
  
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const [chatData, setChatData] = useState<{date: string; chats: number}[]>([]);
  const [toolUsage, setToolUsage] = useState<{name: string; value: number; percentage: number}[]>([]);
  
  // 모델 설정
  const [currentModel, setCurrentModel] = useState<string>('gpt-5-mini');
  const [availableModels, setAvailableModels] = useState<{id: string; name: string; description: string}[]>([]);
  const [isModelChanging, setIsModelChanging] = useState(false);
  
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

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboardData, statusData, modelData, toolUsageData] = await Promise.all([
        getDashboard(),
        getSystemStatus(),
        getCurrentModel().catch(() => null),
        getToolUsage(30).catch(() => null),  // 최근 30일 도구 사용 통계
      ]);
      
      setDashboard(dashboardData);
      setSystemStatus(statusData);
      
      if (modelData) {
        setCurrentModel(modelData.current_model);
        setAvailableModels(modelData.available_models);
      }
      
      // 실제 도구 사용 통계 (API에서 가져옴)
      if (toolUsageData?.tool_usage) {
        setToolUsage(toolUsageData.tool_usage);
      } else {
        // API 실패 시 빈 배열
        setToolUsage([
          { name: 'SQL Agent', value: 0, percentage: 0 },
          { name: 'RAG Agent', value: 0, percentage: 0 },
          { name: 'Web Search', value: 0, percentage: 0 },
          { name: 'Itinerary', value: 0, percentage: 0 },
        ]);
      }
      
      // 임시 채팅 데이터 (나중에 실제 API로 교체)
      const now = new Date();
      const mockChatData = Array.from({length: 7}, (_, i) => {
        const date = new Date(now);
        date.setDate(date.getDate() - (6 - i));
        return {
          date: `${date.getMonth() + 1}/${date.getDate()}`,
          chats: Math.floor(Math.random() * 50) + 10
        };
      });
      setChatData(mockChatData);
      
    } catch (error) {
      console.error('데이터 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchDashboardData();
    setTimeout(() => setIsRefreshing(false), 500);
  };
  
  const handleModelChange = async (modelId: string) => {
    if (modelId === currentModel) return;
    
    setIsModelChanging(true);
    try {
      await updateModel(modelId);
      setCurrentModel(modelId);
    } catch (error) {
      console.error('모델 변경 실패:', error);
    } finally {
      setIsModelChanging(false);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-orange-50 via-white to-cyan-50">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">🍊</div>
          <span className="text-gray-600">로딩 중...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* 배경 장식 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-orange-200/30 dark:bg-orange-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-200/30 dark:bg-cyan-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 헤더 - 제주 테마 */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-14 h-14 bg-gradient-to-br from-orange-400 to-orange-500 rounded-2xl flex items-center justify-center text-3xl shadow-lg shadow-orange-200 dark:shadow-orange-900/30 transform hover:scale-110 transition-transform">
                🍊
              </div>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-cyan-400 rounded-full flex items-center justify-center text-xs">
                🌊
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-cyan-500 bg-clip-text text-transparent">
                제주 여행 플래너
              </h1>
              <p className="text-gray-500 dark:text-gray-400 text-sm flex items-center gap-1">
                <Plane size={14} className="text-orange-400" />
                관리자 대시보드
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2.5 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-orange-100 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md hover:border-orange-200 transition-all disabled:opacity-50"
            >
              <RefreshCw size={18} className={`text-orange-500 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="text-gray-700 dark:text-gray-300">{isRefreshing ? '새로고침...' : '새로고침'}</span>
            </button>
            <button
              onClick={toggleDarkMode}
              className="p-2.5 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-orange-100 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md transition-all"
              title={isDarkMode ? '라이트 모드' : '다크 모드'}
            >
              {isDarkMode ? <Sun size={20} className="text-yellow-500" /> : <Moon size={20} className="text-cyan-600" />}
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl shadow-lg shadow-orange-200 dark:shadow-orange-900/30 hover:shadow-xl hover:from-orange-600 hover:to-orange-700 transition-all"
            >
              <LogOut size={18} />
              로그아웃
            </button>
          </div>
        </div>

        {/* 상단 요약 카드 - 제주 테마 */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {/* 회원 수 */}
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-5 border border-orange-100 dark:border-gray-700 shadow-sm hover:shadow-lg hover:border-orange-200 transition-all group">
            <div className="flex items-center justify-between mb-3">
              <span className="text-2xl">👥</span>
              <span className="text-xs text-orange-500 bg-orange-50 dark:bg-orange-900/30 px-2 py-1 rounded-full">전체</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white group-hover:text-orange-500 transition-colors">
              {dashboard?.users.total || 0}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">회원 수</div>
          </div>

          {/* 생성된 일정 */}
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-5 border border-cyan-100 dark:border-gray-700 shadow-sm hover:shadow-lg hover:border-cyan-200 transition-all group">
            <div className="flex items-center justify-between mb-3">
              <span className="text-2xl">🗓️</span>
              <span className="text-xs text-cyan-500 bg-cyan-50 dark:bg-cyan-900/30 px-2 py-1 rounded-full">생성</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white group-hover:text-cyan-500 transition-colors">
              {dashboard?.schedules.total || 0}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">여행 일정</div>
          </div>

          {/* 오늘 사용 토큰 */}
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-5 border border-green-100 dark:border-gray-700 shadow-sm hover:shadow-lg hover:border-green-200 transition-all group">
            <div className="flex items-center justify-between mb-3">
              <span className="text-2xl">⚡</span>
              <span className="text-xs text-green-500 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded-full">오늘</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white group-hover:text-green-500 transition-colors">
              {formatNumber(dashboard?.llm_usage.today_tokens || 0)}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">사용 토큰</div>
          </div>

          {/* API 비용 */}
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-5 border border-amber-100 dark:border-gray-700 shadow-sm hover:shadow-lg hover:border-amber-200 transition-all group">
            <div className="flex items-center justify-between mb-3">
              <span className="text-2xl">💰</span>
              <span className="text-xs text-amber-500 bg-amber-50 dark:bg-amber-900/30 px-2 py-1 rounded-full">비용</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white group-hover:text-amber-500 transition-colors">
              ${(dashboard?.llm_usage.today_cost || 0).toFixed(2)}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">오늘 API</div>
          </div>
        </div>

        {/* 2행: 일별 채팅 + 도구 사용 분포 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* 일별 채팅 수 */}
          <div className="lg:col-span-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl border border-orange-100 dark:border-gray-700 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <span className="text-xl">💬</span>
                일별 채팅 수
              </h3>
              <span className="text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full">최근 7일</span>
            </div>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chatData}>
                  <defs>
                    <linearGradient id="colorChatsJeju" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FF6B35" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#FF6B35" stopOpacity={0.05}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                  <XAxis dataKey="date" stroke="#9ca3af" fontSize={11} axisLine={false} tickLine={false} />
                  <YAxis stroke="#9ca3af" fontSize={11} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'rgba(255,255,255,0.95)',
                      border: '1px solid #fed7aa',
                      borderRadius: '12px',
                      boxShadow: '0 4px 12px rgba(255,107,53,0.15)',
                    }}
                  />
                  <Area type="monotone" dataKey="chats" stroke="#FF6B35" strokeWidth={3} fill="url(#colorChatsJeju)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 도구 사용 분포 */}
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl border border-cyan-100 dark:border-gray-700 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <span className="text-xl">🤖</span>
                도구 사용
              </h3>
            </div>
            <div className="h-[140px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={toolUsage}
                    cx="50%"
                    cy="50%"
                    innerRadius="50%"
                    outerRadius="90%"
                    paddingAngle={3}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {toolUsage.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={TOOL_COLORS[index % TOOL_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* 범례 */}
            <div className="mt-4 space-y-2">
              {toolUsage.map((tool, index) => (
                <div key={tool.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: TOOL_COLORS[index] }} />
                    <span className="text-gray-600 dark:text-gray-400">{tool.name}</span>
                  </div>
                  <span className="text-gray-900 dark:text-white font-medium">{tool.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 3행: LLM 토큰 사용량 차트 */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span className="text-xl">📊</span>
            LLM 토큰 사용량
          </h2>
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl border border-orange-100 dark:border-gray-700 p-6 shadow-sm">
            <TokenUsageChart days={7} />
          </div>
        </div>

        {/* 4행: 시스템 상태 */}
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl border border-green-100 dark:border-gray-700 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span className="text-xl">🖥️</span>
            시스템 상태
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-700/50 dark:to-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-600">
              <span className="text-gray-600 dark:text-gray-300 flex items-center gap-2">
                <Database size={16} className="text-orange-500" />
                PostgreSQL
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                systemStatus?.database === 'connected' 
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              }`}>
                {systemStatus?.database === 'connected' ? '연결됨' : '연결 안됨'}
              </span>
            </div>
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-700/50 dark:to-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-600">
              <span className="text-gray-600 dark:text-gray-300 flex items-center gap-2">
                <TrendingUp size={16} className="text-cyan-500" />
                Elasticsearch
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                systemStatus?.elasticsearch === 'connected' 
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              }`}>
                {systemStatus?.elasticsearch === 'connected' ? '연결됨' : '연결 안됨'}
              </span>
            </div>
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-700/50 dark:to-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-600">
              <span className="text-gray-600 dark:text-gray-300 flex items-center gap-2">
                <Bot size={16} className="text-green-500" />
                LLM 모델
              </span>
              <select
                value={currentModel}
                onChange={(e) => handleModelChange(e.target.value)}
                disabled={isModelChanging}
                className="px-3 py-1.5 bg-gradient-to-r from-orange-100 to-cyan-100 dark:from-orange-900/30 dark:to-cyan-900/30 text-orange-700 dark:text-orange-400 rounded-lg text-sm font-medium border-0 cursor-pointer focus:ring-2 focus:ring-orange-300 disabled:opacity-50"
              >
                {availableModels.length > 0 ? (
                  availableModels.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))
                ) : (
                  <option value={currentModel}>{currentModel}</option>
                )}
              </select>
            </div>
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-700/50 dark:to-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-600">
              <span className="text-gray-600 dark:text-gray-300 flex items-center gap-1">
                <Clock size={16} className="text-amber-500" />
                업데이트
              </span>
              <span className="text-gray-900 dark:text-white text-sm font-medium">
                {systemStatus?.timestamp ? new Date(systemStatus.timestamp).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'}) : '-'}
              </span>
            </div>
          </div>
        </div>

        {/* 푸터 */}
        <div className="mt-8 text-center text-gray-400 dark:text-gray-500 text-sm">
          <p className="flex items-center justify-center gap-2">
            🍊 제주 여행 플래너 © 2025
            <span className="text-cyan-400">|</span>
            🌊 감귤처럼 상큼한 여행
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
