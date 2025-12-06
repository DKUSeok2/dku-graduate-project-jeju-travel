/**
 * DM Page - 제주도 감성 1:1 채팅 페이지
 */
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, Loader2, Wifi, WifiOff } from 'lucide-react';
import { getConversation, getMessages } from '../api/dm';
import type { ConversationSummary, DmMessage } from '../api/dm';
import { useWebSocketDm } from '../hooks/useWebSocketDm';
import type { DmWsMessage } from '../hooks/useWebSocketDm';
import { useAuth } from '../contexts/AuthContext';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

const DmPage: React.FC = () => {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [conversation, setConversation] = useState<ConversationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [inputMessage, setInputMessage] = useState('');
  
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const prevMessageCountRef = useRef(0);

  // 제주 색상 팔레트
  const getJejuColor = (name: string) => {
    const colors = [
      'bg-orange-400', // 감귤
      'bg-cyan-500',   // 바다
      'bg-emerald-500', // 한라산
      'bg-yellow-400',  // 유채꽃
      'bg-rose-400',    // 동백꽃
    ];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  // WebSocket 연결
  const {
    messages: wsMessages,
    connected,
    connecting,
    sendMessage,
    setInitialMessages,
  } = useWebSocketDm(conversationId ? parseInt(conversationId) : null, {
    onConnected: (userId, userName) => {
      console.log(`Connected as ${userName} (${userId})`);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  // 새 메시지가 추가되었을 때만 스크롤 (초기 로드 제외, 채팅 영역만)
  useEffect(() => {
    if (wsMessages.length > prevMessageCountRef.current && prevMessageCountRef.current > 0) {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
      }
    }
    prevMessageCountRef.current = wsMessages.length;
  }, [wsMessages]);

  // 대화방 정보 및 기존 메시지 로드
  useEffect(() => {
    if (!conversationId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const [convData, msgData] = await Promise.all([
          getConversation(parseInt(conversationId)),
          getMessages(parseInt(conversationId)),
        ]);
        setConversation(convData);
        
        // 기존 메시지를 WebSocket 메시지 형식으로 변환
        const formattedMessages: DmWsMessage[] = msgData.map((m: DmMessage) => ({
          id: m.id,
          sender_id: m.sender_id,
          sender_name: m.sender_name,
          content: m.content,
          created_at: m.created_at,
        }));
        setInitialMessages(formattedMessages);
      } catch (err: any) {
        console.error('DM 로드 실패:', err);
        setError(err.response?.data?.detail || '대화를 불러오는데 실패했습니다');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [conversationId, setInitialMessages]);


  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !connected) return;

    const sent = sendMessage(inputMessage.trim());
    if (sent) {
      setInputMessage('');
      inputRef.current?.focus();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-sky-50 to-orange-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="text-5xl mb-4 animate-bounce">🍊</div>
          <Loader2 className="animate-spin mx-auto text-orange-400" size={32} />
        </div>
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-sky-50 to-orange-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center bg-white dark:bg-gray-800 rounded-3xl p-12 shadow-lg border-2 border-orange-100 dark:border-gray-700">
          <div className="text-6xl mb-4">🏝️</div>
          <p className="text-gray-600 dark:text-gray-400 text-xl font-bold mb-6">{error || '대화를 찾을 수 없습니다'}</p>
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 bg-orange-400 hover:bg-orange-500 text-white px-8 py-3 rounded-2xl font-bold transition-all"
          >
            <ArrowLeft size={20} />
            뒤로 가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-sky-50 via-white to-orange-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* 헤더 */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border-b border-orange-100 dark:border-gray-700 px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dm')}
              className="p-2 hover:bg-orange-100 dark:hover:bg-gray-700 rounded-full transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-600 dark:text-gray-400" />
            </button>
            
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-2xl ${getJejuColor(conversation.partner_name)} flex items-center justify-center text-white font-bold shadow-md`}>
                {conversation.partner_name[0].toUpperCase()}
              </div>
              <h1 className="font-bold text-gray-900 dark:text-white">
                {conversation.partner_name}
              </h1>
            </div>
          </div>

          {/* 연결 상태 */}
          <div className="flex items-center gap-2">
            {connecting ? (
              <div className="flex items-center gap-1.5 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 px-3 py-1.5 rounded-full">
                <Loader2 size={14} className="animate-spin" />
                <span className="text-xs font-medium">연결 중</span>
              </div>
            ) : connected ? (
              <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 px-3 py-1.5 rounded-full">
                <Wifi size={14} />
                <span className="text-xs font-medium">연결됨</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-1.5 rounded-full">
                <WifiOff size={14} />
                <span className="text-xs font-medium">연결 끊김</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-3">
          {wsMessages.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-6xl mb-4">🌺</div>
              <p className="text-gray-600 dark:text-gray-400 font-medium">
                아직 대화 내용이 없어요
              </p>
              <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                {conversation.partner_name}님에게 먼저 인사해보세요! 🤙
              </p>
            </div>
          ) : (
            wsMessages.map((msg, idx) => {
              const isMe = msg.sender_id === user?.id;
              return (
                <div
                  key={msg.id ? `msg-${msg.id}` : `temp-${idx}-${msg.created_at}`}
                  className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                      isMe
                        ? 'bg-orange-400 text-white rounded-br-sm'
                        : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-white rounded-bl-sm shadow-sm border border-orange-100 dark:border-gray-700'
                    }`}
                  >
                    {!isMe && (
                      <p className="text-xs font-semibold text-orange-500 dark:text-orange-400 mb-1">
                        {msg.sender_name}
                      </p>
                    )}
                    <p className="whitespace-pre-wrap break-words text-[15px]">{msg.content}</p>
                    {msg.created_at && (
                      <p className={`text-[11px] mt-1.5 ${isMe ? 'text-orange-100' : 'text-gray-400'}`}>
                        {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true, locale: ko })}
                      </p>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* 입력 영역 */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border-t border-orange-100 dark:border-gray-700 px-4 py-4">
        <form onSubmit={handleSend} className="max-w-3xl mx-auto flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={connected ? "메시지를 입력하세요... 🍊" : "연결 중..."}
            disabled={!connected}
            className="flex-1 px-5 py-3 rounded-2xl border-2 border-orange-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-orange-400 transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || !connected}
            className="px-5 py-3 bg-orange-400 hover:bg-orange-500 text-white rounded-2xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2 shadow-md hover:shadow-lg"
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default DmPage;
