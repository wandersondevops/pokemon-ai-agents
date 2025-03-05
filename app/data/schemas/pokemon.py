"""
Schema definitions for the Pokemon AI Research Agent.

This module contains Pydantic models that define the structure of data used throughout the application.
These schemas are used for validation, serialization, and documentation purposes.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# -------------------- Search and General Knowledge Schemas -------------------- #

class Reflection(BaseModel):
    """Schema for agent's reflection on a user question."""
    
    reasoning: str = Field(
        description="Reasoning about how to process the user question"
    )
    answer: str = Field(
        description="Direct answer for general knowledge questions, or delegation query for Research Pokemon Agent"
    )


class SupervisorAgent(BaseModel):
    """Schema for the supervisor agent's complete answer to a user question."""
    answer: str = Field(
        description="Final answer after reflection and analysis"
    )
    reflection: Reflection = Field(
        description="Reflection on the question and answer process"
    )
    search_queries: Optional[List[str]] = Field(
        default=None,
        description="Highly precise queries sent to the search API for answering the user question with precision and detail. Only include when the agent doesn't know the answer."
    )
    needs_search: bool = Field(
        default=False,
        description="Indicates if the query requires search to be answered"
    )
    is_pokemon_query: bool = Field(
        default=False,
        description="Indicates if the query is about Pokémon and should be delegated to the Researcher Agent"
    )
    pokemon_names: Optional[List[str]] = Field(
        default=None,
        description="List of Pokémon names extracted from the query (maximum of 2), if it's a Pokémon-related query"
    )

# -------------------- Pokemon Research Schemas -------------------- #

class ResearchPokemon(BaseModel):
    """Schema for comprehensive Pokémon research results."""
    
    name: str = Field(
        description="Name of the Pokémon"
    )
    pokemon_details: List[str] = Field(
        description="Detailed information about the Pokémon including stats, types, abilities, etc."
    )
    research_queries: List[str] = Field(
        description="Queries for additional research about the Pokémon"
    )
    
    # Optional detailed fields that match the researcher_agent_template
    base_stats: Optional[Dict[str, int]] = Field(
        default=None,
        description="Base stats including HP, Attack, Defense, Special Attack, Special Defense, and Speed"
    )
    types: Optional[List[str]] = Field(
        default=None,
        description="Pokémon types (e.g., Fire, Water, Grass)"
    )
    abilities: Optional[List[str]] = Field(
        default=None,
        description="Pokémon abilities"
    )
    height: Optional[float] = Field(
        default=None,
        description="Height in meters"
    )
    weight: Optional[float] = Field(
        default=None,
        description="Weight in kilograms"
    )
    analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed analysis including type advantages/disadvantages, role, abilities explanation, etc."
    )

# -------------------- Pokemon Expert Analysis Schemas -------------------- #

class PokemonExpertAnalystAgent(BaseModel):
    """Schema for expert Pokémon analysis."""
    
    pokemon_1: str = Field(
        description="Name of the first Pokémon being analyzed"
    )
    pokemon_2: str = Field(
        description="Name of the second Pokémon being analyzed"
    )
    analysis: str = Field(
        description="Analyzes the data retrieved by the Researcher Agent"
    )
    reasoning: str = Field(
        description="Determines the probable winner in a Pokémon battle based on stats and type advantages."
    )
    winner: str = Field(
        description="Name of the Pokemon's winner."
    )
