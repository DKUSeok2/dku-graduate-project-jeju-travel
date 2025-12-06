/**
 * DM List Page - 제주도 감성 메시지 목록
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, Search } from 'lucide-react';
import { getConversations } from '../api/dm';
import type { ConversationSummary } from '../api/dm';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

const DmListPage: React.FC = () => {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setLoading(true);
        const data = await getConversations();
        setConversations(data);
      } catch (err: any) {
        console.error('대화 목록 로드 실패:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, []);

  // 제주 색상 팔레트
  const getJejuColor = (name: string) => {
    const colors = [
      'bg-orange-400', // 감귤
      'bg-cyan-500',   // 바다
      'bg-emerald-500', // 한라산
      'bg-yellow-400',  // 유채꽃
      'bg-rose-400',    // 동백꽃
      'bg-sky-400',     // 하늘
    ];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  // 검색 필터
  const filteredConversations = conversations.filter(conv =>
    conv.partner_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-sky-50 to-orange-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="text-5xl mb-4 animate-bounce">🍊</div>
          <Loader2 className="animate-spin text-orange-400 mx-auto" size={24} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 via-white to-orange-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* 배경 장식 */}
      <div className="fixed top-20 right-10 text-6xl opacity-20 pointer-events-none">🌴</div>
      <div className="fixed bottom-20 left-10 text-6xl opacity-20 pointer-events-none">🌊</div>
      
      <div className="max-w-lg mx-auto relative">
        {/* 헤더 */}
        <div className="sticky top-0 z-10 backdrop-blur-xl bg-white/70 dark:bg-gray-900/70 border-b border-orange-100 dark:border-gray-800">
          <div className="flex items-center gap-4 px-4 py-4">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-orange-100 dark:hover:bg-gray-800 rounded-full transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-700 dark:text-gray-300" />
            </button>
            
            <div className="flex items-center gap-2">
              <span className="text-2xl">💬</span>
              <h1 className="text-xl font-bold text-gray-800 dark:text-white">DM</h1>
            </div>
          </div>

          {/* 검색창 */}
          <div className="px-4 pb-4">
            <div className="relative">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="친구 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-white dark:bg-gray-800 border-2 border-orange-200 dark:border-gray-700 rounded-2xl text-gray-800 dark:text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 dark:focus:border-orange-500 transition-colors shadow-sm"
              />
            </div>
          </div>
        </div>

        {/* 대화 목록 */}
        <div className="p-4 space-y-3">
          {filteredConversations.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-7xl mb-6">🏝️</div>
              <h3 className="text-xl font-bold text-gray-700 dark:text-gray-300 mb-2">
                아직 대화가 없어요
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                제주에서 만난 친구에게<br />먼저 인사해보세요! 🤙
              </p>
            </div>
          ) : (
            filteredConversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => navigate(`/dm/${conv.id}`)}
                className="w-full p-4 bg-white dark:bg-gray-800 rounded-3xl shadow-sm hover:shadow-md border-2 border-transparent hover:border-orange-200 dark:hover:border-orange-900 transition-all flex items-center gap-4 group"
              >
                {/* 아바타 */}
                <div className={`w-14 h-14 rounded-2xl ${getJejuColor(conv.partner_name)} flex items-center justify-center text-white text-xl font-bold shadow-md group-hover:scale-105 transition-transform`}>
                  {conv.partner_name[0].toUpperCase()}
                </div>

                {/* 대화 정보 */}
                <div className="flex-1 min-w-0 text-left">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-gray-800 dark:text-white truncate">
                      {conv.partner_name}
                    </span>
                    {conv.last_message_at && (
                      <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0 ml-2">
                        {formatDistanceToNow(new Date(conv.last_message_at), { 
                          addSuffix: false, 
                          locale: ko 
                        })}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                    {conv.last_message || '대화를 시작해보세요 🍊'}
                  </p>
                </div>

                {/* 화살표 */}
                <div className="w-8 h-8 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-orange-500">→</span>
                </div>
              </button>
            ))
          )}
        </div>

        {/* 하단 제주 일러스트 */}
        {filteredConversations.length > 0 && (
          <div className="text-center py-8 opacity-50">
            <span className="text-3xl">🍊</span>
            <span className="text-2xl mx-1">🌺</span>
            <span className="text-3xl">🐴</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default DmListPage;
