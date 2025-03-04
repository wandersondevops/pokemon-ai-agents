"""
Pytest configuration for API tests.

This module contains fixtures for API tests.
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from langchain_openai import ChatOpenAI

from app.main import app
from app.core.dependencies import get_llm, get_search_wrapper

# Create mock LLM and search wrapper
mock_llm = MagicMock(spec=ChatOpenAI)
mock_search_wrapper = MagicMock()

@pytest.fixture
def test_client():
    """
    Create a FastAPI TestClient instance with dependency overrides.
    
    Returns:
        TestClient: A FastAPI TestClient instance.
    """
    # Override dependencies
    app.dependency_overrides[get_llm] = lambda: mock_llm
    app.dependency_overrides[get_search_wrapper] = lambda: mock_search_wrapper
    
    client = TestClient(app)
    
    yield client
    
    # Clean up dependency overrides after test
    app.dependency_overrides = {}
