"""
Tests for the Pokemon API models.

This module contains tests for the Pokemon API models validation.
"""

import pytest
from pydantic import ValidationError

from app.api.models.pokemon import (
    ChatRequest, 
    PokemonStats, 
    PokemonResearchDetails,
    BattleAnalysis,
    SupervisorResult,
    ChatResponse,
    BattleResponse
)

class TestPokemonModels:
    """Tests for the Pokemon API models."""
    
    def test_chat_request_valid(self):
        """Test ChatRequest with valid data."""
        data = {"message": "Test message"}
        request = ChatRequest(**data)
        
        assert request.message == "Test message"
    
    def test_chat_request_invalid(self):
        """Test ChatRequest with invalid data."""
        # Missing required field
        data = {}
        
        with pytest.raises(ValidationError):
            ChatRequest(**data)
    
    def test_pokemon_stats_valid(self):
        """Test PokemonStats with valid data."""
        data = {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "special_attack": 50,
            "special_defense": 50,
            "speed": 90
        }
        stats = PokemonStats(**data)
        
        assert stats.hp == 35
        assert stats.attack == 55
        assert stats.defense == 40
        assert stats.special_attack == 50
        assert stats.special_defense == 50
        assert stats.speed == 90
    
    def test_pokemon_stats_invalid(self):
        """Test PokemonStats with invalid data."""
        # Missing required field
        data = {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "special_attack": 50,
            "special_defense": 50
            # Missing speed
        }
        
        with pytest.raises(ValidationError):
            PokemonStats(**data)
        
        # Note: Pydantic v2 automatically converts strings to ints when possible,
        # so we'll test with an invalid string that can't be converted
        data = {
            "hp": "invalid",  # String that can't be converted to int
            "attack": 55,
            "defense": 40,
            "special_attack": 50,
            "special_defense": 50,
            "speed": 90
        }
        
        with pytest.raises(ValidationError):
            PokemonStats(**data)
    
    def test_pokemon_research_details_valid(self):
        """Test PokemonResearchDetails with valid data."""
        data = {
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
            "pokemon_details": ["Pikachu is an Electric-type Pokémon."],
            "research_queries": ["How does Pikachu evolve?"]
        }
        details = PokemonResearchDetails(**data)
        
        assert details.name == "pikachu"
        assert details.base_stats["hp"] == 35
        assert details.types == ["electric"]
        assert details.abilities == ["static", "lightning-rod"]
        assert details.height == 0.4
        assert details.weight == 6.0
        assert details.pokemon_details == ["Pikachu is an Electric-type Pokémon."]
        assert details.research_queries == ["How does Pikachu evolve?"]
        assert details.analysis is None  # Optional field
    
    def test_pokemon_research_details_with_analysis(self):
        """Test PokemonResearchDetails with analysis field."""
        data = {
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
            "pokemon_details": ["Pikachu is an Electric-type Pokémon."],
            "research_queries": ["How does Pikachu evolve?"],
            "analysis": {
                "strengths": "High speed and decent special attack",
                "weaknesses": "Low HP and defense",
                "recommended_role": "Fast attacker"
            }
        }
        details = PokemonResearchDetails(**data)
        
        assert details.analysis is not None
        assert details.analysis["strengths"] == "High speed and decent special attack"
    
    def test_pokemon_research_details_invalid(self):
        """Test PokemonResearchDetails with invalid data."""
        # Missing required field
        data = {
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
            # Missing pokemon_details
            "research_queries": ["How does Pikachu evolve?"]
        }
        
        with pytest.raises(ValidationError):
            PokemonResearchDetails(**data)
    
    def test_battle_analysis_valid(self):
        """Test BattleAnalysis with valid data."""
        data = {
            "pokemon_1": "pikachu",
            "pokemon_2": "bulbasaur",
            "analysis": "Analysis of the battle between Pikachu and Bulbasaur",
            "reasoning": "Reasoning for the battle outcome",
            "winner": "bulbasaur"
        }
        analysis = BattleAnalysis(**data)
        
        assert analysis.pokemon_1 == "pikachu"
        assert analysis.pokemon_2 == "bulbasaur"
        assert analysis.analysis == "Analysis of the battle between Pikachu and Bulbasaur"
        assert analysis.reasoning == "Reasoning for the battle outcome"
        assert analysis.winner == "bulbasaur"
    
    def test_battle_analysis_invalid(self):
        """Test BattleAnalysis with invalid data."""
        # Missing required field
        data = {
            "pokemon_1": "pikachu",
            "pokemon_2": "bulbasaur",
            "analysis": "Analysis of the battle between Pikachu and Bulbasaur",
            # Missing reasoning
            "winner": "bulbasaur"
        }
        
        with pytest.raises(ValidationError):
            BattleAnalysis(**data)
    
    def test_supervisor_result_valid(self):
        """Test SupervisorResult with valid data."""
        data = {
            "answer": "This is the answer",
            "reflection": {
                "reasoning": "This is the reasoning",
                "answer": "This is the reflection answer"
            },
            "is_pokemon_query": True,
            "pokemon_names": ["pikachu", "bulbasaur"]
        }
        result = SupervisorResult(**data)
        
        assert result.answer == "This is the answer"
        assert result.reflection["reasoning"] == "This is the reasoning"
        assert result.is_pokemon_query is True
        assert result.pokemon_names == ["pikachu", "bulbasaur"]
        assert result.search_queries is None  # Optional field
    
    def test_supervisor_result_with_search_queries(self):
        """Test SupervisorResult with search_queries field."""
        data = {
            "answer": "This is the answer",
            "reflection": {
                "reasoning": "This is the reasoning",
                "answer": "This is the reflection answer"
            },
            "is_pokemon_query": False,
            "search_queries": ["query 1", "query 2"]
        }
        result = SupervisorResult(**data)
        
        assert result.search_queries == ["query 1", "query 2"]
        assert result.pokemon_names is None  # Optional field
    
    def test_supervisor_result_invalid(self):
        """Test SupervisorResult with invalid data."""
        # Missing required field
        data = {
            "answer": "This is the answer",
            # Missing reflection
            "is_pokemon_query": True,
            "pokemon_names": ["pikachu", "bulbasaur"]
        }
        
        with pytest.raises(ValidationError):
            SupervisorResult(**data)
    
    def test_chat_response_valid(self):
        """Test ChatResponse with valid data."""
        data = {
            "response": {
                "supervisor_result": {
                    "answer": "This is the answer",
                    "reflection": {
                        "reasoning": "This is the reasoning",
                        "answer": "This is the reflection answer"
                    },
                    "is_pokemon_query": False
                },
                "pokemon_research": {},
                "battle_analysis": None
            }
        }
        response = ChatResponse(**data)
        
        assert response.response is not None
        assert response.response["supervisor_result"]["answer"] == "This is the answer"
    
    def test_chat_response_with_extra_fields(self):
        """Test ChatResponse with extra fields (allowed by model_config)."""
        data = {
            "Pikachu": {
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
                "abilities": ["static", "lightning-rod"]
            }
        }
        response = ChatResponse(**data)
        
        # Extra fields should be accessible
        assert response.Pikachu["name"] == "pikachu"
    
    def test_battle_response_valid(self):
        """Test BattleResponse with valid data."""
        data = {
            "pokemon1": {
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
                "abilities": ["static", "lightning-rod"]
            },
            "pokemon2": {
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
                "abilities": ["overgrow", "chlorophyll"]
            },
            "battle_analysis": {
                "pokemon_1": "pikachu",
                "pokemon_2": "bulbasaur",
                "analysis": "Analysis of the battle between Pikachu and Bulbasaur",
                "reasoning": "Reasoning for the battle outcome",
                "winner": "bulbasaur"
            }
        }
        response = BattleResponse(**data)
        
        assert response.pokemon1["name"] == "pikachu"
        assert response.pokemon2["name"] == "bulbasaur"
        assert response.battle_analysis["winner"] == "bulbasaur"
    
    def test_battle_response_invalid(self):
        """Test BattleResponse with invalid data."""
        # Missing required field
        data = {
            "pokemon1": {
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
                "abilities": ["static", "lightning-rod"]
            },
            # Missing pokemon2
            "battle_analysis": {
                "pokemon_1": "pikachu",
                "pokemon_2": "bulbasaur",
                "analysis": "Analysis of the battle between Pikachu and Bulbasaur",
                "reasoning": "Reasoning for the battle outcome",
                "winner": "bulbasaur"
            }
        }
        
        with pytest.raises(ValidationError):
            BattleResponse(**data)
