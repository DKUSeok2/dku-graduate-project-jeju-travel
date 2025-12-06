"""
Configuration and Settings
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 정의되지 않은 환경 변수 무시
    )
    
    # Database
    database_url: str = "postgresql://jeju_user:jeju_password@localhost:5433/jeju_travel"
    
    # JWT
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    
    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9201"  # 9201 포트로 변경 (klid가 9200 사용)
    elasticsearch_api_key: Optional[str] = None  # Elastic Cloud API 키 (선택)
    elasticsearch_index_attractions: str = "jeju-attractions"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # Tavily (Web Search)
    tavily_api_key: str = ""
    
    # Embedding Model
    embedding_model_name: str = "jhgan/ko-sroberta-multitask"
    
    # API Keys (optional)
    kakao_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    
    # Email (Gmail SMTP)
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_from: Optional[str] = None
    
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    
    # Frontend URL
    frontend_url: str = "http://localhost:5173"
    
    # Application
    app_name: str = "Jeju AI Travel Planner"
    debug: bool = True
    
    # CORS - 환경변수로 설정 시 쉼표로 구분된 문자열 사용
    # 예: CORS_ORIGINS=https://example.com,https://app.example.com
    cors_origins_str: str = "http://localhost:3000,http://localhost:5173"


settings = Settings()





