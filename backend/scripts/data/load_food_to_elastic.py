"""
visitjeju_food_rag.json을 Elasticsearch에 적재
- 인덱스: jeju_attractions
- 임베딩: OpenAI text-embedding-3-small
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path

import httpx
from openai import AsyncOpenAI

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 설정
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9201")
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "jeju_attractions")
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50  # 배치 크기

# OpenAI 클라이언트
openai_client = AsyncOpenAI()


async def create_embedding(text: str) -> list[float]:
    """OpenAI 임베딩 생성"""
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000],  # 토큰 제한
    )
    return response.data[0].embedding


async def bulk_index(http_client: httpx.AsyncClient, documents: list[dict]):
    """Elasticsearch bulk 인덱싱"""
    if not documents:
        return 0
    
    # NDJSON 형식으로 변환
    bulk_body = ""
    for doc in documents:
        action = {"index": {"_index": ES_INDEX_NAME, "_id": doc["document_id"]}}
        bulk_body += json.dumps(action) + "\n"
        bulk_body += json.dumps(doc) + "\n"
    
    response = await http_client.post(
        f"{ES_URL}/_bulk",
        content=bulk_body,
        headers={"Content-Type": "application/x-ndjson"}
    )
    
    result = response.json()
    if result.get("errors"):
        error_count = sum(1 for item in result["items"] if "error" in item.get("index", {}))
        logger.warning(f"  - {error_count}개 에러 발생")
    
    return len(documents)


async def load_food_data():
    """visitjeju_food_rag.json 적재"""
    data_path = Path(__file__).parent.parent.parent / "data" / "visitjeju_food_rag.json"
    
    if not data_path.exists():
        logger.error(f"파일 없음: {data_path}")
        return
    
    with open(data_path, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    logger.info(f"📂 로드: {len(documents)}개 문서")
    
    async with httpx.AsyncClient(timeout=60.0) as http_client:
        # 기존 food 문서 삭제 (선택적)
        # await http_client.post(f"{ES_URL}/{ES_INDEX_NAME}/_delete_by_query", json={
        #     "query": {"prefix": {"document_id": "food_"}}
        # })
        
        batch = []
        total_indexed = 0
        
        for i, doc in enumerate(documents):
            # 임베딩 생성 (query 필드 사용)
            query_text = doc.get("query", doc.get("document", ""))[:500]
            
            try:
                embedding = await create_embedding(query_text)
                doc["embedding"] = embedding
            except Exception as e:
                logger.warning(f"  임베딩 실패 [{doc.get('metadata', {}).get('title')}]: {e}")
                continue
            
            batch.append(doc)
            
            # 배치 처리
            if len(batch) >= BATCH_SIZE:
                indexed = await bulk_index(http_client, batch)
                total_indexed += indexed
                logger.info(f"  진행: {total_indexed}/{len(documents)} ({total_indexed*100//len(documents)}%)")
                batch = []
                
                # API 레이트 리밋 방지
                await asyncio.sleep(0.5)
        
        # 남은 배치 처리
        if batch:
            indexed = await bulk_index(http_client, batch)
            total_indexed += indexed
        
        logger.info(f"✅ 완료: {total_indexed}개 인덱싱됨")


if __name__ == "__main__":
    asyncio.run(load_food_data())




