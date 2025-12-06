"""
Supervisor Agent Service
"""
from typing import Optional, Dict, Any, List, AsyncGenerator
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
    AnyMessage,
)
from langchain_core.callbacks import UsageMetadataCallbackHandler
from sqlalchemy import text

from src.supervisor_agent.graph import create_langgraph_agent
from src.supervisor_agent.state import LangGraphAgentState
from src.supervisor_agent.helper import AgentHelper
from src.config import settings
from src.database import AsyncSessionLocal


# Tool name → 통계용 이름 매핑
TOOL_NAME_MAP = {
    "query_jeju_database": "sql_agent",
    "search_jeju_attractions": "rag_agent",
    "search_realtime_info": "web_search",
    "generate_travel_itinerary": "itinerary",
}


async def log_tool_usage(tool_name: str, session_id: str = None):
    """도구 사용 기록 저장"""
    mapped_name = TOOL_NAME_MAP.get(tool_name)
    if not mapped_name:
        return  # 매핑되지 않은 도구는 기록 안 함
    
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("INSERT INTO tool_usage (tool_name, session_id) VALUES (:tool_name, :session_id)"),
                {"tool_name": mapped_name, "session_id": session_id}
            )
            await db.commit()
            print(f"   📊 Tool 사용 기록: {mapped_name}")
    except Exception as e:
        print(f"   ⚠️ Tool 사용 기록 실패: {e}")


