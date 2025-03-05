"""
Pokemon router for the FastAPI application.

This module contains the routes for the Pokemon-related endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from typing import Dict, Any, List, Annotated
import json

from langchain_openai import ChatOpenAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

from app.core.dependencies import get_llm, get_search_wrapper
from app.api.models.pokemon import ChatRequest, ChatResponse, BattleResponse
from app.services.pokemon.research import research_pokemon, analyze_pokemon_battle
from app.services.agents.supervisor import process_query, process_search_results
from app.utils.helpers.tool_executor import execute_tools

# Create router
router = APIRouter(
    prefix="/pokemon",
    tags=["Pokemon"],
    responses={404: {"description": "Not found"}},
)

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        Dict with status message
    """
    return {"status": "ok", "message": "Pokemon API is running"}

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest = Body(..., description="User's message or query"),
    llm: ChatOpenAI = Depends(get_llm),
    search_wrapper: TavilySearchAPIWrapper = Depends(get_search_wrapper)
):
    """
    Process a chat message using the supervisor agent.
    
    This endpoint handles general queries as well as Pokémon-specific queries.
    For Pokémon queries, it will research the Pokémon and provide detailed information.
    If the query mentions two Pokémon, it will also analyze a potential battle between them.
    
    Args:
        request: ChatRequest containing the user message
        
    Returns:
        ChatResponse containing the agent's response with supervisor results, 
        Pokémon research (if applicable), and battle analysis (if applicable)
        

    """
    try:
        # Process the query using the supervisor agent
        supervisor_result = process_query(request.message, llm, search_wrapper)
        
        # Initialize response
        response = {
            "supervisor_result": supervisor_result,
            "pokemon_research": {},
            "battle_analysis": None,
            "final_answer": None
        }
        
        # If search is needed, process the search results and generate a final answer
        if supervisor_result.get("needs_search", False):
            # Create a mock state with the original question
            from langchain_core.messages import AIMessage, HumanMessage
            mock_state = [
                HumanMessage(content=request.message),
                AIMessage(content=json.dumps(supervisor_result))
            ]
            
            # Execute the search using the original question
            from app.utils.helpers.tool_executor import ToolExecutor
            tool_executor = ToolExecutor([search_wrapper])
            
            try:
                search_results = execute_tools(mock_state, tool_executor)
            except Exception as e:
                search_results = []
                response["final_answer"] = {"answer": f"Error executing search: {str(e)}", "sources": []}
            
            # If search results were found, process them
            if search_results and len(search_results) > 0:
                # Extract the search results from the ToolMessage
                search_data = search_results[0].content
                
                # If search_data is a string, try to parse it as JSON
                if isinstance(search_data, str):
                    try:
                        # First, try to parse it directly
                        parsed_data = json.loads(search_data)
                        search_data = parsed_data
                    except json.JSONDecodeError:
                        # If that fails, try to extract the JSON part
                        try:
                            # Extract the part that looks like JSON
                            import re
                            json_match = re.search(r'\{"[^"]+":\s*\[.+\]\}', search_data)
                            if json_match:
                                json_str = json_match.group(0)
                                parsed_data = json.loads(json_str)
                                search_data = parsed_data
                            else:
                                # Try to fix single quotes to double quotes
                                import ast
                                try:
                                    # Use ast.literal_eval to safely evaluate the string as a Python literal
                                    python_obj = ast.literal_eval(search_data)
                                    # Convert to proper JSON
                                    search_data = python_obj
                                except Exception:
                                    pass
                        except Exception:
                            pass
                
                try:
                    # Process the search results to generate a final answer
                    final_answer = process_search_results(request.message, search_data, llm)
                    
                    # Ensure final_answer is a dictionary with answer and sources
                    if isinstance(final_answer, dict):
                        if "answer" not in final_answer:
                            final_answer["answer"] = "No answer was generated from the search results."
                        if "sources" not in final_answer:
                            final_answer["sources"] = []
                    else:
                        # If final_answer is not a dictionary, convert it to one
                        final_answer = {
                            "answer": str(final_answer),
                            "sources": []
                        }
                    
                    # Add the final answer to the response
                    response["final_answer"] = final_answer
                except Exception as e:
                    # Add error information to the response
                    response["final_answer"] = {"answer": f"Error processing search results: {str(e)}", "sources": []}
            else:
                response["final_answer"] = {"answer": "No search results were found for your query.", "sources": []}
        
        # If it's a Pokemon query, research the Pokemon
        if supervisor_result.get("is_pokemon_query", False):
            pokemon_names = supervisor_result.get("pokemon_names", [])
            
            # Research each Pokemon
            pokemon_research = {}
            for pokemon_name in pokemon_names[:2]:  # Limit to 2 Pokemon
                research_result = research_pokemon(pokemon_name, llm)
                
                # Create the simplified Pokemon data structure
                simplified_result = {
                    "name": research_result.get("name", "").lower(),
                    "pokemon_details": research_result.get("pokemon_details", []),
                    "base_stats": research_result.get("base_stats", {}),
                    "types": [t.lower() for t in research_result.get("types", [])],
                    "abilities": [a.lower() for a in research_result.get("abilities", [])],
                    "height": research_result.get("height", 0),
                    "weight": research_result.get("weight", 0)
                }
                
                pokemon_research[pokemon_name.capitalize()] = simplified_result
            
            # If there are exactly 2 Pokemon, analyze a potential battle
            if len(pokemon_names) == 2:
                battle_analysis = analyze_pokemon_battle(pokemon_research, llm)
                response["battle_analysis"] = battle_analysis
            
            # If there are Pokemon results, return only the Pokemon research data
            if pokemon_research:
                # For battle queries, include the battle analysis in the response
                if response["battle_analysis"]:
                    pokemon_research["battle_analysis"] = response["battle_analysis"]
                return pokemon_research
        
        # Only return the simplified Pokemon data if it's a Pokemon query
        # Otherwise, return the standard response
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}"
        )

