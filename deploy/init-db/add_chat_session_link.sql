-- schedules 테이블에 chat_session_id 필드 추가
ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS chat_session_id VARCHAR(255);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_schedules_chat_session_id ON schedules(chat_session_id);

-- Foreign Key 제약조건 추가 (선택 사항 - chat_session이 삭제되어도 schedule은 유지)
-- ALTER TABLE schedules
-- ADD CONSTRAINT fk_schedules_chat_session
-- FOREIGN KEY (chat_session_id) REFERENCES chat_sessions(session_id) ON DELETE SET NULL;

COMMENT ON COLUMN schedules.chat_session_id IS '연결된 채팅 세션 ID (채팅에서 생성된 일정인 경우)';


