"""
LangGraph nodes for the Pokemon AI Agents.

This module contains the node definitions for the LangGraph implementation.
"""

from typing import Dict, Any, List, Annotated, TypedDict, Tuple, Optional
import json

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.data.schemas.pokemon import SupervisorAgent, ResearchPokemon, PokemonExpertAnalystAgent
from app.services.agents.prompts import supervisor_prompt_template, researcher_agent_template, expert_agent_template
from app.utils.helpers.tool_executor import ToolExecutor, execute_tools
from app.data.repositories.pokemon import fetch_pokemon_data
from app.core.config import settings


class State(TypedDict):
    """State for the LangGraph."""
    messages: Annotated[List[BaseMessage], add_messages]
    pokemon_research_data: Dict[str, Any]
    battle_analysis_result: Optional[Dict[str, Any]]
    search_results: Optional[Dict[str, Any]]


def supervisor_node(state: State, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Supervisor node for the LangGraph.
    
    Args:
        state: The current state
        llm: The language model to use
        
    Returns:
        Dict with next node information
    """
    # Get the last human message
    human_message = None
    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            human_message = message
            break
    
    if not human_message:
        return {"next": END}
    
    # Define tools in the format expected by OpenAI
    supervisor_tool = {
        "type": "function",
        "function": {
            "name": "SupervisorAgent",
            "description": "Supervisor agent that processes user queries with precision",
            "parameters": SupervisorAgent.model_json_schema()
        }
    }
    
    # Create the parser
    parser = PydanticToolsParser(tools=[SupervisorAgent])
    
    # Create the chain for the supervisor agent
    chain = (
        supervisor_prompt_template
        | llm.bind(tools=[supervisor_tool], tool_choice={"type": "function", "function": {"name": "SupervisorAgent"}})
        | parser
    )
    
    # Invoke the chain with the message
    result = chain.invoke(input={"messages": [human_message]})
    
    # Process the result
    if result and len(result) > 0:
        supervisor_result = result[0]
        
        # Add the result to the messages
        state["messages"].append(AIMessage(content=json.dumps(supervisor_result.model_dump())))
        
        # Determine the next node
        if supervisor_result.needs_search:
            return {"next": "search"}
        elif supervisor_result.is_pokemon_query:
            return {"next": "pokemon_research_node"}
        else:
            return {"next": END}
    
    return {"next": END}


def search_node(state: State, search_wrapper: TavilySearchAPIWrapper) -> Dict[str, Any]:
    """
    Search node for the LangGraph.
    
    Args:
        state: The current state
        search_wrapper: The search wrapper to use
        
    Returns:
        Dict with next node information
    """
    # Create the tool executor
    tool_executor = ToolExecutor([search_wrapper])
    
    # Execute the search
    search_results = execute_tools(state["messages"], tool_executor)
    
    # Add the search results to the state
    if search_results and len(search_results) > 0:
        state["search_results"] = search_results[0].content
        state["messages"].append(search_results[0])
        return {"next": "final_answer"}
    
    return {"next": END}


def final_answer_node(state: State, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Final answer node for the LangGraph.
    
    Args:
        state: The current state
        llm: The language model to use
        
    Returns:
        Dict with next node information
    """
    # Get the original question
    human_message = None
    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            human_message = message
            break
    
    if not human_message or not state.get("search_results"):
        return {"next": END}
    
    # Create a system message with instructions
    system_message = """
    You are a helpful AI assistant that generates comprehensive answers based on search results.
    
    Given the search results, your task is to:
    1. Extract the most relevant information
    2. Organize it into a coherent, detailed answer
    3. Include specific facts, figures, and data points
    4. Cite sources when providing information
    5. Acknowledge any limitations or gaps in the information
    
    Format your response as a well-structured answer that directly addresses the user's question.
    """
    
    # Create a prompt with the search results
    prompt = f"""
    User Question: {human_message.content}
    
    Search Results:
    {json.dumps(state["search_results"], indent=2)}
    
    Based on these search results, provide a comprehensive answer to the user's question.
    Include relevant facts, figures, and cite sources where appropriate.
    """
    
    # Generate the final answer
    response = llm.invoke([
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ])
    
    # Add the final answer to the messages
    state["messages"].append(AIMessage(content=response.content))
    
    return {"next": END}


def pokemon_research_node(state: State, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Pokemon research node for the LangGraph.
    
    Args:
        state: The current state
        llm: The language model to use
        
    Returns:
        Dict with next node information
    """
    # Extract Pokemon names from the supervisor result
    supervisor_result = None
    for message in state["messages"]:
        if isinstance(message, AIMessage) and hasattr(message, "content"):
            try:
                content = json.loads(message.content)
                if "is_pokemon_query" in content and content["is_pokemon_query"]:
                    supervisor_result = content
                    break
            except:
                continue
    
    if not supervisor_result or "pokemon_names" not in supervisor_result or not supervisor_result["pokemon_names"]:
        return {"next": END}
    
    # Initialize pokemon_research_data if not present
    if "pokemon_research_data" not in state:
        state["pokemon_research_data"] = {}
    
    # Research each Pokemon
    pokemon_names = supervisor_result["pokemon_names"]
    for pokemon_name in pokemon_names[:2]:  # Limit to 2 Pokemon
        # Define tools in the format expected by OpenAI
        researcher_tool = {
            "type": "function",
            "function": {
                "name": "ResearchPokemon",
                "description": "Researcher agent that processes Pokemon data",
                "parameters": ResearchPokemon.model_json_schema()
            }
        }
        
        # Fetch Pokemon data from the API
        pokemon_data = fetch_pokemon_data(pokemon_name)
        
        # If there was an error fetching the data, skip this Pokemon
        if "error" in pokemon_data:
            continue
        
        # Create a system message with the Pokemon data and clear instructions
        system_message = f"""Here is the Pokemon data for {pokemon_name}:
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
        
        # Create a human message asking for analysis
        human_message = f"Please analyze the Pokemon {pokemon_name} based on the provided data and return a comprehensive research report with all relevant details."
        
        # Create the parser
        parser = PydanticToolsParser(tools=[ResearchPokemon])
        
        # Create the chain for the researcher agent
        chain = (
            researcher_agent_template
            | llm.bind(tools=[researcher_tool], tool_choice={"type": "function", "function": {"name": "ResearchPokemon"}})
            | parser
        )
        
        # Invoke the chain with the messages
        result = chain.invoke(input={"messages": [
            {"role": "system", "content": system_message},
            {"role": "human", "content": human_message}
        ]})
        
        # Ensure all data from the API is included in the result
        if result and len(result) > 0:
            # Copy the data directly from the API response to ensure it's included
            result[0].base_stats = pokemon_data["base_stats"]
            result[0].types = pokemon_data["types"]
            result[0].abilities = pokemon_data["abilities"]
            result[0].height = pokemon_data["height"]
            result[0].weight = pokemon_data["weight"]
            
            # Add the research result to the state
            state["pokemon_research_data"][pokemon_name] = result[0].model_dump()
    
    # Add the research results to the messages
    research_message = f"I've researched the following Pokemon: {', '.join(state['pokemon_research_data'].keys())}"
    state["messages"].append(AIMessage(content=research_message))
    
    # If there are exactly 2 Pokemon, proceed to battle analysis
    if len(state["pokemon_research_data"]) == 2:
        return {"next": "battle_analysis"}
    
    return {"next": END}


def battle_analysis_node(state: State, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Battle analysis node for the LangGraph.
    
    Args:
        state: The current state
        llm: The language model to use
        
    Returns:
        Dict with next node information
    """
    # Check if we have exactly 2 Pokemon
    if not state.get("pokemon_research_data") or len(state["pokemon_research_data"]) != 2:
        return {"next": END}
    
    # Format the research results for the expert agent
    formatted_results = {}
    for pokemon_name, research in state["pokemon_research_data"].items():
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
    system_message = f"""
    You are analyzing a battle between {pokemon_1} and {pokemon_2} ONLY.
    
    Here is the data for {pokemon_1}:
    {json.dumps(formatted_results[pokemon_1], indent=2)}
    
    Here is the data for {pokemon_2}:
    {json.dumps(formatted_results[pokemon_2], indent=2)}
    
    Analyze their stats, types, and abilities to determine which one would likely win in a battle.
    Consider type advantages/disadvantages, base stats, and how abilities might affect the outcome.
    
    IMPORTANT: Your analysis must ONLY be about these two specific Pokémon. Do not analyze or mention any other Pokémon.
    """
    
    # Create a human message with a specific battle analysis request
    human_message = f"Analyze a battle between ONLY {pokemon_1} and {pokemon_2} based on their stats, types, and abilities. Which one would likely win in a battle? DO NOT analyze any other Pokémon besides these two."
    
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
    result = chain.invoke(input={"messages": [
        {"role": "system", "content": system_message},
        {"role": "human", "content": human_message}
    ]})
    
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
        
        # Add the battle analysis to the state
        state["battle_analysis_result"] = result[0].model_dump()
        
        # Add the battle analysis to the messages
        battle_message = f"Battle Analysis: {result[0].winner} would likely win against {pokemon_1 if result[0].winner != pokemon_1 else pokemon_2} because {result[0].reasoning}"
        state["messages"].append(AIMessage(content=battle_message))
    
    return {"next": END}


def create_pokemon_agent_graph(llm: ChatOpenAI, search_wrapper: TavilySearchAPIWrapper) -> StateGraph:
    """
    Create the Pokemon agent graph.
    
    Args:
        llm: The language model to use
        search_wrapper: The search wrapper to use
        
    Returns:
        StateGraph: The Pokemon agent graph
    """
    # Create the graph
    graph_builder = StateGraph(State)
    
    # Add nodes
    graph_builder.add_node("supervisor", lambda state: supervisor_node(state, llm))
    graph_builder.add_node("search", lambda state: search_node(state, search_wrapper))
    graph_builder.add_node("final_answer", lambda state: final_answer_node(state, llm))
    graph_builder.add_node("pokemon_research_node", lambda state: pokemon_research_node(state, llm))
    graph_builder.add_node("battle_analysis", lambda state: battle_analysis_node(state, llm))
    
    # Add edges
    graph_builder.add_edge(START, "supervisor")
    graph_builder.add_edge("supervisor", "search")
    graph_builder.add_edge("supervisor", "pokemon_research_node")
    graph_builder.add_edge("search", "final_answer")
    graph_builder.add_edge("pokemon_research_node", "battle_analysis")
    graph_builder.add_edge("pokemon_research_node", END)
    graph_builder.add_edge("battle_analysis", END)
    graph_builder.add_edge("final_answer", END)
    
    # Compile the graph
    return graph_builder.compile()
