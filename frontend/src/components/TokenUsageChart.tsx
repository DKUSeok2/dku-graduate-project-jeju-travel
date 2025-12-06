/**
 * Token Usage Chart Component - klid-aicb 스타일 토큰 사용량 그래프
 */
import React, { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, Loader2 } from 'lucide-react';
import { getDailyUsage, getModelUsage, getUsageSummary } from '../api/tokenUsage';
import type { DailyUsage, ModelUsage, UsageSummary } from '../api/tokenUsage';

interface TokenUsageChartProps {
  days?: number;
}

const TokenUsageChart: React.FC<TokenUsageChartProps> = ({ days = 7 }) => {
  const [dailyData, setDailyData] = useState<DailyUsage[]>([]);
  const [modelData, setModelData] = useState<ModelUsage[]>([]);
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  // 초기 데이터 로드 (모델 목록 + 요약)
  useEffect(() => {
    fetchInitialData();
  }, [days]);

  // selectedModel 변경 시 일별 데이터만 다시 조회
  useEffect(() => {
    fetchDailyData();
  }, [days, selectedModel]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [model, sum] = await Promise.all([
        getModelUsage(days),
        getUsageSummary(days)
      ]);
      
      setModelData(model);
      setSummary(sum);
    } catch (err: unknown) {
      console.error('토큰 사용량 조회 실패:', err);
      setError(err instanceof Error ? err.message : '데이터 조회 실패');
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyData = async () => {
    try {
      // 모델별 일별 데이터 조회 (selectedModel이 null이면 전체)
      const daily = await getDailyUsage(days, selectedModel);
      // 날짜순 정렬 (오래된 순)
      setDailyData(daily.reverse());
    } catch (err: unknown) {
      console.error('일별 사용량 조회 실패:', err);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-blue-500" size={32} />
        <span className="ml-2 text-gray-500">토큰 사용량 로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p className="text-red-500">{error}</p>
        <button 
          onClick={fetchInitialData}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          다시 시도
        </button>
      </div>
    );
  }

  // 데이터가 없을 경우
  if (!dailyData.length && !modelData.length) {
    return (
      <div className="text-center py-12 text-gray-500">
        <TrendingUp size={48} className="mx-auto mb-4 opacity-50" />
        <p>아직 토큰 사용 기록이 없습니다.</p>
        <p className="text-sm mt-1">채팅을 시작하면 사용량이 기록됩니다.</p>
      </div>
    );
  }

  // LLM 모델 (gpt-4o-mini 등)과 임베딩 모델 분리
  const llmModels = modelData.filter(m => !m.model.includes('embedding'));
  const embeddingModels = modelData.filter(m => m.model.includes('embedding'));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* LLM 토큰 사용량 카드 - 모델 선택 탭 */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden">
        {/* 헤더 + 모델 선택 탭 */}
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              LLM 토큰 사용량
            </h3>
            <div className="flex items-center gap-2 bg-blue-50 dark:bg-blue-900/30 px-4 py-2 rounded-full">
              <TrendingUp className="text-blue-500" size={16} />
              <span className="text-blue-600 dark:text-blue-400 font-bold">
                총 {formatNumber(
                  selectedModel 
                    ? llmModels.find(m => m.model === selectedModel)?.total_tokens || 0
                    : llmModels.reduce((sum, m) => sum + m.total_tokens, 0)
                )}
              </span>
            </div>
          </div>
          {/* 모델 선택 탭 */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedModel(null)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                selectedModel === null
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              전체
            </button>
            {llmModels.map((model) => (
              <button
                key={model.model}
                onClick={() => setSelectedModel(model.model)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  selectedModel === model.model
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {model.model} ({formatNumber(model.total_tokens)})
              </button>
            ))}
          </div>
        </div>
        
        {/* Area Chart - Input/Output */}
        <div className="p-6">
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyData}>
                <defs>
                  <linearGradient id="colorInput" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05}/>
                  </linearGradient>
                  <linearGradient id="colorOutput" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.05}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatDate}
                  stroke="#9ca3af"
                  fontSize={11}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis 
                  tickFormatter={formatNumber}
                  stroke="#9ca3af"
                  fontSize={11}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    formatNumber(value),
                    name === 'prompt_tokens' ? 'Input' : 'Output'
                  ]}
                  labelFormatter={(label) => label}
                  contentStyle={{
                    backgroundColor: 'rgba(255,255,255,0.95)',
                    border: '1px solid #e5e7eb',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="prompt_tokens" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  fill="url(#colorInput)"
                  name="prompt_tokens"
                />
                <Area 
                  type="monotone" 
                  dataKey="completion_tokens" 
                  stroke="#06b6d4" 
                  strokeWidth={2}
                  fill="url(#colorOutput)"
                  name="completion_tokens"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          {/* 범례 */}
          <div className="flex justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-sm text-gray-600 dark:text-gray-400">Input</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-cyan-500"></div>
              <span className="text-sm text-gray-600 dark:text-gray-400">Output</span>
            </div>
          </div>
        </div>
      </div>

      {/* Embedding 토큰 사용량 카드 */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden">
        {/* 헤더 */}
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {embeddingModels[0]?.model || 'text-embedding-3-small'}
            </h3>
          </div>
          <div className="flex items-center gap-2 bg-cyan-50 dark:bg-cyan-900/30 px-4 py-2 rounded-full">
            <TrendingUp className="text-cyan-500" size={16} />
            <span className="text-cyan-600 dark:text-cyan-400 font-bold">
              총 {formatNumber(embeddingModels.reduce((sum, m) => sum + m.total_tokens, 0))}
            </span>
          </div>
        </div>
        
        {/* Area Chart - Embedding */}
        <div className="p-6">
          <div className="h-[200px]">
            {embeddingModels.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dailyData}>
                  <defs>
                    <linearGradient id="colorEmbedding" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.05}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatDate}
                    stroke="#9ca3af"
                    fontSize={11}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis 
                    tickFormatter={formatNumber}
                    stroke="#9ca3af"
                    fontSize={11}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip 
                    formatter={(value: number) => [formatNumber(value), 'Embedding']}
                    labelFormatter={(label) => label}
                    contentStyle={{
                      backgroundColor: 'rgba(255,255,255,0.95)',
                      border: '1px solid #e5e7eb',
                      borderRadius: '12px',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="prompt_tokens"  
                    stroke="#06b6d4" 
                    strokeWidth={2}
                    fill="url(#colorEmbedding)"
                    name="embedding"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">
                <div className="text-center">
                  <TrendingUp size={32} className="mx-auto mb-2 opacity-50" />
                  <p className="text-sm">아직 임베딩 사용 기록이 없습니다</p>
                </div>
              </div>
            )}
          </div>
          
          {/* 범례 */}
          <div className="flex justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-cyan-500"></div>
              <span className="text-sm text-gray-600 dark:text-gray-400">Embedding</span>
            </div>
          </div>
        </div>
      </div>

      {/* 요약 통계 - 하단 전체 너비 */}
      {summary && (
        <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl p-4 text-white">
            <div className="text-sm opacity-80 mb-1">총 토큰</div>
            <div className="text-2xl font-bold">{formatNumber(summary.total_tokens)}</div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl p-4 text-white">
            <div className="text-sm opacity-80 mb-1">Input / Output</div>
            <div className="text-lg font-bold">
              {formatNumber(summary.total_prompt_tokens)} / {formatNumber(summary.total_completion_tokens)}
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-xl p-4 text-white">
            <div className="text-sm opacity-80 mb-1">예상 비용</div>
            <div className="text-2xl font-bold">${summary.total_cost.toFixed(4)}</div>
          </div>
          
          <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl p-4 text-white">
            <div className="text-sm opacity-80 mb-1">요청 횟수</div>
            <div className="text-2xl font-bold">{summary.total_requests}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TokenUsageChart;
