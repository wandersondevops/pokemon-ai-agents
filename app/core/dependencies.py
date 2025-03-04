"""
Dependency injection for FastAPI.

This module contains dependencies that can be injected into FastAPI route functions.
"""

from langchain_openai import ChatOpenAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

from app.core.config import settings

def get_llm():
    """Get the language model instance."""
    return ChatOpenAI(model=settings.LLM_MODEL)

def get_search_wrapper():
    """Get the search wrapper instance."""
    return TavilySearchAPIWrapper()
