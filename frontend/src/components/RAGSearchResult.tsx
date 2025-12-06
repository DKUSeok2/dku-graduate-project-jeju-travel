import { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, MapPin, Star, FileText } from 'lucide-react';

interface RAGSearchResultItem {
  id: number;
  title: string;
  category: string;
  rating: number;
  address: string;
  lat: number | null;
  lng: number | null;
  score: number;
  description: string;
}

interface RAGSearchResultProps {
  query: string;
  searchType: string;
  results: RAGSearchResultItem[];
}

export function RAGSearchResult({ query, searchType, results }: RAGSearchResultProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  // 카테고리별 색상
  const getCategoryColor = (category: string) => {
    if (category.includes('맛집') || category.includes('음식')) return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
    if (category.includes('카페')) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400';
    if (category.includes('숙박') || category.includes('호텔')) return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400';
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
  };

  return (
    <div className="mt-3 rounded-xl border-2 border-emerald-200 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/10 dark:to-teal-900/10 dark:border-emerald-700 shadow-sm">
      <div className={`p-4 ${isExpanded ? 'border-b-2 border-emerald-200 dark:border-emerald-700' : ''}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-emerald-500 rounded-lg">
              <BookOpen className="h-4 w-4 text-white" />
            </div>
            <div>
              <span className="text-sm font-bold text-emerald-700 dark:text-emerald-400">
                RAG 검색 결과
              </span>
              <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                {results.length}개 장소 ({searchType})
              </span>
            </div>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-3 py-1.5 text-xs font-medium flex items-center gap-1 rounded-lg bg-emerald-100 hover:bg-emerald-200 dark:bg-emerald-800 dark:hover:bg-emerald-700 text-emerald-700 dark:text-emerald-200 transition-colors"
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
          <div className="mb-4 px-3 py-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
            <span className="text-xs text-gray-600 dark:text-gray-400">검색 쿼리:</span>
            <span className="ml-2 text-sm font-semibold text-emerald-700 dark:text-emerald-300">{query}</span>
          </div>

          {/* 결과 목록 */}
          <div className="space-y-3">
            {results.map((result) => (
              <div
                key={result.id}
                className="rounded-lg border border-gray-200 bg-white p-4 dark:bg-gray-800 dark:border-gray-600 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 text-white font-bold text-xs shadow">
                    {result.id}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100">
                        {result.title}
                      </h4>
                      {result.category && (
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(result.category)}`}>
                          {result.category}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mb-2">
                      {result.rating > 0 && (
                        <span className="flex items-center gap-1">
                          <Star className="h-3.5 w-3.5 text-yellow-500 fill-yellow-500" />
                          <span className="font-medium text-gray-700 dark:text-gray-300">{result.rating.toFixed(1)}</span>
                        </span>
                      )}
                      {result.address && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5 text-gray-400" />
                          <span className="truncate max-w-[200px]">{result.address}</span>
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <FileText className="h-3.5 w-3.5 text-gray-400" />
                        <span>관련도: {(result.score * 100).toFixed(0)}%</span>
                      </span>
                    </div>
                    
                    {result.description && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed line-clamp-2">
                        {result.description.substring(0, 150)}...
                      </p>
                    )}
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


