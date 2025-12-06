"""
챗봇별 시스템 프롬프트
"""
from src.supervisor_agent.prompts.itinerary import ITINERARY_PROMPT
from src.supervisor_agent.prompts.sql import SQL_PROMPT
from src.supervisor_agent.prompts.rag import RAG_PROMPT
from src.supervisor_agent.prompts.web import WEB_PROMPT


def get_prompt_by_bot_id(bot_id: str) -> str:
    """bot_id에 따른 시스템 프롬프트 반환"""
    prompts = {
        "itinerary": ITINERARY_PROMPT,
        "sql": SQL_PROMPT,
        "rag": RAG_PROMPT,
        "web": WEB_PROMPT,
    }
    return prompts.get(bot_id, ITINERARY_PROMPT)


__all__ = [
    "ITINERARY_PROMPT",
    "SQL_PROMPT", 
    "RAG_PROMPT",
    "WEB_PROMPT",
    "get_prompt_by_bot_id",
]


