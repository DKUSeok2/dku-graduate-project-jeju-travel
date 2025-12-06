#!/usr/bin/env python
"""
LLM 기반 Query 생성기 (klid-aicb 방식)
각 콘텐츠에 대해 LLM이 적합한 검색 쿼리를 생성합니다.

Rate Limiting 전략:
1. Throttling: 요청 간 딜레이 적용
2. Batching: 여러 문서를 한 번에 처리
3. Exponential Backoff: 429 에러 시 재시도
"""
import os
import sys
import asyncio
import logging
import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from openai import AsyncOpenAI, RateLimitError
from pydantic import BaseModel, Field
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate Limiting 설정
DEFAULT_REQUESTS_PER_SECOND = 0.5  # 2초에 1개 요청 (보수적)
MAX_RETRIES = 5  # 최대 재시도 횟수
BATCH_SIZE = 5  # 한 번에 처리할 문서 수

# 데이터 디렉토리
DATA_DIR = Path(__file__).parent.parent.parent / "data"


class GeneratedQueries(BaseModel):
    """LLM이 생성한 쿼리 목록"""
    queries: List[str] = Field(
        description="사용자가 이 장소를 찾기 위해 검색할 수 있는 자연어 질문들"
    )


@dataclass
class RAGDocument:
    """Elasticsearch에 적재할 RAG 문서"""
    document_id: str
    query: str
    document: str
    metadata: Dict[str, Any]
    embedding: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "query": self.query,
            "document": self.document,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }


class LLMQueryGenerator:
    """LLM 기반 Query 생성기 (klid-aicb 방식)"""
    
    SYSTEM_PROMPT = """당신은 제주도 관광 정보 검색 시스템의 쿼리 생성 전문가입니다.
주어진 관광지/음식점/숙소 정보를 보고, 사용자가 이 장소를 찾기 위해 검색할 수 있는 자연어 질문을 생성해주세요.

규칙:
1. 질문은 구체적이고 자연스러워야 합니다
2. 장소의 특징, 위치, 카테고리를 반영해야 합니다
3. 한국어로 작성해주세요
4. 일반적인 질문(예: "맛집 추천")보다 특정 장소에 적합한 질문을 생성하세요

예시:
- "성산일출봉 근처 가볼만한 곳"
- "제주 흑돼지 고기 맛집"
- "아이와 함께 가기 좋은 제주 카페"
- "제주 서귀포 해변 추천"
"""

    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"  # 비용 효율적인 모델
    
    async def generate_queries(
        self, 
        document: str, 
        num_queries: int = 3,
        max_retries: int = MAX_RETRIES,
    ) -> List[str]:
        """문서에 대한 검색 쿼리 생성 (Exponential Backoff 적용)
        
        Args:
            document: 문서 텍스트
            num_queries: 생성할 쿼리 수
            max_retries: 최대 재시도 횟수
        """
        for attempt in range(max_retries):
            try:
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": f"다음 장소 정보에 대해 검색 질문 {num_queries}개를 생성해주세요:\n\n{document}"}
                    ],
                    response_format=GeneratedQueries,
                )
                return response.choices[0].message.parsed.queries
            except RateLimitError:
                # Exponential Backoff: 2^attempt + random jitter (0~1초)
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    f"⚠️ Rate limit hit (attempt {attempt + 1}/{max_retries}), "
                    f"waiting {wait_time:.1f}s..."
                )
                await asyncio.sleep(wait_time)
            except Exception:
                logger.exception("Query generation error")
                return []
        
        logger.error(f"❌ Max retries ({max_retries}) exceeded")
        return []
    
    async def generate_queries_for_batch(
        self,
        documents: List[Dict[str, Any]],
        num_queries: int = 3,
        max_retries: int = MAX_RETRIES,
    ) -> Dict[int, List[str]]:
        """여러 문서에 대한 쿼리를 한 번의 API 호출로 생성 (Batching)
        
        Args:
            documents: 문서 리스트 (최대 BATCH_SIZE개)
            num_queries: 문서당 생성할 쿼리 수
            max_retries: 최대 재시도 횟수
            
        Returns:
            {문서_인덱스: [쿼리 리스트]} 형태의 딕셔너리
        """
        # 배치 프롬프트 구성
        batch_prompt = "다음 각 장소에 대해 검색 질문을 생성해주세요:\n\n"
        for idx, doc in enumerate(documents):
            # 문서 내용 요약 (토큰 절약)
            doc_text = doc["document"][:500]
            batch_prompt += f"[장소 {idx + 1}: {doc['metadata'].get('title', 'Unknown')}]\n{doc_text}\n\n"
        
        batch_prompt += f"\n각 장소마다 {num_queries}개의 질문을 생성하세요. 반드시 장소 순서대로 생성해주세요."
        
        for attempt in range(max_retries):
            try:
                # Structured output으로 배치 응답 받기
                class BatchQueries(BaseModel):
                    """여러 장소에 대한 쿼리 배치"""
                    queries_per_place: List[List[str]] = Field(
                        description="각 장소별 검색 질문 리스트 (장소 순서대로)"
                    )
                
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": batch_prompt}
                    ],
                    response_format=BatchQueries,
                )
                
                result = {}
                parsed = response.choices[0].message.parsed
                for idx, queries in enumerate(parsed.queries_per_place):
                    if idx < len(documents):
                        result[idx] = queries[:num_queries]  # 쿼리 수 제한
                
                return result
                
            except RateLimitError:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    f"⚠️ Rate limit hit on batch (attempt {attempt + 1}/{max_retries}), "
                    f"waiting {wait_time:.1f}s..."
                )
                await asyncio.sleep(wait_time)
            except Exception:
                logger.exception("Batch query generation error")
                return {}
        
        logger.error(f"❌ Max retries ({max_retries}) exceeded for batch")
        return {}

    async def generate_queries_batch(
        self, 
        documents: List[Dict[str, Any]], 
        num_queries: int = 3,
        requests_per_second: float = DEFAULT_REQUESTS_PER_SECOND,
        batch_size: int = BATCH_SIZE,
        use_batching: bool = True,
    ) -> List[RAGDocument]:
        """Query 생성 (Rate Limiting + Batching 적용)
        
        Args:
            documents: 문서 리스트
            num_queries: 문서당 생성할 쿼리 수
            requests_per_second: 초당 요청 수 (기본 0.5 = 2초 간격)
            batch_size: 한 번에 처리할 문서 수 (기본 5)
            use_batching: 배치 처리 사용 여부
        """
        rag_docs = []
        delay = 1.0 / requests_per_second
        
        if use_batching:
            # 🚀 Batching 모드: 여러 문서를 한 번에 처리
            logger.info(f"📦 Batching mode: {batch_size} docs/request, {requests_per_second} req/sec")
            
            for i in tqdm(range(0, len(documents), batch_size), desc="Batch processing"):
                batch = documents[i:i + batch_size]
                
                # 배치 쿼리 생성
                batch_result = await self.generate_queries_for_batch(batch, num_queries)
                
                # RAGDocument 생성
                for idx, doc in enumerate(batch):
                    queries = batch_result.get(idx, [])
                    
                    if not queries:
                        # 실패 시 기본 쿼리 사용
                        queries = [
                            f"{doc['metadata']['title']} 정보",
                            f"{doc['metadata']['title']} 위치",
                        ]
                    
                    for query in queries:
                        doc_id = hashlib.sha256((query + doc["document"]).encode()).hexdigest()[:32]
                        rag_doc = RAGDocument(
                            document_id=doc_id,
                            query=query,
                            document=doc["document"],
                            metadata=doc["metadata"],
                        )
                        rag_docs.append(rag_doc)
                
                # Rate limiting
                await asyncio.sleep(delay)
        else:
            # 순차 모드: 기존 방식 (문서당 1개 API 호출)
            logger.info(f"📝 Sequential mode: {requests_per_second} req/sec (delay: {delay:.2f}s)")
            
            for doc in tqdm(documents, desc="Generating queries"):
                queries = await self.generate_queries(doc["document"], num_queries)
                
                if not queries:
                    queries = [
                        f"{doc['metadata']['title']} 정보",
                        f"{doc['metadata']['title']} 위치",
                    ]
                
                for query in queries:
                    doc_id = hashlib.sha256((query + doc["document"]).encode()).hexdigest()[:32]
                    rag_doc = RAGDocument(
                        document_id=doc_id,
                        query=query,
                        document=doc["document"],
                        metadata=doc["metadata"],
                    )
                    rag_docs.append(rag_doc)
                
                await asyncio.sleep(delay)
        
        return rag_docs


