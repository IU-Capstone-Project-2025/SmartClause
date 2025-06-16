import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://smartclause:smartclause@localhost:5432/smartclause_analyzer"
    )
    
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
    
    class Config:
        env_file = ".env"


settings = Settings() 