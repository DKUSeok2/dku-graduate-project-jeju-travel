-- Initialize Jeju Travel Database

-- Enable PostGIS extension (for geographic queries)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users table (인증 시스템)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT false,  -- 관리자 권한
    provider VARCHAR(20) DEFAULT 'local',  -- 'local', 'kakao', 'google'
    provider_id VARCHAR(255),
    profile_image TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_provider ON users(provider, provider_id);

-- Schedules table (일정 저장)
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    attractions JSONB,  -- 관광지 리스트 및 순서
    route_data JSONB,   -- 최적화된 경로 정보
    memo TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_schedules_user_id ON schedules(user_id);
CREATE INDEX idx_schedules_dates ON schedules(start_date, end_date);

-- Attractions table
CREATE TABLE IF NOT EXISTS attractions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    avg_rating DECIMAL(3, 2),
    price_range VARCHAR(20),
    kid_friendly BOOLEAN DEFAULT false,
    estimated_time INTEGER,
    operating_hours JSONB,
    tags TEXT[],
    address TEXT,
    phone VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_attractions_category ON attractions(category);
CREATE INDEX idx_attractions_name ON attractions(name);
CREATE INDEX idx_attractions_kid_friendly ON attractions(kid_friendly);
CREATE INDEX idx_attractions_rating ON attractions(avg_rating);

-- Accommodations table
CREATE TABLE IF NOT EXISTS accommodations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50),
    area VARCHAR(50),
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    price_per_night INTEGER,
    rating DECIMAL(3, 2),
    amenities JSONB,
    address TEXT,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accommodations_type ON accommodations(type);
CREATE INDEX idx_accommodations_area ON accommodations(area);

-- Restaurants table
CREATE TABLE IF NOT EXISTS restaurants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cuisine VARCHAR(50),
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    avg_price INTEGER,
    rating DECIMAL(3, 2),
    address TEXT,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_restaurants_cuisine ON restaurants(cuisine);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);

-- LLM Usage Tracking table (토큰 사용량 추적)
CREATE TABLE IF NOT EXISTS llm_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(100),
    model VARCHAR(50) NOT NULL,  -- 'gpt-4', 'gpt-3.5-turbo' 등
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost DECIMAL(10, 6),  -- 예상 비용 (달러)
    endpoint VARCHAR(100),  -- 어느 API 엔드포인트에서 사용했는지
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llm_usage_user_id ON llm_usage(user_id);
CREATE INDEX idx_llm_usage_created_at ON llm_usage(created_at);
CREATE INDEX idx_llm_usage_model ON llm_usage(model);

-- API Call Logs table (API 호출 로그)
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,  -- 응답 시간 (밀리초)
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX idx_api_logs_created_at ON api_logs(created_at);
CREATE INDEX idx_api_logs_endpoint ON api_logs(endpoint);

-- Insert sample data (optional)
INSERT INTO attractions (name, category, lat, lng, avg_rating, price_range, kid_friendly, tags, description) VALUES
('성산일출봉', '자연', 33.4597, 126.9426, 4.8, '보통', true, ARRAY['일출', '등산', '유네스코'], '유네스코 세계자연유산으로 지정된 화산 분출로 형성된 거대한 바위산'),
('협재해수욕장', '해변', 33.3942, 126.2397, 4.7, '무료', true, ARRAY['해수욕', '일몰', '가족'], '에메랄드빛 바다와 하얀 모래사장이 아름다운 해변')
ON CONFLICT DO NOTHING;

COMMIT;





