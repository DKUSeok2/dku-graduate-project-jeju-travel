"""
Web Search Agent Domains - 데이터 구조
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WebResult:
    """웹 검색 결과 단일 항목"""
    url: str
    summary: str
    title: str
    answer: Optional[str] = None
    score: Optional[float] = None


@dataclass
class WebSearchResponse:
    """웹 검색 응답 전체 구조"""
    query: str
    results: List[WebResult]
    answer: Optional[str] = None
    error: Optional[str] = None
    
    def to_markdown(self) -> str:
        """검색 결과를 마크다운 형식으로 변환"""
        
        if self.error:
            return f"**웹 검색 실패**\n\n**쿼리**: {self.query}\n\n**오류**: {self.error}\n\n다른 방법을 시도해주세요."
        
        if not self.results:
            return "검색 결과를 찾을 수 없습니다."

        header = "| 제목 | 요약 | 출처 |"
        separator = "|---|---|---|"
        rows: List[str] = []
        for result in self.results:
            title = (result.title or "").replace("\n", " ")
            summary = (result.summary or "").replace("\n", " ")
            url = (result.url or "").strip()
            rows.append(f"| {title} | {summary} | {url} |")

        results_table = "\n".join([header, separator, "\n".join(rows)]) if rows else "검색 결과가 없습니다."

        return WEB_SEARCH_RESULT_MARKDOWN.format(
            query=self.query,
            answer=self.answer or "검색 요약이 제공되지 않았습니다.",
            results_table=results_table,
        )
    
    @classmethod
    def from_artifact(cls, artifact: dict) -> "WebSearchResponse":
        """artifact에서 WebSearchResponse 생성"""
        results = [
            WebResult(
                url=item.get("url", ""),
                summary=item.get("summary", ""),
                title=item.get("title", ""),
                answer=item.get("answer"),
                score=item.get("score")
            )
            for item in artifact.get("results", [])
        ]
        
        return cls(
            query=artifact.get("query", ""),
            results=results,
            answer=artifact.get("answer"),
            error=artifact.get("error"),
        )


WEB_SEARCH_RESULT_MARKDOWN = """# 🔍 실시간 검색 결과

## 검색어
{query}

## 요약
{answer}

## 상세 정보

{results_table}

---
위 검색 결과를 바탕으로 사용자에게 답변을 작성하세요.
답변 마지막에 출처 링크를 포함하세요.
"""

