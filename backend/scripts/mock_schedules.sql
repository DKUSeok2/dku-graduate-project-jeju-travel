-- Mock 일정 데이터 삽입
-- 사용자 ID는 1번을 가정 (실제 사용자 ID로 변경 필요)

-- 1. 힐링 제주 3박 4일 (공개)
INSERT INTO schedules (user_id, title, start_date, end_date, attractions, route_data, memo, is_public, created_at, updated_at)
VALUES (
    1,
    '🌊 힐링 제주 3박 4일',
    '2025-11-15',
    '2025-11-18',
    '{"day1": [{"name": "제주국제공항", "time": "09:00", "emoji": "✈️"}, {"name": "협재해수욕장", "time": "10:30", "emoji": "🏖️"}, {"name": "한림공원", "time": "13:30", "emoji": "🌺"}], "day2": [{"name": "성산일출봉", "time": "06:00", "emoji": "🌋"}, {"name": "섭지코지", "time": "09:00", "emoji": "🌊"}, {"name": "아쿠아플라넷", "time": "11:30", "emoji": "🐠"}], "day3": [{"name": "한라산 등반", "time": "08:00", "emoji": "🏔️"}, {"name": "테디베어 박물관", "time": "15:30", "emoji": "🧸"}]}'::jsonb,
    '{"total_distance": 87, "total_time": 5.5}'::jsonb,
    '자연과 함께하는 여유로운 제주 여행',
    true,
    NOW(),
    NOW()
);

-- 2. 제주 맛집 투어 2박 3일 (공개)
INSERT INTO schedules (user_id, title, start_date, end_date, attractions, route_data, memo, is_public, created_at, updated_at)
VALUES (
    1,
    '🍊 제주 맛집 투어 2박 3일',
    '2025-12-01',
    '2025-12-03',
    '{"day1": [{"name": "흑돼지거리", "time": "12:00", "emoji": "🐷"}, {"name": "동문시장", "time": "15:00", "emoji": "🏪"}, {"name": "애월 카페거리", "time": "17:00", "emoji": "☕"}], "day2": [{"name": "해녀의 집", "time": "11:00", "emoji": "🍽️"}, {"name": "올레시장", "time": "14:00", "emoji": "🛒"}, {"name": "중문 맛집거리", "time": "18:00", "emoji": "🍜"}]}'::jsonb,
    '{"total_distance": 45, "total_time": 3}'::jsonb,
    '제주의 모든 맛을 경험하는 미식 여행',
    true,
    NOW(),
    NOW()
);

-- 3. 제주 드라이브 코스 당일치기 (공개)
INSERT INTO schedules (user_id, title, start_date, end_date, attractions, route_data, memo, is_public, created_at, updated_at)
VALUES (
    1,
    '🚗 제주 드라이브 코스 당일치기',
    '2025-11-20',
    '2025-11-20',
    '{"day1": [{"name": "제주 올레길 7코스", "time": "08:00", "emoji": "🚶"}, {"name": "사려니숲길", "time": "11:00", "emoji": "🌲"}, {"name": "천지연폭포", "time": "14:00", "emoji": "💧"}, {"name": "서귀포 매일올레시장", "time": "17:00", "emoji": "🏪"}]}'::jsonb,
    '{"total_distance": 62, "total_time": 4.5}'::jsonb,
    '제주의 자연을 느끼는 드라이브',
    true,
    NOW(),
    NOW()
);

-- 4. 가족 여행 제주 4박 5일 (공개)
INSERT INTO schedules (user_id, title, start_date, end_date, attractions, route_data, memo, is_public, created_at, updated_at)
VALUES (
    1,
    '👨‍👩‍👧‍👦 가족 여행 제주 4박 5일',
    '2025-12-10',
    '2025-12-14',
    '{"day1": [{"name": "제주미니랜드", "time": "10:00", "emoji": "🏰"}, {"name": "제주러브랜드", "time": "13:00", "emoji": "🎨"}], "day2": [{"name": "에코랜드", "time": "09:00", "emoji": "🚂"}, {"name": "김녕미로공원", "time": "14:00", "emoji": "🌿"}], "day3": [{"name": "우도", "time": "08:00", "emoji": "🏝️"}, {"name": "해녀박물관", "time": "15:00", "emoji": "🏛️"}], "day4": [{"name": "제주민속촌", "time": "10:00", "emoji": "🏘️"}, {"name": "중문해수욕장", "time": "14:00", "emoji": "🏖️"}]}'::jsonb,
    '{"total_distance": 120, "total_time": 8}'::jsonb,
    '온 가족이 즐기는 행복한 제주 여행',
    true,
    NOW(),
    NOW()
);

-- 5. 인스타 감성 제주 여행 (공개)
INSERT INTO schedules (user_id, title, start_date, end_date, attractions, route_data, memo, is_public, created_at, updated_at)
VALUES (
    1,
    '📸 인스타 감성 제주 여행',
    '2025-11-25',
    '2025-11-27',
    '{"day1": [{"name": "카멜리아힐", "time": "10:00", "emoji": "🌺"}, {"name": "월정리해변", "time": "13:00", "emoji": "🏖️"}, {"name": "애월 카페거리", "time": "16:00", "emoji": "☕"}], "day2": [{"name": "성산일출봉", "time": "06:00", "emoji": "🌋"}, {"name": "광치기해변", "time": "09:00", "emoji": "🌊"}, {"name": "섭지코지", "time": "11:00", "emoji": "🌅"}]}'::jsonb,
    '{"total_distance": 78, "total_time": 5}'::jsonb,
    '사진으로 남기는 제주의 순간들',
    true,
    NOW(),
    NOW()
);

-- 6. 액티브 제주 여행 (비공개)
INSERT INTO schedules (user_id, title, start_date, end_date, attractions, route_data, memo, is_public, created_at, updated_at)
VALUES (
    1,
    '🏃 액티브 제주 여행 (개인 일정)',
    '2025-12-05',
    '2025-12-07',
    '{"day1": [{"name": "한라산 등반", "time": "05:00", "emoji": "🏔️"}, {"name": "천지연폭포", "time": "14:00", "emoji": "💧"}], "day2": [{"name": "올레길 1코스", "time": "07:00", "emoji": "🚶"}, {"name": "수월봉", "time": "15:00", "emoji": "⛰️"}]}'::jsonb,
    '{"total_distance": 95, "total_time": 12}'::jsonb,
    '등산과 트레킹으로 제주 정복하기',
    false,
    NOW(),
    NOW()
);


