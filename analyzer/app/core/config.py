import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://smartclause:smartclause@localhost:5432/smartclause_analyzer"
    )
    
    # Postgres environment variables (for Docker Compose)
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    
    # API Settings
    api_title: str = "SmartClause Analyzer API"
    api_version: str = "1.0.0"
    api_description: str = "RAG-based legal document analysis microservice"

    # Embedding settings
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024

    # File size settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # RAG settings
    default_k: int = 5
    max_k: int = 20
    
    # OpenRouter LLM settings
    openrouter_api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    site_url: Optional[str] = os.getenv("SITE_URL", "SmartClause")
    site_name: Optional[str] = os.getenv("SITE_NAME", "SmartClause Legal Analyzer")
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from environment


settings = Settings() 