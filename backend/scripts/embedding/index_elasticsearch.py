#!/usr/bin/env python
"""
Elasticsearch Indexing Script
제주관광 데이터를 OpenAI text-embedding-3-small로 임베딩하여 Elasticsearch에 적재

Usage:
    python scripts/embedding/index_elasticsearch.py
    python scripts/embedding/index_elasticsearch.py --force --limit 100
    
환경변수:
    OPENAI_API_KEY: OpenAI API 키
    ELASTICSEARCH_URL: Elasticsearch URL (기본: http://localhost:9201)
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import httpx
from openai import AsyncOpenAI
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 설정
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9201")
ES_API_KEY = os.getenv("ELASTICSEARCH_API_KEY", None)  # Elastic Cloud API 키
ES_INDEX_NAME = "jeju_attractions"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536
BATCH_SIZE = 50  # OpenAI 배치 크기


class EmbeddingService:
    """OpenAI 임베딩 서비스"""
    
    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = EMBEDDING_MODEL
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트에 대한 임베딩 생성"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise


class ElasticsearchClient:
    """간단한 Elasticsearch HTTP 클라이언트"""
    
    def __init__(self, base_url: str = ES_URL, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or ES_API_KEY
        self.client = httpx.AsyncClient(timeout=60.0)
    
    def _get_headers(self, content_type: str = "application/json") -> dict:
        """HTTP 헤더 생성 (API 키 포함)"""
        headers = {"Content-Type": content_type}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        return headers
    
    async def _request(self, method: str, path: str, json_data: dict = None) -> dict:
        """HTTP 요청"""
        url = f"{self.base_url}{path}"
        response = await self.client.request(
            method=method,
            url=url,
            json=json_data,
            headers=self._get_headers()
        )
        return response.json() if response.text else {}
    
    async def index_exists(self, index_name: str) -> bool:
        """인덱스 존재 여부 확인"""
        try:
            response = await self.client.head(
                f"{self.base_url}/{index_name}",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def create_index(self, index_name: str, settings: dict, mappings: dict):
        """인덱스 생성"""
        body = {
            "settings": settings,
            "mappings": mappings,
        }
        return await self._request("PUT", f"/{index_name}", body)
    
    async def delete_index(self, index_name: str):
        """인덱스 삭제"""
        return await self._request("DELETE", f"/{index_name}")
    
    async def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]):
        """대량 인덱싱 (ndjson 형식)"""
        lines = []
        for doc in documents:
            action = {"index": {"_index": index_name, "_id": doc["document_id"]}}
            lines.append(json.dumps(action))
            lines.append(json.dumps(doc))
        
        body = "\n".join(lines) + "\n"
        
        response = await self.client.post(
            f"{self.base_url}/_bulk",
            content=body,
            headers=self._get_headers("application/x-ndjson")
        )
        return response.json()
    
    async def count(self, index_name: str) -> int:
        """문서 수 조회"""
        result = await self._request("GET", f"/{index_name}/_count")
        return result.get("count", 0)
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()


# 인덱스 설정
INDEX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
}

INDEX_MAPPINGS = {
    "properties": {
        "document_id": {"type": "keyword"},
        "query": {"type": "text"},
        "document": {"type": "text"},
        "embedding": {
            "type": "dense_vector",
            "dims": EMBEDDING_DIMS,
            "index": True,
            "similarity": "cosine",
        },
        "metadata": {
            "type": "object",
            "properties": {
                "content_id": {"type": "keyword"},
                "title": {"type": "text"},
                "category": {"type": "keyword"},
                "lat": {"type": "float"},
                "lng": {"type": "float"},
                "rating": {"type": "float"},
                "address": {"type": "text"},
            }
        }
    }
}


async def load_rag_documents(
    use_llm: bool = False, 
    num_queries: int = 3,
    from_json: str = None,
) -> List[Dict[str, Any]]:
    """RAG 문서 로드
    
    Args:
        use_llm: LLM으로 Query 생성 (klid-aicb 방식)
        num_queries: LLM 사용 시 생성할 쿼리 수
        from_json: 기존 JSON 파일에서 로드 (예: rag_documents_llm.json)
    """
    # 1. 기존 JSON 파일에서 로드
    if from_json:
        json_path = Path(__file__).parent.parent.parent / "data" / from_json
        if json_path.exists():
            logger.info(f"📂 Loading from existing JSON: {json_path}")
            with open(json_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            logger.info(f"✅ Loaded {len(documents)} documents from JSON")
            return documents
        else:
            logger.warning(f"⚠️ JSON file not found: {json_path}, falling back to CSV...")
    
    from scripts.data.load_jeju_data import merge_all_data, create_rag_documents
    
    logger.info("Loading and processing CSV data...")
    contents = merge_all_data()
    
    if use_llm:
        # LLM 방식 (klid-aicb)
        from scripts.data.query_generator import LLMQueryGenerator, DEFAULT_REQUESTS_PER_SECOND, BATCH_SIZE
        
        logger.info("🤖 Using LLM for query generation (klid-aicb style)...")
        logger.info(f"⚙️ Rate limiting: {DEFAULT_REQUESTS_PER_SECOND} req/sec, batch_size={BATCH_SIZE}")
        
        documents = [
            {"document": content.to_document(), "metadata": content.to_metadata()}
            for content in contents
        ]
        
        generator = LLMQueryGenerator()
        rag_docs = await generator.generate_queries_batch(
            documents, 
            num_queries=num_queries,
            requests_per_second=DEFAULT_REQUESTS_PER_SECOND,  # 2초에 1개 요청
            batch_size=BATCH_SIZE,  # 5개 문서씩 배치 처리
            use_batching=True,  # 배치 모드 활성화
        )
        return [doc.to_dict() for doc in rag_docs]
    else:
        # 기존 키워드 방식
        rag_docs = create_rag_documents(contents)
        return [doc.to_dict() for doc in rag_docs]


async def main(
    force_recreate: bool = False, 
    limit: int = None, 
    use_llm: bool = False, 
    num_queries: int = 3,
    from_json: str = None,
):
    """메인 실행 함수
    
    Args:
        force_recreate: 인덱스 강제 재생성 여부
        limit: 처리할 문서 수 제한 (테스트용)
        use_llm: LLM으로 Query 생성 (klid-aicb 방식)
        num_queries: LLM 사용 시 생성할 쿼리 수
        from_json: 기존 JSON 파일에서 로드 (예: rag_documents_llm.json)
    """
    logger.info("🚀 Starting Elasticsearch indexing...")
    if from_json:
        logger.info(f"📂 Using pre-generated JSON: {from_json}")
    elif use_llm:
        logger.info("🤖 LLM Query Generation enabled (klid-aicb style)")
    
    # 1. 서비스 초기화
    es_client = ElasticsearchClient(ES_URL)
    embedding_service = EmbeddingService()
    
    try:
        # 2. 인덱스 생성
        exists = await es_client.index_exists(ES_INDEX_NAME)
        
        if exists:
            if force_recreate:
                logger.info(f"Deleting existing index: {ES_INDEX_NAME}")
                await es_client.delete_index(ES_INDEX_NAME)
            else:
                logger.info(f"Index {ES_INDEX_NAME} already exists. Skipping creation.")
        
        if not exists or force_recreate:
            logger.info(f"Creating index: {ES_INDEX_NAME}")
            result = await es_client.create_index(ES_INDEX_NAME, INDEX_SETTINGS, INDEX_MAPPINGS)
            if "error" in result:
                logger.error(f"Index creation error: {result}")
                return
            logger.info(f"✅ Index {ES_INDEX_NAME} created successfully")
        
        # 3. RAG 문서 로드
        documents = await load_rag_documents(
            use_llm=use_llm, 
            num_queries=num_queries,
            from_json=from_json,
        )
        
        if limit:
            documents = documents[:limit]
            logger.info(f"Limited to {limit} documents for testing")
        
        logger.info(f"Loaded {len(documents)} documents")
        
        # 4. 배치 처리 (임베딩 생성 + 인덱싱)
        total_indexed = 0
        
        for i in tqdm(range(0, len(documents), BATCH_SIZE), desc="Processing batches"):
            batch = documents[i:i + BATCH_SIZE]
            
            # 임베딩 생성 (query + document 일부)
            texts = [doc["query"] + " " + doc["document"][:300] for doc in batch]
            embeddings = await embedding_service.create_embeddings(texts)
            
            # 임베딩 추가
            for doc, embedding in zip(batch, embeddings):
                doc["embedding"] = embedding
            
            # Elasticsearch에 인덱싱
            result = await es_client.bulk_index(ES_INDEX_NAME, batch)
            
            if result.get("errors"):
                error_count = sum(1 for item in result.get("items", []) if "error" in item.get("index", {}))
                logger.warning(f"Batch had {error_count} errors")
            
            total_indexed += len(batch)
        
        # 5. 결과 확인
        count = await es_client.count(ES_INDEX_NAME)
        logger.info(f"✅ Indexing completed! Total documents: {count}")
        
    except Exception as e:
        logger.error(f"❌ Error during indexing: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await es_client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Index Jeju data to Elasticsearch")
    parser.add_argument("--force", action="store_true", help="Force recreate index")
    parser.add_argument("--limit", type=int, help="Limit number of documents (for testing)")
    parser.add_argument("--llm", action="store_true", help="Use LLM for query generation (klid-aicb style)")
    parser.add_argument("--queries", type=int, default=3, help="Number of queries per content (for LLM mode)")
    parser.add_argument("--from-json", type=str, help="Load from existing JSON file (e.g., rag_documents_llm.json)")
    args = parser.parse_args()
    
    asyncio.run(main(
        force_recreate=args.force, 
        limit=args.limit,
        use_llm=args.llm,
        num_queries=args.queries,
        from_json=args.from_json,
    ))
