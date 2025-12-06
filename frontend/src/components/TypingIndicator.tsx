/**
 * Typing Indicator Component
 * AI 응답 대기 중일 때 표시되는 애니메이션 인디케이터
 */
import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-center gap-2 px-4 py-3">
      {/* 텍스트와 점들 */}
      <span className="text-gray-700 dark:text-gray-200 text-sm font-medium">생각하는 중</span>
      <div className="flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="inline-flex h-1.5 w-1.5 rounded-full bg-gray-500 dark:bg-gray-400"
            style={{
              animation: 'pulse 1.4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default TypingIndicator;

