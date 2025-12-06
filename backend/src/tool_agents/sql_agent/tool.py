"""
SQL Agent Tool - 구조화 데이터 조회 (klid-aicb 패턴)
+ Self-correction: 결과 없을 시 조건 완화 재시도
+ Intent Router 연동: 규칙 기반 조건 강제 반영
"""
from typing import Any, Optional, Type, Literal, Tuple, Dict
import re
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage
from langgraph.graph.state import CompiledStateGraph
import logging

from src.tool_agents.base import BaseAgentTool
from src.tool_agents.sql_agent.domains import SQLQueryResult
from src.supervisor_agent.intent_router import get_intent_router

logger = logging.getLogger(__name__)


# 지역 키워드 → region 매핑 (DB의 실제 region 값과 일치)
# DB에는 구체적인 지역명(애월, 중문, 성산 등)과 큰 지역(제주시, 서귀포시, 동부, 서부)이 모두 있음
REGION_MAPPING = {
    # 구체적인 지역명 (우선순위 높음 - DB에 직접 저장됨)
    "애월": "애월", "애월읍": "애월", "애월해안": "애월",
    "한림": "한림", "한림읍": "한림",
    "협재": "협재",
    "조천": "조천", "조천읍": "조천",
    "함덕": "함덕",
    "중문": "중문", "중문관광단지": "중문",
    "안덕": "안덕", "안덕면": "안덕", "남원": "안덕", "남원읍": "안덕", "화순": "안덕", "위미": "안덕",
    "성산": "성산", "성산일출봉": "성산", "섭지코지": "성산",
    "표선": "표선", "표선해수욕장": "표선",
    "우도": "우도", "우도면": "우도",
    "구좌": "구좌", "구좌읍": "구좌",
    "김녕": "김녕",
    "세화": "세화",
    "대정": "대정", "대정읍": "대정", "모슬포": "대정", "마라도": "대정",
    "한경": "한경", "한경면": "한경",
    
    # 큰 지역 (구체적 지역명이 없을 때 사용)
    "제주시": "제주시", "제주공항": "제주시", "용두암": "제주시",
    "서귀포": "서귀포시", "서귀포시": "서귀포시",
}


class SQLQueryToolInputArgs(BaseModel):
    """SQL 쿼리 입력 파라미터"""
    query: str = Field(
        ...,
        description="데이터 조회에 필요한 자연어 질문 (예: '평점 4.5 이상 카페', '주차 가능한 맛집')"
    )


