"""
Pokemon router for the FastAPI application.

This module contains the routes for the Pokemon-related endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from typing import Dict, Any, List, Annotated, Optional
import json
import datetime

from langchain_openai import ChatOpenAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

from app.core.dependencies import get_llm, get_search_wrapper
from app.api.models.pokemon import ChatRequest, ChatResponse, BattleResponse
from app.services.pokemon.research import research_pokemon, analyze_pokemon_battle
from app.services.agents.supervisor import process_query, process_search_results
from app.utils.helpers.tool_executor import execute_tools
from app.utils.helpers.langsmith_integration import (
    configure_langsmith, 
    create_langsmith_agent, 
    run_with_langsmith,
    add_to_auto_dataset,
    get_recent_runs
)

# Configuration variables
use_langgraph = True

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
        # Configure LangSmith - this is now handled automatically in run_with_langsmith
        
        # Check if we should use the LangGraph implementation
        # use_langgraph is now defined at the module level
        
        if use_langgraph:
            # Create the LangSmith agent
            agent = create_langsmith_agent(llm, search_wrapper)
            
            # Run the agent with LangSmith tracing and automatic dataset creation
            result = run_with_langsmith(
                agent,
                request.message,
                metadata={
                    "source": "api", 
                    "endpoint": "chat",
                    "timestamp": str(datetime.datetime.now()),
                    "client_info": request.client_info if hasattr(request, "client_info") else None
                },
                auto_create_dataset=True  # Automatically add to dataset for future evaluation
            )
            
            # Extract messages, Pokemon research, and battle analysis from the state
            messages = result.get("messages", [])
            pokemon_research_data = result.get("pokemon_research_data", {})
            battle_analysis_result = result.get("battle_analysis_result")
            search_results = result.get("search_results")
            
            # If we have Pokemon research, return it directly
            if pokemon_research_data:
                # For battle queries, include the battle analysis in the response
                if battle_analysis_result:
                    pokemon_research_data["battle_analysis"] = battle_analysis_result
                return pokemon_research_data
            
            # If we have search results, create a final answer
            if search_results:
                final_answer = process_search_results(request.message, search_results, llm)
            else:
                final_answer = None
            
            # Create a supervisor result from the last AI message
            last_ai_message = None
            for message in reversed(messages):
                if hasattr(message, 'type') and message.type == "ai":
                    last_ai_message = message
                    break
            
            supervisor_result = {
                "answer": last_ai_message.content if last_ai_message else "",
                "reflection": {"reasoning": "Processed using LangGraph"},
                "is_pokemon_query": bool(pokemon_research_data),
                "pokemon_names": list(pokemon_research_data.keys()) if pokemon_research_data else None,
                "needs_search": bool(search_results)
            }
        else:
            # Process the query using the original supervisor agent
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
            
            # If two Pokemon are mentioned, analyze the battle
            if len(pokemon_research) == 2:
                battle_analysis = analyze_pokemon_battle(pokemon_research, llm)
                response["battle_analysis"] = battle_analysis
            else:
                response["battle_analysis"] = None
            
            # If there are Pokemon results, return only the Pokemon research data
            if pokemon_research:
                # For battle queries, include the battle analysis in the response
                if response.get("battle_analysis"):
                    # Add the battle analysis as a top-level key in the response
                    return {**pokemon_research, "battle_analysis": response["battle_analysis"]}
                return pokemon_research
        
        # Only return the simplified Pokemon data if it's a Pokemon query
        # Otherwise, return the standard response
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}"
        )

@router.get("/analytics/runs", status_code=status.HTTP_200_OK)
async def get_langsmith_runs(
    limit: int = Query(10, description="Number of runs to retrieve", ge=1, le=100),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint (chat, battle, etc.)"),
    pokemon_name: Optional[str] = Query(None, description="Filter by Pokemon name")
):
    """
    Get recent LangSmith runs for analytics purposes.
    
    This endpoint retrieves recent runs from LangSmith with optional filtering
    by endpoint or Pokemon name. It provides valuable insights into how the
    system is being used and performing.
    
    Args:
        limit: Number of runs to retrieve (default: 10, max: 100)
        endpoint: Optional filter by endpoint (chat, battle)
        pokemon_name: Optional filter by Pokemon name
        
    Returns:
        List of recent LangSmith runs with metadata
    """
    try:
        # Build filter criteria
        filter_criteria = {}
        if endpoint:
            filter_criteria["endpoint"] = endpoint
        if pokemon_name:
            # Check both pokemon1 and pokemon2 fields
            filter_criteria["pokemon_name"] = pokemon_name
            
        # Get recent runs with filtering
        runs = get_recent_runs(limit=limit, filter_criteria=filter_criteria)
        
        # Return the runs
        return {
            "runs": runs,
            "count": len(runs),
            "filters_applied": {
                "limit": limit,
                "endpoint": endpoint,
                "pokemon_name": pokemon_name
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving LangSmith runs: {str(e)}"
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
    llm: ChatOpenAI = Depends(get_llm),
    search_wrapper: TavilySearchAPIWrapper = Depends(get_search_wrapper)
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
        # Try to use LangGraph with LangSmith tracing first
        try:
            # Create a battle query
            battle_query = f"Compare {pokemon1} and {pokemon2} in a Pokemon battle. Who would win and why?"
            
            # Create the LangSmith agent
            agent = create_langsmith_agent(llm, search_wrapper)
            
            # Run the agent with LangSmith tracing
            result = run_with_langsmith(
                agent,
                battle_query,
                metadata={
                    "source": "api", 
                    "endpoint": "battle",
                    "pokemon1": pokemon1,
                    "pokemon2": pokemon2,
                    "timestamp": str(datetime.datetime.now())
                },
                auto_create_dataset=True  # Automatically add to dataset for future evaluation
            )
            
            # If we have battle analysis in the result, return it
            if result and "battle_analysis" in result:
                return result
                
            # If LangGraph worked but didn't produce battle analysis, fall back to traditional approach
        except Exception as e:
            # Log the error but continue with the traditional approach
            import logging
            logging.error(f"Error using LangGraph for battle analysis: {e}")
        
        # Traditional approach as fallback
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
