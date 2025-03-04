"""
Tests for the Pokemon repository.

This module contains tests for the Pokemon repository functions.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.data.repositories.pokemon import fetch_pokemon_data

class TestPokemonRepository:
    """Tests for the Pokemon repository."""
    
    @patch('app.data.repositories.pokemon.requests.get')
    def test_fetch_pokemon_data_success(self, mock_get, pokemon_pikachu_data):
        """Test successful fetch of Pokemon data."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "pikachu",
            "stats": [
                {"base_stat": 35},  # HP
                {"base_stat": 55},  # Attack
                {"base_stat": 40},  # Defense
                {"base_stat": 50},  # Special Attack
                {"base_stat": 50},  # Special Defense
                {"base_stat": 90},  # Speed
            ],
            "types": [{"type": {"name": "electric"}}],
            "abilities": [
                {"ability": {"name": "static"}},
                {"ability": {"name": "lightning-rod"}}
            ],
            "height": 4,  # 0.4m after conversion
            "weight": 60,  # 6.0kg after conversion
            "sprites": {"front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png"}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the function
        result = fetch_pokemon_data("pikachu")
        
        # Assertions
        assert result == pokemon_pikachu_data
        mock_get.assert_called_once()
        
    @patch('app.data.repositories.pokemon.requests.get')
    def test_fetch_pokemon_data_http_error(self, mock_get):
        """Test HTTP error when fetching Pokemon data."""
        # Setup mock response
        from requests.exceptions import HTTPError
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Client Error: Not Found")
        mock_get.return_value = mock_response
        
        # Call the function
        result = fetch_pokemon_data("nonexistent_pokemon")
        
        # Assertions
        assert "error" in result
        assert "Failed to fetch data for nonexistent_pokemon" in result["error"]
        mock_get.assert_called_once()
        
    @patch('app.data.repositories.pokemon.requests.get')
    def test_fetch_pokemon_data_key_error(self, mock_get):
        """Test key error when processing Pokemon data."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"incomplete": "data"}  # Missing required keys
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the function
        result = fetch_pokemon_data("pikachu")
        
        # Assertions
        assert "error" in result
        assert "Failed to process data for pikachu" in result["error"]
        mock_get.assert_called_once()
        
    @patch('app.data.repositories.pokemon.requests.get')
    def test_fetch_pokemon_data_name_normalization(self, mock_get):
        """Test that Pokemon names are normalized before API call."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "pikachu",
            "stats": [
                {"base_stat": 35},  # HP
                {"base_stat": 55},  # Attack
                {"base_stat": 40},  # Defense
                {"base_stat": 50},  # Special Attack
                {"base_stat": 50},  # Special Defense
                {"base_stat": 90},  # Speed
            ],
            "types": [{"type": {"name": "electric"}}],
            "abilities": [
                {"ability": {"name": "static"}},
                {"ability": {"name": "lightning-rod"}}
            ],
            "height": 4,
            "weight": 60,
            "sprites": {"front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png"}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the function with mixed case and spaces
        fetch_pokemon_data("  PiKaChu  ")
        
        # Assertions
        mock_get.assert_called_once_with(f"{pytest.importorskip('app.core.config').settings.POKEMON_API_BASE_URL}/pikachu")
