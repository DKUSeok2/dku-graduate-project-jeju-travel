import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, MessageCircle, Calendar, X, Save, History, Plus as PlusIcon, Trash2, Copy, Edit2, Check, ThumbsUp, ThumbsDown, Map } from 'lucide-react';
import { createSchedule } from '../api/schedules';
import type { ChatMessage as ScheduleChatMessage } from '../api/schedules';
import { useNavigate, useLocation } from 'react-router-dom';
import { useChatSession } from '../hooks/useChatSession';
import { useChatStream } from '../hooks/useChatStream';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import TypingIndicator from '../components/TypingIndicator';
import ChatMarkdown from '../components/ChatMarkdown';
import { WebSearchResult } from '../components/WebSearchResult';
import { RAGSearchResult } from '../components/RAGSearchResult';
import { SQLQueryResult } from '../components/SQLQueryResult';
import { ItineraryTimeline } from '../components/ItineraryTimeline';
import { toast } from 'sonner';
import { saveFeedback } from '../api/chatSessions';
import { extractAttractionNames, getAttractionsByNames, type Attraction } from '../api/attractions';
import KakaoMap from '../components/KakaoMap';
import apiClient from '../api/client';

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    currentSessionId,
    messages,
    sessions,
    loading: sessionLoading,
    selectedAttractions,
    createNewSession,
    loadSession,
    addAttraction,
    addAttractions,
    removeAttraction,
    deleteSession,
    updateSessionTitle,
    setMessages,
    clearSession,
    itineraryMapData, // AI 일정 경로 정보
  } = useChatSession();

  // URL 쿼리에서 botId, query 추출
  const searchParams = new URLSearchParams(location.search);
  const botId = searchParams.get('botId') ?? 'itinerary';
  const initialQuery = searchParams.get('query');  // 예시 질의 자동 실행용
  const queryProcessedRef = useRef(false);  // 중복 실행 방지

  // 🎨 챗봇별 테마 색상 정의
  const botThemes: Record<string, {
    name: string;
    gradient: string;
    bgGradient: string;
    primary: string;
    buttonGradient: string;
    focusRing: string;
    badge: string;
    // 추가 색상들
    iconBg: string;
    iconText: string;
    lightBg: string;
    lightHoverBg: string;
    lightText: string;
    activeBorder: string;
    userBubble: string;
    countBadge: string;
    hoverText: string;
    cardBg: string;
  }> = {
    itinerary: {
      name: '✈️ 일정 짜기',
      gradient: 'from-orange-500 to-pink-500',
      bgGradient: 'from-orange-50 via-white to-pink-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800',
      primary: 'orange',
      buttonGradient: 'from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600',
      focusRing: 'focus:ring-orange-200 dark:focus:ring-orange-800 focus:border-orange-400',
      badge: '일정 생성',
      iconBg: 'from-orange-400 to-orange-500',
      iconText: 'text-orange-500',
      lightBg: 'bg-orange-100 dark:bg-orange-900/30',
      lightHoverBg: 'hover:bg-orange-200 dark:hover:bg-orange-800/40',
      lightText: 'text-orange-700 dark:text-orange-400',
      activeBorder: 'border-orange-300 dark:border-orange-700',
      userBubble: 'from-orange-500 to-orange-600',
      countBadge: 'bg-orange-500',
      hoverText: 'group-hover:text-orange-600 dark:group-hover:text-orange-400',
      cardBg: 'from-orange-50 to-pink-50',
    },
    sql: {
      name: '🍽️ 맛집·카페 검색',
      gradient: 'from-sky-500 to-indigo-500',
      bgGradient: 'from-sky-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800',
      primary: 'sky',
      buttonGradient: 'from-sky-500 to-indigo-500 hover:from-sky-600 hover:to-indigo-600',
      focusRing: 'focus:ring-sky-200 dark:focus:ring-sky-800 focus:border-sky-400',
      badge: '장소 검색',
      iconBg: 'from-sky-400 to-indigo-500',
      iconText: 'text-sky-500',
      lightBg: 'bg-sky-100 dark:bg-sky-900/30',
      lightHoverBg: 'hover:bg-sky-200 dark:hover:bg-sky-800/40',
      lightText: 'text-sky-700 dark:text-sky-400',
      activeBorder: 'border-sky-300 dark:border-sky-700',
      userBubble: 'from-sky-500 to-indigo-500',
      countBadge: 'bg-sky-500',
      hoverText: 'group-hover:text-sky-600 dark:group-hover:text-sky-400',
      cardBg: 'from-sky-50 to-indigo-50',
    },
    rag: {
      name: '🏝️ 관광지 안내',
      gradient: 'from-violet-500 to-purple-500',
      bgGradient: 'from-violet-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800',
      primary: 'violet',
      buttonGradient: 'from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600',
      focusRing: 'focus:ring-violet-200 dark:focus:ring-violet-800 focus:border-violet-400',
      badge: '관광 정보',
      iconBg: 'from-violet-400 to-purple-500',
      iconText: 'text-violet-500',
      lightBg: 'bg-violet-100 dark:bg-violet-900/30',
      lightHoverBg: 'hover:bg-violet-200 dark:hover:bg-violet-800/40',
      lightText: 'text-violet-700 dark:text-violet-400',
      activeBorder: 'border-violet-300 dark:border-violet-700',
      userBubble: 'from-violet-500 to-purple-500',
      countBadge: 'bg-violet-500',
      hoverText: 'group-hover:text-violet-600 dark:group-hover:text-violet-400',
      cardBg: 'from-violet-50 to-purple-50',
    },
    web: {
      name: '🔍 실시간 검색',
      gradient: 'from-emerald-500 to-lime-500',
      bgGradient: 'from-emerald-50 via-white to-lime-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800',
      primary: 'emerald',
      buttonGradient: 'from-emerald-500 to-lime-500 hover:from-emerald-600 hover:to-lime-600',
      focusRing: 'focus:ring-emerald-200 dark:focus:ring-emerald-800 focus:border-emerald-400',
      badge: '실시간',
      iconBg: 'from-emerald-400 to-lime-500',
      iconText: 'text-emerald-500',
      lightBg: 'bg-emerald-100 dark:bg-emerald-900/30',
      lightHoverBg: 'hover:bg-emerald-200 dark:hover:bg-emerald-800/40',
      lightText: 'text-emerald-700 dark:text-emerald-400',
      activeBorder: 'border-emerald-300 dark:border-emerald-700',
      userBubble: 'from-emerald-500 to-lime-500',
      countBadge: 'bg-emerald-500',
      hoverText: 'group-hover:text-emerald-600 dark:group-hover:text-emerald-400',
      cardBg: 'from-emerald-50 to-lime-50',
    },
  };
  const theme = botThemes[botId] || botThemes.itinerary;

  // 세션 초기화: location.state에서 sessionId가 있으면 해당 세션 로드
  useEffect(() => {
    const initChatSession = async () => {
      const targetSessionId = location.state?.sessionId;
      
      if (targetSessionId) {
        // location.state에서 sessionId가 전달된 경우 해당 세션 로드
        console.log('📂 전달된 세션 ID로 로드:', targetSessionId);
        try {
          await loadSession(targetSessionId);
        } catch (err: any) {
          console.error('세션 로드 실패:', err);
        }
        // state 초기화 (뒤로가기 시 재로드 방지)
        navigate(location.pathname, { replace: true, state: {} });
      }
    };

    if (location.state?.sessionId) {
      initChatSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state?.sessionId]);
  
  // 세션이 없으면 빈 화면으로 시작 (새 세션은 첫 메시지 전송 시 생성)

  const [inputMessage, setInputMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isComposingRef = useRef<boolean>(false);
  const [isLoading, setIsLoading] = useState(false);
  const [aiReasoning, setAiReasoning] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showHistorySidebar, setShowHistorySidebar] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>('');
  const [streamingText, setStreamingText] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  const isSendingRef = useRef(false); // 중복 전송 방지용
  const [feedbackStates, setFeedbackStates] = useState<Record<string, boolean | null>>({});
  const [showRightPanel, setShowRightPanel] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [showMapForMessage, setShowMapForMessage] = useState<Record<string, boolean>>({});
  const [attractionsForMessage, setAttractionsForMessage] = useState<Record<string, Attraction[]>>({});

  // THINKING 마커 버퍼 (여러 청크에 걸쳐 올 수 있음)
  const thinkingBufferRef = useRef<string>('');
  
  const [startChatStream] = useChatStream({
    onChunk: (chunk: string) => {
      // 청크를 버퍼에 누적
      let text = thinkingBufferRef.current + chunk;
      thinkingBufferRef.current = '';
      
      // THINKING 마커 처리
      while (text.includes('[THINKING]')) {
        const startIdx = text.indexOf('[THINKING]');
        const endIdx = text.indexOf('[/THINKING]');
        
        if (endIdx !== -1) {
          // 완전한 THINKING 마커 발견
          const thinkingContent = text.substring(startIdx + '[THINKING]'.length, endIdx);
          setAiReasoning(thinkingContent);
          
          // 마커 제거
          text = text.substring(0, startIdx) + text.substring(endIdx + '[/THINKING]'.length);
        } else {
          // 닫는 태그가 아직 안 왔음 - 버퍼에 저장하고 대기
          thinkingBufferRef.current = text.substring(startIdx);
          text = text.substring(0, startIdx);
          break;
        }
      }
      
      // 남은 텍스트 추가 (THINKING 마커가 있으면 클리어)
      if (text.trim()) {
        // 실제 응답 텍스트가 오면 thinking 클리어
        if (text.length > 10) {
          setAiReasoning('');
        }
        setStreamingText((prev) => prev + text);
      }
    },
    onError: (error: Error) => {
      console.error('스트리밍 오류:', error);
      setIsStreaming(false);
      setStreamingText('');
      
      // API 키 관련 에러인 경우 더 명확한 메시지 표시
      if (error.message.includes('API 키') || error.message.includes('API key')) {
        toast.error('OpenAI API 키가 설정되지 않았습니다. 관리자에게 문의하세요.', {
          duration: 5000,
        });
      } else {
        toast.error(`메시지 전송에 실패했습니다: ${error.message}`);
      }
    },
    onCompleted: async (fullResponse: string) => {
      // 🔥 [THINKING] 태그 제거 (최종 메시지에서)
      let cleanedResponse = fullResponse;
      while (cleanedResponse.includes('[THINKING]')) {
        const startIdx = cleanedResponse.indexOf('[THINKING]');
        const endIdx = cleanedResponse.indexOf('[/THINKING]');
        if (endIdx !== -1) {
          cleanedResponse = cleanedResponse.substring(0, startIdx) + cleanedResponse.substring(endIdx + '[/THINKING]'.length);
        } else {
          // 닫는 태그가 없으면 [THINKING] 이후 전체 제거
          cleanedResponse = cleanedResponse.substring(0, startIdx);
          break;
        }
      }
      cleanedResponse = cleanedResponse.trim();
      
      // 스트리밍 완료 후 메시지를 로컬 상태에만 추가 (중복 방지)
      const aiMessage = {
        id: Date.now().toString(),
        role: 'assistant' as const,
        content: cleanedResponse,
        timestamp: new Date(),
      };
      
      setMessages(prev => {
        // 마지막 메시지가 이미 같은 내용이면 추가하지 않음
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.content === fullResponse && lastMsg?.role === 'assistant') {
          return prev;
        }
        
        return [...prev, aiMessage];
      });
      
      // AI 응답에서 관광지 이름 추출 및 위치 정보 가져오기
      // 🔥 웹 검색/RAG/SQL 결과가 있으면 스킵 (별도 UI로 표시됨)
      const hasWebSearchResult = cleanedResponse.includes('[WEB_SEARCH_RESULT]');
      const hasRagSearchResult = cleanedResponse.includes('[RAG_SEARCH_RESULT]');
      const hasSqlQueryResult = cleanedResponse.includes('[SQL_QUERY_RESULT]');
      const hasItineraryData = cleanedResponse.includes('[ITINERARY_DATA]');
      
      if (!hasWebSearchResult && !hasRagSearchResult && !hasSqlQueryResult && !hasItineraryData) {
        const attractionNames = extractAttractionNames(cleanedResponse);
        
        if (attractionNames.length > 0) {
          try {
            const attractions = await getAttractionsByNames(attractionNames);
            
            // 유효한 위치 정보가 있는 관광지만 필터링
            const validAttractions = attractions.filter(a => a.lat && a.lng);
            
            if (validAttractions.length > 0) {
              setAttractionsForMessage(prev => ({
                ...prev,
                [aiMessage.id]: validAttractions
              }));
              
              // 3개 이상이면 자동으로 지도 펼치기
              if (validAttractions.length >= 3) {
                setShowMapForMessage(prev => ({
                  ...prev,
                  [aiMessage.id]: true
                }));
              }
            }
          } catch (error) {
            console.error('❌ 관광지 위치 조회 실패:', error);
          }
        }
      }
      
      setStreamingText('');
      setAiReasoning('');  // thinking 상태도 클리어
      setIsStreaming(false);
      setIsLoading(false);
    },
  });
  const [scheduleForm, setScheduleForm] = useState({
    title: '',
    start_date: '',
    end_date: '',
    memo: ''
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const scrollToBottom = () => {
    if (autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // 사용자가 스크롤했는지 감지
  const handleScroll = () => {
    if (!messagesContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    // 맨 아래에서 100px 이내면 자동 스크롤 활성화
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setAutoScroll(isNearBottom);
  };

  // 초기 로드 완료 체크
  useEffect(() => {
    if (messages.length > 0) {
      setIsInitialLoad(false);
    }
  }, [messages]);

  // 메시지가 추가되거나 스트리밍 중일 때만 스크롤 (초기 로드 제외)
  const prevMessagesLengthRef = useRef(messages.length);
  
  useEffect(() => {
    // 초기 로드가 아니고, 메시지가 실제로 추가되었을 때
    if (!isInitialLoad && messages.length > prevMessagesLengthRef.current) {
      // DM 방식: autoScroll이 true일 때만 스크롤 (사용자가 위에서 보고 있으면 안 내림)
      if (autoScroll) {
        scrollToBottom();
      }
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages.length, isInitialLoad, autoScroll]);

  // 스트리밍 중에는 자동 스크롤 (사용자가 위로 스크롤하지 않았을 때만)
  useEffect(() => {
    if (isStreaming && autoScroll) {
      scrollToBottom();
    }
  }, [isStreaming, streamingText, autoScroll]);

  const quickMessages = [
    '🏖️ 3박 4일 가족여행',
    '🏔️ 한라산 등산',
    '🍊 맛집 추천',
    '📸 포토 스팟',
  ];

  const handleSendMessage = async () => {
    // 중복 전송 방지 (ref로 즉시 체크)
    if (isSendingRef.current) return;
    if (!inputMessage.trim() || isLoading || isStreaming) return;
    
    isSendingRef.current = true; // 즉시 잠금

    let sessionId = currentSessionId;
    
    // 세션이 없으면 새 세션 생성
    if (!sessionId) {
      console.log('🆕 첫 메시지 - 새 세션 생성');
      const newSessionId = await createNewSession();
      if (!newSessionId) {
        toast.error('세션 생성에 실패했습니다.');
        return;
      }
      sessionId = newSessionId;
    }

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: inputMessage,
      timestamp: new Date(),
    };

    // 로컬 상태에만 추가 (서버는 스트리밍 API가 처리)
    setMessages(prev => [...prev, userMessage]);
    
    const messageToSend = inputMessage;
    setInputMessage('');
    setIsLoading(true);
    setIsStreaming(true);
    setStreamingText('');
    
    // 내가 메시지 보내면 → 무조건 맨 아래로 (DM 방식)
    setAutoScroll(true);
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);

    // 스트리밍 시작
    try {
      await startChatStream(sessionId, messageToSend, botId);
    } finally {
      isSendingRef.current = false; // 잠금 해제
    }
  };

  // 🔥 예시 질의 자동 실행 (URL에 query 파라미터가 있을 때)
  useEffect(() => {
    if (initialQuery && !queryProcessedRef.current && !isLoading && !isStreaming) {
      queryProcessedRef.current = true;  // 중복 실행 방지
      setInputMessage(initialQuery);
      
      // 다음 렌더링 사이클에서 메시지 전송
      const timer = setTimeout(() => {
        const sendButton = document.querySelector('[data-send-button]') as HTMLButtonElement;
        if (sendButton) sendButton.click();
      }, 100);
      
      // URL에서 query 파라미터 제거 (새로고침 시 재실행 방지)
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.delete('query');
      window.history.replaceState({}, '', newUrl.toString());
      
      return () => clearTimeout(timer);
    }
  }, [initialQuery, isLoading, isStreaming]);

  const handleAddAttraction = (attraction: any) => {
    if (!selectedAttractions.find(a => a.name === attraction.name)) {
      addAttraction(attraction);
    }
  };

  const handleRemoveAttraction = (name: string) => {
    removeAttraction(name);
  };

  // AI 추천 일정 전체를 내 일정에 추가 (map_data 포함)
  const handleAddItineraryToSchedule = async (attractions: any[], mapData?: any) => {
    // 중복 제거
    const newAttractions = attractions.filter(
      attr => !selectedAttractions.find(a => a.name === attr.name)
    );
    
    if (newAttractions.length === 0) {
      toast.info('이미 모든 장소가 추가되어 있습니다!');
      return;
    }
    
    // mapData도 함께 전달 (경로 정보 포함)
    await addAttractions(newAttractions, mapData);
    setShowRightPanel(true); // 우측 패널 열기
    toast.success(`${newAttractions.length}개의 장소가 내 일정에 추가되었습니다!`);
  };

  // AI 추천 일정의 개별 장소를 내 일정에 추가
  const handleAddItineraryPlace = (place: any) => {
    if (!selectedAttractions.find(a => a.name === place.name)) {
      addAttraction(place);
      setShowRightPanel(true); // 우측 패널 열기
      toast.success(`"${place.name}"이(가) 내 일정에 추가되었습니다!`);
    }
  };

  // AI 추천 일정 수정 (OR-Tools 기반 대안 선택)
  const handleEditItinerary = (messageIndex: number, updatedData: any) => {
    // 메시지 내용에서 ITINERARY_DATA를 업데이트된 데이터로 교체
    setMessages(prev => prev.map((msg, idx) => {
      if (idx === messageIndex && msg.role === 'assistant') {
        // 기존 ITINERARY_DATA 추출 및 교체
        const itineraryMatch = msg.content.match(/\[ITINERARY_DATA\](.*?)\[\/ITINERARY_DATA\]/s);
        if (itineraryMatch) {
          const newContent = msg.content.replace(
            /\[ITINERARY_DATA\](.*?)\[\/ITINERARY_DATA\]/s,
            `[ITINERARY_DATA]${JSON.stringify(updatedData)}[/ITINERARY_DATA]`
          );
          return { ...msg, content: newContent };
        }
      }
      return msg;
    }));
    
    toast.success('일정이 수정되었습니다! 🗺️');
  };

  const handleSaveSchedule = () => {
    if (selectedAttractions.length === 0) {
      alert('최소 1개 이상의 관광지를 선택해주세요!');
      return;
    }
    setShowSaveModal(true);
  };

  const handleConfirmSave = async () => {
    if (!scheduleForm.title || !scheduleForm.start_date || !scheduleForm.end_date) {
      alert('제목, 시작일, 종료일을 모두 입력해주세요!');
      return;
    }

    setIsSaving(true);
    try {
      // 대화 내역을 ChatMessage 형식으로 변환
      const chatHistory: ScheduleChatMessage[] = messages.map(msg => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        timestamp: msg.timestamp.toISOString()
      }));

      // attractions를 day별로 구성 (3개씩 묶어서 하루)
      const attractionsByDay: any = {};
      selectedAttractions.forEach((attr, idx) => {
        const dayNum = attr.day || Math.floor(idx / 3) + 1; // 사용자 지정 day 또는 자동 계산
        const dayKey = `day${dayNum}`;
        if (!attractionsByDay[dayKey]) {
          attractionsByDay[dayKey] = [];
        }
        attractionsByDay[dayKey].push({
          ...attr,
          day: dayNum,
          order: attractionsByDay[dayKey].length + 1,
        });
      });

      // 🚗 경로 계산: 기존 routes가 없으면 API로 계산
      let calculatedRoutes = itineraryMapData?.routes || [];
      
      if (calculatedRoutes.length === 0 && selectedAttractions.length >= 2) {
        console.log('🚗 경로 계산 API 호출 중...');
        try {
          const validPlaces = selectedAttractions
            .filter((a: any) => a.lat && a.lng)
            .map((attr: any) => ({
              name: attr.name,
              lat: Number(attr.lat),
              lng: Number(attr.lng),
              day: attr.day || 1,
            }));
          
          if (validPlaces.length >= 2) {
            const routeResponse = await apiClient.post('/api/routes/calculate', { places: validPlaces });
            if (routeResponse.data?.routes) {
              calculatedRoutes = routeResponse.data.routes;
              console.log('✅ 경로 계산 완료:', calculatedRoutes.length, '일');
            }
          }
        } catch (routeErr) {
          console.warn('⚠️ 경로 계산 실패 (직선으로 표시됨):', routeErr);
        }
      }

      // 지도 데이터 구성 (요일별 색상 지원 + 경로 정보)
      let markerOrder = 0;
      
      // 🔥 유효한 좌표가 있는 장소만 필터링해서 center 계산
      const validCoordsAttractions = selectedAttractions.filter(
        (a: any) => a.lat && a.lng && a.lat > 30 && a.lat < 40 && a.lng > 120 && a.lng < 130
      );
      
      const mapData = {
        markers: selectedAttractions.map((attr, idx) => {
          const dayNum = attr.day || Math.floor(idx / 3) + 1;
          markerOrder++;
          return {
            id: idx,
            name: attr.name,
            position: { lat: attr.lat, lng: attr.lng },
            lat: attr.lat,
            lng: attr.lng,
            emoji: attr.emoji,
            day: dayNum,
            order: markerOrder,
          };
        }),
        center: validCoordsAttractions.length > 0 
          ? {
              lat: validCoordsAttractions.reduce((sum, a) => sum + a.lat, 0) / validCoordsAttractions.length,
              lng: validCoordsAttractions.reduce((sum, a) => sum + a.lng, 0) / validCoordsAttractions.length,
            }
          : { lat: 33.45, lng: 126.57 }, // 제주도 기본값
        zoom: 10,
        showDayColors: true,
        routes: calculatedRoutes, // 계산된 경로 정보!
      };

      const newSchedule = await createSchedule({
        title: scheduleForm.title,
        start_date: scheduleForm.start_date,
        end_date: scheduleForm.end_date,
        memo: scheduleForm.memo || undefined,
        attractions: attractionsByDay,
        route_data: null,
        chat_history: chatHistory,
        ai_reasoning: aiReasoning,
        map_data: mapData,
        chat_session_id: currentSessionId ?? undefined, // 채팅 세션 ID 저장
      });

      alert('일정이 성공적으로 저장되었습니다! 🎉');
      setShowSaveModal(false);
      
      // 일정 상세 페이지로 이동
      navigate(`/schedule/${newSchedule.id}`);
    } catch (error: any) {
      console.error('일정 저장 실패:', error);
      alert(error.response?.data?.detail || '일정 저장에 실패했습니다');
    } finally {
      setIsSaving(false);
    }
  };

  // Textarea 자동 높이 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '56px';
      const scrollHeight = textareaRef.current.scrollHeight;
      if (scrollHeight > 56) {
        textareaRef.current.style.height = `${Math.min(scrollHeight, 120)}px`;
      }
    }
  }, [inputMessage]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const isComposing = isComposingRef.current;
    if (e.key === 'Enter' && !e.shiftKey) {
      if (isComposing) {
        e.preventDefault();
        return;
      }
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = () => {
    // 빈 화면으로 초기화 (세션은 첫 메시지 전송 시 생성)
    clearSession();
    setAiReasoning('');
    setShowHistorySidebar(false);
  };

  const handleLoadSession = async (sessionId: string) => {
    console.log('📂 세션 선택:', sessionId);
    try {
      await loadSession(sessionId);
      console.log('✅ 세션 로드 완료, 메시지 수:', messages.length);
    } catch (err) {
      console.error('❌ 세션 로드 실패:', err);
      toast.error('세션을 불러오는데 실패했습니다');
    }
    setShowHistorySidebar(false);
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const confirm = window.confirm('이 대화를 삭제하시겠습니까?');
    if (confirm) {
      await deleteSession(sessionId);
    }
  };

  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('메시지가 복사되었습니다!');
    } catch (error) {
      console.error('복사 실패:', error);
      toast.error('복사에 실패했습니다');
    }
  };

  const handleStartEditTitle = (sessionId: string, currentTitle: string) => {
    setEditingSessionId(sessionId);
    setEditingTitle(currentTitle);
  };

  const handleSaveTitle = async (sessionId: string) => {
    if (!editingTitle.trim()) {
      toast.error('제목을 입력해주세요');
      return;
    }
    
    try {
      await updateSessionTitle(sessionId, editingTitle.trim());
      toast.success('제목이 변경되었습니다');
      setEditingSessionId(null);
      setEditingTitle('');
    } catch (error) {
      toast.error('제목 변경에 실패했습니다');
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleFeedback = async (messageId: string, isLike: boolean) => {
    if (!currentSessionId) return;

    // 이미 같은 피드백을 했으면 취소
    if (feedbackStates[messageId] === isLike) {
      return;
    }

    try {
      await saveFeedback(currentSessionId, messageId, isLike);
      setFeedbackStates((prev) => ({
        ...prev,
        [messageId]: isLike,
      }));
      toast.success(isLike ? '좋아요를 눌렀습니다' : '싫어요를 눌렀습니다');
    } catch (error) {
      console.error('피드백 저장 실패:', error);
      toast.error('피드백 저장에 실패했습니다');
    }
  };

  return (
    <div className={`h-screen flex bg-gradient-to-br ${theme.bgGradient}`}>
      {/* 저장 모달 */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 max-w-md w-full shadow-2xl border-2 border-gray-200 dark:border-gray-700">
            <h2 className="text-2xl font-black text-gray-900 dark:text-white mb-6 flex items-center gap-3">
              <Save className={theme.iconText} size={28} />
              일정 저장하기
            </h2>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                  제목 *
                </label>
                <input
                  type="text"
                  value={scheduleForm.title}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, title: e.target.value })}
                  placeholder="예: 가족 여행 제주 3박 4일"
                  className={`w-full px-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none ${theme.focusRing} transition-colors`}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                    시작일 *
                  </label>
                  <input
                    type="date"
                    value={scheduleForm.start_date}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, start_date: e.target.value })}
                    className={`w-full px-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none ${theme.focusRing} transition-colors`}
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                    종료일 *
                  </label>
                  <input
                    type="date"
                    value={scheduleForm.end_date}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, end_date: e.target.value })}
                    className={`w-full px-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none ${theme.focusRing} transition-colors`}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                  메모
                </label>
                <textarea
                  value={scheduleForm.memo}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, memo: e.target.value })}
                  placeholder="여행 메모를 입력하세요..."
                  rows={3}
                  className={`w-full px-4 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none ${theme.focusRing} transition-colors resize-none`}
                />
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/30 rounded-xl p-4 border border-blue-200 dark:border-blue-800">
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  <span className="font-bold">💾 저장되는 내용:</span><br/>
                  • AI와의 대화 내역<br/>
                  • AI 추천 이유<br/>
                  • 선택한 관광지 ({selectedAttractions.length}곳)<br/>
                  • 지도 정보
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleConfirmSave}
                disabled={isSaving}
                className={`flex-1 bg-gradient-to-r ${theme.buttonGradient} text-white py-3 rounded-xl font-bold disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg transition-all`}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    저장 중...
                  </>
                ) : (
                  <>
                    <Save size={20} />
                    저장하기
                  </>
                )}
              </button>
              <button
                onClick={() => setShowSaveModal(false)}
                disabled={isSaving}
                className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl font-bold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 히스토리 사이드바 */}
      {showHistorySidebar && (
        <>
          <div 
            className="fixed inset-0 bg-black/30 z-40"
            onClick={() => setShowHistorySidebar(false)}
          />
          <div className="fixed left-0 top-0 bottom-0 w-80 bg-white dark:bg-gray-800 shadow-2xl z-50 overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-black text-gray-900 dark:text-white flex items-center gap-2">
                  <History size={24} className={theme.iconText} />
                  대화 기록
                </h2>
                <button
                  onClick={() => setShowHistorySidebar(false)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <button
                onClick={handleNewChat}
                className={`w-full mb-4 flex items-center justify-center gap-2 bg-gradient-to-r ${theme.buttonGradient} text-white py-3 rounded-xl font-bold hover:shadow-lg transition-all`}
              >
                <PlusIcon size={20} />
                새 대화 시작
              </button>

              {sessionLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className={`animate-spin ${theme.iconText}`} size={32} />
                </div>
              ) : sessions.length === 0 ? (
                <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                  저장된 대화가 없습니다
                </p>
              ) : (
                <div className="space-y-2">
                  {sessions.map((session) => (
                    <div
                      key={session.session_id}
                      onClick={() => {
                        console.log('🖱️ 세션 클릭:', session.session_id, '편집모드:', editingSessionId);
                        if (!editingSessionId) {
                          handleLoadSession(session.session_id);
                        }
                      }}
                      className={`p-4 rounded-xl transition-all ${
                        currentSessionId === session.session_id
                          ? `bg-gradient-to-r ${theme.lightBg} border-2 ${theme.activeBorder}`
                          : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 border-2 border-transparent'
                      } ${editingSessionId === session.session_id ? '' : 'cursor-pointer'}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        {editingSessionId === session.session_id ? (
                          <div className="flex-1 flex items-center gap-2">
                            <input
                              type="text"
                              value={editingTitle}
                              onChange={(e) => setEditingTitle(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleSaveTitle(session.session_id);
                                } else if (e.key === 'Escape') {
                                  handleCancelEdit();
                                }
                              }}
                              className={`flex-1 px-2 py-1 text-sm font-bold text-gray-900 dark:text-white bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 ${theme.focusRing}`}
                              autoFocus
                              onClick={(e) => e.stopPropagation()}
                            />
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSaveTitle(session.session_id);
                              }}
                              className="p-1 hover:bg-green-100 dark:hover:bg-green-900/30 rounded transition-colors"
                            >
                              <Check size={14} className="text-green-600 dark:text-green-400" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCancelEdit();
                              }}
                              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                            >
                              <X size={14} className="text-gray-400" />
                            </button>
                          </div>
                        ) : (
                          <>
                            <h3 className="font-bold text-gray-900 dark:text-white text-sm line-clamp-1 flex-1">
                              {session.title || '새로운 대화'}
                            </h3>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStartEditTitle(session.session_id, session.title || '새로운 대화');
                                }}
                                className="p-1 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded transition-colors"
                              >
                                <Edit2 size={14} className="text-gray-400 hover:text-blue-600" />
                              </button>
                              <button
                                onClick={(e) => handleDeleteSession(session.session_id, e)}
                                className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
                              >
                                <Trash2 size={14} className="text-gray-400 hover:text-red-600" />
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                        {session.last_message_preview || '메시지 없음'}
                      </p>
                      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-500">
                        <span>{session.message_count}개 메시지</span>
                        <span>
                          {formatDistanceToNow(new Date(session.updated_at), { 
                            addSuffix: true, 
                            locale: ko 
                          })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* 좌측: 채팅 영역 */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* 헤더 */}
        <div className="bg-white dark:bg-gray-800 border-b-2 border-gray-200 dark:border-gray-700 px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowHistorySidebar(true)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="대화 기록"
              >
                <History size={24} className="text-gray-600 dark:text-gray-400" />
              </button>
              <div className={`w-12 h-12 bg-gradient-to-br ${theme.iconBg} rounded-2xl flex items-center justify-center shadow-lg`}>
                <MessageCircle className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-xl font-black text-gray-900 dark:text-white">{theme.name}</h1>
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-gradient-to-r ${theme.gradient} text-white`}>
                  {theme.badge}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* 지도 버튼: itinerary 챗봇에서만 표시 */}
              {botId === 'itinerary' && (
                <button
                  onClick={() => setShowRightPanel(!showRightPanel)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                    showRightPanel
                      ? 'bg-blue-500 text-white hover:bg-blue-600'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                  title="지도 & 일정"
                >
                  <Map size={18} />
                  <span className="hidden sm:inline">지도 & 일정</span>
                  {selectedAttractions.length > 0 && (
                    <span className={`${theme.countBadge} text-white text-xs font-bold px-2 py-0.5 rounded-full`}>
                      {selectedAttractions.length}
                    </span>
                  )}
                </button>
              )}
              <button
                onClick={handleNewChat}
                className={`hidden sm:flex items-center gap-2 px-4 py-2 ${theme.lightBg} ${theme.lightHoverBg} ${theme.lightText} rounded-lg font-medium transition-colors`}
              >
                <PlusIcon size={18} />
                새 대화
              </button>
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-green-100 dark:bg-green-900/30 rounded-full">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-bold text-green-700 dark:text-green-400">온라인</span>
              </div>
            </div>
          </div>
        </div>

        {/* 채팅 메시지 */}
        <div 
          ref={messagesContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto min-h-0"
        >
          <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
            {/* 빈 상태 UI */}
            {messages.length === 0 && !isLoading && !isStreaming && (
              <div className="flex h-full flex-col items-center justify-center py-20">
                {/* 챗봇 배지 */}
                <span className={`inline-flex items-center px-4 py-1.5 rounded-full text-sm font-semibold bg-gradient-to-r ${theme.gradient} text-white mb-4 shadow-lg`}>
                  {theme.badge}
                </span>
                <div className={`mb-6 rounded-full bg-gradient-to-br ${theme.gradient} p-8 shadow-xl`}>
                  <Sparkles className="h-12 w-12 text-white" />
                </div>
                <h3 className="mb-3 text-xl font-semibold text-gray-900 dark:text-white">
                  {theme.name}
                </h3>
                <p className="text-muted-foreground mb-6 max-w-md text-center leading-relaxed text-gray-600 dark:text-gray-400">
                  궁금한 것을 물어보거나 도움이 필요한 일이 있으면
                  <br />
                  언제든 말씀해주세요
                </p>
              </div>
            )}

            {messages.map((message, messageIndex) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {/* AI 메시지 */}
                {message.role === 'assistant' && (
                  <div className="flex items-start gap-3 max-w-4xl w-full">
                    <div className="flex-shrink-0 rounded-full bg-blue-100 dark:bg-blue-600/20 p-2">
                      <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-sm p-5 shadow-md border border-gray-100 dark:border-gray-700 relative group">
                        <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                          <button
                            onClick={() => handleCopyMessage(message.content)}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                            title="복사"
                          >
                            <Copy className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                          </button>
                          <button
                            onClick={() => handleFeedback(message.id, true)}
                            className={`p-2 rounded-lg transition-colors ${
                              feedbackStates[message.id] === true
                                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                                : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400'
                            }`}
                            title="좋아요"
                          >
                            <ThumbsUp className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleFeedback(message.id, false)}
                            className={`p-2 rounded-lg transition-colors ${
                              feedbackStates[message.id] === false
                                ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                                : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400'
                            }`}
                            title="싫어요"
                          >
                            <ThumbsDown className="h-4 w-4" />
                          </button>
                        </div>
                        
                        {/* Web Search, RAG, SQL Query 결과 파싱 및 렌더링 */}
                        {(() => {
                          const webSearchMatch = message.content.match(/\[WEB_SEARCH_RESULT\]([\s\S]*?)\[\/WEB_SEARCH_RESULT\]/);
                          const ragSearchMatch = message.content.match(/\[RAG_SEARCH_RESULT\]([\s\S]*?)\[\/RAG_SEARCH_RESULT\]/);
                          const sqlQueryMatch = message.content.match(/\[SQL_QUERY_RESULT\](.*?)\[\/SQL_QUERY_RESULT\]/s);
                          if (sqlQueryMatch) {
                            console.log('✅ SQL_QUERY_RESULT 마커 발견:', sqlQueryMatch[1].substring(0, 200));
                          } else {
                            console.log('❌ SQL_QUERY_RESULT 마커 없음, 전체 content 길이:', message.content.length);
                            // 디버깅: 마커가 있는지 확인
                            if (message.content.includes('[SQL_QUERY_RESULT]')) {
                              console.log('⚠️ [SQL_QUERY_RESULT]는 있지만 파싱 실패. content 일부:', message.content.substring(0, 500));
                            }
                          }
                          if (ragSearchMatch) {
                            console.log('✅ RAG_SEARCH_RESULT 마커 발견');
                          }
                          const mapDataMatch = message.content.match(/\[MAP_DATA\](.*?)\[\/MAP_DATA\]/s);
                          const attractionsDataMatch = message.content.match(/\[ATTRACTIONS_DATA\](.*?)\[\/ATTRACTIONS_DATA\]/s);
                          // ITINERARY_DATA 매칭 (닫는 태그가 있는 경우)
                          let itineraryDataMatch: RegExpMatchArray | string[] | null = message.content.match(/\[ITINERARY_DATA\](.*?)\[\/ITINERARY_DATA\]/s);
                          
                          // 닫는 태그가 없는 경우도 처리 (JSON 객체 끝까지)
                          if (!itineraryDataMatch) {
                            const openTagMatch = message.content.match(/\[ITINERARY_DATA\](\{[\s\S]*)/);
                            if (openTagMatch) {
                              // JSON 파싱 시도해서 유효한 JSON 끝 찾기
                              try {
                                const jsonStr = openTagMatch[1];
                                // 중괄호 균형 맞추기
                                let depth = 0;
                                let endIdx = 0;
                                for (let i = 0; i < jsonStr.length; i++) {
                                  if (jsonStr[i] === '{') depth++;
                                  else if (jsonStr[i] === '}') depth--;
                                  if (depth === 0) {
                                    endIdx = i + 1;
                                    break;
                                  }
                                }
                                if (endIdx > 0) {
                                  itineraryDataMatch = ['', jsonStr.substring(0, endIdx)];
                                }
                              } catch (e) {
                                // 파싱 실패 시 무시
                              }
                            }
                          }
                          
                          // 순수 AI 응답 (마커 제거)
                          // ITINERARY_DATA 태그 제거 (닫는 태그 있는 경우와 없는 경우 모두 처리)
                          let cleanContent = message.content;
                          
                          // [ITINERARY_DATA]...[/ITINERARY_DATA] 패턴 제거
                          const itineraryStartIdx = cleanContent.indexOf('[ITINERARY_DATA]');
                          if (itineraryStartIdx !== -1) {
                            const itineraryEndIdx = cleanContent.indexOf('[/ITINERARY_DATA]');
                            if (itineraryEndIdx !== -1) {
                              // 닫는 태그가 있는 경우
                              cleanContent = cleanContent.slice(0, itineraryStartIdx) + cleanContent.slice(itineraryEndIdx + '[/ITINERARY_DATA]'.length);
                            } else {
                              // 닫는 태그가 없는 경우 - [ITINERARY_DATA] 이후 모두 제거
                              cleanContent = cleanContent.slice(0, itineraryStartIdx);
                            }
                          }
                          
                          cleanContent = cleanContent
                            .replace(/\[WEB_SEARCH_RESULT\][\s\S]*?\[\/WEB_SEARCH_RESULT\]/g, '')
                            .replace(/\[RAG_SEARCH_RESULT\][\s\S]*?\[\/RAG_SEARCH_RESULT\]/g, '')
                            .replace(/\[SQL_QUERY_RESULT\][\s\S]*?\[\/SQL_QUERY_RESULT\]/g, '')
                            .replace(/\[MAP_DATA\][\s\S]*?\[\/MAP_DATA\]/g, '')
                            .replace(/\[ATTRACTIONS_DATA\][\s\S]*?\[\/ATTRACTIONS_DATA\]/g, '')
                            .replace(/\n*성산일출봉 위치\s*$/m, '')
                            .replace(/\n{3,}/g, '\n\n')
                            .trim();
                          
                          // 마커가 제거된 후 빈 내용이면 기본 메시지 표시
                          if (!cleanContent) {
                            cleanContent = "찾았어요! 👇 아래 결과를 확인해보세요 😊";
                          }
                          
                          // 지도 데이터 파싱
                          let parsedMapData = null;
                          if (mapDataMatch) {
                            try {
                              parsedMapData = JSON.parse(mapDataMatch[1]);
                            } catch (e) {
                              console.error('❌ MAP_DATA 파싱 오류:', e);
                            }
                          } else if (attractionsDataMatch) {
                            try {
                              parsedMapData = JSON.parse(attractionsDataMatch[1]);
                            } catch (e) {
                              console.error('❌ ATTRACTIONS_DATA 파싱 오류:', e);
                            }
                          }
                          
                          // 지도 표시 여부 (기본적으로 숨김, 버튼으로만 표시)
                          void parsedMapData?.markers?.length; // 나중에 사용
                          void showMapForMessage[message.id]; // 나중에 사용
                          
                          return (
                            <>
                              {/* AI 응답 (마커 제거된 순수 텍스트) */}
                              <div className="text-gray-800 dark:text-gray-200 pr-24">
                                <ChatMarkdown content={cleanContent} mode="static" />
                              </div>
                              
                              {/* Web Search 결과 UI (artifact 패턴 지원) */}
                              {webSearchMatch && (() => {
                                try {
                                  const webData = JSON.parse(webSearchMatch[1]);
                                  // artifact 패턴: JSON에서 직접 파싱
                                  if (webData.type === 'web_search' && webData.results) {
                                    return (
                                      <WebSearchResult 
                                        query={webData.query || ''} 
                                        results={webData.results.map((r: { title: string; summary: string; url: string }) => ({
                                          title: r.title || '제목 없음',
                                          summary: r.summary || '요약 없음',
                                          url: r.url || '#'
                                        }))} 
                                      />
                                    );
                                  }
                                } catch {
                                  // JSON 파싱 실패 시 기존 마크다운 방식으로 fallback
                                  const markdown = webSearchMatch[1];
                                  const queryMatch = markdown.match(/## 검색어\s*\n\s*(.+)/);
                                  const tableMatch = markdown.match(/\| 제목 \| 요약 \| 출처 \|\s*\n\s*\|---\|---\|---\|\s*\n([\s\S]+?)(?=\n\n|---|$)/);
                                  
                                  if (queryMatch && tableMatch) {
                                    const query = queryMatch[1].trim();
                                    const rows = tableMatch[1].split('\n').filter(r => r.trim() && r.includes('|'));
                                    const results = rows.map(row => {
                                      const cols = row.split('|').map(c => c.trim()).filter(c => c);
                                      if (cols.length >= 3) {
                                        return {
                                          title: cols[0] || '제목 없음',
                                          summary: cols[1] || '요약 없음',
                                          url: cols[2] || '#'
                                        };
                                      }
                                      return null;
                                    }).filter(r => r !== null);
                                    
                                    if (results.length > 0) {
                                      return <WebSearchResult query={query} results={results as { title: string; summary: string; url: string }[]} />;
                                    }
                                  }
                                }
                                return null;
                              })()}
                              
                              {/* RAG Search 결과 UI (artifact 패턴) */}
                              {ragSearchMatch && (() => {
                                try {
                                  const ragData = JSON.parse(ragSearchMatch[1]);
                                  if (ragData.type === 'rag_search' && ragData.results) {
                                    return (
                                      <RAGSearchResult 
                                        query={ragData.query || ''} 
                                        searchType={ragData.search_type || 'vector'}
                                        results={ragData.results} 
                                      />
                                    );
                                  }
                                } catch (e) {
                                  console.error('❌ RAG_SEARCH_RESULT 파싱 오류:', e);
                                }
                                return null;
                              })()}
                              
                              {/* SQL Query 결과 UI (artifact 패턴) */}
                              {sqlQueryMatch && (() => {
                                try {
                                  const sqlData = JSON.parse(sqlQueryMatch[1]);
                                  console.log('📊 SQL 데이터 파싱 성공:', {
                                    hasArtifact: !!sqlData.artifact,
                                    artifactType: sqlData.artifact?.type,
                                    artifactDataExists: !!sqlData.artifact?.data,
                                    documentsCount: sqlData.artifact?.data?.documents?.length || 0,
                                    rowCount: sqlData.row_count,
                                    hasSqlQuery: !!sqlData.sql_query
                                  });
                                  // artifact가 있으면 사용, 없으면 기존 data 사용
                                  const artifact = sqlData.artifact || (sqlData.data?.documents ? {
                                    type: 'sql_agent',
                                    sql_query: sqlData.sql_query,
                                    data: sqlData.data
                                  } : undefined);
                                  console.log('📦 최종 artifact:', {
                                    exists: !!artifact,
                                    hasData: !!artifact?.data,
                                    documentsCount: artifact?.data?.documents?.length || 0
                                  });
                                  
                                  return (
                                    <SQLQueryResult
                                      query={sqlData.query || ''}
                                      sqlQuery={sqlData.sql_query || ''}
                                      artifact={artifact}
                                      data={typeof sqlData.data === 'string' ? sqlData.data : ''}
                                      rowCount={sqlData.row_count || artifact?.data?.documents?.length || 0}
                                    />
                                  );
                                } catch (e) {
                                  console.error('❌ SQL_QUERY_RESULT 파싱 오류:', e);
                                return null;
                                }
                              })()}

                              {/* Itinerary 결과 UI (OR-Tools 기반 수정 지원) */}
                              {itineraryDataMatch && (() => {
                                try {
                                  const itineraryData = JSON.parse(itineraryDataMatch[1]);
                                  
                                  // needs_info인 경우 또는 days가 없는 경우 렌더링하지 않음
                                  if (itineraryData.needs_info || !itineraryData.days || !Array.isArray(itineraryData.days) || itineraryData.days.length === 0) {
                                    return null;
                                  }
                                  
                                  return (
                                    <ItineraryTimeline 
                                      data={itineraryData} 
                                      onAddToSchedule={handleAddItineraryToSchedule}
                                      onAddPlace={handleAddItineraryPlace}
                                      onEditItinerary={(updatedData) => handleEditItinerary(messageIndex, updatedData)}
                                      hideOptimizeButton={true}
                                      hideMapButton={true}
                                    />
                                  );
                                } catch (e) {
                                  console.error('❌ ITINERARY_DATA 파싱 오류:', e);
                                  return null;
                                }
                              })()}
                            </>
                          );
                        })()}
                        
                        {/* 관광지 카드 (ATTRACTIONS_DATA 또는 extractedAttractions 사용) */}
                        {(() => {
                          // 1순위: ATTRACTIONS_DATA에서 파싱한 markers
                          const attractionsDataMatch = message.content.match(/\[ATTRACTIONS_DATA\](.*?)\[\/ATTRACTIONS_DATA\]/s);
                          let markersFromData: any[] = [];
                          if (attractionsDataMatch) {
                            try {
                              const parsed = JSON.parse(attractionsDataMatch[1]);
                              markersFromData = (parsed.markers || []).map((m: any) => ({
                                id: m.id,
                                name: m.name,
                                category: m.category || '',
                                rating: m.rating || 0,
                                price: m.price || '',
                                lat: m.position?.lat,
                                lng: m.position?.lng,
                              }));
                            } catch (e) {
                              // 파싱 실패시 무시
                            }
                          }
                          
                          // 2순위: extractedAttractions 또는 message.attractions
                          const extractedAttractions = attractionsForMessage[message.id];
                          const attractionsToShow = markersFromData.length > 0 
                            ? markersFromData 
                            : (extractedAttractions || message.attractions || []);
                          
                          if (attractionsToShow.length === 0) return null;
                          
                          return (
                            <div className="mt-4 space-y-3">
                              {attractionsToShow.map((attraction: any, idx: number) => (
                                <div
                                  key={idx}
                                  className={`bg-gradient-to-br ${theme.cardBg} dark:from-gray-700 dark:to-gray-600 rounded-xl p-4 hover:shadow-lg transition-all border border-gray-200 dark:border-gray-600 group`}
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3 flex-1">
                                      <span className="text-3xl">
                                        {attraction.emoji || 
                                         (attraction.category === '산/오름' ? '🏔️' :
                                          attraction.category === '해변' ? '🏖️' :
                                          attraction.category === '폭포' ? '💧' :
                                          attraction.category === '박물관/체험' ? '🎨' :
                                          attraction.category === '문화/자연' ? '🌿' :
                                          attraction.category === '테마파크' ? '🎢' : '📍')}
                                      </span>
                                      <div>
                                        <h4 className={`font-bold text-gray-900 dark:text-white ${theme.hoverText} transition-colors`}>
                                          {attraction.name}
                                        </h4>
                                        <div className="flex items-center gap-3 text-xs text-gray-600 dark:text-gray-400 mt-1">
                                          <span>📍 {attraction.category}</span>
                                          {attraction.rating && <span>⭐ {attraction.rating}</span>}
                                          {attraction.price && <span>💰 {attraction.price}</span>}
                                          {attraction.time && <span>⏱️ {attraction.time}</span>}
                                        </div>
                                      </div>
                                    </div>
                                    <button 
                                      onClick={() => handleAddAttraction(attraction)}
                                      className={`px-4 py-2 bg-gradient-to-r ${theme.buttonGradient} text-white rounded-lg font-bold text-sm shadow-md hover:shadow-lg transition-all`}
                                    >
                                      추가
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          );
                        })()}
                      </div>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 ml-1">
                        {message.timestamp.toLocaleTimeString('ko-KR', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                )}

                {/* 사용자 메시지 */}
                {message.role === 'user' && (
                  <div className="flex items-start gap-3 max-w-xl ml-auto">
                    <div className="flex-1 text-right">
                      <div className={`inline-block bg-gradient-to-r ${theme.userBubble} text-white rounded-2xl rounded-tr-sm p-4 shadow-md`}>
                        <p className="whitespace-pre-line leading-relaxed break-words">{message.content}</p>
                      </div>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 mr-1">
                        {message.timestamp.toLocaleTimeString('ko-KR', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                    <div className="flex-shrink-0 rounded-full bg-teal-100 dark:bg-teal-600/20 p-2">
                      <MessageCircle className="h-4 w-4 text-teal-600 dark:text-teal-400" />
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* AI Thinking 표시 (도구 실행 중) */}
            {isStreaming && aiReasoning && (
              <div className="flex justify-start mb-3">
                <div className="flex items-center gap-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl px-4 py-3 border border-gray-200 dark:border-gray-700">
                  <div className="relative">
                    <div className="h-5 w-5 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
                  </div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {aiReasoning}
                  </span>
                </div>
              </div>
            )}

            {/* 스트리밍 중 메시지 */}
            {isStreaming && streamingText && (
              <div className="flex justify-start">
                <div className="flex items-start gap-3 max-w-4xl w-full">
                  <div className="flex-shrink-0 rounded-full bg-blue-100 dark:bg-blue-600/20 p-2">
                    <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-sm p-5 shadow-md border border-gray-100 dark:border-gray-700">
                      {(() => {
                        const webSearchMatch = streamingText.match(/\[WEB_SEARCH_RESULT\]([\s\S]*?)\[\/WEB_SEARCH_RESULT\]/);
                        const ragSearchMatch = streamingText.match(/\[RAG_SEARCH_RESULT\]([\s\S]*?)\[\/RAG_SEARCH_RESULT\]/);
                        
                        // ITINERARY_DATA 매칭 (닫는 태그가 있는 경우)
                        let itineraryDataMatch: RegExpMatchArray | string[] | null = streamingText.match(/\[ITINERARY_DATA\](.*?)\[\/ITINERARY_DATA\]/s);
                        
                        // 닫는 태그가 없는 경우도 처리
                        if (!itineraryDataMatch) {
                          const openTagMatch = streamingText.match(/\[ITINERARY_DATA\](\{[\s\S]*)/);
                          if (openTagMatch) {
                            try {
                              const jsonStr = openTagMatch[1];
                              let depth = 0;
                              let endIdx = 0;
                              for (let i = 0; i < jsonStr.length; i++) {
                                if (jsonStr[i] === '{') depth++;
                                else if (jsonStr[i] === '}') depth--;
                                if (depth === 0) {
                                  endIdx = i + 1;
                                  break;
                                }
                              }
                              if (endIdx > 0) {
                                itineraryDataMatch = ['', jsonStr.substring(0, endIdx)];
                              }
                            } catch {
                              // 파싱 실패 시 무시
                            }
                          }
                        }
                        
                        // ITINERARY_DATA 태그 제거
                        let cleanContent = streamingText;
                        const itineraryStartIdx = cleanContent.indexOf('[ITINERARY_DATA]');
                        if (itineraryStartIdx !== -1) {
                          const itineraryEndIdx = cleanContent.indexOf('[/ITINERARY_DATA]');
                          if (itineraryEndIdx !== -1) {
                            cleanContent = cleanContent.slice(0, itineraryStartIdx) + cleanContent.slice(itineraryEndIdx + '[/ITINERARY_DATA]'.length);
                          } else {
                            cleanContent = cleanContent.slice(0, itineraryStartIdx);
                          }
                        }
                        
                        cleanContent = cleanContent
                          .replace(/\[WEB_SEARCH_RESULT\][\s\S]*?\[\/WEB_SEARCH_RESULT\]/g, '')
                          .replace(/\[RAG_SEARCH_RESULT\][\s\S]*?\[\/RAG_SEARCH_RESULT\]/g, '')
                          .replace(/\[SQL_QUERY_RESULT\][\s\S]*?\[\/SQL_QUERY_RESULT\]/g, '')
                          .replace(/\[MAP_DATA\][\s\S]*?\[\/MAP_DATA\]/g, '')
                          .replace(/\[ATTRACTIONS_DATA\][\s\S]*?\[\/ATTRACTIONS_DATA\]/g, '')
                          .replace(/\n*성산일출봉 위치\s*$/m, '')
                          .replace(/\n{3,}/g, '\n\n')
                          .trim();
                        
                        return (
                          <>
                            {/* AI 응답 텍스트 */}
                            <div className="text-gray-800 dark:text-gray-200">
                              <ChatMarkdown content={cleanContent} mode="stream" />
                              <span className="inline-block w-2 h-4 bg-gray-400 dark:bg-gray-500 animate-pulse ml-1" />
                            </div>
                            
                            {/* Web Search 결과 (스트리밍 중, artifact 패턴) */}
                            {webSearchMatch && (() => {
                              try {
                                const webData = JSON.parse(webSearchMatch[1]);
                                if (webData.type === 'web_search' && webData.results) {
                                  return (
                                    <WebSearchResult 
                                      query={webData.query || ''} 
                                      results={webData.results.map((r: { title: string; summary: string; url: string }) => ({
                                        title: r.title || '제목 없음',
                                        summary: r.summary || '요약 없음',
                                        url: r.url || '#'
                                      }))} 
                                    />
                                  );
                                }
                              } catch {
                                // JSON 파싱 실패 시 무시
                              }
                              return null;
                            })()}
                            
                            {/* RAG Search 결과 (스트리밍 중, artifact 패턴) */}
                            {ragSearchMatch && (() => {
                              try {
                                const ragData = JSON.parse(ragSearchMatch[1]);
                                if (ragData.type === 'rag_search' && ragData.results) {
                                  return (
                                    <RAGSearchResult 
                                      query={ragData.query || ''} 
                                      searchType={ragData.search_type || 'vector'}
                                      results={ragData.results} 
                                    />
                                  );
                                }
                              } catch {
                                // JSON 파싱 실패 시 무시
                              }
                              return null;
                            })()}

                            {/* Itinerary 결과 (스트리밍 중) */}
                            {itineraryDataMatch && (() => {
                              try {
                                const itineraryData = JSON.parse(itineraryDataMatch[1]);
                                return (
                                  <ItineraryTimeline 
                                    data={itineraryData}
                                    onAddToSchedule={handleAddItineraryToSchedule}
                                    onAddPlace={handleAddItineraryPlace}
                                    hideOptimizeButton={true}
                                    hideMapButton={true}
                                  />
                                );
                              } catch (e) {
                                return null;
                              }
                            })()}
                          </>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 로딩 (스트리밍 시작 전 또는 스트리밍 중이지만 텍스트가 없을 때) */}
            {isLoading && (!streamingText || streamingText.length === 0) && (
              <div className="flex justify-start">
                <div className="flex items-start gap-3 max-w-2xl">
                  <div className="flex-shrink-0 rounded-full bg-blue-100 dark:bg-blue-600/20 p-2">
                    <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-sm p-4 shadow-md border border-gray-100 dark:border-gray-700">
                    <TypingIndicator />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 빠른 질문 */}
        {messages.length === 1 && (
          <div className="border-t-2 border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm px-6 py-4">
            <p className="text-sm font-bold text-gray-600 dark:text-gray-400 mb-3">💬 빠른 질문</p>
            <div className="flex flex-wrap gap-2">
              {quickMessages.map((msg, idx) => (
                <button
                  key={idx}
                  onClick={() => setInputMessage(msg)}
                  className={`px-4 py-2 bg-white dark:bg-gray-700 ${theme.lightHoverBg} text-gray-700 dark:text-gray-300 ${theme.lightText} rounded-xl text-sm font-medium transition-all border border-gray-200 dark:border-gray-600 ${theme.activeBorder} shadow-sm hover:shadow-md`}
                >
                  {msg}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 입력 영역 */}
        <div className="border-t-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-4 shadow-lg">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                onCompositionStart={() => {
                  isComposingRef.current = true;
                }}
                onCompositionEnd={() => {
                  requestAnimationFrame(() => {
                    isComposingRef.current = false;
                  });
                }}
                placeholder="메시지를 입력하세요... (Enter: 전송, Shift+Enter: 줄바꿈)"
                rows={1}
                className={`w-full px-5 py-4 border-2 border-gray-300 dark:border-gray-600 rounded-2xl focus:outline-none focus:ring-4 ${theme.focusRing} resize-none bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500`}
                style={{ minHeight: '56px', maxHeight: '120px', overflowY: 'auto' }}
              />
            </div>
            <button
              data-send-button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading || isStreaming}
              className={`px-6 py-4 bg-gradient-to-r ${theme.buttonGradient} text-white rounded-2xl font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg hover:shadow-xl transition-all disabled:hover:shadow-lg`}
            >
              {isLoading ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <>
                  <Send size={20} />
                  <span className="hidden sm:inline">전송</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 우측: 지도 & 일정 패널 (itinerary 챗봇에서만 표시) */}
      {botId === 'itinerary' && showRightPanel && (
        <div className="w-96 h-full bg-white dark:bg-gray-800 border-l-2 border-gray-200 dark:border-gray-700 flex flex-col shadow-xl overflow-hidden">
          {/* 지도 영역 - 항상 카카오 지도 표시 */}
          <div className="h-1/2 border-b-2 border-gray-200 dark:border-gray-700 relative">
            <KakaoMap
              className="absolute inset-0"
              hideRoutes={true}  // 챗봇에서는 경로(선) 숨김, 마커만 표시
              mapData={{
                markers: selectedAttractions.map((attr, idx) => ({
                  id: attr.id || idx,
                  position: { lat: attr.lat, lng: attr.lng },
                  label: String(idx + 1),
                  name: attr.name,
                  category: attr.category || '',
                  rating: attr.rating || 0,
                  price: attr.price || '',
                  day: attr.day || 1, // 요일 정보 (기본: Day 1)
                  order: idx + 1, // 순서
                })),
                center: (() => {
                  // 🔥 유효한 좌표(제주도 범위)만 필터링
                  const valid = selectedAttractions.filter(
                    (a: any) => a.lat && a.lng && a.lat > 30 && a.lat < 40 && a.lng > 120 && a.lng < 130
                  );
                  if (valid.length > 0) {
                    return {
                      lat: valid.reduce((sum, a) => sum + a.lat, 0) / valid.length,
                      lng: valid.reduce((sum, a) => sum + a.lng, 0) / valid.length,
                    };
                  }
                  return { lat: 33.45, lng: 126.57 }; // 제주도 중심
                })(),
                zoom: selectedAttractions.length > 0 ? 10 : 9,
                showDayColors: true,
              }}
            />
            {/* 빈 지도일 때 안내 오버레이 */}
            {selectedAttractions.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl p-6 text-center shadow-xl border border-gray-200 dark:border-gray-700">
                  <div className="text-5xl mb-3">📍</div>
                  <p className="text-gray-700 dark:text-gray-200 font-bold text-lg mb-1">여행지를 추가해보세요</p>
                  <p className="text-gray-500 dark:text-gray-400 text-sm">
                    AI 추천에서 "추가" 버튼을 눌러<br />지도에 표시하세요
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* 일정 영역 */}
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            <div className={`bg-gradient-to-r ${theme.userBubble} px-6 py-4 flex items-center justify-between`}>
              <div className="flex items-center gap-3">
                <Calendar className="text-white" size={20} />
                <h2 className="text-white font-black text-lg">내 일정</h2>
              </div>
              <div className="flex items-center gap-2">
                <div className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full">
                  <span className="text-white font-bold text-sm">{selectedAttractions.length}곳</span>
                </div>
              </div>
            </div>
            
            <div className="flex-1 min-h-0 overflow-y-auto p-4">
              {selectedAttractions.length === 0 ? (
                <div className="h-full flex items-center justify-center text-center px-4">
                  <div>
                    <div className="text-5xl mb-4">📍</div>
                    <p className="text-gray-600 dark:text-gray-400 font-medium mb-2">
                      아직 선택한 관광지가 없어요
                    </p>
                    <p className="text-gray-500 dark:text-gray-500 text-sm">
                      AI 추천 중에서<br />마음에 드는 곳을 추가해보세요!
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {selectedAttractions.map((attraction, idx) => (
                    <div
                      key={idx}
                      className={`bg-gradient-to-br ${theme.cardBg} dark:from-gray-700 dark:to-gray-600 rounded-xl p-4 border-2 border-gray-200 dark:border-gray-600 hover:${theme.activeBorder} transition-all group`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{attraction.emoji}</span>
                          <div>
                            <h3 className="font-bold text-gray-900 dark:text-white">{attraction.name}</h3>
                            <p className="text-xs text-gray-600 dark:text-gray-400">{attraction.category}</p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleRemoveAttraction(attraction.name)}
                          className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors group"
                        >
                          <X size={16} className="text-gray-400 group-hover:text-red-600" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                        <span>⏱️ {attraction.time}</span>
                        <span>•</span>
                        <span>💰 {attraction.price}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 일정 저장 버튼 */}
            {selectedAttractions.length > 0 && (
              <div className="p-4 border-t-2 border-gray-200 dark:border-gray-700">
                <button 
                  onClick={handleSaveSchedule}
                  className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all"
                >
                  <Save size={20} />
                  일정으로 저장하기
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatPage;
