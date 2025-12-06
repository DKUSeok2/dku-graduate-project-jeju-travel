-- Schedule 테이블에 AI 대화 내역 및 지도 데이터 필드 추가
-- 마이그레이션 스크립트

-- chat_history 컬럼 추가 (AI 대화 내역)
ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS chat_history JSONB;

-- ai_reasoning 컬럼 추가 (AI 추천 이유/맥락)
ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS ai_reasoning TEXT;

-- map_data 컬럼 추가 (지도 시각화 데이터)
ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS map_data JSONB;

-- 인덱스 추가 (JSON 쿼리 성능 향상)
CREATE INDEX IF NOT EXISTS idx_schedules_chat_history ON schedules USING GIN (chat_history);
CREATE INDEX IF NOT EXISTS idx_schedules_map_data ON schedules USING GIN (map_data);

-- 주석 추가
COMMENT ON COLUMN schedules.chat_history IS 'AI와의 대화 내역 (JSON 배열)';
COMMENT ON COLUMN schedules.ai_reasoning IS 'AI가 해당 일정을 추천한 이유 및 맥락';
COMMENT ON COLUMN schedules.map_data IS '지도 시각화 데이터 (마커, 경로선 등)';


