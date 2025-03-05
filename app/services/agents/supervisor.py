"""
Supervisor agent service.

This module contains functions for processing user queries using the supervisor agent.
"""

from typing import Dict, Any, List, Optional
import re
import json

from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.messages import HumanMessage, SystemMessage
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
    if result and len(result) > 0:
        # If it's a Pokemon query and pokemon_names is not set but is_pokemon_query is True, extract names
        if result[0].is_pokemon_query and not result[0].pokemon_names:
            pokemon_names = extract_pokemon_names(query)
            result[0].pokemon_names = pokemon_names[:2]  # Limit to 2 names
            
        # Remove search_queries from the result to provide a cleaner output
        # We'll still use the original query for search in execute_tools
        if hasattr(result[0], 'search_queries') and result[0].search_queries:
            # Store that search is needed but don't include the queries in the output
            result[0].needs_search = True
            result[0].search_queries = None
    
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


def process_search_results(query: str, search_results: Any, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Process search results and generate a final answer.
    
    Args:
        query (str): The original user query
        search_results (Any): The search results from Tavily (can be Dict or str)
        llm (ChatOpenAI): The language model to use
        
    Returns:
        Dict[str, Any]: The final answer and sources based on the search results
    """
    # Check if search_results is None or empty
    if not search_results:
        return {
            "answer": "No search results were found for your query. Please try a different question or provide more details.",
            "sources": []
        }
    
    # If search_results is a string, try to parse it as JSON
    if isinstance(search_results, str):
        try:
            # First try standard JSON parsing
            try:
                search_results = json.loads(search_results)
            except json.JSONDecodeError:
                # Try to fix single quotes in the JSON string
                import ast
                try:
                    # Use ast.literal_eval to safely evaluate the string as a Python literal
                    search_results = ast.literal_eval(search_results)
                except Exception:
                    # Try a more aggressive approach - replace single quotes with double quotes
                    # but only for the keys and string values
                    import re
                    try:
                        # Fix the query key first
                        fixed_json = re.sub(r"\{\s*'([^']+)'\s*:", '{"\\1":', search_results)
                        # Fix the url and content keys
                        fixed_json = re.sub(r"'url'\s*:", '"url":', fixed_json)
                        fixed_json = re.sub(r"'content'\s*:", '"content":', fixed_json)
                        search_results = json.loads(fixed_json)
                    except Exception:
                        return {
                            "answer": "There was an error processing the search results for your query.",
                            "sources": []
                        }
        except Exception:
            return {
                "answer": "There was an error processing the search results for your query.",
                "sources": []
            }
    
    # Format the search results for the LLM
    formatted_results = []
    sources = []
    
    # Extract the search results
    # The search_results structure is a dict where the key is the query and the value is the search results
    try:
        for query_key, results in search_results.items():
            # Results is a list of search result items
            if isinstance(results, list):
                for item in results:
                    if isinstance(item, dict):
                        # Extract title from URL if not present
                        title = item.get('title', None)
                        if not title and 'url' in item:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(item['url'])
                            title = parsed_url.netloc
                        
                        content = item.get('content', 'No content')
                        url = item.get('url', 'No URL')
                        
                        # Try to clean up content if it's a JSON string
                        if isinstance(content, str) and content.startswith('{') and content.endswith('}'):
                            try:
                                # First try standard JSON parsing
                                try:
                                    content_json = json.loads(content)
                                except json.JSONDecodeError:
                                    # If that fails, try to handle single quotes
                                    import ast
                                    try:
                                        content_json = ast.literal_eval(content)
                                    except Exception:
                                        # Try a more aggressive approach with regex
                                        import re
                                        try:
                                            # Replace single quotes with double quotes for keys
                                            fixed_content = re.sub(r"'([^']+)'\s*:", '"\\1":', content)
                                            content_json = json.loads(fixed_content)
                                        except Exception:
                                            content_json = None
                                
                                if isinstance(content_json, dict):
                                    # Format JSON content more readably
                                    if 'location' in content_json and 'current' in content_json:
                                        location = content_json.get('location', {})
                                        current = content_json.get('current', {})
                                        condition = current.get('condition', {})
                                        content = f"Location: {location.get('name', 'Unknown')}, {location.get('country', 'Unknown')}\n"
                                        content += f"Temperature: {current.get('temp_c', 'Unknown')}°C / {current.get('temp_f', 'Unknown')}°F\n"
                                        content += f"Condition: {condition.get('text', 'Unknown')}\n"
                                        content += f"Wind: {current.get('wind_kph', 'Unknown')} km/h {current.get('wind_dir', '')}\n"
                                        content += f"Humidity: {current.get('humidity', 'Unknown')}%\n"
                                        content += f"Last Updated: {current.get('last_updated', 'Unknown')}\n"
                            except Exception:
                                # Keep original content if parsing fails
                                pass
                        
                        formatted_results.append(f"Source: {title or 'No title'}\nURL: {url}\nContent: {content}\n")
                        sources.append({
                            "title": title or 'No title',
                            "url": url,
                            "snippet": content[:200] + "..." if len(content) > 200 else content
                        })
    except Exception:
        return {
            "answer": "There was an error processing the search results for your query.",
            "sources": []
        }
    
    # If no results were found, return a message indicating this
    if not formatted_results:
        return {
            "answer": "I couldn't find any relevant information about your query. Please try a different question or provide more details.",
            "sources": []
        }
    
    # Create a system message with instructions and search results
    system_message = SystemMessage(
        content=f"""You are an AI assistant that provides accurate and helpful responses based on search results.
        
        The user asked: "{query}"
        
        Here are the search results:
        
        {' '.join(formatted_results[:5])}
        
        Based on these search results, provide a comprehensive and accurate answer to the user's question.
        Include specific details from the search results such as numbers, dates, and facts.
        If the search results don't contain enough information to answer the question, acknowledge this limitation.
        Format your response in a clear, well-structured way.
        """
    )
    
    # Create a human message asking for the answer
    human_message = HumanMessage(
        content=f"Please provide a comprehensive answer to my question: {query}"
    )
    
    # Get the response from the LLM
    response = llm.invoke([system_message, human_message])
    
    # Return a dictionary with the answer and sources
    return {
        "answer": response.content,
        "sources": sources
    }
