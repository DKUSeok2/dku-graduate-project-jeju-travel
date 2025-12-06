"""
Supervisor Agent Nodes - LangGraph 노드들 (klid-aicb 방식)
+ 대화 맥락 요약 기능
+ Intent Router 연동 (규칙 기반 도구 선택)
"""
import logging
from typing import Any, Dict, List, Optional
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
    AnyMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool
from langchain_core.messages.utils import trim_messages

from src.supervisor_agent.state import LangGraphAgentState
from src.supervisor_agent.prompt_generator import PromptGenerator
from src.supervisor_agent.intent_router import get_intent_router, ParsedQuery

logger = logging.getLogger(__name__)


# 맥락 요약 임계값 (메시지 개수)
CONTEXT_SUMMARY_THRESHOLD = 10


class LangAgentNode:
    """LLM을 통해 응답을 생성하는 노드 (klid-aicb 방식 + 맥락 요약)"""
    
    def __init__(
        self,
        execution_service,
        tool_factory,
        prompt_generator: PromptGenerator,
    ):
        self.execution_service = execution_service
        self.tool_factory = tool_factory
        self.prompt_generator = prompt_generator
        self._context_cache: Dict[str, str] = {}  # session_id → context_summary
    
    async def __call__(
        self,
        state: LangGraphAgentState,
        config: RunnableConfig = None
    ) -> LangGraphAgentState:
        """
        Agent 노드 실행
        
        1. Intent Router로 도구 선택 강제
        2. 프롬프트 템플릿 로드
        3. 도구 바인딩 (tool_choice로 강제!)
        4. LLM 호출
        """
        # 🔥 Intent Router: 도구 선택을 강제로 결정
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        # 🔥 핵심 수정: 마지막 메시지가 ToolMessage면 tool_choice 해제! (무한 루프 방지)
        # Tool 결과를 받은 후에는 자동 선택 모드로 전환하여 LLM이 응답 생성
        if isinstance(last_message, ToolMessage):
            print(f"⚠️ 마지막 메시지가 ToolMessage → tool_choice 해제 (응답 생성 모드)")
            forced_tool = None
        else:
            # HumanMessage가 있으면 Intent Router로 tool 선택
            last_human = get_last_human_message(messages)
            forced_tool = None
            
            if last_human:
                router = get_intent_router()
                parsed = router.parse(last_human.content)
                forced_tool = parsed.tool_name
                
                # 🔴 일정 도구인데 기간 정보가 없으면 tool_choice 해제 (바로 질문)
                if forced_tool == "generate_travel_itinerary":
                    query = last_human.content
                    import re
                    has_duration = any(re.search(p, query) for p in [
                        r'\d+박\s*\d+일', r'\d+일', r'\d+박'
                    ])
                    if not has_duration:
                        print(f"⚠️ 일정 요청이지만 기간 없음 → tool_choice 해제 (바로 질문)")
                        forced_tool = None
                
                print(f"🎯 Intent Router 도구 강제: {forced_tool} (intent={parsed.intent})")
        
        # config에 forced_tool 저장
        if config is None:
            config = {}
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"]["forced_tool"] = forced_tool
        
        # Chain 로드 (프롬프트 + 모델 + 도구)
        chain = await self.load_chain_from_config(config)
        
        # LLM 호출
        message = await self.invoke_llm(chain, state, config)
        
        # 결과 반환
        result = {"messages": [message]}
        
        # 도구 호출이 없으면 최종 응답으로 설정
        if not (hasattr(message, "tool_calls") and message.tool_calls):
            result["final_response"] = message.content
        
        return result
    
    async def load_chain_from_config(self, config: RunnableConfig) -> Runnable:
        """
        config에서 LLM Chain을 생성
        
        1. 프롬프트 템플릿 생성
        2. 도구 목록 가져오기
        3. LLM 모델 로드
        4. 도구 바인딩
        """
        # 도구 목록 가져오기
        tools = await self.get_tool_list(config)  # await 추가!
        
        print(f"🔗 load_chain_from_config: {len(tools)}개 도구 로드됨")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
        
        # 프롬프트 템플릿 생성
        prompt = await self.prompt_generator.create_prompt_template(config, tools)
        
        # LLM 모델 로드 (기본 모델)
        # klid-aicb는 model_id를 사용하지만, 우리는 단순화
        model = self.execution_service.llm
        
        # 도구가 있으면 바인딩
        if tools:
            print(f"🔗 LLM에 {len(tools)}개 도구 바인딩 중...")
            
            # 🔥 Intent Router가 지정한 도구 강제 (tool_choice)
            forced_tool = config.get("configurable", {}).get("forced_tool")
            
            if forced_tool:
                # 해당 도구가 실제로 있는지 확인
                tool_exists = any(t.name == forced_tool for t in tools)
                
                if tool_exists:
                    print(f"🎯 도구 강제: {forced_tool}")
                    bound_model = model.bind_tools(
                        tools, 
                        tool_choice={"type": "function", "function": {"name": forced_tool}}
                    )
                else:
                    print(f"⚠️ 강제 도구 {forced_tool}가 목록에 없음, 자동 선택")
                    bound_model = model.bind_tools(tools)
            else:
                bound_model = model.bind_tools(tools)
            
            print(f"✅ 도구 바인딩 완료!")
            return prompt | bound_model
        else:
            print(f"⚠️ 도구 없음 - 바인딩 생략")
            return prompt | model
    
    async def get_tool_list(self, config: RunnableConfig) -> List[BaseTool]:
        """Tool 목록을 반환 (klid-aicb 방식)"""
        configurable = config.get("configurable", {})
        tool_agents = configurable.get("tool_agents", {})
        
        print(f"🔧 get_tool_list 호출됨")
        print(f"   tool_agents config: {tool_agents}")
        
        # DynamicToolFactory를 사용하여 tool 목록 생성
        tools = []
        for tool_type, tool_config in tool_agents.items():
            print(f"   Checking tool: {tool_type}")
            
            # 🔥 이미 등록된 도구가 있으면 재사용
            existing_tools = self.tool_factory.get_all_tools()
            tool_found = False
            
            for existing_tool in existing_tools:
                # 도구 타입으로 매칭 (이름이 다를 수 있으므로)
                if tool_type == "web_search" and existing_tool.name == "search_realtime_info":
                    tools.append(existing_tool)
                    tool_found = True
                    print(f"   ♻️ Reusing existing tool: {existing_tool.name}")
                    break
                elif tool_type == "sql_query" and existing_tool.name == "query_jeju_database":
                    tools.append(existing_tool)
                    tool_found = True
                    print(f"   ♻️ Reusing existing tool: {existing_tool.name}")
                    break
                elif tool_type == "map_visualization" and existing_tool.name == "visualize_attractions_on_map":
                    tools.append(existing_tool)
                    tool_found = True
                    print(f"   ♻️ Reusing existing tool: {existing_tool.name}")
                    break
                elif tool_type == "rag_search" and existing_tool.name == "search_jeju_attractions":
                    tools.append(existing_tool)
                    tool_found = True
                    print(f"   ♻️ Reusing existing tool: {existing_tool.name}")
                    break
                elif tool_type == "route_optimizer" and existing_tool.name == "optimize_travel_route":
                    tools.append(existing_tool)
                    tool_found = True
                    print(f"   ♻️ Reusing existing tool: {existing_tool.name}")
                    break
            
            # 없으면 새로 생성
            if not tool_found:
                print(f"   Creating new tool: {tool_config}")
                tool = await self.tool_factory.create_tool(tool_config)
                if tool:
                    print(f"   ✅ Tool created: {tool.name}")
                    # Factory에 등록
                    self.tool_factory.register_tool(tool)
                    tools.append(tool)
                else:
                    print(f"   ❌ Tool creation failed")
        
        print(f"🔧 Total tools in list: {len(tools)}")
        return tools
    
    async def invoke_llm(
        self,
        chain: Runnable,
        state: LangGraphAgentState,
        config: RunnableConfig
    ) -> AIMessage:
        """
        LLM 호출 (klid-aicb 방식 + 맥락 요약 + Intent Router)
        
        1. Intent Router로 도구/조건 추출 (규칙 기반)
        2. 대화가 길면 맥락 요약 생성
        3. 메시지 히스토리 trim (토큰 제한)
        4. Chain 실행
        """
        try:
            messages = state["messages"]
            trimmed_messages = list(messages)
            
            # 🔥 Intent Router: 사용자 쿼리에서 도구/조건 추출
            parsed_query = None
            last_human = get_last_human_message(messages)
            if last_human:
                router = get_intent_router()
                parsed_query = router.parse(last_human.content)
                
                print(f"🎯 Intent Router 결과:")
                print(f"   - Intent: {parsed_query.intent}")
                print(f"   - Tool: {parsed_query.tool_name}")
                print(f"   - Conditions: {parsed_query.conditions}")
                
                # 추출된 조건을 시스템 메시지에 추가
                if parsed_query.conditions:
                    condition_str = self._format_conditions(parsed_query)
                    
                    if trimmed_messages and isinstance(trimmed_messages[0], SystemMessage):
                        original_content = trimmed_messages[0].content
                        enhanced_content = f"{original_content}\n\n{condition_str}"
                        trimmed_messages[0] = SystemMessage(content=enhanced_content)
                        print(f"✅ 조건이 시스템 메시지에 추가됨")
            
            # 대화가 길면 맥락 요약 추가
            if len(messages) >= CONTEXT_SUMMARY_THRESHOLD:
                context_summary = self._extract_context_info(messages)
                if context_summary:
                    # 첫 번째 메시지가 SystemMessage인지 확인
                    if trimmed_messages and isinstance(trimmed_messages[0], SystemMessage):
                        # 시스템 메시지에 맥락 추가
                        original_content = trimmed_messages[0].content
                        enhanced_content = f"{original_content}\n\n## 📋 대화 맥락 요약\n{context_summary}"
                        trimmed_messages = [
                            SystemMessage(content=enhanced_content)
                        ] + list(trimmed_messages[1:])
                        logger.info(f"🧠 대화 맥락 요약 추가됨")
                        print(f"🧠 대화 맥락 요약 추가됨: {context_summary[:100]}...")
            
            # 메시지가 너무 많으면 trim (10,000 토큰 제한)
            if len(trimmed_messages) > 20:
                from langchain_openai import ChatOpenAI
                
                # token_counter를 위한 임시 LLM 인스턴스
                temp_llm = ChatOpenAI(model="gpt-4o-mini")
                
                trimmed_messages = trim_messages(
                    trimmed_messages,
                    max_tokens=10000,
                    strategy="last",  # 마지막 메시지들을 우선 유지
                    token_counter=temp_llm,
                    include_system=True,  # 시스템 메시지 포함
                    start_on="human",
                )
                logger.info(f"메시지 trim: {len(state['messages'])} → {len(trimmed_messages)}")
            
            print(f"🤖 LLM 호출 중... ({len(trimmed_messages)}개 메시지)")
            
            # Chain 실행
            message = await chain.ainvoke(trimmed_messages, config=config)
            
            print(f"✅ LLM 응답 받음")
            print(f"   - Content: {message.content[:100] if message.content else 'None'}...")
            print(f"   - Has tool_calls: {hasattr(message, 'tool_calls') and bool(message.tool_calls)}")
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                print(f"   🔧 Tool calls detected: {len(message.tool_calls)}개")
                for i, tool_call in enumerate(message.tool_calls):
                    print(f"      [{i}] {tool_call.get('name', 'unknown')}({tool_call.get('args', {})})")
            else:
                print(f"   ⚠️ No tool calls - LLM이 도구를 호출하지 않음")
            
            return message
            
        except Exception as e:
            logger.error(f"LLM 호출 중 에러: {e}")
            # 에러 메시지 반환
            return AIMessage(content=f"오류가 발생했습니다: {str(e)}")
    
    def _extract_context_info(self, messages: List[AnyMessage]) -> Optional[str]:
        """대화에서 맥락 정보 추출 (간단한 규칙 기반)
        
        이전 대화에서 중요한 정보를 추출:
        - 생성된 일정 정보
        - 검색된 장소들
        - 사용자의 선호도
        """
        context_parts = []
        
        # 사용자 요청 키워드 추출
        user_requests = []
        searched_places = []
        itinerary_info = None
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                # 주요 요청 키워드 추출
                if any(kw in content for kw in ["일정", "계획", "코스", "박", "일"]):
                    user_requests.append(f"일정 요청: {content[:50]}")
                elif any(kw in content for kw in ["맛집", "카페", "추천"]):
                    user_requests.append(f"장소 검색: {content[:50]}")
            
            elif isinstance(msg, ToolMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                # 일정 생성 결과 감지
                if "ITINERARY_DATA" in content or "일정" in content:
                    itinerary_info = "여행 일정이 생성됨"
                # 장소 검색 결과 감지
                if "name" in content and ("rating" in content or "카페" in content or "맛집" in content):
                    searched_places.append("장소 검색 결과 있음")
        
        # 맥락 요약 생성
        if user_requests:
            context_parts.append(f"이전 요청: {', '.join(user_requests[-3:])}")  # 최근 3개
        
        if itinerary_info:
            context_parts.append(f"상태: {itinerary_info}")
        
        if searched_places:
            context_parts.append("이전에 장소 검색 결과가 제공됨")
        
        if context_parts:
            return "\n".join(context_parts)
        
        return None
    
    def _format_conditions(self, parsed: ParsedQuery) -> str:
        """추출된 조건을 시스템 메시지용 문자열로 포맷팅 + 도구 선택 강제"""
        
        # 도구 설명 매핑
        tool_descriptions = {
            "search_jeju_attractions": "관광지/볼거리/액티비티 검색 (Elasticsearch)",
            "query_jeju_database": "맛집/카페/숙소 검색 (PostgreSQL)",
            "generate_travel_itinerary": "여행 일정 생성",
            "search_realtime_info": "실시간 정보 검색 (날씨/축제/행사)",
            "optimize_travel_route": "경로 최적화",
            "visualize_attractions_on_map": "지도 시각화",
        }
        
        tool_desc = tool_descriptions.get(parsed.tool_name, parsed.tool_name)
        
        parts = [
            "## ⚠️ 도구 선택 지시 (반드시 따르세요!)",
            f"",
            f"🔴 **반드시 `{parsed.tool_name}` 도구를 사용하세요!**",
            f"   - 용도: {tool_desc}",
            f"   - 의도 분류: {parsed.intent}",
            f"",
        ]
        
        conditions = parsed.conditions
        
        if conditions:
            parts.append("## 추출된 조건")
            
            if "region" in conditions:
                parts.append(f"- 지역: {conditions.get('region_keyword', '')} → region = '{conditions['region']}'")
            
            if "min_rating" in conditions:
                parts.append(f"- 평점: rating >= {conditions['min_rating']}")
            
            if conditions.get("parking"):
                parts.append("- 주차: parking = true")
            
            if conditions.get("kid_friendly"):
                parts.append("- 아이동반: kid_friendly = true")
            
            if "limit" in conditions:
                parts.append(f"- 개수: LIMIT {conditions['limit']}")
            
            if "category_hint" in conditions:
                hint_map = {"restaurant": "음식점", "cafe": "카페", "accommodation": "숙소"}
                parts.append(f"- 카테고리: {hint_map.get(conditions['category_hint'], conditions['category_hint'])}")
        
        return "\n".join(parts)


def create_agent_node(execution_service, tool_factory):
    """
    Agent 노드 생성 (클로저로 의존성 주입)
    """
    prompt_generator = PromptGenerator(tool_factory)  # tool_factory 전달!
    agent = LangAgentNode(
        execution_service=execution_service,
        tool_factory=tool_factory,
        prompt_generator=prompt_generator,
    )
    return agent.__call__


def create_dynamic_tool_node(tool_factory):
    """
    Dynamic Tool 노드 생성 (klid-aicb 패턴: ToolNode 사용)
    """
    from langgraph.prebuilt import ToolNode
    
    async def dynamic_tool_node(
        state: LangGraphAgentState,
        config: RunnableConfig = None
    ) -> Dict[str, Any]:
        """
        Tool 노드 - ToolNode를 사용하여 artifact 자동 처리 (klid-aicb 패턴)
        """
        print(f"🔧 dynamic_tool_node 호출됨 (klid-aicb 패턴: ToolNode 사용)")
        
        # 동적으로 tool 목록 가져오기
        tools = tool_factory.get_all_tools()
        print(f"   🔧 Available tools: {[t.name for t in tools]}")
        
        # ToolNode 생성 및 실행 (artifact 자동 처리!)
        tool_node = ToolNode(tools)
        result = await tool_node.ainvoke(state, config)
        
        print(f"   ✅ ToolNode execution completed")
        
        return result
    
    return dynamic_tool_node


def tools_condition(state: LangGraphAgentState) -> str:
    """
    도구 호출 여부를 결정하는 조건 함수
    
    마지막 AIMessage에 tool_calls가 있으면 "tools"
    없으면 "__end__"
    """
    messages = state.get("messages", [])
    if not messages:
        return "__end__"
    
    last_message = messages[-1]
    
    # AIMessage이고 tool_calls가 있으면 tools로
    if isinstance(last_message, AIMessage):
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
    
    return "__end__"


def get_last_human_message(messages: List[AnyMessage]) -> HumanMessage | None:
    """메시지 목록에서 마지막 HumanMessage를 반환"""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message
    return None
