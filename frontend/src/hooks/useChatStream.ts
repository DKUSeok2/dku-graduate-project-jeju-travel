/**
 * useChatStream Hook
 * 실시간 스트리밍 채팅을 위한 커스텀 훅
 */
import { useState, useCallback, useRef } from 'react';
import { safeLocalStorage } from '../utils/storage';

export interface StreamMessage {
  type: 'AIMessageChunk' | 'done' | 'error';
  content: string;
  id: string;
}

export interface UseChatStreamParams {
  onChunk?: (chunk: string) => void;
  onError?: (error: Error) => void;
  onCompleted?: (fullResponse: string) => void;
}

export const useChatStream = ({
  onChunk,
  onError,
  onCompleted,
}: UseChatStreamParams) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startChat = useCallback(
    async (sessionId: string, message: string, botId: string = 'itinerary') => {
      if (isStreaming) {
        console.warn('이미 스트리밍 중입니다');
        return;
      }

      setIsStreaming(true);
      abortControllerRef.current = new AbortController();
      
      let fullResponse = '';

      try {
        const token = safeLocalStorage.getItem('access_token');
        const apiUrl = import.meta.env.PROD 
          ? 'https://jeju-travel-chatbot-production.up.railway.app'
          : 'http://localhost:8000';
        const response = await fetch(
          `${apiUrl}/api/chat/sessions/${sessionId}/stream`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ message, bot_id: botId }),
            signal: abortControllerRef.current.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No readable stream available');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = line.slice(6); // 'data: ' 제거
                const message: StreamMessage = JSON.parse(data);

                if (message.type === 'AIMessageChunk') {
                  fullResponse += message.content;
                  onChunk?.(message.content);
                } else if (message.type === 'done') {
                  onCompleted?.(fullResponse);
                  break;
                } else if (message.type === 'error') {
                  // 에러 메시지 처리
                  const error = new Error(message.content);
                  onError?.(error);
                  break;
                }
              } catch (error) {
                console.warn('Failed to parse stream message:', line, error);
              }
            }
          }
        }
      } catch (error: any) {
        if (error.name === 'AbortError') {
          console.log('Stream aborted');
          return;
        }
        console.error('Stream error:', error);
        onError?.(error instanceof Error ? error : new Error('Unknown error'));
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [isStreaming, onChunk, onError, onCompleted]
  );

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  return [startChat, isStreaming, stopStream] as const;
};