async def main(
    limit: int = None, 
    num_queries: int = 3,
    requests_per_second: float = DEFAULT_REQUESTS_PER_SECOND,
    batch_size: int = BATCH_SIZE,
    use_batching: bool = True,
):
    """LLM Query 생성 실행
    
    Args:
        limit: 처리할 문서 수 제한
        num_queries: 문서당 생성할 쿼리 수
        requests_per_second: 초당 요청 수
        batch_size: 배치당 문서 수
        use_batching: 배치 모드 사용 여부
    """
    from load_jeju_data import merge_all_data
    
    logger.info("🚀 LLM Query 생성 시작...")
    logger.info(f"⚙️ 설정: {requests_per_second} req/sec, batch_size={batch_size}, batching={use_batching}")
    
    # 1. 콘텐츠 로드
    contents = merge_all_data()
    
    if limit:
        contents = contents[:limit]
        logger.info(f"Limited to {limit} contents for testing")
    
    # 2. document 준비
    documents = []
    for content in contents:
        documents.append({
            "document": content.to_document(),
            "metadata": content.to_metadata(),
        })
    
    logger.info(f"Loaded {len(documents)} documents")
    
    # 3. LLM Query 생성 (Rate Limiting + Batching 적용)
    generator = LLMQueryGenerator()
    rag_docs = await generator.generate_queries_batch(
        documents, 
        num_queries=num_queries,
        requests_per_second=requests_per_second,
        batch_size=batch_size,
        use_batching=use_batching,
    )
    
    logger.info(f"✅ Generated {len(rag_docs)} RAG documents")
    
    # 4. JSON 저장
    output_path = DATA_DIR / "rag_documents_llm.json"
    data = [doc.to_dict() for doc in rag_docs]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved to {output_path}")
    
    # 5. 샘플 출력
    print("\n샘플 RAG 문서:")
    for doc in rag_docs[:10]:
        print(f"\n{'='*50}")
        print(f"Query: {doc.query}")
        print(f"Title: {doc.metadata.get('title')}")
    
    return rag_docs


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate queries using LLM")
    parser.add_argument("--limit", type=int, help="Limit number of contents")
    parser.add_argument("--queries", type=int, default=3, help="Number of queries per content")
    parser.add_argument("--rps", type=float, default=DEFAULT_REQUESTS_PER_SECOND, 
                        help=f"Requests per second (default: {DEFAULT_REQUESTS_PER_SECOND})")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                        help=f"Documents per batch (default: {BATCH_SIZE})")
    parser.add_argument("--no-batch", action="store_true", 
                        help="Disable batching (process one document at a time)")
    args = parser.parse_args()
    
    asyncio.run(main(
        limit=args.limit, 
        num_queries=args.queries,
        requests_per_second=args.rps,
        batch_size=args.batch_size,
        use_batching=not args.no_batch,
    ))