class SupervisorAgentService:
    """Supervisor Agent 서비스 (klid-aicb 방식)"""
    
    def __init__(
        self,
        execution_service,
        tool_factory,
        helper: Optional[AgentHelper] = None
    ):
        self.execution_service = execution_service
        self.tool_factory = tool_factory
        self.helper = helper or AgentHelper()
        self._agent = None
    
    async def initialize(self):
        """Agent 초기화"""
        self._agent = await create_langgraph_agent(
            execution_service=self.execution_service,
            tool_factory=self.tool_factory,
            helper=self.helper
        )
    
    async def get_chat_history(self, session_id: str) -> List[AnyMessage]:
        """
        세션의 대화 히스토리 조회 (klid-aicb 방식)
        
        Args:
            session_id: 세션 ID
        
        Returns:
            메시지 리스트
        """
        if not self._agent:
            await self.initialize()
        
        config = await self.helper.get_runnable_config(session_id)
        state = await self._agent.aget_state(config)
        messages = state.values.get("messages", [])
        
        return messages
    
    async def chat(
        self,
        message: str,
        session_id: str,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        채팅 실행 (비스트리밍)
        
        Args:
            message: 사용자 메시지
            session_id: 세션 ID (대화 상태 관리)
            user_profile: 사용자 프로필
        
        Returns:
            응답 및 메타데이터
        """
        if not self._agent:
            await self.initialize()
        
        # RunnableConfig 생성 (thread_id로 이전 대화 자동 로드)
        config = await self.helper.get_runnable_config(
            session_id=session_id,
            metadata=user_profile
        )
        
        # 새 메시지만 전달 (LangGraph가 자동으로 이전 대화와 합침)
        inbound = HumanMessage(content=message)
        
        try:
            result = await self._agent.ainvoke(
                {"messages": [inbound]},
                config=config
            )
            
            # 최종 응답 추출
            final_response = result.get("final_response")
            if not final_response:
                # 마지막 AIMessage에서 응답 추출
                messages = result.get("messages", [])
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        final_response = msg.content
                        break
            
            return {
                "response": final_response or "응답을 생성하지 못했습니다",
                "tool_results": result.get("tool_results", []),
                "metadata": {
                    "session_id": session_id,
                    "message_count": len(result.get("messages", []))
                }
            }
        except Exception as e:
            return {
                "response": f"오류가 발생했습니다: {str(e)}",
                "tool_results": [],
                "metadata": {"session_id": session_id, "error": str(e)}
            }
    
    async def stream_chat(
        self,
        message: str,
        session_id: str,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        스트리밍 채팅 실행 (klid-aicb 방식)
        
        Args:
            message: 사용자 메시지
            session_id: 세션 ID
            user_profile: 사용자 프로필
        
        Yields:
            스트림 청크 (텍스트)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        print(f"🔥🔥🔥 stream_chat 호출됨: session_id={session_id}, message={message[:50]}")
        
        if not self._agent:
            print("🔥 Agent 초기화 시작...")
            await self.initialize()
            print("🔥 Agent 초기화 완료!")
        
        # RunnableConfig 생성 (thread_id로 이전 대화 자동 로드)
        config = await self.helper.get_runnable_config(
            session_id=session_id,
            metadata=user_profile
        )
        
        # 🔥 klid-aicb 방식: UsageMetadataCallbackHandler로 토큰 수집
        usage_callback = UsageMetadataCallbackHandler()
        config["callbacks"] = [usage_callback]
        
        print(f"💬 세션 {session_id}로 스트리밍 시작")
        logger.info(f"💬 세션 {session_id}로 스트리밍 시작")
        
        # 이전 대화 히스토리 확인 (디버깅용)
        try:
            state = await self._agent.aget_state(config)
            history = state.values.get("messages", [])
            print(f"📜 기존 대화 히스토리: {len(history)}개 메시지")
            logger.info(f"📜 기존 대화 히스토리: {len(history)}개 메시지")
            for i, msg in enumerate(history[-5:]):  # 최근 5개만
                print(f"  [{i}] {msg.__class__.__name__}: {msg.content[:50]}...")
                logger.info(f"  [{i}] {msg.__class__.__name__}: {msg.content[:50]}...")
        except Exception as e:
            print(f"⚠️ 대화 히스토리 조회 실패: {e}")
            logger.warning(f"대화 히스토리 조회 실패: {e}")
        
        # 새 메시지만 전달 (LangGraph가 자동으로 이전 대화와 합침)
        inbound = HumanMessage(content=message)
        print(f"➡️ 새 메시지: {message}")
        logger.info(f"➡️  새 메시지: {message}")
        
        # 🔥 Intent Router 결과 미리 보여주기
        from src.supervisor_agent.intent_router import get_intent_router
        router = get_intent_router()
        parsed = router.parse(message)
        
        # 사용자에게 분석 과정 피드백
        intent_labels = {
            "itinerary": "📅 일정 생성",
            "attraction": "🏝️ 관광지 검색", 
            "place_search": "🍽️ 장소 검색",
            "realtime": "🌐 실시간 정보",
            "route_optimize": "🗺️ 경로 최적화",
            "map": "📍 지도 표시"
        }
        intent_label = intent_labels.get(parsed.intent, "🔍 검색")
        
        # 조건이 있으면 표시
        conditions_text = ""
        if parsed.conditions:
            cond_parts = []
            if "region" in parsed.conditions:
                cond_parts.append(f"지역: {parsed.conditions.get('region_keyword', parsed.conditions['region'])}")
            if "min_rating" in parsed.conditions:
                cond_parts.append(f"평점: {parsed.conditions['min_rating']}↑")
            if parsed.conditions.get("parking"):
                cond_parts.append("주차 가능")
            if parsed.conditions.get("kid_friendly"):
                cond_parts.append("아이 동반")
            if cond_parts:
                conditions_text = f" ({', '.join(cond_parts)})"
        
        try:
            # LangGraph astream 사용 (klid-aicb 방식)
            # Note: Checkpointer가 설정되어 있으면 자동으로 대화 상태 저장/로드
            # UsageMetadataCallbackHandler가 콜백으로 토큰 사용량 수집
            
            # 🔥 빠른 피드백: Intent Router 결과 기반으로 **먼저** THINKING 전송
            intent_thinking_map = {
                "itinerary": "여행 일정 생성 중",
                "attraction": f"관광지 DB 검색 중{conditions_text}",
                "subjective_place": f"분위기/감성 검색 중{conditions_text}",  # 🆕 감성 검색
                "place_search": f"맛집/카페 DB 검색 중{conditions_text}",
                "accommodation": f"숙소 DB 검색 중{conditions_text}",
                "realtime": "웹 검색 중 (날씨/축제/행사)",
                "route_optimize": "최적 경로 계산 중",
                "map": "지도 생성 중",
            }
            initial_thinking = intent_thinking_map.get(parsed.intent, "처리 중")
            yield f"[THINKING]{initial_thinking}[/THINKING]"
            
            tool_call_detected = False
            feedback_sent = True  # 이미 Intent Router 기반으로 보냈으므로 True
            
            # 🔥 중복 전송 방지: 이미 전송된 마커 추적
            sent_markers = set()  # 'itinerary', 'sql', 'web_search', 'map', 'attractions'
            
            # recursion_limit 설정 (무한 루프 방지)
            config["recursion_limit"] = 30  # 도구 호출 횟수 제한
            
            async for stream_mode, chunk in self._agent.astream(
                {"messages": [inbound]},
                config,
                stream_mode=["messages", "updates"]
            ):
                if stream_mode == "messages":
                    msg, metadata = chunk
                    # agent 노드에서 나온 AIMessageChunk만 전송
                    if metadata.get("langgraph_node") != "agent":
                        continue
                    if isinstance(msg, AIMessageChunk):
                        # 🔥 도구 호출 감지 시 즉시 피드백 (THINKING 마커로 전송)
                        if hasattr(msg, 'tool_calls') and msg.tool_calls and not feedback_sent:
                            tool_call_detected = True
                            
                            # 도구별 피드백 메시지 (데이터 소스 명확히 구분)
                            for tc in msg.tool_calls:
                                tool_name = tc.get('name', '')
                                
                                thinking_msg = ""
                                if tool_name == 'query_jeju_database':
                                    # SQL Agent → PostgreSQL (맛집, 카페, 숙소 등 구조화 데이터)
                                    thinking_msg = f"맛집/카페 DB 검색 중{conditions_text}"
                                elif tool_name == 'search_jeju_attractions':
                                    # RAG Agent → Elasticsearch (관광지 정보)
                                    thinking_msg = f"관광지 DB 검색 중{conditions_text}"
                                elif tool_name == 'generate_travel_itinerary':
                                    thinking_msg = "여행 일정 생성 중"
                                elif tool_name == 'search_realtime_info':
                                    # Web Search → 네이버/구글 (실시간 정보)
                                    thinking_msg = "웹 검색 중 (날씨/축제/행사)"
                                elif tool_name == 'optimize_travel_route':
                                    thinking_msg = "최적 경로 계산 중"
                                elif tool_name == 'visualize_attractions_on_map':
                                    thinking_msg = "지도 생성 중"
                                else:
                                    thinking_msg = "처리 중"
                                
                                # THINKING 마커로 전송 (프론트에서 특별 처리)
                                yield f"[THINKING]{thinking_msg}[/THINKING]"
                            feedback_sent = True
                        
                        if msg.content:
                            yield msg.content
                
                elif stream_mode == "updates":
                    # Tool 실행 결과 처리
                    print(f"🔧 updates 수신: {chunk}")
                    logger.info(f"🔧 updates 수신: {chunk}")
                    
                    node_name, node_result = list(chunk.items())[0]
                    print(f"   노드: {node_name}")
                    
                    if node_name == "tools":
                        print(f"   🛠️ tools 노드 처리 중...")
                        
                        # 🔥 도구 실행 완료 → "응답 생성 중" 전송
                        yield "[THINKING]응답 생성 중[/THINKING]"
                        
                        # Tool 메시지에서 artifact 추출
                        messages = node_result.get("messages", [])
                        print(f"   메시지 개수: {len(messages)}")
                        
                        for msg in messages:
                            print(f"   메시지 타입: {type(msg).__name__}")
                            if isinstance(msg, ToolMessage):
                                print(f"      ✅ ToolMessage 발견! name={msg.name}")
                                
                                # 🔥 Tool 사용 통계 기록 (4개만: sql_agent, rag_agent, web_search, itinerary)
                                await log_tool_usage(msg.name, session_id)
                                
                                # ToolMessage의 name으로 tool 타입 확인
                                if msg.name == "search_realtime_info":
                                    print(f"      🌐 Web Search 결과 전송!")
                                    import json as json_lib
                                    
                                    # 🔥 중복 전송 방지
                                    if 'web_search' in sent_markers:
                                        print(f"      ⚠️ WEB_SEARCH 이미 전송됨, 스킵!")
                                        continue
                                    
                                    # artifact에서 데이터 추출 (klid-aicb 패턴)
                                    artifact = getattr(msg, 'artifact', None)
                                    if artifact and artifact.get('type') == 'web_search':
                                        marker_content = f"\n\n[WEB_SEARCH_RESULT]{json_lib.dumps(artifact, ensure_ascii=False)}[/WEB_SEARCH_RESULT]\n\n"
                                        print(f"      ✅ artifact 사용: {artifact.get('total_results', 0)}개 결과")
                                    else:
                                        # fallback: content 사용
                                        marker_content = f"\n\n[WEB_SEARCH_RESULT]{msg.content}[/WEB_SEARCH_RESULT]\n\n"
                                        print(f"      ⚠️ fallback: content 사용")
                                    
                                    print(f"      마커 길이: {len(marker_content)}")
                                    sent_markers.add('web_search')
                                    yield marker_content
                                    
                                elif msg.name == "search_jeju_attractions":
                                    print(f"      🔍 RAG Search 결과 전송!")
                                    import json as json_lib
                                    
                                    # 🔥 중복 전송 방지
                                    if 'rag_search' in sent_markers:
                                        print(f"      ⚠️ RAG_SEARCH 이미 전송됨, 스킵!")
                                        continue
                                    
                                    # artifact에서 데이터 추출 (klid-aicb 패턴)
                                    artifact = getattr(msg, 'artifact', None)
                                    if artifact and artifact.get('type') == 'rag_search':
                                        marker_content = f"\n\n[RAG_SEARCH_RESULT]{json_lib.dumps(artifact, ensure_ascii=False)}[/RAG_SEARCH_RESULT]\n\n"
                                        print(f"      ✅ artifact 사용: {artifact.get('total_results', 0)}개 결과")
                                    else:
                                        # fallback: content 사용
                                        marker_content = f"\n\n[RAG_SEARCH_RESULT]{msg.content}[/RAG_SEARCH_RESULT]\n\n"
                                        print(f"      ⚠️ fallback: content 사용")
                                    
                                    print(f"      마커 길이: {len(marker_content)}")
                                    sent_markers.add('rag_search')
                                    yield marker_content
                                    
                                elif msg.name == "query_jeju_database":
                                    print(f"      🗄️ SQL Agent 결과 전송!")
                                    # 🔥 중복 전송 방지
                                    if 'sql' in sent_markers:
                                        print(f"      ⚠️ SQL 이미 전송됨, 스킵!")
                                        continue
                                    
                                    import re
                                    import json as json_lib
                                    
                                    # artifact에서 직접 데이터 추출 (hallucination 방지!)
                                    artifact = getattr(msg, 'artifact', None)
                                    
                                    # 🔥 핵심 수정: artifact가 있으면 무조건 사용 (data가 비어있어도)
                                    if artifact:
                                        # artifact 패턴: 구조화된 데이터 사용
                                        sql_query = artifact.get('sql_query', '')
                                        # data가 없거나 빈 dict일 수 있으므로 안전하게 처리
                                        data_dict = artifact.get('data', {})
                                        documents = data_dict.get('documents', []) if isinstance(data_dict, dict) else []
                                        row_count = len(documents)
                                        
                                        sql_result_data = {
                                            "query": "",  # 사용자 질의는 별도 추출 필요 시 추가
                                            "sql_query": sql_query,
                                            "artifact": artifact,  # 🔥 artifact 직접 포함!
                                            "row_count": row_count
                                        }
                                        print(f"      ✅ artifact 사용: {row_count}개 데이터 (artifact.data 존재: {bool(data_dict)})")
                                    else:
                                        # fallback: 기존 방식 (마크다운 파싱)
                                        content = msg.content
                                        
                                        # SQL 쿼리 추출
                                        sql_match = re.search(r'```sql\s*\n(.*?)\n```', content, re.DOTALL)
                                        sql_query = sql_match.group(1).strip() if sql_match else ""
                                        
                                        # 조회 결과 추출
                                        result_match = re.search(r'## 조회 결과 \((\d+)개\)', content)
                                        row_count = int(result_match.group(1)) if result_match else 0
                                        
                                        sql_result_data = {
                                            "query": "",
                                            "sql_query": sql_query,
                                            "data": content,
                                            "row_count": row_count
                                        }
                                        print(f"      ⚠️ fallback 사용: 마크다운 파싱 (artifact 없음)")
                                    
                                    # SQL 마커 추가
                                    marker_content = f"\n\n[SQL_QUERY_RESULT]{json_lib.dumps(sql_result_data, ensure_ascii=False)}[/SQL_QUERY_RESULT]\n\n"
                                    print(f"      SQL 마커 길이: {len(marker_content)}")
                                    print(f"      SQL 결과 데이터: artifact={bool(sql_result_data.get('artifact'))}, row_count={sql_result_data.get('row_count')}, sql_query 존재={bool(sql_result_data.get('sql_query'))}")
                                    if sql_result_data.get('artifact'):
                                        artifact = sql_result_data['artifact']
                                        print(f"      Artifact 구조: type={artifact.get('type')}, data 존재={bool(artifact.get('data'))}, documents 개수={len(artifact.get('data', {}).get('documents', []))}")
                                    sent_markers.add('sql')  # 🔥 전송 표시
                                    yield marker_content
                                elif msg.name == "visualize_attractions_on_map":
                                    print(f"      🗺️ Map Visualization 결과 전송!")
                                    # 🔥 중복 전송 방지
                                    if 'map' in sent_markers:
                                        print(f"      ⚠️ MAP 이미 전송됨, 스킵!")
                                        continue
                                    # Map 결과는 프론트엔드에서 파싱하기 위해 그대로 전달
                                    # (이미 [MAP_DATA]...[/MAP_DATA] 형태로 감싸져 있음)
                                    sent_markers.add('map')
                                    yield msg.content
                                elif msg.name == "optimize_travel_route":
                                    print(f"      🗺️ Route Optimizer 결과 전송!")
                                    # 🔥 중복 전송 방지
                                    if 'attractions' in sent_markers:
                                        print(f"      ⚠️ ATTRACTIONS 이미 전송됨, 스킵!")
                                        continue
                                    
                                    import re
                                    
                                    content = msg.content
                                    
                                    # [ATTRACTIONS_DATA] 마커 추출 및 전송
                                    attractions_match = re.search(r'\[ATTRACTIONS_DATA\](.*?)\[/ATTRACTIONS_DATA\]', content, re.DOTALL)
                                    if attractions_match:
                                        attractions_marker = f"\n\n[ATTRACTIONS_DATA]{attractions_match.group(1)}[/ATTRACTIONS_DATA]\n\n"
                                        print(f"      ATTRACTIONS 마커 길이: {len(attractions_marker)}")
                                        sent_markers.add('attractions')
                                        yield attractions_marker
                                elif msg.name == "generate_travel_itinerary":
                                    print(f"      🗓️ Itinerary Generator 결과 전송!")
                                    import json as json_lib
                                    
                                    # 🔥 중복 전송 방지
                                    if 'itinerary' in sent_markers:
                                        print(f"      ⚠️ ITINERARY 이미 전송됨, 스킵!")
                                        continue
                                    
                                    # artifact에서 일정 데이터 추출
                                    artifact = getattr(msg, 'artifact', None)
                                    
                                    if artifact and artifact.get('type') == 'itinerary':
                                        # ITINERARY_DATA 마커로 감싸서 전송
                                        itinerary_marker = f"\n\n[ITINERARY_DATA]{json_lib.dumps(artifact, ensure_ascii=False)}[/ITINERARY_DATA]\n\n"
                                        print(f"      ITINERARY 마커 길이: {len(itinerary_marker)}")
                                        sent_markers.add('itinerary')  # 🔥 전송 표시
                                        yield itinerary_marker
            
            # 🔥 klid-aicb 방식: 콜백에서 토큰 사용량 수집
            total_input_tokens = 0
            total_output_tokens = 0
            
            if usage_callback.usage_metadata:
                for usage in usage_callback.usage_metadata.values():
                    total_input_tokens += usage.get('input_tokens', 0)
                    total_output_tokens += usage.get('output_tokens', 0)
                print(f"📊 콜백에서 토큰 수집: input={total_input_tokens}, output={total_output_tokens}")
            
            # 토큰 사용량 DB 저장
            if total_input_tokens > 0 or total_output_tokens > 0:
                try:
                    from src.services.token_usage_service import TokenUsageService
                    async with AsyncSessionLocal() as db:
                        token_service = TokenUsageService(db)
                        await token_service.record_usage(
                            user_id=None,  # 현재는 user_id 미사용
                            session_id=session_id,
                            model=settings.openai_model,
                            prompt_tokens=total_input_tokens,
                            completion_tokens=total_output_tokens,
                            endpoint="chat"
                        )
                        print(f"💾 토큰 사용량 저장 완료: input={total_input_tokens}, output={total_output_tokens}")
                except Exception as save_error:
                    logger.warning(f"토큰 사용량 저장 실패: {save_error}")
                    
        except Exception as e:
            yield f"오류가 발생했습니다: {str(e)}"





