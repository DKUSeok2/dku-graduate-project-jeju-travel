"""
RAG Agent Retriever - Elasticsearch 벡터 검색
klid-aicb 패턴: 
- hybrid: Min-Max 정규화 + 동적 가중치
- rrf: Reciprocal Rank Fusion
"""
import os
import logging
import hashlib
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

import httpx
import numpy as np
from openai import AsyncOpenAI

from src.config import settings
from src.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# 설정 - settings 객체 사용으로 통일 (pydantic-settings가 환경변수 자동 매핑)
ES_URL = settings.elasticsearch_url
ES_API_KEY = settings.elasticsearch_api_key
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "jeju_attractions")
EMBEDDING_MODEL = "text-embedding-3-small"

# 디버그 로깅
logger.info(f"🔍 Elasticsearch URL: {ES_URL}")
logger.info(f"🔑 Elasticsearch API Key: {'설정됨' if ES_API_KEY else '없음'}")


def minmax_scale(data: np.ndarray) -> np.ndarray:
    """Min-Max 정규화 (0~1 범위)"""
    min_val = data.min()
    max_val = data.max()
    
    if max_val == min_val:
        return np.zeros_like(data)
    
    return (data - min_val) / (max_val - min_val)


def calculate_dynamic_weights(query: str) -> Tuple[float, float]:
    """쿼리 길이에 따른 동적 가중치 계산 (klid-aicb 방식)
    
    - 짧은 쿼리 (1-3단어): keyword 우선 (정확한 매칭)
    - 중간 쿼리 (4-7단어): 균형
    - 긴 쿼리 (8+단어): vector 우선 (의미론적 이해)
    """
    query_length = len(query.split())
    
    if query_length <= 3:
        return 0.6, 0.4  # keyword, vector
    elif query_length <= 7:
        return 0.5, 0.5
    else:
        return 0.4, 0.6


