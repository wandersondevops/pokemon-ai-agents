"""
Configuration settings for the Pokemon AI Agents application.

This module contains configuration settings, environment variables, and constants
used throughout the application.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Pokemon AI Agents API"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8088"))
    API_DEBUG: bool = os.getenv("API_DEBUG", "True").lower() == "true"
    
    # Streamlit settings
    STREAMLIT_HOST: str = os.getenv("STREAMLIT_HOST", "0.0.0.0")
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # LLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    
    # Pokemon API settings
    POKEMON_API_BASE_URL: str = "https://pokeapi.co/api/v2/pokemon"
    
    # Search API settings
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # LangSmith settings
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "pokemon-ai-agents")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings()
