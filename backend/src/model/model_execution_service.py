"""
Model Execution Service - LLM 실행 관리
"""
from typing import List, Optional, Any, Dict, AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from src.config import settings


class ModelExecutionService:
    """LLM 실행 서비스"""
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 1.0,  # gpt-5-mini는 temperature=0 미지원
        api_key: str = None
    ):
        self.model_name = model_name or settings.openai_model
        self.temperature = temperature
        self.api_key = api_key or settings.openai_api_key
        
        # API 키가 없으면 에러 발생
        if not self.api_key:
            raise ValueError(
                "OpenAI API 키가 설정되지 않았습니다. "
                "환경 변수 OPENAI_API_KEY를 설정해주세요."
            )
        
        # LangChain ChatOpenAI 초기화
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.api_key,
            stream_usage=True  # 토큰 사용량 추적 활성화
        )
    
    async def execute(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> BaseMessage:
        """
        LLM 실행
        
        Args:
            messages: 메시지 리스트
            tools: 사용 가능한 도구 (LangChain Tool 형식)
            **kwargs: 추가 파라미터
        
        Returns:
            LLM 응답 메시지
        """
        if tools:
            # Tool binding
            llm_with_tools = self.llm.bind_tools(tools)
            response = await llm_with_tools.ainvoke(messages, **kwargs)
        else:
            response = await self.llm.ainvoke(messages, **kwargs)
        
        return response
    
    async def stream(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        스트리밍 LLM 실행
        
        Args:
            messages: 메시지 리스트
            tools: 사용 가능한 도구 (LangChain Tool 형식)
            **kwargs: 추가 파라미터
        
        Yields:
            스트림 청크 (텍스트)
        """
        if tools:
            # Tool binding
            llm_with_tools = self.llm.bind_tools(tools)
            async for chunk in llm_with_tools.astream(messages, **kwargs):
                # AIMessageChunk에서 content 추출
                if hasattr(chunk, 'content'):
                    content = chunk.content
                    if content:
                        # 문자열이면 그대로, 리스트면 합치기
                        if isinstance(content, str):
                            yield content
                        elif isinstance(content, list):
                            # Delta 형식일 수 있음
                            for delta in content:
                                if isinstance(delta, str):
                                    yield delta
                                elif hasattr(delta, 'content'):
                                    yield delta.content
        else:
            async for chunk in self.llm.astream(messages, **kwargs):
                if hasattr(chunk, 'content'):
                    content = chunk.content
                    if content:
                        if isinstance(content, str):
                            yield content
                        elif isinstance(content, list):
                            for delta in content:
                                if isinstance(delta, str):
                                    yield delta
                                elif hasattr(delta, 'content'):
                                    yield delta.content
    
    def create_streaming_executor(self):
        """스트리밍 실행기 생성 (하위 호환성)"""
        return self





