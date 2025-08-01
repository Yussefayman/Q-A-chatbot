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

    # Document Processing Configuration
    max_file_size_mb: int = 10
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_for_context: int = 3

    # Vector Database Configuration
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "documents"
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # Database Configuration
    database_url: str = "sqlite:///./qa_system.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()