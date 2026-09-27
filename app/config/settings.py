# Application Configuration
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # LLM Provider
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # Database
    DATABASE_URL: str = "sqlite:///./vera.db"
    
    # API
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Timeouts
    LLM_TIMEOUT: int = 30
    VALIDATION_MAX_RETRIES: int = 1
    
    # Feature flags
    ENABLE_LANGGRAPH: bool = True
    ENABLE_VECTOR_RAG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()