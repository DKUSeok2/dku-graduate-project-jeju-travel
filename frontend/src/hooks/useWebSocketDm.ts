/**
 * useWebSocketDm - DM용 WebSocket 훅
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { safeLocalStorage } from '../utils/storage';

export interface DmWsMessage {
  id?: number;
  sender_id: number;
  sender_name?: string;
  content: string;
  created_at?: string;
}

interface UseWebSocketDmOptions {
  onMessage?: (message: DmWsMessage) => void;
  onConnected?: (userId: number, userName: string) => void;
  onError?: (error: string) => void;
}

export const useWebSocketDm = (
  conversationId: number | null,
  options: UseWebSocketDmOptions = {}
) => {
  const [messages, setMessages] = useState<DmWsMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  
  // options를 ref로 관리하여 불필요한 재연결 방지
  const optionsRef = useRef(options);
  optionsRef.current = options;
  
  // 연결 시도 중인지 추적
  const isConnectingRef = useRef(false);

  const connect = useCallback(() => {
    if (!conversationId) return;
    
    // 이미 연결 시도 중이면 무시
    if (isConnectingRef.current) return;
    
    const token = safeLocalStorage.getItem('access_token');
    if (!token) {
      optionsRef.current.onError?.('로그인이 필요합니다');
      return;
    }

    // 이미 연결 중이거나 연결된 상태면 무시
    if (wsRef.current?.readyState === WebSocket.CONNECTING || 
        wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    isConnectingRef.current = true;
    setConnecting(true);

    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = baseUrl.replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/dm/${conversationId}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      setConnecting(false);
      isConnectingRef.current = false;
      reconnectAttemptsRef.current = 0;
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setConnected(false);
      setConnecting(false);
      isConnectingRef.current = false;
      wsRef.current = null;

      // 정상적인 종료가 아니면 재연결 시도
      if (event.code !== 1000 && event.code !== 4001 && event.code !== 4003 && event.code !== 4004) {
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnecting(false);
      isConnectingRef.current = false;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'connected':
            optionsRef.current.onConnected?.(data.user_id, data.user_name);
            break;
            
          case 'message':
            const msg: DmWsMessage = {
              id: data.id,
              sender_id: data.sender_id,
              sender_name: data.sender_name,
              content: data.content,
              created_at: data.created_at,
            };
            // 중복 메시지 방지: 같은 id가 이미 있으면 추가하지 않음
            setMessages(prev => {
              if (msg.id && prev.some(m => m.id === msg.id)) {
                return prev;
              }
              return [...prev, msg];
            });
            optionsRef.current.onMessage?.(msg);
            break;
            
          case 'error':
            console.error('WebSocket server error:', data.message);
            optionsRef.current.onError?.(data.message);
            break;
            
          case 'pong':
            // ping-pong 응답
            break;
            
          default:
            console.log('Unknown message type:', data.type);
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };
  }, [conversationId]); // options 제거 - ref로 관리

  // 연결 관리
  useEffect(() => {
    if (conversationId) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
      isConnectingRef.current = false;
      setConnected(false);
      setMessages([]);
    };
  }, [conversationId, connect]);

  // 메시지 전송
  const sendMessage = useCallback((content: string, context?: Record<string, any>) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return false;
    }

    wsRef.current.send(JSON.stringify({
      type: 'message',
      content,
      context,
    }));
    return true;
  }, []);

  // 수동 재연결
  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  // 메시지 목록 초기화 (기존 메시지 로드 시 사용)
  const setInitialMessages = useCallback((msgs: DmWsMessage[]) => {
    setMessages(msgs);
  }, []);

  return {
    messages,
    connected,
    connecting,
    sendMessage,
    reconnect,
    setInitialMessages,
  };
};

export default useWebSocketDm;

