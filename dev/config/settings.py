import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # LLM Configuration
    groq_api_key: str
    groq_model: str = "llama3-8b-8192"
    groq_temperature: float = 0.1
    groq_max_tokens: int = 1000
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()