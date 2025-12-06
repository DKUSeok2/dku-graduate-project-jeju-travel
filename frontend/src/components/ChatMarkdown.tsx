/**
 * Chat Markdown Component
 * AI 응답을 마크다운으로 렌더링
 */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

type ChatMarkdownProps = {
  content: string;
  mode?: 'static' | 'stream';
};

// 마크다운 펜스 제거 (```markdown으로 감싸진 경우)
function unwrapMarkdownFence(text: string): string {
  if (!text) {
    return '';
  }
  const startsWithFence = /^```(?:markdown|md)\s*\r?\n/i;
  if (startsWithFence.test(text)) {
    let content = text.replace(startsWithFence, '');
    content = content.replace(/\r?\n```\s*$/, '');
    return content;
  }
  return text;
}

export const ChatMarkdown: React.FC<ChatMarkdownProps> = ({ content }) => {
  const processedContent = unwrapMarkdownFence(content);

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // 코드 블록 스타일링
          code: ({ node, inline, className, children, ...props }: any) => {
            if (inline) {
              return (
                <code
                  className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code
                className="block p-4 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-x-auto text-sm font-mono"
                {...props}
              >
                {children}
              </code>
            );
          },
          // 링크 스타일링
          a: ({ node, ...props }: any) => (
            <a
              className="text-blue-600 dark:text-blue-400 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),
          // 리스트 스타일링
          ul: ({ node, ...props }: any) => (
            <ul className="list-disc list-inside space-y-1 my-2" {...props} />
          ),
          ol: ({ node, ...props }: any) => (
            <ol className="list-decimal list-inside space-y-1 my-2" {...props} />
          ),
          // 제목 스타일링
          h1: ({ node, ...props }: any) => (
            <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />
          ),
          h2: ({ node, ...props }: any) => (
            <h2 className="text-xl font-bold mt-3 mb-2" {...props} />
          ),
          h3: ({ node, ...props }: any) => (
            <h3 className="text-lg font-semibold mt-2 mb-1" {...props} />
          ),
          // 테이블 스타일링
          table: ({ node, ...props }: any) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600" {...props} />
            </div>
          ),
          th: ({ node, ...props }: any) => (
            <th className="border border-gray-300 dark:border-gray-600 px-4 py-2 bg-gray-100 dark:bg-gray-800 font-semibold" {...props} />
          ),
          td: ({ node, ...props }: any) => (
            <td className="border border-gray-300 dark:border-gray-600 px-4 py-2" {...props} />
          ),
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};

export default ChatMarkdown;

