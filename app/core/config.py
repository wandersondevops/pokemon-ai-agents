"""
Configuration settings for the Pokemon AI Agents application.

This module contains configuration settings, environment variables, and constants
used throughout the application.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(verbose=True)

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
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "pokemon-ai-agents")
    
    # LangChain environment variables (for compatibility)
    LANGCHAIN_TRACING_V2: bool = LANGSMITH_TRACING
    LANGCHAIN_ENDPOINT: str = LANGSMITH_ENDPOINT
    LANGCHAIN_PROJECT: str = LANGSMITH_PROJECT
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        
    def validate(self):
        """Validate the settings."""
        missing_keys = []
        
        # Validate LangSmith settings if tracing is enabled
        if self.LANGSMITH_TRACING:
            if not self.LANGSMITH_API_KEY:
                missing_keys.append("LANGSMITH_API_KEY")
            if not self.LANGSMITH_PROJECT:
                missing_keys.append("LANGSMITH_PROJECT")
        
        # Validate OpenAI API key
        if not self.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
        
        # Validate Tavily API key
        if not self.TAVILY_API_KEY:
            missing_keys.append("TAVILY_API_KEY")
        
        if missing_keys:
            print(f"Warning: The following environment variables are missing or empty: {', '.join(missing_keys)}")
            
        return self

# Create settings instance
# Initialize settings and validate
settings = Settings().validate()

# Set LangChain environment variables for compatibility
os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGSMITH_TRACING).lower()
os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT

# Log configuration (without sensitive data)
if os.getenv("DEBUG", "false").lower() == "true":
    print(f"LangSmith configured with project: {settings.LANGSMITH_PROJECT}")
    print(f"LangSmith tracing enabled: {settings.LANGSMITH_TRACING}")
    print(f"LangSmith endpoint: {settings.LANGSMITH_ENDPOINT}")
