"""
Tests for the Pokemon router.

This module contains tests for the Pokemon router endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.core.config import settings
from app.api.models.pokemon import ChatRequest
from app.core.dependencies import get_llm, get_search_wrapper
from tests.unit.api.conftest import mock_llm, mock_search_wrapper

class TestPokemonRouter:
    """Tests for the Pokemon router."""
    
    def test_health_check(self, test_client):
        """Test the health check endpoint."""
        response = test_client.get(f"{settings.API_V1_STR}/pokemon/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ok", "message": "Pokemon API is running"}
    
    @patch('app.api.routers.pokemon.process_query')
    def test_chat_general_query(self, mock_process_query, test_client):
        """Test the chat endpoint with a general query."""
        # Setup mock
        mock_process_query.return_value = {
            "answer": "This is a general answer.",
            "reflection": {
                "reasoning": "Some reasoning",
                "answer": "Some answer"
            },
            "is_pokemon_query": False
        }
        
        # Make request
        response = test_client.post(
            f"{settings.API_V1_STR}/pokemon/chat",
            json={"message": "What is the capital of France?"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "response" in response_data
        assert response_data["response"]["supervisor_result"]["answer"] == "This is a general answer."
        assert not response_data["response"]["supervisor_result"]["is_pokemon_query"]
        
        # Verify mock was called correctly
        # Use any instance of the mocks from the fixture
        mock_process_query.assert_called_once_with(
            "What is the capital of France?", 
            mock_llm, 
            mock_search_wrapper
        )
    
    @patch('app.api.routers.pokemon.process_query')
    @patch('app.api.routers.pokemon.research_pokemon')
    def test_chat_pokemon_query_single(self, mock_research, mock_process_query, test_client):
        """Test the chat endpoint with a query about a single Pokemon."""
        # Setup mocks
        mock_process_query.return_value = {
            "answer": "Let me research Pikachu for you.",
            "reflection": {
                "reasoning": "This is a Pokemon query about Pikachu.",
                "answer": "I'll delegate to the Pokemon researcher."
            },
            "is_pokemon_query": True,
            "pokemon_names": ["pikachu"]
        }
        
        mock_research.return_value = {
            "name": "pikachu",
            "pokemon_details": ["Pikachu is an Electric-type Pokémon."],
            "research_queries": ["How does Pikachu evolve?"],
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
            "weight": 6.0
        }
        
        # Make request
        response = test_client.post(
            f"{settings.API_V1_STR}/pokemon/chat",
            json={"message": "Tell me about Pikachu"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        # For a Pokemon query, the response should directly contain the Pokemon data
        assert "Pikachu" in response_data
        assert response_data["Pikachu"]["name"] == "pikachu"
        assert "electric" in response_data["Pikachu"]["types"]
        
        # Verify mocks were called correctly
        mock_process_query.assert_called_once()
        mock_research.assert_called_once_with("pikachu", mock_llm)
    
    @patch('app.api.routers.pokemon.process_query')
    @patch('app.api.routers.pokemon.research_pokemon')
    @patch('app.api.routers.pokemon.analyze_pokemon_battle')
    def test_chat_pokemon_query_battle(self, mock_battle, mock_research, mock_process_query, test_client):
        """Test the chat endpoint with a query about a battle between two Pokemon."""
        # Setup mocks
        mock_process_query.return_value = {
            "answer": "Let me analyze a battle between Pikachu and Bulbasaur.",
            "reflection": {
                "reasoning": "This is a Pokemon battle query.",
                "answer": "I'll delegate to the Pokemon researcher and battle analyst."
            },
            "is_pokemon_query": True,
            "pokemon_names": ["pikachu", "bulbasaur"]
        }
        
        # Mock research results for both Pokemon
        pikachu_research = {
            "name": "pikachu",
            "pokemon_details": ["Pikachu is an Electric-type Pokémon."],
            "research_queries": ["How does Pikachu evolve?"],
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
            "weight": 6.0
        }
        
        bulbasaur_research = {
            "name": "bulbasaur",
            "pokemon_details": ["Bulbasaur is a Grass/Poison-type Pokémon."],
            "research_queries": ["How does Bulbasaur evolve?"],
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
            "weight": 6.9
        }
        
        # Configure the mock to return different values based on input
        def research_side_effect(pokemon_name, _):
            if pokemon_name.lower() == "pikachu":
                return pikachu_research
            elif pokemon_name.lower() == "bulbasaur":
                return bulbasaur_research
            return {"error": "Pokemon not found"}
        
        mock_research.side_effect = research_side_effect
        
        # Mock battle analysis
        battle_analysis = {
            "pokemon_1": "pikachu",
            "pokemon_2": "bulbasaur",
            "analysis": "Analysis of the battle between Pikachu and Bulbasaur",
            "reasoning": "Reasoning for the battle outcome",
            "winner": "bulbasaur"
        }
        mock_battle.return_value = battle_analysis
        
        # Make request
        response = test_client.post(
            f"{settings.API_V1_STR}/pokemon/chat",
            json={"message": "Who would win in a battle between Pikachu and Bulbasaur?"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        # For a Pokemon query with two Pokemon, the response should contain both Pokemon data
        assert "Pikachu" in response_data
        assert "Bulbasaur" in response_data
        
        # With our updated implementation, battle_analysis should be included in the response
        assert "battle_analysis" in response_data
        assert response_data["battle_analysis"] is not None
        
        # Verify that analyze_pokemon_battle was called
        mock_battle.assert_called_once()
        
        # Verify mocks were called correctly
        mock_process_query.assert_called_once()
        assert mock_research.call_count == 2
        mock_battle.assert_called_once()
    
    @patch('app.api.routers.pokemon.research_pokemon')
    @patch('app.api.routers.pokemon.analyze_pokemon_battle')
    def test_battle_endpoint(self, mock_battle, mock_research, test_client):
        """Test the battle endpoint."""
        # Setup mocks
        pikachu_research = {
            "name": "pikachu",
            "pokemon_details": ["Pikachu is an Electric-type Pokémon."],
            "research_queries": ["How does Pikachu evolve?"],
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
            "weight": 6.0
        }
        
        bulbasaur_research = {
            "name": "bulbasaur",
            "pokemon_details": ["Bulbasaur is a Grass/Poison-type Pokémon."],
            "research_queries": ["How does Bulbasaur evolve?"],
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
            "weight": 6.9
        }
        
        # Configure the mock to return different values based on input
        def research_side_effect(pokemon_name, _):
            if pokemon_name.lower() == "pikachu":
                return pikachu_research
            elif pokemon_name.lower() == "bulbasaur":
                return bulbasaur_research
            return {"error": f"Failed to fetch data for {pokemon_name}"}
        
        mock_research.side_effect = research_side_effect
        
        # Mock battle analysis
        mock_battle.return_value = {
            "pokemon_1": "pikachu",
            "pokemon_2": "bulbasaur",
            "analysis": "Analysis of the battle between Pikachu and Bulbasaur",
            "reasoning": "Reasoning for the battle outcome",
            "winner": "bulbasaur"
        }
        
        # Make request
        response = test_client.get(
            f"{settings.API_V1_STR}/pokemon/battle?pokemon1=Pikachu&pokemon2=Bulbasaur"
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        assert "pokemon1" in response_data
        assert "pokemon2" in response_data
        assert "battle_analysis" in response_data
        assert response_data["battle_analysis"]["winner"] == "bulbasaur"
        
        # Verify mocks were called correctly
        assert mock_research.call_count == 2
        mock_battle.assert_called_once()
    
    @patch('app.api.routers.pokemon.research_pokemon')
    def test_battle_endpoint_pokemon_not_found(self, mock_research, test_client):
        """Test the battle endpoint when a Pokemon is not found."""
        # Setup mock to return error for nonexistent_pokemon and success for Bulbasaur
        def research_side_effect(pokemon_name, _):
            if pokemon_name.lower() == "nonexistent_pokemon":
                return {"error": "Failed to fetch data for nonexistent_pokemon"}
            else:
                return {
                    "name": "bulbasaur",
                    "pokemon_details": ["Bulbasaur is a Grass/Poison-type Pokémon."],
                    "base_stats": {"hp": 45},
                    "types": ["grass", "poison"],
                    "abilities": ["overgrow"],
                    "height": 0.7,
                    "weight": 6.9,
                    "research_queries": []
                }
        
        mock_research.side_effect = research_side_effect
        
        # Make request
        response = test_client.get(
            f"{settings.API_V1_STR}/pokemon/battle?pokemon1=nonexistent_pokemon&pokemon2=Bulbasaur"
        )
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert "detail" in response_data
        assert "Failed to fetch data for nonexistent_pokemon" in response_data["detail"]
        
        # Verify mock was called with nonexistent_pokemon
        mock_research.assert_any_call("nonexistent_pokemon", mock_llm)
    
    def test_chat_invalid_request(self, test_client):
        """Test the chat endpoint with an invalid request."""
        # Make request with missing message
        response = test_client.post(
            f"{settings.API_V1_STR}/pokemon/chat",
            json={}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    @patch('app.api.routers.pokemon.process_query')
    def test_chat_internal_error(self, mock_process_query, test_client):
        """Test the chat endpoint when an internal error occurs."""
        # Setup mock to raise an exception
        mock_process_query.side_effect = Exception("Test error")
        
        # Make request
        response = test_client.post(
            f"{settings.API_V1_STR}/pokemon/chat",
            json={"message": "Test message"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = response.json()
        assert "detail" in response_data
        assert "An error occurred" in response_data["detail"]
        
        # Verify mock was called correctly
        mock_process_query.assert_called_once()


