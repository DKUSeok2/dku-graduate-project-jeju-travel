"""
SQL Agent Domains - 데이터 구조 (klid-aicb 패턴)
"""
import uuid
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import pandas as pd
from langchain_core.runnables import RunnableConfig


# 상수 정의
MAX_ROWS_FOR_MARKDOWN_DISPLAY = 30


@dataclass
class SQLQueryResult:
    """SQL 쿼리 실행 결과 (klid-aicb 패턴)
    
    pandas DataFrame을 사용하여 구조화된 데이터 관리
    """
    sql_query: str
    data: pd.DataFrame
    data_id: str
    error_message: Optional[str] = None

    @staticmethod
    def from_error(error_message: str) -> "SQLQueryResult":
        return SQLQueryResult(
            data_id="",
            sql_query="",
            data=pd.DataFrame(),
            error_message=error_message,
        )

    @staticmethod
    def from_data(sql_query: str, data: List[Dict[str, Any]]) -> "SQLQueryResult":
        """SQL 실행 결과로부터 생성"""
        return SQLQueryResult(
            data_id=generate_data_id(),
            sql_query=sql_query,
            data=pd.DataFrame(data),
            error_message=None,
        )

    def to_markdown(self) -> str:
        """Tool message content - 요약 정보만! (artifact 패턴)
        
        데이터 상세는 artifact로 전달되므로, 
        LLM에게는 통계/요약만 제공
        """
        if self.error_message:
            return f"**에러**:\n{self.error_message}"
        
        if self.data.empty:
            return "조회 결과가 없습니다."
        
        total_rows = len(self.data)
        
        # 통계 정보만 제공 (개별 이름 X)
        lines = [f"## 📊 데이터 조회 완료"]
        lines.append(f"- 총 **{total_rows}개** 결과 조회됨")
        
        # 평점 통계
        if 'rating' in self.data.columns:
            valid_ratings = self.data['rating'].dropna()
            if len(valid_ratings) > 0:
                avg_rating = valid_ratings.mean()
                max_rating = valid_ratings.max()
                lines.append(f"- 평균 평점: **{avg_rating:.1f}**")
                lines.append(f"- 최고 평점: **{max_rating}**")
        
        # 카테고리 분포
        if 'category' in self.data.columns:
            top_categories = self.data['category'].value_counts().head(3)
            if len(top_categories) > 0:
                cat_str = ", ".join([f"{cat}({cnt}개)" for cat, cnt in top_categories.items()])
                lines.append(f"- 주요 카테고리: {cat_str}")
        
        lines.append(f"\n*상세 데이터는 화면에 표시됩니다.*")
        
        return "\n".join(lines)

    def to_artifact(self) -> Dict[str, Any]:
        """Artifact 형태로 변환 (구조화된 데이터)"""
        from decimal import Decimal
        
        if self.error_message:
            return {
                "type": "sql_agent",
                "error_message": self.error_message,
            }
        
        def convert_value(v):
            """JSON 직렬화 가능한 형태로 변환"""
            if pd.isna(v) or v is None:
                return None
            if isinstance(v, Decimal):
                return float(v)
            if isinstance(v, (int, float, str, bool)):
                return v
            return str(v)  # 기타 타입은 문자열로
        
        # NaN을 None으로 변환
        df_cleaned = self.data.where(pd.notnull(self.data), None)
        documents = df_cleaned.to_dict("records")
        # Decimal 등 JSON 직렬화 불가능한 타입 변환
        documents = [
            {k: convert_value(v) for k, v in doc.items()}
            for doc in documents
        ]
        parent_columns = self.data.columns.tolist()
        
        return {
            "type": "sql_agent",
            "sql_query": self.sql_query,
            "data_id": self.data_id,
            "data": {
                "documents": documents,
                "parent_columns": parent_columns,
            },
            "documents": documents,
            "parent_columns": parent_columns,
        }

    @staticmethod
    def from_artifact(artifact: Dict[str, Any]) -> "SQLQueryResult":
        """Artifact에서 SQLQueryResult 복원"""
        if error_message := artifact.get("error_message"):
            return SQLQueryResult(
                data_id="",
                sql_query="",
                data=pd.DataFrame(),
                error_message=error_message,
            )

        # data 키 안의 구조 사용
        data_dict = artifact.get("data", {})
        documents = data_dict.get("documents", [])
        parent_columns = data_dict.get("parent_columns", [])

        return SQLQueryResult(
            sql_query=artifact.get("sql_query", ""),
            data=pd.DataFrame(documents, columns=parent_columns) if documents else pd.DataFrame(),
            data_id=artifact.get("data_id", ""),
        )


def generate_data_id() -> str:
    """고유 data_id 생성"""
    return str(uuid.uuid4())[:8]


# 기존 코드와의 호환성을 위한 alias
@dataclass
class SQLAgentResponse:
    """SQL Agent 응답 (호환성용)"""
    query: str
    sql_query: str
    data: str
    attractions: List[Dict[str, Any]]
    row_count: int = 0
    error: Optional[str] = None
    
    def to_markdown(self) -> str:
        if self.error:
            return f"**데이터베이스 조회 실패**\n\n**오류**: {self.error}"
        
        if not self.data or self.row_count == 0:
            return f"**질의**: {self.query}\n\n**결과**: 조회 결과가 없습니다."
        
        return f"""# 🗄️ 데이터베이스 조회 결과

## 사용자 질의
{self.query}

## 생성된 SQL 쿼리
```sql
{self.sql_query}
```

## 조회 결과 ({self.row_count}개)

{self.data}
"""
    
    @classmethod
    def from_result(cls, query: str, result: Dict[str, Any]) -> "SQLAgentResponse":
        attractions = result.get("attractions", [])
        data = result.get("data", "")
        row_count = len(attractions) if attractions else cls._extract_row_count_from_data(data)
        
        return cls(
            query=query,
            sql_query=result.get("sql_query", ""),
            data=data,
            attractions=attractions,
            row_count=row_count,
            error=result.get("error"),
        )
    
    @staticmethod
    def _extract_row_count_from_data(data: str) -> int:
        if not data:
            return 0
        
        import re
        match = re.search(r'총\s*(\d+)\s*개', data)
        if match:
            return int(match.group(1))
        
        lines = data.split('\n')
        table_started = False
        row_count = 0
        for line in lines:
            if '|' in line and '---' not in line:
                if table_started:
                    row_count += 1
                else:
                    table_started = True
        
        return row_count
