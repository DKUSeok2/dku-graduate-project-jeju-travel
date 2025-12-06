/**
 * useChatSession Hook
 * 채팅 세션 관리 커스텀 Hook
 */
import { useState, useEffect, useCallback } from 'react';
import {
  createChatSession,
  getChatSession,
  getChatSessions,
  addMessageToSession,
  updateChatSession,
  deleteChatSession,
  updateSessionContext,
} from '../api/chatSessions';
import type { ChatMessage, ChatSessionListItem } from '../api/chatSessions';
import { safeLocalStorage } from '../utils/storage';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attractions?: any[];
  timestamp: Date;
}

export const useChatSession = () => {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<ChatSessionListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAttractions, setSelectedAttractions] = useState<any[]>([]);
  const [itineraryMapData, setItineraryMapData] = useState<any>(null); // AI 일정의 map_data (경로 정보)

  // ===== 세션 목록 불러오기 =====
  const loadSessions = useCallback(async () => {
    console.log('📋 세션 목록 로드 시작');
    try {
      setLoading(true);
      const data = await getChatSessions();
      console.log('📋 세션 목록:', data?.length || 0, '개');
      setSessions(data);
      setError(null);
    } catch (err: any) {
      console.error('❌ 세션 목록 로드 실패:', err);
      // 401 또는 403 에러면 인증 문제
      if (err.response?.status === 401 || err.response?.status === 403) {
        console.warn('인증이 필요합니다. 로그인 페이지로 이동합니다.');
        // safeLocalStorage 클리어
        safeLocalStorage.removeItem('access_token');
        safeLocalStorage.removeItem('user');
        // 로그인 페이지로 리다이렉트
        window.location.href = '/login';
        return;
      }
      setError(err.response?.data?.detail || '세션 목록을 불러오는데 실패했습니다');
      console.error('세션 목록 로드 실패:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // ===== 새 세션 생성 =====
  const createNewSession = useCallback(async (title?: string) => {
    try {
      setLoading(true);
      const newSession = await createChatSession({ title, context: {} });
      setCurrentSessionId(newSession.session_id);
      
      // 초기 메시지 설정
      const initialMessage = {
        id: '1',
        role: 'assistant' as const,
        content: '안녕하세요! 🍊\n제주 여행 계획을 도와드릴게요.\n\n어떤 여행을 원하시나요?',
        timestamp: new Date(),
      };
      
      setMessages([initialMessage]);
      
      // 초기 메시지를 서버에도 저장
      try {
        await addMessageToSession(newSession.session_id, {
          role: initialMessage.role,
          content: initialMessage.content,
          timestamp: initialMessage.timestamp.toISOString(),
        });
      } catch (err) {
        console.error('초기 메시지 저장 실패:', err);
      }
      
      setSelectedAttractions([]);
      setError(null);
      
      // safeLocalStorage에 현재 세션 ID 저장
      safeLocalStorage.setItem('current_chat_session', newSession.session_id);
      
      // 세션 목록 갱신
      await loadSessions();
      
      return newSession.session_id;
    } catch (err: any) {
      setError(err.response?.data?.detail || '세션 생성에 실패했습니다');
      console.error('세션 생성 실패:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [loadSessions]);

  // ===== 기존 세션 불러오기 =====
  const loadSession = useCallback(async (sessionId: string) => {
    console.log('📂 세션 로드 시작:', sessionId);
    try {
      setLoading(true);
      const session = await getChatSession(sessionId);
      console.log('📂 세션 데이터:', session);
      console.log('📂 메시지 수:', session.messages?.length || 0);
      
      setCurrentSessionId(session.session_id);
      
      // 메시지 변환 (백엔드 형식 -> 프론트엔드 형식)
      const loadedMessages: Message[] = (session.messages || []).map((msg, idx) => ({
        id: `${idx + 1}`,
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        attractions: msg.attractions,
        timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
      }));
      
      console.log('📂 변환된 메시지:', loadedMessages);
      setMessages(loadedMessages);
      
      // 컨텍스트에서 선택한 관광지 복원
      if (session.context?.selectedAttractions) {
        setSelectedAttractions(session.context.selectedAttractions);
      } else {
        setSelectedAttractions([]);
      }
      
      setError(null);
      
      // safeLocalStorage에 현재 세션 ID 저장
      safeLocalStorage.setItem('current_chat_session', session.session_id);
      console.log('✅ 세션 로드 완료');
    } catch (err: any) {
      console.error('❌ 세션 로드 에러:', err);
      // 401 또는 403 에러면 인증 문제
      if (err.response?.status === 401 || err.response?.status === 403) {
        console.warn('인증이 필요합니다. 로그인 페이지로 이동합니다.');
        safeLocalStorage.removeItem('access_token');
        safeLocalStorage.removeItem('user');
        window.location.href = '/login';
        throw err;
      }
      // 404 에러면 세션이 없는 것이므로 새 세션 생성
      if (err.response?.status === 404) {
        console.warn('세션을 찾을 수 없습니다. 새 세션을 생성합니다.');
        safeLocalStorage.removeItem('current_chat_session');
        throw err;
      }
      setError(err.response?.data?.detail || '세션을 불러오는데 실패했습니다');
      console.error('세션 로드 실패:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // ===== 메시지 추가 (로컬 + 서버 동기화) =====
  const addMessage = useCallback(async (message: Message) => {
    if (!currentSessionId) {
      console.error('세션 ID가 없습니다');
      return false;
    }

    try {
      // 로컬 상태 업데이트 (즉시 반영)
      setMessages((prev) => [...prev, message]);

      // 서버에 동기화
      const chatMessage: ChatMessage = {
        role: message.role,
        content: message.content,
        timestamp: message.timestamp.toISOString(),
        attractions: message.attractions,
      };

      await addMessageToSession(currentSessionId, chatMessage);
      
      return true;
    } catch (err: any) {
      console.error('메시지 추가 실패:', err);
      setError(err.response?.data?.detail || '메시지 추가에 실패했습니다');
      return false;
    }
  }, [currentSessionId]);

  // ===== 관광지 추가 (단일) =====
  const addAttraction = useCallback(async (attraction: any) => {
    if (!currentSessionId) return;

    const newAttractions = [...selectedAttractions, attraction];
    setSelectedAttractions(newAttractions);

    // 컨텍스트 업데이트
    try {
      await updateSessionContext(currentSessionId, {
        selectedAttractions: newAttractions,
      });
    } catch (err) {
      console.error('관광지 추가 실패:', err);
    }
  }, [currentSessionId, selectedAttractions]);

  // ===== 관광지 여러 개 추가 (배치) =====
  const addAttractions = useCallback(async (attractions: any[], mapData?: any) => {
    if (!currentSessionId) return;

    // 중복 제거하면서 추가
    const existingNames = new Set(selectedAttractions.map(a => a.name));
    const newItems = attractions.filter(a => !existingNames.has(a.name));
    
    if (newItems.length === 0) return;

    const newAttractions = [...selectedAttractions, ...newItems];
    setSelectedAttractions(newAttractions);
    
    // map_data (경로 정보) 저장
    if (mapData) {
      setItineraryMapData(mapData);
    }

    // 컨텍스트 업데이트
    try {
      await updateSessionContext(currentSessionId, {
        selectedAttractions: newAttractions,
      });
    } catch (err) {
      console.error('관광지 배치 추가 실패:', err);
    }
  }, [currentSessionId, selectedAttractions]);

  // ===== 관광지 제거 =====
  const removeAttraction = useCallback(async (name: string) => {
    if (!currentSessionId) return;

    const newAttractions = selectedAttractions.filter((a) => a.name !== name);
    setSelectedAttractions(newAttractions);

    // 컨텍스트 업데이트
    try {
      await updateSessionContext(currentSessionId, {
        selectedAttractions: newAttractions,
      });
    } catch (err) {
      console.error('관광지 제거 실패:', err);
    }
  }, [currentSessionId, selectedAttractions]);

  // ===== 세션 삭제 =====
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await deleteChatSession(sessionId);
      
      // 현재 세션이 삭제된 경우
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
        setSelectedAttractions([]);
        safeLocalStorage.removeItem('current_chat_session');
      }
      
      // 세션 목록 갱신
      await loadSessions();
      
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || '세션 삭제에 실패했습니다');
      console.error('세션 삭제 실패:', err);
      return false;
    }
  }, [currentSessionId, loadSessions]);

  // ===== 세션 제목 변경 =====
  const updateSessionTitle = useCallback(async (sessionId: string, title: string) => {
    try {
      await updateChatSession(sessionId, { title });
      await loadSessions();
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || '제목 변경에 실패했습니다');
      console.error('제목 변경 실패:', err);
      return false;
    }
  }, [loadSessions]);

  // ===== 초기화: 세션 목록만 로드 (빈 화면으로 시작) =====
  useEffect(() => {
    const initSession = async () => {
      console.log('🚀 useChatSession 초기화 시작');
      
      // 세션 목록만 로드 (마지막 세션 복원 안 함)
      await loadSessions();
      
      console.log('🚀 useChatSession 초기화 완료 (빈 화면)');
    };

    initSession();
  }, []); // 빈 배열로 최초 1회만 실행

  // ===== 세션 초기화 (빈 화면으로) =====
  const clearSession = useCallback(() => {
    setCurrentSessionId(null);
    setMessages([]);
    setSelectedAttractions([]);
    safeLocalStorage.removeItem('current_chat_session');
    console.log('🧹 세션 초기화 완료 (빈 화면)');
  }, []);

  return {
    // 상태
    currentSessionId,
    messages,
    sessions,
    loading,
    error,
    selectedAttractions,
    itineraryMapData, // AI 일정 경로 정보
    
    // 액션
    createNewSession,
    loadSession,
    loadSessions,
    clearSession, // 빈 화면으로 초기화
    addMessage,
    addAttraction,
    addAttractions, // 여러 개 한 번에 추가 (mapData도 받음)
    removeAttraction,
    deleteSession,
    updateSessionTitle,
    setMessages, // 로컬 메시지 직접 수정용
  };
};

