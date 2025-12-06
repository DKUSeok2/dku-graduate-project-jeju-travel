import React from 'react';
import { Github, Database, Cpu, Zap } from 'lucide-react';

const AboutPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 헤더 */}
        <div className="text-center mb-16">
          <div className="text-6xl mb-6">🏝️</div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">제주 AI 여행 플래너</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            LangGraph 기반 멀티 에이전트 시스템을 활용한
            <br />
            제주도 여행 일정 추천 AI 챗봇
          </p>
        </div>

        {/* AI 에이전트 시스템 구조 */}
        <div className="card-jeju p-8 mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            🤖 AI 에이전트 시스템 구조
          </h2>

          {/* 다이어그램 */}
          <div className="max-w-4xl mx-auto">
            {/* Supervisor */}
            <div className="flex justify-center mb-8">
              <div className="bg-gradient-to-r from-jeju-blue-500 to-jeju-blue-600 text-white px-8 py-4 rounded-2xl shadow-lg">
                <div className="text-center">
                  <div className="text-3xl mb-2">🧠</div>
                  <div className="font-bold text-lg">Supervisor Agent</div>
                  <div className="text-sm opacity-90">중앙 조율 에이전트</div>
                </div>
              </div>
            </div>

            {/* 화살표 */}
            <div className="flex justify-center mb-8">
              <div className="text-4xl text-gray-400">↓</div>
            </div>

            {/* Tool Agents */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { emoji: '📚', name: 'RAG Agent', desc: '관광지 검색' },
                { emoji: '🗄️', name: 'SQL Agent', desc: 'DB 조회' },
                { emoji: '🌐', name: 'Web Search', desc: '실시간 검색' },
                { emoji: '🚗', name: 'Route Optimizer', desc: '경로 최적화' },
                { emoji: '🗺️', name: 'Map Visualization', desc: '지도 시각화' },
              ].map((agent) => (
                <div
                  key={agent.name}
                  className="bg-gray-50 border-2 border-gray-200 p-4 rounded-xl text-center hover:border-jeju-orange-300 hover:bg-jeju-orange-50 transition-all"
                >
                  <div className="text-3xl mb-2">{agent.emoji}</div>
                  <div className="font-bold text-gray-900 text-sm mb-1">{agent.name}</div>
                  <div className="text-xs text-gray-600">{agent.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 각 에이전트 상세 설명 */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            각 에이전트의 역할
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card-jeju p-6">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-jeju-blue-100 rounded-xl flex items-center justify-center text-2xl flex-shrink-0">
                  🧠
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 mb-2">Supervisor Agent</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    사용자의 의도를 파악하고, 적절한 Tool Agent를 선택하여 라우팅합니다. 
                    LangGraph로 대화 상태를 관리합니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="card-jeju p-6">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-jeju-green-100 rounded-xl flex items-center justify-center text-2xl flex-shrink-0">
                  📚
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 mb-2">RAG Agent</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Elasticsearch를 활용하여 사용자 질문과 유사한 관광지 정보를 
                    벡터 검색으로 찾아냅니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="card-jeju p-6">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-jeju-blue-100 rounded-xl flex items-center justify-center text-2xl flex-shrink-0">
                  🗄️
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 mb-2">SQL Agent</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    PostgreSQL 데이터베이스에서 구조화된 관광지 데이터를 
                    조건에 맞게 조회합니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="card-jeju p-6">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-jeju-orange-100 rounded-xl flex items-center justify-center text-2xl flex-shrink-0">
                  🌐
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 mb-2">Web Search Agent</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Tavily API를 통해 최신 날씨, 축제, 이벤트 정보를 
                    실시간으로 검색합니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="card-jeju p-6">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center text-2xl flex-shrink-0">
                  🚗
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 mb-2">Route Optimizer Agent</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Nearest Neighbor 알고리즘으로 
                    관광지 간 이동 거리를 최소화합니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="card-jeju p-6">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center text-2xl flex-shrink-0">
                  🗺️
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 mb-2">Map Visualization Agent</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    추천된 관광지와 최적화된 경로를 
                    지도에 시각적으로 표현합니다.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 기술 스택 */}
        <div className="card-jeju p-8 mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            🛠️ 기술 스택
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Backend */}
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Cpu className="text-jeju-blue-600" size={24} />
                <h3 className="font-bold text-lg text-gray-900">Backend</h3>
              </div>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li>• Python 3.11</li>
                <li>• FastAPI</li>
                <li>• LangChain & LangGraph</li>
                <li>• OpenAI GPT-4</li>
                <li>• Nearest Neighbor TSP</li>
              </ul>
            </div>

            {/* Database */}
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Database className="text-jeju-orange-600" size={24} />
                <h3 className="font-bold text-lg text-gray-900">Database</h3>
              </div>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li>• PostgreSQL 15</li>
                <li>• Elasticsearch 8.11</li>
                <li>• Sentence Transformers</li>
                <li>• Vector Search</li>
              </ul>
            </div>

            {/* Frontend */}
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Zap className="text-jeju-green-600" size={24} />
                <h3 className="font-bold text-lg text-gray-900">Frontend</h3>
              </div>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li>• React 18</li>
                <li>• TypeScript</li>
                <li>• Tailwind CSS</li>
                <li>• Vite</li>
                <li>• React Router</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 프로젝트 링크 */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">프로젝트 정보</h2>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-gray-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-800 transition-colors flex items-center space-x-2"
            >
              <Github size={20} />
              <span>GitHub Repository</span>
            </a>
            
            <a
              href={`${import.meta.env.PROD ? 'https://jeju-travel-chatbot-production.up.railway.app' : 'http://localhost:8000'}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors border-2 border-gray-200"
            >
              API 문서 (FastAPI Docs)
            </a>
          </div>

          <p className="text-gray-500 text-sm mt-8">
            © 2025 Jeju AI Travel Planner. 졸업 프로젝트.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;




