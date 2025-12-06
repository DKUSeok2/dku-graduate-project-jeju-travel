"""
Token Usage Service - LLM 토큰 사용량 추적 및 저장
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from src.models.admin import LLMUsage
from src.config import settings

logger = logging.getLogger(__name__)

# 모델별 가격 (1K 토큰당 USD)
MODEL_PRICING = {
    "gpt-5-mini": {"input": 0.00025, "output": 0.002},  # GPT-5 mini (공식 가격)
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}


class TokenUsageService:
    """토큰 사용량 서비스"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Decimal:
        """토큰 사용량에 따른 비용 계산"""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("gpt-5-mini"))
        
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        
        return Decimal(str(round(input_cost + output_cost, 6)))
    
    async def record_usage(
        self,
        user_id: Optional[int],
        session_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        endpoint: str = "chat"
    ) -> LLMUsage:
        """토큰 사용량 기록"""
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
        
        usage = LLMUsage(
            user_id=user_id,
            session_id=session_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            endpoint=endpoint,
            created_at=datetime.utcnow()
        )
        
        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)
        
        logger.info(
            f"📊 토큰 사용량 기록: model={model}, "
            f"prompt={prompt_tokens}, completion={completion_tokens}, "
            f"total={total_tokens}, cost=${cost}"
        )
        
        return usage
    
    async def get_daily_usage(
        self,
        days: int = 7,
        user_id: Optional[int] = None,
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """일별 토큰 사용량 조회 (모델별 필터링 가능)"""
        user_filter = "AND user_id = :user_id" if user_id else ""
        model_filter = "AND model = :model" if model else ""
        query = text(f"""
            SELECT 
                DATE(created_at) as date,
                COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost), 0) as cost,
                COUNT(*) as request_count
            FROM llm_usage
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            {user_filter}
            {model_filter}
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        
        params = {}
        if user_id:
            params["user_id"] = user_id
        if model:
            params["model"] = model
        
        result = await self.db.execute(query, params)
        rows = result.fetchall()
        
        return [
            {
                "date": str(row[0]),
                "prompt_tokens": int(row[1] or 0),
                "completion_tokens": int(row[2] or 0),
                "total_tokens": int(row[3] or 0),
                "cost": float(row[4] or 0),
                "request_count": int(row[5] or 0)
            }
            for row in rows
        ]
    
    async def get_model_usage(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """모델별 토큰 사용량 조회"""
        query = text(f"""
            SELECT 
                model,
                COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost), 0) as cost,
                COUNT(*) as request_count
            FROM llm_usage
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            GROUP BY model
            ORDER BY total_tokens DESC
        """)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "model": row[0],
                "prompt_tokens": int(row[1] or 0),
                "completion_tokens": int(row[2] or 0),
                "total_tokens": int(row[3] or 0),
                "cost": float(row[4] or 0),
                "request_count": int(row[5] or 0)
            }
            for row in rows
        ]
    
    async def get_hourly_usage(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """시간별 토큰 사용량 조회 (최근 N시간)"""
        query = text(f"""
            SELECT 
                DATE_TRUNC('hour', created_at) as hour,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost), 0) as cost,
                COUNT(*) as request_count
            FROM llm_usage
            WHERE created_at >= NOW() - INTERVAL '{hours} hours'
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour DESC
        """)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "hour": str(row[0]),
                "total_tokens": int(row[1] or 0),
                "cost": float(row[2] or 0),
                "request_count": int(row[3] or 0)
            }
            for row in rows
        ]
    
    async def get_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """토큰 사용량 요약"""
        query = text(f"""
            SELECT 
                COALESCE(SUM(prompt_tokens), 0) as total_prompt,
                COALESCE(SUM(completion_tokens), 0) as total_completion,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost), 0) as total_cost,
                COUNT(*) as total_requests,
                COALESCE(AVG(total_tokens), 0) as avg_tokens_per_request
            FROM llm_usage
            WHERE created_at >= NOW() - INTERVAL '{days} days'
        """)
        
        result = await self.db.execute(query)
        row = result.fetchone()
        
        return {
            "total_prompt_tokens": int(row[0] or 0),
            "total_completion_tokens": int(row[1] or 0),
            "total_tokens": int(row[2] or 0),
            "total_cost": float(row[3] or 0),
            "total_requests": int(row[4] or 0),
            "avg_tokens_per_request": float(row[5] or 0)
        }

