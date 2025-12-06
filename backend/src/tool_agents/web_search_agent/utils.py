"""
Web Search Agent Utils - 유틸리티 함수
"""
from typing import List, Literal
from langchain_core.runnables import RunnableConfig


def get_search_depth(config: RunnableConfig = None) -> Literal["basic", "advanced"]:
    """검색 깊이 설정 가져오기"""
    if not config:
        return "basic"
    
    configurable = config.get("configurable", {})
    web_search_config = configurable.get("web_search", {})
    return web_search_config.get("search_depth", "basic")


def get_include_domains(config: RunnableConfig = None) -> List[str]:
    """검색 도메인 필터 가져오기"""
    if not config:
        return get_default_jeju_domains()
    
    configurable = config.get("configurable", {})
    web_search_config = configurable.get("web_search", {})
    return web_search_config.get("include_domains", get_default_jeju_domains())


def get_default_jeju_domains() -> List[str]:
    """제주 관련 기본 도메인 (실시간 뉴스 포함)"""
    return [
        # 제주 공식
        "visitjeju.net",
        "jeju.go.kr",
        # 날씨/교통
        "weather.go.kr",
        "airport.co.kr",
        "jejuair.net",
        # 포털/뉴스
        "naver.com",
        "daum.net",
        "news.naver.com",
        "news.daum.net",
        # 제주 지역 뉴스
        "jejunews.com",
        "headlinejeju.co.kr",
        "jejusori.net",
    ]

