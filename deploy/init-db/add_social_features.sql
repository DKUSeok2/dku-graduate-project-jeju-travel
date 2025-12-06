-- Phase 1 소셜 기능 추가를 위한 마이그레이션 스크립트

-- 1. 좋아요 테이블
CREATE TABLE IF NOT EXISTS schedule_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, schedule_id)
);

CREATE INDEX idx_schedule_likes_user_id ON schedule_likes(user_id);
CREATE INDEX idx_schedule_likes_schedule_id ON schedule_likes(schedule_id);

-- 2. 북마크 테이블
CREATE TABLE IF NOT EXISTS schedule_bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, schedule_id)
);

CREATE INDEX idx_schedule_bookmarks_user_id ON schedule_bookmarks(user_id);
CREATE INDEX idx_schedule_bookmarks_schedule_id ON schedule_bookmarks(schedule_id);

-- 3. 조회수 테이블
CREATE TABLE IF NOT EXISTS schedule_views (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_schedule_views_schedule_id ON schedule_views(schedule_id);
CREATE INDEX idx_schedule_views_user_id ON schedule_views(user_id);
CREATE INDEX idx_schedule_views_created_at ON schedule_views(created_at);

-- 4. 통계 조회를 위한 뷰 생성 (선택 사항 - 성능 최적화)
CREATE OR REPLACE VIEW schedule_stats AS
SELECT 
    s.id as schedule_id,
    COUNT(DISTINCT sl.id) as likes_count,
    COUNT(DISTINCT sb.id) as bookmarks_count,
    COUNT(DISTINCT sv.id) as views_count
FROM schedules s
LEFT JOIN schedule_likes sl ON s.id = sl.schedule_id
LEFT JOIN schedule_bookmarks sb ON s.id = sb.schedule_id
LEFT JOIN schedule_views sv ON s.id = sv.schedule_id
GROUP BY s.id;

-- 5. 데이터 확인 쿼리
-- SELECT * FROM schedule_stats ORDER BY likes_count DESC LIMIT 10;

-- 6. 1:1 DM(Direct Message) 대화방
-- user1_id < user2_id로 정규화하여 중복 방지
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_message_id INTEGER,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_conversations_pair UNIQUE (user1_id, user2_id),
    CONSTRAINT chk_user_order CHECK (user1_id < user2_id)
);

CREATE INDEX IF NOT EXISTS idx_conversations_user1 ON conversations(user1_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user2 ON conversations(user2_id);

-- 7. DM 메시지
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- 8. 일정 댓글
CREATE TABLE IF NOT EXISTS schedule_comments (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    parent_id INTEGER REFERENCES schedule_comments(id) ON DELETE CASCADE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schedule_comments_schedule_id ON schedule_comments(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedule_comments_user_id ON schedule_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_schedule_comments_parent_id ON schedule_comments(parent_id);

-- 9. 일정 사진
CREATE TABLE IF NOT EXISTS schedule_photos (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    caption TEXT,
    day INTEGER,
    order_in_day INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schedule_photos_schedule_id ON schedule_photos(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedule_photos_user_id ON schedule_photos(user_id);


