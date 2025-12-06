"""
Elasticsearch Settings
"""
from elasticsearch import AsyncElasticsearch
from typing import Optional

from src.config import settings


class ElasticsearchClient:
    """Elasticsearch 클라이언트"""
    
    def __init__(self, url: str = None, api_key: str = None):
        self.url = url or settings.elasticsearch_url
        self.api_key = api_key or settings.elasticsearch_api_key
        self._client: Optional[AsyncElasticsearch] = None
    
    async def connect(self):
        """Elasticsearch 연결"""
        # Elastic Cloud API 키 인증 지원
        if self.api_key:
            self._client = AsyncElasticsearch(
                [self.url],
                api_key=self.api_key,
            )
        else:
        self._client = AsyncElasticsearch([self.url])
        
        # 연결 테스트
        info = await self._client.info()
        print(f"✅ Elasticsearch connected: {info['version']['number']}")
    
    async def close(self):
        """연결 종료"""
        if self._client:
            await self._client.close()
    
    @property
    def client(self) -> AsyncElasticsearch:
        """클라이언트 반환"""
        if not self._client:
            raise RuntimeError("Elasticsearch not connected. Call connect() first.")
        return self._client
    
    async def create_index(
        self,
        index_name: str,
        mappings: dict,
        settings: dict = None
    ):
        """인덱스 생성"""
        body = {"mappings": mappings}
        if settings:
            body["settings"] = settings
        
        await self._client.indices.create(
            index=index_name,
            body=body,
            ignore=400  # 이미 존재하면 무시
        )
        print(f"✅ Index created: {index_name}")


# 전역 Elasticsearch 클라이언트
es_client = ElasticsearchClient()





