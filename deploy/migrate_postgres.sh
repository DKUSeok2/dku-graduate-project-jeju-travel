#!/bin/bash
# PostgreSQL 데이터 마이그레이션 스크립트
# 사용법: ./migrate_postgres.sh <RAILWAY_DATABASE_URL>

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 로컬 DB 설정
LOCAL_HOST="localhost"
LOCAL_PORT="5433"
LOCAL_USER="jeju_user"
LOCAL_DB="jeju_travel"

# 인자 확인
if [ -z "$1" ]; then
    echo -e "${RED}사용법: ./migrate_postgres.sh <RAILWAY_DATABASE_URL>${NC}"
    echo -e "${YELLOW}예시: ./migrate_postgres.sh postgresql://postgres:xxx@xxx.railway.app:5432/railway${NC}"
    exit 1
fi

RAILWAY_URL="$1"
BACKUP_FILE="backup/jeju_travel_$(date +%Y%m%d_%H%M%S).sql"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PostgreSQL 데이터 마이그레이션 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 로컬 DB 덤프
echo -e "\n${YELLOW}[1/3] 로컬 데이터베이스 덤프 중...${NC}"
PGPASSWORD=jeju_password pg_dump \
    -h $LOCAL_HOST \
    -p $LOCAL_PORT \
    -U $LOCAL_USER \
    -d $LOCAL_DB \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    -t places \
    -t menus \
    -t attractions \
    -t users \
    -t chat_sessions \
    -t chat_feedbacks \
    -t schedules \
    -t schedule_items \
    -t token_usage \
    > "$BACKUP_FILE"

echo -e "${GREEN}✓ 덤프 완료: $BACKUP_FILE${NC}"
echo -e "  파일 크기: $(ls -lh "$BACKUP_FILE" | awk '{print $5}')"

# 2. Railway DB에 복원
echo -e "\n${YELLOW}[2/3] Railway 데이터베이스에 복원 중...${NC}"
psql "$RAILWAY_URL" < "$BACKUP_FILE"

echo -e "${GREEN}✓ 복원 완료${NC}"

# 3. 데이터 확인
echo -e "\n${YELLOW}[3/3] 데이터 확인 중...${NC}"
psql "$RAILWAY_URL" -c "
SELECT 'places' as table_name, COUNT(*) as count FROM places
UNION ALL
SELECT 'menus', COUNT(*) FROM menus
UNION ALL
SELECT 'attractions', COUNT(*) FROM attractions
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'chat_sessions', COUNT(*) FROM chat_sessions;
"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 마이그레이션 완료!${NC}"
echo -e "${GREEN}========================================${NC}"

