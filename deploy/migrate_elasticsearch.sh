#!/bin/bash
# Elasticsearch 데이터 마이그레이션 스크립트
# 사용법: ./migrate_elasticsearch.sh <ELASTIC_CLOUD_URL> <API_KEY>

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 로컬 ES 설정
LOCAL_ES="http://localhost:9201"
INDEX_NAME="jeju-attractions"

# 인자 확인
if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}사용법: ./migrate_elasticsearch.sh <ELASTIC_CLOUD_URL> <API_KEY>${NC}"
    echo -e "${YELLOW}예시: ./migrate_elasticsearch.sh https://xxx.es.aws.cloud.es.io:443 base64encodedapikey${NC}"
    exit 1
fi

CLOUD_URL="$1"
API_KEY="$2"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Elasticsearch 데이터 마이그레이션 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# elasticdump 설치 확인
if ! command -v elasticdump &> /dev/null; then
    echo -e "${YELLOW}elasticdump 설치 중...${NC}"
    npm install -g elasticdump
fi

# 1. 로컬 인덱스 문서 수 확인
echo -e "\n${YELLOW}[1/4] 로컬 인덱스 확인 중...${NC}"
LOCAL_COUNT=$(curl -s "$LOCAL_ES/$INDEX_NAME/_count" | jq '.count')
echo -e "${GREEN}✓ 로컬 문서 수: $LOCAL_COUNT${NC}"

# 2. 매핑 마이그레이션
echo -e "\n${YELLOW}[2/4] 매핑 마이그레이션 중...${NC}"
elasticdump \
    --input="$LOCAL_ES/$INDEX_NAME" \
    --output="$CLOUD_URL/$INDEX_NAME" \
    --headers='{"Authorization": "ApiKey '"$API_KEY"'"}' \
    --type=mapping \
    --quiet

echo -e "${GREEN}✓ 매핑 마이그레이션 완료${NC}"

# 3. 설정 마이그레이션
echo -e "\n${YELLOW}[3/4] 설정 마이그레이션 중...${NC}"
elasticdump \
    --input="$LOCAL_ES/$INDEX_NAME" \
    --output="$CLOUD_URL/$INDEX_NAME" \
    --headers='{"Authorization": "ApiKey '"$API_KEY"'"}' \
    --type=settings \
    --quiet

echo -e "${GREEN}✓ 설정 마이그레이션 완료${NC}"

# 4. 데이터 마이그레이션
echo -e "\n${YELLOW}[4/4] 데이터 마이그레이션 중...${NC}"
elasticdump \
    --input="$LOCAL_ES/$INDEX_NAME" \
    --output="$CLOUD_URL/$INDEX_NAME" \
    --headers='{"Authorization": "ApiKey '"$API_KEY"'"}' \
    --type=data \
    --limit=1000

echo -e "${GREEN}✓ 데이터 마이그레이션 완료${NC}"

# 5. 클라우드 인덱스 문서 수 확인
echo -e "\n${YELLOW}데이터 확인 중...${NC}"
sleep 2  # 인덱싱 대기
CLOUD_COUNT=$(curl -s -H "Authorization: ApiKey $API_KEY" "$CLOUD_URL/$INDEX_NAME/_count" | jq '.count')
echo -e "${GREEN}✓ 클라우드 문서 수: $CLOUD_COUNT${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 마이그레이션 완료!${NC}"
echo -e "${GREEN}  로컬: $LOCAL_COUNT 문서${NC}"
echo -e "${GREEN}  클라우드: $CLOUD_COUNT 문서${NC}"
echo -e "${GREEN}========================================${NC}"

