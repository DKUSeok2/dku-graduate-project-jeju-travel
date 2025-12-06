"""
Tool Agent Domain Models
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Tool execution result"""
    
    tool_name: str
    success: bool
    text_response: str
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None


class AttractionSearchParams(BaseModel):
    """관광지 검색 파라미터"""
    
    query: str
    category: Optional[str] = None
    kid_friendly: Optional[bool] = None
    price_range: Optional[str] = None
    limit: int = 10


class RouteOptimizationParams(BaseModel):
    """경로 최적화 파라미터"""
    
    attractions: List[Dict[str, Any]]
    start_location: Dict[str, float]  # {"lat": 33.5, "lng": 126.5}
    end_location: Optional[Dict[str, float]] = None
    time_windows: Optional[Dict[str, Any]] = None


class MapVisualizationParams(BaseModel):
    """지도 시각화 파라미터"""
    
    attractions: List[Dict[str, Any]]
    route: List[int]  # 방문 순서
    center: Optional[Dict[str, float]] = None





