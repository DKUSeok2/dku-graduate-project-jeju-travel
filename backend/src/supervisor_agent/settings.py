"""
Supervisor Agent Settings
"""
from pydantic import BaseModel
from typing import List, Optional


class AgentSettings(BaseModel):
    """Agent 설정"""
    
    # LLM 설정
    model_name: str = "gpt-5-mini"  # GPT-5 mini로 업그레이드
    temperature: float = 1.0  # gpt-5-mini는 temperature=0 미지원
    max_tokens: int = 2000
    
    # Agent 설정
    max_iterations: int = 10  # 최대 반복 횟수
    verbose: bool = True
    
    # 활성화된 도구 목록
    enabled_tools: List[str] = [
        "search_jeju_attractions",
        "query_jeju_database",
        "search_realtime_info",
        "optimize_travel_route",
        "visualize_map"
    ]
    
    # Checkpointer 설정
    use_checkpointer: bool = True
    checkpoint_db_url: Optional[str] = None