@router.get("/battle", response_model=BattleResponse, status_code=status.HTTP_200_OK)
async def battle(
    pokemon1: Annotated[str, Query(
        ..., 
        description="Name of the first Pokemon", 
        min_length=2,
        max_length=50
    )],
    pokemon2: Annotated[str, Query(
        ..., 
        description="Name of the second Pokemon", 
        min_length=2,
        max_length=50
    )],
    llm: ChatOpenAI = Depends(get_llm)
):
    """
    Analyze a battle between two Pokemon.
    
    This endpoint researches both Pokemon and analyzes a potential battle between them.
    It provides detailed information about both Pokemon, including their stats, types, and abilities,
    along with an analysis of which Pokemon would likely win in a battle based on these attributes.
    
    Args:
        pokemon1: Name of the first Pokemon (case-insensitive)
        pokemon2: Name of the second Pokemon (case-insensitive)
        
    Returns:
        BattleResponse containing:
        - Research results for both Pokemon
        - Battle analysis with reasoning and predicted winner
        - Error message if something went wrong
        

    """
    try:
        # Research both Pokemon
        pokemon1_research = research_pokemon(pokemon1, llm)
        pokemon2_research = research_pokemon(pokemon2, llm)
        
        # Check for errors
        if "error" in pokemon1_research:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=pokemon1_research["error"]
            )
        
        if "error" in pokemon2_research:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=pokemon2_research["error"]
            )
        
        # Analyze the battle
        pokemon_research = {
            pokemon1: pokemon1_research,
            pokemon2: pokemon2_research
        }
        
        battle_analysis = analyze_pokemon_battle(pokemon_research, llm)
        
        # Return the response
        return {
            "pokemon1": pokemon1_research,
            "pokemon2": pokemon2_research,
            "battle_analysis": battle_analysis
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while analyzing the battle: {str(e)}"
        )
