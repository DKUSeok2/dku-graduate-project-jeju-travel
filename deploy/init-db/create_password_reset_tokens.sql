-- 비밀번호 재설정 토큰 테이블
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

-- 테이블 설명
COMMENT ON TABLE password_reset_tokens IS '비밀번호 재설정 토큰';
COMMENT ON COLUMN password_reset_tokens.user_id IS '사용자 ID';
COMMENT ON COLUMN password_reset_tokens.token IS '재설정 토큰 (UUID)';
COMMENT ON COLUMN password_reset_tokens.expires_at IS '만료 시간 (발급 후 30분)';
COMMENT ON COLUMN password_reset_tokens.used IS '사용 여부';


