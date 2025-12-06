"""
Prompt Generator - 시스템 프롬프트 생성 (klid-aicb 패턴)
"""
import logging
from typing import List, Dict
from langchain_core.messages import SystemMessage, BaseMessage, ToolMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool

from src.tool_agents.base import BaseAgentTool

logger = logging.getLogger(__name__)


# 기본 시스템 프롬프트
DEFAULT_SYSTEM_PROMPT = """당신은 제주도 여행 전문가 AI 어시스턴트입니다.

## 역할
사용자의 제주도 여행 계획을 도와주는 친절한 가이드입니다.

## 🔴 중요: 대화 맥락 유지
- **이전 대화 내용을 항상 정확히 참조**하세요
- 사용자가 "거기", "그것", "방금" 등을 언급하면 이전 대화에서 관련 정보를 찾으세요
- 확실하지 않은 정보는 추측하지 말고, 이전 대화에 없다면 솔직히 말하세요
- **절대 없는 정보를 지어내지 마세요**

## 지침
1. **이전 대화를 정확히 참조**하여 맥락을 유지하세요
2. 사용자의 의도를 정확히 파악하세요
3. 친절하고 자연스러운 한국어로 응답하세요
4. 구체적이고 실용적인 정보를 제공하세요
5. **확실하지 않은 정보는 추측하지 마세요**
6. **도구 결과의 특수 마커([WEB_SEARCH_RESULT], [ATTRACTIONS_DATA], [SQL_QUERY_RESULT], [MAP_DATA] 등)는 응답에 포함하지 마세요**
"""


class PromptGenerator:
    """시스템 프롬프트를 생성합니다 (klid-aicb 패턴)
    
    klid-aicb 패턴을 따라:
    - 각 Tool Factory에서 프롬프트를 동적으로 생성
    - Tool 결과를 format_content로 포맷팅
    """
    
    def __init__(self, tool_factory):
        self.tool_factory = tool_factory
    
    async def create_prompt_template(
        self,
        config: RunnableConfig,
        tools: List[BaseTool]
    ) -> ChatPromptTemplate:
        """
        프롬프트 템플릿 생성
        
        Args:
            config: RunnableConfig (chatbot_prompt, metadata 등 포함)
            tools: 사용 가능한 도구 목록
        
        Returns:
            ChatPromptTemplate
        """
        # config에서 커스텀 프롬프트 가져오기
        chatbot_prompt = self.get_chatbot_prompt(config)
        
        # 메타데이터 프롬프트 생성
        metadata_prompt = self.get_metadata_prompt(config)
        
        # Factory에서 도구 프롬프트 생성 (상세 가이드 포함)
        tool_prompt = await self.tool_factory.generate_tool_prompt(config)
        
        # 최종 시스템 프롬프트 조합
        system_content = "\n\n".join(filter(None, [
            chatbot_prompt,
            metadata_prompt,
            tool_prompt
        ]))
        
        # Tool 이름으로 매핑 (format_content 적용용)
        toolkit: Dict[str, BaseTool] = {tool.name: tool for tool in tools}
        
        def format_inputs(messages: List[BaseMessage]) -> Dict:
            """LLM에 전달할 메시지를 포맷팅 (klid-aicb 패턴)
            
            ToolMessage를 만나면 해당 Tool의 format_content를 호출하여
            결과를 포맷팅하고 다음 지시사항을 추가합니다.
            """
            outputs = []
            
            for message in messages:
                # ToolMessage가 아니면 그대로 추가
                if not isinstance(message, ToolMessage):
                    outputs.append(message)
                    continue
                
                # ToolMessage인 경우 format_content 적용
                tool_name = message.name
                tool = toolkit.get(tool_name)
                
                if isinstance(tool, BaseAgentTool):
                    # BaseAgentTool의 format_content 호출
                    formatted_message = tool.format_content(message)
                    outputs.append(formatted_message)
                else:
                    # 일반 Tool이면 그대로 추가
                    outputs.append(message)
            
            return {"messages": outputs}
        
        # Prompt Template 생성
        return RunnableLambda(format_inputs) | ChatPromptTemplate.from_messages([
            SystemMessage(content=system_content),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def get_chatbot_prompt(self, config: RunnableConfig) -> str:
        """config에서 챗봇 프롬프트 가져오기"""
        configurable = config.get("configurable", {})
        return configurable.get("chatbot_prompt", DEFAULT_SYSTEM_PROMPT)
    
    def get_metadata_prompt(self, config: RunnableConfig) -> str:
        """config에서 메타데이터 가져와서 프롬프트 생성"""
        configurable = config.get("configurable", {})
        metadata = configurable.get("metadata")
        
        if metadata and isinstance(metadata, dict):
            items = [f"- {key}: {value}" for key, value in metadata.items()]
            return "## 참고 메타데이터\n" + "\n".join(items)
        
        return ""
