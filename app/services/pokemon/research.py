"""
Pokemon research service.

This module contains functions for researching Pokemon using the AI agents.
"""

import json
from typing import Dict, Any, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.data.repositories.pokemon import fetch_pokemon_data
from app.data.schemas.pokemon import ResearchPokemon, PokemonExpertAnalystAgent
from app.services.agents.prompts import researcher_agent_template, expert_agent_template

def research_pokemon(pokemon_name: str, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Research a Pokemon using the API and the researcher agent.
    
    Args:
        pokemon_name (str): The name of the Pokemon to research
        llm (ChatOpenAI): The language model to use
        
    Returns:
        Dict[str, Any]: Research results for the Pokemon
    """
    # Fetch Pokemon data from the API
    pokemon_data = fetch_pokemon_data(pokemon_name)
    
    # If there was an error fetching the data, return the error
    if "error" in pokemon_data:
        return {"error": pokemon_data["error"]}
    
    # Define tools in the format expected by OpenAI
    researcher_tool = {
        "type": "function",
        "function": {
            "name": "ResearchPokemon",
            "description": "Researcher agent that processes Pokemon data",
            "parameters": ResearchPokemon.model_json_schema()
        }
    }
    
    # Create a system message with the Pokemon data and clear instructions
    system_message = SystemMessage(
        content=f"""Here is the Pokemon data for {pokemon_name}:
            {json.dumps(pokemon_data, indent=2)}

            As a Pokemon Researcher Agent, your task is to:
            1. Extract and organize ALL relevant details from this data
            2. You MUST include the following information in your response:
            - Name: The exact name of the Pokemon
            - Base Stats: All stats including HP, Attack, Defense, Special Attack, Special Defense, and Speed
            - Types: All types the Pokemon has
            - Abilities: All abilities the Pokemon has
            - Height: The height in meters
            - Weight: The weight in kilograms

            3. Provide a comprehensive analysis including:
            - Base stats interpretation (what the Pokemon excels at)
            - Type advantages and disadvantages
            - How its abilities can be utilized effectively
            - Recommended battle role based on stats and abilities
            - Suggested moves and items that complement its strengths

            Ensure your response includes ALL the detailed information available in the data. Do not omit any stats, types, or abilities.
            """
    )
    
    # Create a human message asking for analysis
    human_message = HumanMessage(
        content=f"Please analyze the Pokemon {pokemon_name} based on the provided data and return a comprehensive research report with all relevant details."
    )
    
    # Create the parser
    parser = PydanticToolsParser(tools=[ResearchPokemon])
    
    # Create the chain for the researcher agent
    chain = (
        researcher_agent_template
        | llm.bind(tools=[researcher_tool], tool_choice={"type": "function", "function": {"name": "ResearchPokemon"}})
        | parser
    )
    
    # Invoke the chain with the messages
    result = chain.invoke(input={"messages": [system_message, human_message]})
    
    # Ensure all data from the API is included in the result
    if result and len(result) > 0:
        # Copy the data directly from the API response to ensure it's included
        result[0].base_stats = pokemon_data["base_stats"]
        result[0].types = pokemon_data["types"]
        result[0].abilities = pokemon_data["abilities"]
        result[0].height = pokemon_data["height"]
        result[0].weight = pokemon_data["weight"]
    
    return result[0].model_dump() if result and len(result) > 0 else {"error": "Failed to research Pokemon"}

def analyze_pokemon_battle(pokemon_research_results: Dict[str, Dict[str, Any]], llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Analyze the battle potential between two Pokémon using the expert agent.
    
    Args:
        pokemon_research_results: Dictionary containing research results for Pokémon
        llm (ChatOpenAI): The language model to use
        
    Returns:
        Dict[str, Any]: Battle analysis results
    """
    # Format the research results for the expert agent
    formatted_results = {}
    for pokemon_name, research in pokemon_research_results.items():
        formatted_results[pokemon_name] = {
            "name": research["name"],
            "base_stats": research["base_stats"],
            "types": research["types"],
            "abilities": research["abilities"]
        }
    
    # Get the Pokémon names
    pokemon_names = list(formatted_results.keys())
    pokemon_1 = pokemon_names[0]
    pokemon_2 = pokemon_names[1]
    
    # Create a system message with the Pokemon data
    system_message = SystemMessage(
        content=f"""
        You are analyzing a battle between {pokemon_1} and {pokemon_2} ONLY.
        
        Here is the data for {pokemon_1}:
        {json.dumps(formatted_results[pokemon_1], indent=2)}
        
        Here is the data for {pokemon_2}:
        {json.dumps(formatted_results[pokemon_2], indent=2)}
        
        Analyze their stats, types, and abilities to determine which one would likely win in a battle.
        Consider type advantages/disadvantages, base stats, and how abilities might affect the outcome.
        
        IMPORTANT: Your analysis must ONLY be about these two specific Pokémon. Do not analyze or mention any other Pokémon.
        """
    )
    
    # Create a human message with a specific battle analysis request
    human_message = HumanMessage(
        content=f"Analyze a battle between ONLY {pokemon_1} and {pokemon_2} based on their stats, types, and abilities. Which one would likely win in a battle? DO NOT analyze any other Pokémon besides these two."
    )
    
    # Create a custom expert tool with pre-filled Pokémon names
    expert_tool = {
        "type": "function",
        "function": {
            "name": "PokemonExpertAnalystAgent",
            "description": f"Analyzes the battle between {pokemon_1} and {pokemon_2} based on their stats and types.",
            "parameters": PokemonExpertAnalystAgent.model_json_schema()
        }
    }
    
    # Create the parser
    parser = PydanticToolsParser(tools=[PokemonExpertAnalystAgent])
    
    # Create the chain for the expert agent
    chain = (
        expert_agent_template
        | llm.bind(tools=[expert_tool], tool_choice={"type": "function", "function": {"name": "PokemonExpertAnalystAgent"}})
        | parser
    )
    
    # Invoke the chain with the messages
    result = chain.invoke(input={"messages": [system_message, human_message]})
    
    # Verify that the correct Pokémon were analyzed
    if result and len(result) > 0:
        # Check if the Pokémon names in the result match the expected names
        result_pokemon_1 = result[0].pokemon_1.lower()
        result_pokemon_2 = result[0].pokemon_2.lower()
        
        # If the names don't match, correct them
        if result_pokemon_1 != pokemon_1.lower():
            result[0].pokemon_1 = pokemon_1
        if result_pokemon_2 != pokemon_2.lower():
            result[0].pokemon_2 = pokemon_2
    
    return result[0].model_dump() if result and len(result) > 0 else {"error": "Failed to analyze battle"}