class JejuDataQueryTool(BaseAgentTool):
    """제주 관광 데이터 SQL 조회 도구 (klid-aicb 패턴)
    
    핵심: 
    - response_format = "content_and_artifact"
    - _arun에서 return "", artifact
    - format_content에서 artifact → DataFrame → to_markdown()
    """
    
    name: str = "query_jeju_database"
    description: str = """제주도 관광지 데이터베이스를 조회합니다. 자연어 질문을 SQL로 변환하여 실행합니다."""
    args_schema: Type[BaseModel] = SQLQueryToolInputArgs
    
    # klid-aicb 핵심: artifact 사용
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"
    
    # SQL Agent (LangGraph)
    sql_agent: Optional[CompiledStateGraph] = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _run(
        self, 
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        config: RunnableConfig = None
    ) -> Tuple[str, Dict[str, Any]]:
        """동기 실행"""
        import asyncio
        return asyncio.run(self._arun(query, run_manager, config))
    
    async def _arun(
        self, 
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        config: RunnableConfig = None
    ) -> Tuple[str, Dict[str, Any]]:
        """SQL Agent 실행 (klid-aicb 패턴 + Self-correction + Intent Router)
        
        Returns:
            Tuple[str, dict]: ("", artifact) - content는 빈 문자열!
        """
        logger.info(f"🗄️ SQL Agent 호출: {query}")
        
        # 🔥 Intent Router: 조건 추출 및 강화된 쿼리 생성
        router = get_intent_router()
        parsed = router.parse(query)
        enhanced_query = router.build_enhanced_query(parsed)
        
        print(f"🎯 Intent Router 조건 추출:")
        print(f"   - 조건: {parsed.conditions}")
        print(f"   - 강화된 쿼리: {enhanced_query[:100]}...")
        
        # 추출된 조건 저장 (SQL 후처리용)
        self._extracted_conditions = parsed.conditions
        
        # 사용자 요청에서 개수 추출 (예: "5개", "10개")
        self._requested_limit = parsed.conditions.get("limit", 10)
        print(f"📊 요청 개수: {self._requested_limit}개")
        
        try:
            # 1차 시도: 강화된 쿼리로 실행
            data_list, sql_query = await self._execute_query(enhanced_query, config)
            
            # Self-correction: 결과 없으면 단계적으로 조건 완화 재시도
            if not data_list:
                # 단계 1: 시설 조건만 제거 (주차, 아이동반 등)
                relaxed_query = self._relax_query(enhanced_query, step=1)
                if relaxed_query != enhanced_query:
                    logger.info(f"🔄 Self-correction (1단계): 시설 조건 완화")
                    print(f"🔄 조건 완화: 시설 조건(주차 등) 제거하여 재검색 중...")
                    data_list, sql_query = await self._execute_query(relaxed_query, config)
                
                # 단계 2: 평점 조건 완화
                if not data_list:
                    relaxed_query = self._relax_query(enhanced_query, step=2)
                    if relaxed_query != enhanced_query:
                        logger.info(f"🔄 Self-correction (2단계): 평점 조건 완화")
                        print(f"🔄 조건 완화: 평점 조건 완화하여 재검색 중...")
                        data_list, sql_query = await self._execute_query(relaxed_query, config)
                
                # 단계 3: 모든 조건 완화 (시설 + 평점)
                if not data_list:
                    relaxed_query = self._relax_query(enhanced_query, step=3)
                    if relaxed_query != enhanced_query:
                        logger.info(f"🔄 Self-correction (3단계): 모든 조건 완화")
                        print(f"🔄 조건 완화: 모든 조건 완화하여 재검색 중...")
                        data_list, sql_query = await self._execute_query(relaxed_query, config)
            
            # 🔥 SQL 조건 검증: Intent Router 조건이 SQL에 반영되었는지 확인
            sql_query = self._verify_and_fix_sql(sql_query)
            
            # 사용자가 요청한 개수만큼만 결과 반환
            if data_list and hasattr(self, '_requested_limit'):
                data_list = data_list[:self._requested_limit]
                print(f"📊 결과 {self._requested_limit}개로 제한")
            
            if not data_list:
                # Self-correction을 시도했는데도 결과가 없으면 친절한 메시지
                result_obj = SQLQueryResult.from_error(
                    "요청하신 조건에 맞는 장소를 찾지 못했습니다.\n\n"
                    "다음 방법을 시도해보세요:\n"
                    "- 조건을 완화해서 검색 (예: 주차 조건 제거, 평점 기준 낮추기)\n"
                    "- 다른 지역으로 검색 범위 확대\n"
                    "- 더 일반적인 키워드로 검색"
                )
            else:
                result_obj = SQLQueryResult.from_data(
                    sql_query=sql_query,
                    data=data_list
                )
            
            # artifact 생성
            artifact = result_obj.to_artifact()
            
            logger.info(f"📄 Artifact 생성 완료 (data_id: {artifact.get('data_id', 'N/A')})")
            
            # klid-aicb 핵심: content는 빈 문자열, artifact에 데이터
            return "", artifact
            
        except Exception as e:
            error_msg = f"데이터베이스 조회 중 오류가 발생했습니다: {str(e)}"
            logger.error(f"❌ SQL Agent 실행 실패: {error_msg}")
            result_obj = SQLQueryResult.from_error(error_msg)
            return "", result_obj.to_artifact()
    
    async def _execute_query(
        self, 
        query: str, 
        config: RunnableConfig
    ) -> Tuple[list, str]:
        """SQL Agent 실행 후 데이터 파싱"""
        result = await self.sql_agent.ainvoke(
            {"query": query},
            config=config
        )
        
        sql_query = result.get("sql_query", "")
        data = result.get("data", "")
        
        # LIMIT 후처리: 사용자가 요청한 개수로 조정
        if sql_query and hasattr(self, '_requested_limit'):
            sql_query = re.sub(
                r'LIMIT\s+\d+', 
                f'LIMIT {self._requested_limit}', 
                sql_query, 
                flags=re.IGNORECASE
            )
        
        print(f"✅ SQL Agent 실행 완료")
        print(f"🔍 생성된 SQL: {sql_query}")
        logger.info(f"✅ SQL Agent 실행 완료")
        logger.info(f"   SQL: {sql_query[:100] if sql_query else 'None'}...")
        
        # 데이터를 파싱해서 리스트로 변환
        data_list = self._parse_data_to_list(data, sql_query, config)
        
        return data_list, sql_query
    
    def _verify_and_fix_sql(self, sql_query: str) -> str:
        """Intent Router 조건이 SQL에 반영되었는지 검증 및 수정
        
        LLM이 조건을 무시했을 경우 SQL에 직접 추가
        """
        if not sql_query or not hasattr(self, '_extracted_conditions'):
            return sql_query
        
        conditions = self._extracted_conditions
        sql_upper = sql_query.upper()
        fixed_sql = sql_query
        
        # 1. 지역 조건 검증
        if "region" in conditions:
            region = conditions["region"]
            
            # SQL에 region 조건이 없으면 추가
            if "REGION" not in sql_upper:
                region_condition = f"region = '{region}'"
                print(f"⚠️ SQL 수정: region = '{region}' 추가")
                
                # WHERE 절에 추가
                if "WHERE" in sql_upper:
                    fixed_sql = fixed_sql.replace(
                        "WHERE", 
                        f"WHERE {region_condition} AND", 
                        1
                    )
                else:
                    # WHERE 절이 없으면 FROM 뒤에 추가
                    fixed_sql = re.sub(
                        r'(FROM\s+\w+)',
                        f"\\1 WHERE {region_condition}",
                        fixed_sql,
                        count=1,
                        flags=re.IGNORECASE
                    )
        
        # 2. 평점 조건 검증
        if "min_rating" in conditions:
            min_rating = conditions["min_rating"]
            if "RATING" not in sql_upper or str(min_rating) not in sql_query:
                if "WHERE" in fixed_sql.upper():
                    fixed_sql = fixed_sql.replace(
                        "WHERE",
                        f"WHERE rating >= {min_rating} AND",
                        1
                    )
                    print(f"⚠️ SQL 수정: rating >= {min_rating} 추가")
        
        # 3. 주차 조건 검증
        if conditions.get("parking") and "PARKING" not in sql_upper:
            if "WHERE" in fixed_sql.upper():
                fixed_sql = fixed_sql.replace(
                    "WHERE",
                    "WHERE parking = true AND",
                    1
                )
                print(f"⚠️ SQL 수정: parking = true 추가")
        
        # 4. 아이동반 조건 검증
        if conditions.get("kid_friendly") and "KID_FRIENDLY" not in sql_upper:
            if "WHERE" in fixed_sql.upper():
                fixed_sql = fixed_sql.replace(
                    "WHERE",
                    "WHERE kid_friendly = true AND",
                    1
                )
                print(f"⚠️ SQL 수정: kid_friendly = true 추가")
        
        # 5. 🆕 부정 조건 (excludes) 검증 - "~빼고", "~말고"
        if "excludes" in conditions and conditions["excludes"]:
            exclude_conditions = []
            for exclude_kw in conditions["excludes"]:
                # 이미 NOT ILIKE가 있는지 확인
                if exclude_kw.upper() not in sql_upper:
                    exclude_conditions.append(f"category NOT ILIKE '%{exclude_kw}%'")
            
            if exclude_conditions:
                exclude_clause = " AND ".join(exclude_conditions)
                if "WHERE" in fixed_sql.upper():
                    fixed_sql = fixed_sql.replace(
                        "WHERE",
                        f"WHERE {exclude_clause} AND",
                        1
                    )
                    print(f"⚠️ SQL 수정: 제외 조건 추가 - {exclude_clause}")
        
        if fixed_sql != sql_query:
            logger.info(f"🔧 SQL 조건 보정 완료")
            print(f"🔧 보정된 SQL: {fixed_sql[:100]}...")
        
        return fixed_sql
    
    def _relax_query(self, query: str, step: int = 1) -> str:
        """쿼리 조건 완화 (Self-correction) - 단계별 완화
        
        Args:
            query: 원본 쿼리
            step: 완화 단계 (1=시설만, 2=평점만, 3=모든 조건)
        
        조건 완화 우선순위:
        - Step 1: 시설 조건 제거 (주차, 아이 동반 등) - 가장 덜 중요
        - Step 2: 평점 조건 완화 (4.5 → 4.0 → 3.5)
        - Step 3: 모든 조건 완화
        """
        relaxed = query
        
        # Step 1: 시설 조건만 제거 (주차, 아이동반 등)
        if step == 1:
            facility_keywords = ['주차 가능', '주차되는', '주차 되는', '주차', '아이 동반', '아이랑', '반려동물', '아이', '유모차']
            for keyword in facility_keywords:
                if keyword in relaxed:
                    relaxed = relaxed.replace(keyword, "").strip()
                    relaxed = re.sub(r'\s+', ' ', relaxed)
                    logger.info(f"   시설 조건 완화 (Step 1): '{keyword}' 제거")
                    break  # 하나만 제거
        
        # Step 2: 평점 조건만 완화
        elif step == 2:
            # 평점 숫자 찾아서 0.5씩 낮추기
            rating_match = re.search(r'평점\s*(\d+\.?\d*)\s*이상|(\d+\.?\d*)\s*점\s*이상|평점\s*(\d+\.?\d*)', relaxed)
            if rating_match:
                rating = None
                for group in rating_match.groups():
                    if group:
                        try:
                            rating = float(group)
                            break
                        except:
                            pass
                
                if rating and rating > 3.0:
                    new_rating = max(3.0, rating - 0.5)  # 최소 3.0까지
                    relaxed = re.sub(
                        r'평점\s*(\d+\.?\d*)\s*이상|(\d+\.?\d*)\s*점\s*이상|평점\s*(\d+\.?\d*)',
                        f'평점 {new_rating} 이상',
                        relaxed,
                        count=1
                    )
                    logger.info(f"   평점 조건 완화 (Step 2): {rating} → {new_rating}")
            else:
                # 평점 조건이 명시적이지 않으면 "평점 높은"으로 변경
                relaxed = re.sub(r'평점 높은|높은 평점', '평점', relaxed)
        
        # Step 3: 모든 조건 완화 (시설 + 평점)
        elif step == 3:
            # 시설 조건 제거
            facility_keywords = ['주차 가능', '주차되는', '주차 되는', '주차', '아이 동반', '아이랑', '반려동물', '아이', '유모차']
            for keyword in facility_keywords:
                if keyword in relaxed:
                    relaxed = relaxed.replace(keyword, "").strip()
                    relaxed = re.sub(r'\s+', ' ', relaxed)
            
            # 평점 조건 완화
            rating_match = re.search(r'평점\s*(\d+\.?\d*)\s*이상|(\d+\.?\d*)\s*점\s*이상|평점\s*(\d+\.?\d*)', relaxed)
            if rating_match:
                rating = None
                for group in rating_match.groups():
                    if group:
                        try:
                            rating = float(group)
                            break
                        except:
                            pass
                
                if rating and rating > 3.0:
                    new_rating = max(3.0, rating - 1.0)  # 더 많이 완화
                    relaxed = re.sub(
                        r'평점\s*(\d+\.?\d*)\s*이상|(\d+\.?\d*)\s*점\s*이상|평점\s*(\d+\.?\d*)',
                        f'평점 {new_rating} 이상',
                        relaxed,
                        count=1
                    )
            else:
                relaxed = re.sub(r'평점 높은|높은 평점', '평점', relaxed)
            
            logger.info(f"   모든 조건 완화 (Step 3)")
        
        return relaxed.strip()
    
    def _parse_data_to_list(
        self, 
        data: str, 
        sql_query: str, 
        config: RunnableConfig
    ) -> list:
        """마크다운 테이블 데이터를 리스트로 파싱
        
        또는 DB에서 직접 쿼리 재실행
        """
        if not data or "조회 결과가 없습니다" in data:
            return []
        
        try:
            # DB에서 직접 쿼리 실행 (가장 정확)
            from src.tool_agents.sql_agent.database import CustomSQLDatabase
            db_url = config["configurable"]["sql_agent"]["db_url"]
            db = CustomSQLDatabase.from_uri(db_url)
            
            from sqlalchemy import text
            with db.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                columns = list(result.keys())
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.warning(f"DB 직접 쿼리 실패, 마크다운 파싱 시도: {e}")
            
            # 마크다운 테이블 파싱 (fallback)
            return self._parse_markdown_table(data)
    
    def _parse_markdown_table(self, data: str) -> list:
        """마크다운 테이블을 리스트로 파싱"""
        lines = data.split('\n')
        headers = []
        rows = []
        header_found = False
        
        for line in lines:
            if '|' not in line or '---' in line:
                continue
            
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]  # 빈 문자열 제거
            
            if not header_found:
                headers = parts
                header_found = True
            else:
                if len(parts) == len(headers):
                    rows.append(dict(zip(headers, parts)))
        
        return rows
    
    def format_content(self, message: ToolMessage) -> ToolMessage:
        """SQL 결과를 LLM에게 전달하기 위한 형식으로 변환 (klid-aicb 패턴)
        
        artifact에서 데이터를 가져와서 pandas to_markdown() 사용
        """
        import json
        
        print("🔴🔴🔴 format_content 호출됨!")
        logger.info("🔧 format_content 호출됨 (klid-aicb 패턴)")
        
        # artifact가 없으면 에러
        if message.artifact is None:
            error_content = "데이터 조회 중 오류가 발생했습니다."
            instruction = "\n\n[중요] 사용자에게 오류가 발생했음을 알리고, 다른 방법으로 답변을 시도하세요."
            return message.model_copy(
                update={"content": f"{error_content}{instruction}"}
            )
        
        # artifact에서 SQLQueryResult 복원
        result_obj = SQLQueryResult.from_artifact(message.artifact)
        
        # 에러 케이스 처리
        if result_obj.error_message:
            error_content = result_obj.to_markdown()
            instruction = "\n\n[중요] 사용자에게 오류가 발생했음을 알리고, 다른 방법으로 답변을 시도하세요."
            return message.model_copy(
                update={"content": f"{error_content}{instruction}"}
            )
        
        # pandas to_markdown()으로 깔끔한 테이블 생성
        content = result_obj.to_markdown()
        
        # SQL 결과 데이터 태그 추가 (프론트엔드 표시용)
        sql_result_data = {
            "type": "sql_query",
            "sql_query": result_obj.sql_query,
            "total_results": len(result_obj.data),
            "columns": list(result_obj.data[0].keys()) if result_obj.data else [],
            "data": result_obj.data
        }
        content += f"\n[SQL_QUERY_RESULT]{json.dumps(sql_result_data, ensure_ascii=False)}[/SQL_QUERY_RESULT]"
        
        # 지시사항: 친근하게 요약! (artifact 패턴)
        row_count = len(result_obj.data)
        instruction = f"""

## 응답 규칙 (친근하게 요약!)

✅ 해야 할 것:
- 친근한 말투로 대답하세요 (예: "찾았어요!", "좋은 곳들이에요~")
- 결과를 자연스럽게 요약해서 설명해주세요
  예: "애월쪽 오션뷰 카페가 많네요! 평점도 대부분 4.5 이상이에요 ☕"
- 대표적인 곳 1-2개 정도는 언급해도 좋아요
  예: "그 중에서 '카페 델문도'가 특히 인기있어요!"
- 이모지를 적절히 사용

❌ 하지 말 것:
- "N개의 결과를 찾았습니다" 같은 딱딱한 시작
- 전체 목록을 번호 매겨서 나열
- 테이블 전체를 복사

말투 예시:
- ❌ "9개의 카페를 찾았습니다. 결과를 확인하세요."
- ✅ "애월에 평점 좋은 카페 {row_count}곳 찾았어요! ☕ 오션뷰 카페가 많고, 특히 '카페 델문도'가 인기 많아요~"

데이터는 아래 UI에 표시되니까, 요약과 추천 포인트 위주로 답변해주세요!"""
        
        content = f"{content}{instruction}"
        
        print(f"🔴 format_content 결과 ({len(content)} chars):")
        print(content[:500])  # 처음 500자
        logger.info(f"   ✅ format_content 완료 ({len(content)} chars)")
        
        return message.model_copy(update={"content": content})
