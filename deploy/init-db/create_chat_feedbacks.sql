-- Chat Feedbacks 테이블 생성
CREATE TABLE IF NOT EXISTS chat_feedbacks (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    is_like BOOLEAN NOT NULL,  -- true: 좋아요, false: 싫어요
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, message_id, user_id)  -- 한 사용자는 한 메시지에 하나의 피드백만 가능
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_chat_feedbacks_session_id ON chat_feedbacks(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_feedbacks_message_id ON chat_feedbacks(message_id);
CREATE INDEX IF NOT EXISTS idx_chat_feedbacks_user_id ON chat_feedbacks(user_id);

