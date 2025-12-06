"""
Custom SQL Database for Jeju Travel Chatbot
PostgreSQL 연결 및 스키마 조회
"""
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger(__name__)


# 스키마 조회 쿼리
TABLE_SCHEMA_QUERY = """
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = '{table_name}'
ORDER BY ordinal_position;
"""

# 샘플 데이터 조회
SAMPLE_ROWS_QUERY = """
SELECT * 
FROM {table_name}
LIMIT {sample_rows}
"""

# 테이블 정보 포맷
TABLE_INFO_FORMAT = """
테이블: `{table_name}`

/*
스키마:
{table_schema}
*/

/*
샘플 데이터 ({num_sample_rows}행):
{sample_rows}
*/
"""


class CustomSQLDatabase:
    """제주 여행 DB 커스텀 래퍼"""
    
    def __init__(self, engine: Engine, schema: str = "public"):
        self.engine = engine
        self.schema = schema
    
    @classmethod
    def from_uri(cls, database_uri: str, schema: str = "public"):
        """DB URI로부터 생성"""
        engine = create_engine(database_uri)
        return cls(engine, schema)
    
    def get_table_info(self, table_names: List[str] = None) -> str:
        """테이블 스키마 정보 조회"""
        if table_names is None:
            table_names = ["places", "menus"]  # 기본 테이블
        
        table_infos = []
        for table in table_names:
            schema_info = self._get_table_schema(table)
            sample_rows = self._get_sample_rows(table, 3)
            
            table_info = TABLE_INFO_FORMAT.format(
                table_name=table,
                table_schema=schema_info,
                num_sample_rows=len(sample_rows),
                sample_rows=self._format_rows(sample_rows)
            )
            table_infos.append(table_info)
        
        return "\n\n".join(table_infos)
    
    def _get_table_schema(self, table_name: str) -> str:
        """테이블 스키마 조회"""
        query = TABLE_SCHEMA_QUERY.format(table_name=table_name)
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                
                schema_lines = []
                for row in rows:
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    schema_lines.append(
                        f"  - {row[0]}: {row[1]} ({nullable})"
                    )
                return "\n".join(schema_lines) if schema_lines else "(스키마 정보 없음)"
        except Exception as e:
            logger.error(f"스키마 조회 오류: {e}")
            return f"(스키마 조회 실패: {e})"
    
    def _get_sample_rows(self, table_name: str, limit: int = 3) -> List[Dict]:
        """샘플 데이터 조회"""
        query = SAMPLE_ROWS_QUERY.format(table_name=table_name, sample_rows=limit)
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"샘플 데이터 조회 오류: {e}")
            return []
    
    def _format_rows(self, rows: List[Dict]) -> str:
        """행 데이터를 문자열로 포맷"""
        if not rows:
            return "(데이터 없음)"
        
        # 간단한 표 형태로 출력 (주요 컬럼만)
        output_lines = []
        for i, row in enumerate(rows, 1):
            # 중요한 컬럼만 표시
            important_cols = ["id", "name", "category", "rating", "price_range", "price", "place_id"]
            row_data = {k: v for k, v in row.items() if k in important_cols}
            output_lines.append(f"  {i}. {row_data}")
        
        return "\n".join(output_lines)
    
    def run_with_headers(self, query: str) -> str:
        """쿼리 실행 및 결과 반환 (헤더 포함)"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                columns = list(result.keys())
                rows = result.fetchall()
                
                if not rows:
                    return "조회 결과가 없습니다."
                
                # 결과를 마크다운 표 형태로 변환
                output = f"**총 {len(rows)}개의 결과가 조회되었습니다.**\n\n"
                
                # 테이블 헤더
                header = "| " + " | ".join(columns) + " |"
                separator = "|" + "|".join(["---"] * len(columns)) + "|"
                output += header + "\n" + separator + "\n"
                
                # 테이블 데이터 (최대 10개만 표시)
                for row in rows[:10]:
                    row_str = "| " + " | ".join([str(val) if val is not None else "" for val in row]) + " |"
                    output += row_str + "\n"
                
                if len(rows) > 10:
                    output += f"\n... (총 {len(rows)}개 중 10개만 표시)\n"
                
                return output
        except Exception as e:
            logger.error(f"쿼리 실행 오류: {e}")
            return f"Error: {str(e)}"


