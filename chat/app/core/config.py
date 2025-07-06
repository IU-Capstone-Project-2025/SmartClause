from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database settings - simplified to single URL
    database_url: str = "postgresql+asyncpg://user:password@postgres:5432/chatdb"
    
    # Chat service settings
    api_version: str = "v1"
    max_memory_messages: int = 20
    default_memory_messages: int = 10
    
    # OpenRouter API settings
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # LLM model configuration
    llm_model: str = "anthropic/claude-3.5-sonnet"  # Default model
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    
    # Analyzer service settings
    analyzer_base_url: str = "http://localhost:8001/api/v1"
    
    # Authentication settings
    jwt_secret: str = "your_jwt_secret_here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra environment variables
    }


# Global settings instance
settings = Settings() 