import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 text-white mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* 프로젝트 정보 */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <span className="text-2xl">🏝️</span>
              <h3 className="text-lg font-bold">제주 여행 플래너</h3>
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">
              AI 기반 제주도 여행 일정 추천 시스템
            </p>
          </div>

          {/* 기술 스택 */}
          <div>
            <h4 className="font-semibold mb-4 text-jeju-orange-400">기술 스택</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>• Python, FastAPI, LangGraph</li>
              <li>• React, TypeScript, Tailwind</li>
              <li>• PostgreSQL, Elasticsearch</li>
              <li>• OpenAI GPT-4</li>
            </ul>
          </div>

          {/* 링크 */}
          <div>
            <h4 className="font-semibold mb-4 text-jeju-blue-400">프로젝트</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="https://github.com" className="hover:text-white transition-colors">
                  GitHub Repository
                </a>
              </li>
              <li>
                <a href="/docs" className="hover:text-white transition-colors">
                  API 문서
                </a>
              </li>
              <li>
                <a href="/about" className="hover:text-white transition-colors">
                  프로젝트 소개
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-500">
          <p>© 2025 Jeju Travel Planner</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

