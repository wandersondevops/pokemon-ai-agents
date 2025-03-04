"""
Common test fixtures for the Pokemon AI Agents tests.

This module contains fixtures that can be used across multiple test files.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from langchain_openai import ChatOpenAI

from app.main import app
from app.core.config import settings

@pytest.fixture
def test_client():
    """
    Create a test client for the FastAPI application.
    
    Returns:
        TestClient: A test client for the FastAPI application
    """
    return TestClient(app)

@pytest.fixture
def mock_llm():
    """
    Create a mock LLM for testing.
    
    Returns:
        MagicMock: A mock LLM
    """
    mock = MagicMock(spec=ChatOpenAI)
    return mock

@pytest.fixture
def mock_search_wrapper():
    """
    Create a mock search wrapper for testing.
    
    Returns:
        MagicMock: A mock search wrapper
    """
    mock = MagicMock()
    mock.run.return_value = [
        {
            "title": "Test Result",
            "url": "https://example.com",
            "content": "This is a test search result."
        }
    ]
    return mock

@pytest.fixture
def pokemon_pikachu_data():
    """
    Sample Pikachu data for testing.
    
    Returns:
        dict: Sample Pikachu data
    """
    return {
        "name": "pikachu",
        "base_stats": {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "special_attack": 50,
            "special_defense": 50,
            "speed": 90
        },
        "types": ["electric"],
        "abilities": ["static", "lightning-rod"],
        "height": 0.4,
        "weight": 6.0,
        "sprite_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png"
    }

@pytest.fixture
def pokemon_bulbasaur_data():
    """
    Sample Bulbasaur data for testing.
    
    Returns:
        dict: Sample Bulbasaur data
    """
    return {
        "name": "bulbasaur",
        "base_stats": {
            "hp": 45,
            "attack": 49,
            "defense": 49,
            "special_attack": 65,
            "special_defense": 65,
            "speed": 45
        },
        "types": ["grass", "poison"],
        "abilities": ["overgrow", "chlorophyll"],
        "height": 0.7,
        "weight": 6.9,
        "sprite_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png"
    }

@pytest.fixture
def research_pikachu_result():
    """
    Sample research result for Pikachu.
    
    Returns:
        dict: Sample research result
    """
    return {
        "name": "pikachu",
        "pokemon_details": [
            "Pikachu is an Electric-type Pokémon introduced in Generation I.",
            "It is known as the Mouse Pokémon.",
            "Pikachu is famous for being the mascot of the Pokémon franchise."
        ],
        "research_queries": [
            "How does Pikachu evolve?",
            "What are Pikachu's best moves?",
            "How to train Pikachu effectively?"
        ],
        "base_stats": {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "special_attack": 50,
            "special_defense": 50,
            "speed": 90
        },
        "types": ["electric"],
        "abilities": ["static", "lightning-rod"],
        "height": 0.4,
        "weight": 6.0,
        "analysis": {
            "strengths": "High speed and decent special attack",
            "weaknesses": "Low HP and defense",
            "recommended_role": "Fast attacker"
        }
    }

@pytest.fixture
def battle_analysis_result():
    """
    Sample battle analysis result.
    
    Returns:
        dict: Sample battle analysis result
    """
    return {
        "pokemon_1": "pikachu",
        "pokemon_2": "bulbasaur",
        "analysis": "Pikachu has a speed advantage over Bulbasaur, but no type advantage. Bulbasaur has higher HP and defense.",
        "reasoning": "While Pikachu is faster, Bulbasaur's higher HP and defense stats give it an edge in a prolonged battle. Electric attacks are not super effective against Grass/Poison types.",
        "winner": "bulbasaur"
    }
