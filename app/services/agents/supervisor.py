"""
Supervisor agent service.

This module contains functions for processing user queries using the supervisor agent.
"""

from typing import Dict, Any, List, Optional
import re

from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

from app.data.schemas.pokemon import SupervisorAgent
from app.services.agents.prompts import supervisor_prompt_template
from app.utils.helpers.tool_executor import ToolExecutor, execute_tools

def process_query(query: str, llm: ChatOpenAI, search_wrapper: TavilySearchAPIWrapper) -> Dict[str, Any]:
    """
    Process a user query using the supervisor agent.
    
    Args:
        query (str): The user's query
        llm (ChatOpenAI): The language model to use
        search_wrapper (TavilySearchAPIWrapper): The search wrapper to use
        
    Returns:
        Dict[str, Any]: The supervisor agent's response
    """
    # Define tools in the format expected by OpenAI
    supervisor_tool = {
        "type": "function",
        "function": {
            "name": "SupervisorAgent",
            "description": "Supervisor agent that processes user queries with precision",
            "parameters": SupervisorAgent.model_json_schema()
        }
    }
    
    # Create the human message
    human_message = HumanMessage(content=query)
    
    # Create the parser
    parser = PydanticToolsParser(tools=[SupervisorAgent])
    
    # Create the tool executor
    tool_executor = ToolExecutor([search_wrapper])
    
    # Create the chain for the supervisor agent
    chain = (
        supervisor_prompt_template
        | llm.bind(tools=[supervisor_tool], tool_choice={"type": "function", "function": {"name": "SupervisorAgent"}})
        | parser
    )
    
    # Invoke the chain with the message
    result = chain.invoke(input={"messages": [human_message]})
    
    # Extract Pokemon names from the query if it's a Pokemon query
    if result and len(result) > 0 and result[0].is_pokemon_query:
        # If pokemon_names is not set but is_pokemon_query is True, extract names
        if not result[0].pokemon_names:
            pokemon_names = extract_pokemon_names(query)
            result[0].pokemon_names = pokemon_names[:2]  # Limit to 2 names
    
    return result[0].model_dump() if result and len(result) > 0 else {"error": "Failed to process query"}

def extract_pokemon_names(query: str) -> List[str]:
    """
    Extract Pokemon names from a query using regex.
    
    Args:
        query (str): The query to extract Pokemon names from
        
    Returns:
        List[str]: A list of Pokemon names
    """
    # This is a simple implementation and might need to be improved
    # to handle more complex cases
    pokemon_pattern = r'\b([A-Z][a-z]+)\b'
    matches = re.findall(pokemon_pattern, query)
    
    # Filter out common words that might be mistaken for Pokemon names
    common_words = ["The", "And", "But", "For", "With", "About", "What", "Who", "How", "When", "Where", "Why"]
    pokemon_names = [name for name in matches if name not in common_words]
    
    return pokemon_names
