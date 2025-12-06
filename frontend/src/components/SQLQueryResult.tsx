import { useState } from 'react';
import { Database, ChevronDown, ChevronUp, Code, Star, ParkingSquare, Baby, Check, X } from 'lucide-react';

// artifact 데이터 구조
interface PlaceData {
  id?: number;
  name: string;
  category?: string;
  rating?: number | null;
  address?: string;
  parking?: boolean;
  kid_friendly?: boolean;
  [key: string]: unknown;
}

interface SQLArtifact {
  type: string;
  sql_query: string;
  data_id: string;
  data: {
    documents: PlaceData[];
    parent_columns: string[];
  };
}

interface SQLQueryResultProps {
  query: string;
  sqlQuery: string;
  artifact?: SQLArtifact;
  data?: string;
  rowCount: number;
}

export function SQLQueryResult({ sqlQuery, artifact, data, rowCount }: SQLQueryResultProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  const documents = artifact?.data?.documents || [];
  const hasArtifact = documents.length > 0;

  // 테이블에 표시할 컬럼 결정
  const hasParking = documents.some(d => d.parking !== undefined);
  const hasKidFriendly = documents.some(d => d.kid_friendly !== undefined);

  return (
    <div className="mt-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm overflow-hidden">
      {/* 헤더 */}
      <div className="px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-white" />
          <div>
            <span className="text-sm font-bold text-white">
              🍽️ 추천 결과
            </span>
            <span className="ml-2 px-2 py-0.5 text-xs bg-white/20 text-white rounded-full">
              {hasArtifact ? documents.length : rowCount}개
            </span>
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-3 py-1 text-xs font-medium flex items-center gap-1 rounded-lg bg-white/20 hover:bg-white/30 text-white transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="h-3 w-3" />
              접기
            </>
          ) : (
            <>
              <ChevronDown className="h-3 w-3" />
              펼치기
            </>
          )}
        </button>
      </div>

      {isExpanded && (
        <div className="p-4">
          {/* 테이블 형태 렌더링 */}
          {hasArtifact ? (
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th scope="col" className="px-3 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider w-12">
                      #
                    </th>
                    <th scope="col" className="px-3 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                      장소명
                    </th>
                    <th scope="col" className="px-3 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                      카테고리
                    </th>
                    <th scope="col" className="px-3 py-3 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider w-20">
                      평점
                    </th>
                    {hasParking && (
                      <th scope="col" className="px-3 py-3 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider w-16" title="주차">
                        <ParkingSquare className="h-4 w-4 mx-auto" />
                      </th>
                    )}
                    {hasKidFriendly && (
                      <th scope="col" className="px-3 py-3 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider w-16" title="아이동반">
                        <Baby className="h-4 w-4 mx-auto" />
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-100 dark:divide-gray-800">
                  {documents.map((place, idx) => (
                    <tr 
                      key={place.id || idx} 
                      className="hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <td className="px-3 py-3 text-sm text-gray-400 dark:text-gray-500 font-mono">
                        {idx + 1}
                      </td>
                      <td className="px-3 py-3">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {place.name}
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        <span className="inline-flex px-2 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                          {place.category || '-'}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-center">
                        {place.rating ? (
                          <div className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                            <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                            <span className="text-sm font-bold text-yellow-600 dark:text-yellow-400">
                              {Number(place.rating).toFixed(1)}
                            </span>
                          </div>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      {hasParking && (
                        <td className="px-3 py-3 text-center">
                          {place.parking ? (
                            <Check className="h-4 w-4 mx-auto text-green-500" />
                          ) : (
                            <X className="h-4 w-4 mx-auto text-gray-300 dark:text-gray-600" />
                          )}
                        </td>
                      )}
                      {hasKidFriendly && (
                        <td className="px-3 py-3 text-center">
                          {place.kid_friendly ? (
                            <Check className="h-4 w-4 mx-auto text-pink-500" />
                          ) : (
                            <X className="h-4 w-4 mx-auto text-gray-300 dark:text-gray-600" />
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : data ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {data}
            </div>
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              조회 결과가 없습니다.
            </div>
          )}

          {/* SQL 쿼리 (접힌 상태) */}
          <details className="mt-4">
            <summary className="flex items-center gap-2 cursor-pointer text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <Code className="h-3 w-3" />
              SQL 쿼리 보기
            </summary>
            <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg overflow-x-auto border border-gray-200 dark:border-gray-700">
              <code className="text-xs font-mono text-gray-700 dark:text-gray-300 whitespace-pre">
                {sqlQuery}
              </code>
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
