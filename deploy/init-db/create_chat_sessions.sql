-- chat_sessions 테이블 생성
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) UNIQUE NOT NULL,  -- UUID
    title VARCHAR(255),  -- 대화 제목 (첫 메시지에서 자동 생성)
    messages JSONB NOT NULL DEFAULT '[]',  -- 메시지 리스트
    context JSONB,  -- 사용자 프로필, 선택한 관광지 등
    is_active BOOLEAN DEFAULT true,  -- 활성 세션 여부
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions (session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions (updated_at DESC);

-- 코멘트 추가
COMMENT ON TABLE chat_sessions IS 'AI 채팅 세션 관리 테이블';
COMMENT ON COLUMN chat_sessions.session_id IS '세션 고유 ID (UUID)';
COMMENT ON COLUMN chat_sessions.messages IS 'AI와의 대화 메시지 리스트 (JSON 형식)';
COMMENT ON COLUMN chat_sessions.context IS '세션 컨텍스트 (선택한 관광지, 사용자 프로필 등)';
COMMENT ON COLUMN chat_sessions.is_active IS '활성 세션 여부 (비활성 세션은 목록에서 숨김)';


