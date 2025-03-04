"""
Tests for the Pokemon research service.

This module contains tests for the Pokemon research service functions.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.pokemon.research import research_pokemon, analyze_pokemon_battle
from app.data.schemas.pokemon import ResearchPokemon, PokemonExpertAnalystAgent

class TestPokemonResearch:
    """Tests for the Pokemon research service."""
    
    @patch('app.services.pokemon.research.fetch_pokemon_data')
    @patch('app.services.pokemon.research.researcher_agent_template')
    def test_research_pokemon_success(self, mock_template, mock_fetch, mock_llm, research_pikachu_result):
        """Test successful research of a Pokemon."""
        # Setup mocks
        mock_fetch.return_value = {
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
        
        # Mock the chain response
        mock_chain = MagicMock()
        mock_template.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        
        # Create a mock ResearchPokemon object
        mock_result = ResearchPokemon(
            name=research_pikachu_result["name"],
            pokemon_details=research_pikachu_result["pokemon_details"],
            research_queries=research_pikachu_result["research_queries"],
            base_stats=research_pikachu_result["base_stats"],
            types=research_pikachu_result["types"],
            abilities=research_pikachu_result["abilities"],
            height=research_pikachu_result["height"],
            weight=research_pikachu_result["weight"],
            analysis=research_pikachu_result.get("analysis", {})
        )
        
        mock_chain.invoke.return_value = [mock_result]
        
        # Call the function
        result = research_pokemon("pikachu", mock_llm)
        
        # Assertions
        assert result["name"] == research_pikachu_result["name"]
        assert result["base_stats"] == research_pikachu_result["base_stats"]
        mock_fetch.assert_called_once_with("pikachu")
        mock_chain.invoke.assert_called_once()
        
    @patch('app.services.pokemon.research.fetch_pokemon_data')
    def test_research_pokemon_api_error(self, mock_fetch, mock_llm):
        """Test error handling when the Pokemon API returns an error."""
        # Setup mocks
        mock_fetch.return_value = {"error": "Failed to fetch data for nonexistent_pokemon"}
        
        # Call the function
        result = research_pokemon("nonexistent_pokemon", mock_llm)
        
        # Assertions
        assert "error" in result
        assert result["error"] == "Failed to fetch data for nonexistent_pokemon"
        mock_fetch.assert_called_once_with("nonexistent_pokemon")
        
    @patch('app.services.pokemon.research.fetch_pokemon_data')
    @patch('app.services.pokemon.research.researcher_agent_template')
    def test_research_pokemon_llm_error(self, mock_template, mock_fetch, mock_llm):
        """Test error handling when the LLM fails to process the Pokemon data."""
        # Setup mocks
        mock_fetch.return_value = {
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
        
        # Mock the chain response
        mock_chain = MagicMock()
        mock_template.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        
        # Mock the LLM response to return an empty list
        mock_chain.invoke.return_value = []
        
        # Call the function
        result = research_pokemon("pikachu", mock_llm)
        
        # Assertions
        assert "error" in result
        assert result["error"] == "Failed to research Pokemon"
        mock_fetch.assert_called_once_with("pikachu")
        mock_chain.invoke.assert_called_once()
        
    @patch('app.services.pokemon.research.expert_agent_template')
    def test_analyze_pokemon_battle(self, mock_template, mock_llm, research_pikachu_result, pokemon_bulbasaur_data, battle_analysis_result):
        """Test successful analysis of a Pokemon battle."""
        # Setup mocks
        pokemon_research_results = {
            "pikachu": research_pikachu_result,
            "bulbasaur": {
                "name": "bulbasaur",
                "pokemon_details": ["Bulbasaur is a Grass/Poison-type Pokémon."],
                "research_queries": ["How does Bulbasaur evolve?"],
                "base_stats": pokemon_bulbasaur_data["base_stats"],
                "types": pokemon_bulbasaur_data["types"],
                "abilities": pokemon_bulbasaur_data["abilities"],
                "height": pokemon_bulbasaur_data["height"],
                "weight": pokemon_bulbasaur_data["weight"]
            }
        }
        
        # Mock the chain response
        mock_chain = MagicMock()
        mock_template.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        
        # Create a mock PokemonExpertAnalystAgent object
        mock_result = PokemonExpertAnalystAgent(
            pokemon_1=battle_analysis_result["pokemon_1"],
            pokemon_2=battle_analysis_result["pokemon_2"],
            analysis=battle_analysis_result["analysis"],
            reasoning=battle_analysis_result["reasoning"],
            winner=battle_analysis_result["winner"]
        )
        
        mock_chain.invoke.return_value = [mock_result]
        
        # Call the function
        result = analyze_pokemon_battle(pokemon_research_results, mock_llm)
        
        # Assertions
        assert result["pokemon_1"] == battle_analysis_result["pokemon_1"]
        assert result["pokemon_2"] == battle_analysis_result["pokemon_2"]
        assert result["winner"] == battle_analysis_result["winner"]
        mock_chain.invoke.assert_called_once()
        
    @patch('app.services.pokemon.research.expert_agent_template')
    def test_analyze_pokemon_battle_llm_error(self, mock_template, mock_llm):
        """Test error handling when the LLM fails to analyze the battle."""
        # Setup mocks
        pokemon_research_results = {
            "pikachu": {"name": "pikachu", "base_stats": {}, "types": [], "abilities": []},
            "bulbasaur": {"name": "bulbasaur", "base_stats": {}, "types": [], "abilities": []}
        }
        
        # Mock the chain response
        mock_chain = MagicMock()
        mock_template.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        
        # Mock the LLM response to return an empty list
        mock_chain.invoke.return_value = []
        
        # Call the function
        result = analyze_pokemon_battle(pokemon_research_results, mock_llm)
        
        # Assertions
        assert "error" in result
        assert result["error"] == "Failed to analyze battle"
        mock_chain.invoke.assert_called_once()
        
    @patch('app.services.pokemon.research.expert_agent_template')
    def test_analyze_pokemon_battle_name_correction(self, mock_template, mock_llm, research_pikachu_result, pokemon_bulbasaur_data):
        """Test that Pokemon names are corrected if the LLM returns incorrect names."""
        # Setup mocks
        pokemon_research_results = {
            "pikachu": research_pikachu_result,
            "bulbasaur": {
                "name": "bulbasaur",
                "pokemon_details": ["Bulbasaur is a Grass/Poison-type Pokémon."],
                "research_queries": ["How does Bulbasaur evolve?"],
                "base_stats": pokemon_bulbasaur_data["base_stats"],
                "types": pokemon_bulbasaur_data["types"],
                "abilities": pokemon_bulbasaur_data["abilities"],
                "height": pokemon_bulbasaur_data["height"],
                "weight": pokemon_bulbasaur_data["weight"]
            }
        }
        
        # Mock the chain response
        mock_chain = MagicMock()
        mock_template.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        
        # Create a mock PokemonExpertAnalystAgent object with incorrect names
        mock_result = PokemonExpertAnalystAgent(
            pokemon_1="charizard",  # Incorrect name
            pokemon_2="squirtle",   # Incorrect name
            analysis="Analysis text",
            reasoning="Reasoning text",
            winner="charizard"
        )
        
        mock_chain.invoke.return_value = [mock_result]
        
        # Call the function
        result = analyze_pokemon_battle(pokemon_research_results, mock_llm)
        
        # Assertions
        assert result["pokemon_1"] == "pikachu"  # Should be corrected
        assert result["pokemon_2"] == "bulbasaur"  # Should be corrected
        mock_chain.invoke.assert_called_once()
