"""
API models for Pokemon-related endpoints.

This module contains Pydantic models for request and response validation
for Pokemon-related API endpoints.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# Request Models
class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    message: str = Field(..., description="User's message or query")

# Response Models
class PokemonStats(BaseModel):
    """Model for Pokemon base stats."""
    hp: int = Field(..., description="Hit Points stat")
    attack: int = Field(..., description="Attack stat")
    defense: int = Field(..., description="Defense stat")
    special_attack: int = Field(..., description="Special Attack stat")
    special_defense: int = Field(..., description="Special Defense stat")
    speed: int = Field(..., description="Speed stat")

class PokemonResearchDetails(BaseModel):
    """Model for detailed Pokemon research information."""
    name: str = Field(..., description="Name of the Pokemon")
    base_stats: Dict[str, int] = Field(..., description="Base stats of the Pokemon")
    types: List[str] = Field(..., description="Types of the Pokemon")
    abilities: List[str] = Field(..., description="Abilities of the Pokemon")
    height: float = Field(..., description="Height in meters")
    weight: float = Field(..., description="Weight in kilograms")
    pokemon_details: List[str] = Field(..., description="Detailed information about the Pokemon")
    research_queries: List[str] = Field(..., description="Suggested research queries about the Pokemon")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Detailed analysis of the Pokemon")

class BattleAnalysis(BaseModel):
    """Model for battle analysis results."""
    pokemon_1: str = Field(..., description="Name of the first Pokemon")
    pokemon_2: str = Field(..., description="Name of the second Pokemon")
    analysis: str = Field(..., description="Detailed analysis of the battle")
    reasoning: str = Field(..., description="Reasoning for determining the winner")
    winner: str = Field(..., description="Name of the Pokemon that would likely win the battle")

class SupervisorResult(BaseModel):
    """Model for supervisor agent results."""
    answer: str = Field(..., description="Final answer after reflection and analysis")
    reflection: Dict[str, str] = Field(..., description="Reflection on the question and answer process")
    search_queries: Optional[List[str]] = Field(None, description="Queries sent to the search API")
    is_pokemon_query: bool = Field(..., description="Indicates if the query is about Pokémon")
    pokemon_names: Optional[List[str]] = Field(None, description="List of Pokémon names extracted from the query")

class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""
    response: Optional[Dict[str, Any]] = Field(None, description="Response containing supervisor result, Pokemon research, and battle analysis if applicable")
    
    # Allow direct Pokemon data to be returned
    model_config = {
        "extra": "allow"
    }

class BattleResponse(BaseModel):
    """Response model for the battle endpoint."""
    pokemon1: Dict[str, Any] = Field(..., description="Research results for the first Pokemon")
    pokemon2: Dict[str, Any] = Field(..., description="Research results for the second Pokemon")
    battle_analysis: Dict[str, Any] = Field(..., description="Analysis of the battle between the two Pokemon")