def reciprocal_rank_fusion(
    keyword_results: List[Dict[str, Any]], 
    vector_results: List[Dict[str, Any]], 
    k: int = 60
) -> Dict[str, float]:
    """Reciprocal Rank Fusion (RRF) - klid-aicb 방식
    
    순위 기반 점수 결합:
    score = 1/(k + rank_keyword) + 1/(k + rank_vector)
    
    Args:
        keyword_results: 키워드 검색 결과 (순위순)
        vector_results: 벡터 검색 결과 (순위순)
        k: rank constant (기본 60, 상위 결과에 더 높은 가중치)
    
    Returns:
        {doc_id: rrf_score} 딕셔너리
    """
    scores = {}
    
    # 키워드 검색 결과
    for rank, hit in enumerate(keyword_results, start=1):
        doc_id = hit["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    
    # 벡터 검색 결과
    for rank, hit in enumerate(vector_results, start=1):
        doc_id = hit["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    
    return scores


@dataclass
class RetrievalResult:
    """검색 결과 (klid-aicb 스타일)"""
    document_id: str
    query: str
    document: str
    score: float  # hybrid_similarity (0~1 정규화)
    metadata: Dict[str, Any]
    
    # 개별 점수 (디버깅용)
    term_similarity: float = 0.0
    vector_similarity: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "query": self.query,
            "document": self.document,
            "score": self.score,
            "term_similarity": self.term_similarity,
            "vector_similarity": self.vector_similarity,
            "metadata": self.metadata,
        }


class ElasticsearchRetriever:
    """Elasticsearch 기반 검색기 (klid-aicb 패턴)"""
    
    def __init__(
        self,
        es_url: str = ES_URL,
        index_name: str = ES_INDEX_NAME,
        openai_api_key: str = None,
        es_api_key: str = None,
    ):
        self.es_url = es_url.rstrip('/')
        self.index_name = index_name
        self.es_api_key = es_api_key or ES_API_KEY
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.openai_client = AsyncOpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
    
    async def close(self):
        """리소스 정리"""
        await self.http_client.aclose()
    
    async def _es_request(self, method: str, path: str, json_data: dict = None) -> dict:
        """Elasticsearch HTTP 요청"""
        url = f"{self.es_url}{path}"
        headers = {"Content-Type": "application/json"}
        
        # Elastic Cloud API 키 인증
        if self.es_api_key:
            headers["Authorization"] = f"ApiKey {self.es_api_key}"
        
        logger.info(f"🔗 ES Request: {method} {url}")
        logger.info(f"🔑 ES API Key 설정: {'있음' if self.es_api_key else '없음'}")
        
        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                json=json_data,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"❌ ES 응답 에러: {response.status_code} - {response.text[:500]}")
                return {}
            
            return response.json() if response.text else {}
        except Exception as e:
            logger.error(f"❌ ES 요청 실패: {e}")
            return {}
    
    async def _create_embedding(self, text: str, session_id: str = None) -> List[float]:
        """OpenAI 임베딩 생성 + 토큰 수집 (klid-aicb 방식)"""
        response = await self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        
        # 🔥 임베딩 토큰 수집 (klid-aicb 방식)
        if response.usage:
            token_usage = response.usage.total_tokens
            if token_usage > 0:
                try:
                    from src.services.token_usage_service import TokenUsageService
                    async with AsyncSessionLocal() as db:
                        token_service = TokenUsageService(db)
                        await token_service.record_usage(
                            user_id=None,
                            session_id=session_id or "rag_agent",
                            model=EMBEDDING_MODEL,
                            prompt_tokens=token_usage,
                            completion_tokens=0,  # 임베딩은 출력 토큰 없음
                            endpoint="embedding"
                        )
                        logger.info(f"📊 RAG 임베딩 토큰 저장: {token_usage} tokens")
                except Exception as e:
                    logger.warning(f"임베딩 토큰 저장 실패: {e}")
        
        return response.data[0].embedding
    
    async def keyword_search(
        self,
        query: str,
        num_results: int = 10,
        min_score: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """키워드 검색 (BM25) - 원시 결과 반환"""
        search_query = {
            "size": num_results * 3,
            "min_score": min_score,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["query^2", "document", "metadata.title^1.5", "metadata.address"],
                    "type": "best_fields",
                }
            },
            "_source": ["document_id", "query", "document", "metadata"]
        }
        
        response = await self._es_request("POST", f"/{self.index_name}/_search", search_query)
        
        results = []
        seen_documents = set()
        
        for hit in response.get("hits", {}).get("hits", []):
            doc = hit["_source"]
            doc_hash = hashlib.md5(doc["document"].encode()).hexdigest()
            
            if doc_hash not in seen_documents:
                seen_documents.add(doc_hash)
                results.append({
                    "id": doc.get("document_id", hit["_id"]),
                    "source": doc,
                    "score": hit["_score"],
                })
                
                if len(results) >= num_results:
                    break
        
        return results
    
    async def vector_search(
        self,
        query: str,
        num_results: int = 10,
        min_similarity: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """벡터 검색 (kNN) - 원시 결과 반환"""
        query_embedding = await self._create_embedding(query)
        
        search_query = {
            "size": num_results * 3,
            "knn": {
                "field": "embedding",
                "query_vector": query_embedding,
                "k": num_results * 3,
                "num_candidates": max(num_results * 6, 100),
            },
            "_source": ["document_id", "query", "document", "metadata"]
        }
        
        response = await self._es_request("POST", f"/{self.index_name}/_search", search_query)
        
        results = []
        seen_documents = set()
        
        for hit in response.get("hits", {}).get("hits", []):
            if hit["_score"] < min_similarity:
                continue
            
            doc = hit["_source"]
            doc_hash = hashlib.md5(doc["document"].encode()).hexdigest()
            
            if doc_hash not in seen_documents:
                seen_documents.add(doc_hash)
                results.append({
                    "id": doc.get("document_id", hit["_id"]),
                    "source": doc,
                    "score": hit["_score"],
                })
                
                if len(results) >= num_results:
                    break
        
        return results
    
    async def hybrid_search(
        self,
        query: str,
        num_results: int = 5,
    ) -> List[RetrievalResult]:
        """하이브리드 검색 (klid-aicb 방식: Min-Max 정규화 + 동적 가중치)"""
        # 1. 병렬로 키워드 + 벡터 검색
        keyword_task = self.keyword_search(query, num_results * 2)
        vector_task = self.vector_search(query, num_results * 2)
        
        keyword_results, vector_results = await asyncio.gather(keyword_task, vector_task)
        
        # 2. 결과 병합
        docs = {}
        for hit in keyword_results:
            docs[hit["id"]] = {
                "source": hit["source"],
                "term_score": hit["score"],
                "vector_score": 0.0,
            }
        
        for hit in vector_results:
            if hit["id"] in docs:
                docs[hit["id"]]["vector_score"] = hit["score"]
            else:
                docs[hit["id"]] = {
                    "source": hit["source"],
                    "term_score": 0.0,
                    "vector_score": hit["score"],
                }
        
        if not docs:
            return []
        
        # 3. Min-Max 정규화 (klid-aicb 방식)
        term_scores = np.array([v["term_score"] for v in docs.values()]).reshape(-1, 1)
        vector_scores = np.array([v["vector_score"] for v in docs.values()]).reshape(-1, 1)
        
        term_norm = minmax_scale(term_scores).flatten()
        vector_norm = minmax_scale(vector_scores).flatten()
        
        # 4. 동적 가중치 계산 (쿼리 길이 기반)
        keyword_weight, vector_weight = calculate_dynamic_weights(query)
        
        # 5. 최종 hybrid_similarity 계산
        results = []
        for i, (doc_id, data) in enumerate(docs.items()):
            hybrid_score = float(keyword_weight * term_norm[i] + vector_weight * vector_norm[i])
            
            source = data["source"]
            result = RetrievalResult(
                document_id=doc_id,
                query=source.get("query", ""),
                document=source.get("document", ""),
                score=hybrid_score,
                metadata=source.get("metadata", {}),
                term_similarity=float(term_norm[i]),
                vector_similarity=float(vector_norm[i]),
            )
            results.append(result)
        
        # 6. 점수순 정렬
        results.sort(key=lambda r: r.score, reverse=True)
        
        logger.info(f"Hybrid search '{query[:30]}...' returned {len(results[:num_results])} results (weights: kw={keyword_weight}, vec={vector_weight})")
        return results[:num_results]
    
    async def rrf_search(
        self,
        query: str,
        num_results: int = 5,
        rank_constant: int = 60,
    ) -> List[RetrievalResult]:
        """RRF 하이브리드 검색 (klid-aicb hybrid_search 방식)
        
        Reciprocal Rank Fusion을 사용하여 키워드/벡터 검색 결과를 결합합니다.
        점수 스케일에 무관하게 순위 기반으로 결합하므로 안정적입니다.
        """
        # 1. 병렬로 키워드 + 벡터 검색
        keyword_task = self.keyword_search(query, num_results * 2)
        vector_task = self.vector_search(query, num_results * 2)
        
        keyword_results, vector_results = await asyncio.gather(keyword_task, vector_task)
        
        # 2. RRF 점수 계산
        rrf_scores = reciprocal_rank_fusion(keyword_results, vector_results, k=rank_constant)
        
        if not rrf_scores:
            return []
        
        # 3. 모든 결과를 source 정보와 함께 수집
        all_docs = {}
        for hit in keyword_results + vector_results:
            if hit["id"] not in all_docs:
                all_docs[hit["id"]] = hit["source"]
        
        # 4. RRF 점수순으로 정렬하고 RetrievalResult 생성
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, rrf_score in sorted_docs[:num_results]:
            if doc_id not in all_docs:
                continue
            
            source = all_docs[doc_id]
            result = RetrievalResult(
                document_id=doc_id,
                query=source.get("query", ""),
                document=source.get("document", ""),
                score=rrf_score,
                metadata=source.get("metadata", {}),
                term_similarity=0.0,  # RRF는 개별 점수를 사용하지 않음
                vector_similarity=0.0,
            )
            results.append(result)
        
        logger.info(f"RRF search '{query[:30]}...' returned {len(results)} results (k={rank_constant})")
        return results
    
    async def retrieve(
        self,
        query: str,
        num_results: int = 5,
        search_type: str = "hybrid",
    ) -> Tuple[List[RetrievalResult], str]:
        """통합 검색 메서드
        
        Args:
            query: 검색 쿼리
            num_results: 반환할 결과 수
            search_type: 검색 방식
                - "hybrid": Min-Max 정규화 + 동적 가중치 (기본값)
                - "rrf": Reciprocal Rank Fusion
                - "keyword": 키워드 검색만
                - "vector": 벡터 검색만
        """
        if search_type == "hybrid":
            results = await self.hybrid_search(query, num_results)
        elif search_type == "rrf":
            results = await self.rrf_search(query, num_results)
        elif search_type == "keyword":
            # 키워드 검색 결과를 RetrievalResult로 변환
            raw_results = await self.keyword_search(query, num_results)
            results = [
                RetrievalResult(
                    document_id=r["id"],
                    query=r["source"].get("query", ""),
                    document=r["source"].get("document", ""),
                    score=r["score"],
                    metadata=r["source"].get("metadata", {}),
                )
                for r in raw_results
            ]
        elif search_type == "vector":
            # 벡터 검색 결과를 RetrievalResult로 변환
            raw_results = await self.vector_search(query, num_results)
            results = [
                RetrievalResult(
                    document_id=r["id"],
                    query=r["source"].get("query", ""),
                    document=r["source"].get("document", ""),
                    score=r["score"],
                    metadata=r["source"].get("metadata", {}),
                )
                for r in raw_results
            ]
        else:
            logger.warning(f"Unknown search_type: {search_type}, falling back to hybrid")
            results = await self.hybrid_search(query, num_results)
        
        return results, search_type


# 싱글톤 인스턴스
_retriever_instance: Optional[ElasticsearchRetriever] = None


def get_retriever() -> ElasticsearchRetriever:
    """Retriever 싱글톤 인스턴스 반환"""
    global _retriever_instance
    if _retriever_instance is None:
        logger.info(f"🔧 Retriever 생성 - ES_URL: {ES_URL}")
        logger.info(f"🔧 Retriever 생성 - ES_API_KEY: {'설정됨' if ES_API_KEY else '없음'}")
        _retriever_instance = ElasticsearchRetriever()
    return _retriever_instance


async def close_retriever():
    """Retriever 종료"""
    global _retriever_instance
    if _retriever_instance is not None:
        await _retriever_instance.close()
        _retriever_instance = None
