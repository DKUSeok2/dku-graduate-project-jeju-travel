import { useState } from 'react';
import { Search, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

interface WebSearchResultItem {
  url: string;
  summary: string;
  title: string;
}

interface WebSearchResultProps {
  query: string;
  results: WebSearchResultItem[];
}

export function WebSearchResult({ query, results }: WebSearchResultProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  return (
    <div className="mt-3 rounded-xl border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-yellow-50 dark:from-orange-900/10 dark:to-yellow-900/10 dark:border-orange-700 shadow-sm">
      <div className={`p-4 ${isExpanded ? 'border-b-2 border-orange-200 dark:border-orange-700' : ''}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-orange-500 rounded-lg">
              <Search className="h-4 w-4 text-white" />
            </div>
            <div>
              <span className="text-sm font-bold text-orange-700 dark:text-orange-400">
                실시간 검색 결과
              </span>
              <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                {results.length}개 발견
              </span>
            </div>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-3 py-1.5 text-xs font-medium flex items-center gap-1 rounded-lg bg-orange-100 hover:bg-orange-200 dark:bg-orange-800 dark:hover:bg-orange-700 text-orange-700 dark:text-orange-200 transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-3 w-3" />
                접기
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3" />
                자세히 보기
              </>
            )}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-4 bg-white dark:bg-gray-900">
          {/* 검색어 */}
          <div className="mb-4 px-3 py-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
            <span className="text-xs text-gray-600 dark:text-gray-400">검색어:</span>
            <span className="ml-2 text-sm font-semibold text-orange-700 dark:text-orange-300">{query}</span>
          </div>

          {/* 결과 목록 */}
          <div className="space-y-3">
            {results.map((result, index) => (
              <div
                key={index}
                className="rounded-lg border border-gray-200 bg-white p-3 dark:bg-gray-800 dark:border-gray-600 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-3 mb-2">
                  <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-orange-500 text-white font-bold text-xs">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    {result.title && (
                      <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-1 leading-tight">
                        {result.title}
                      </h4>
                    )}
                    <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed mb-2">
                      {result.summary}
                    </p>
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-orange-600 hover:text-orange-700 dark:text-orange-400 dark:hover:text-orange-300 font-medium"
                    >
                      <ExternalLink className="h-3 w-3" />
                      출처 보기
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

