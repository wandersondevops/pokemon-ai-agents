"""
Streamlit frontend for the Pokemon AI Agents API.
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, Optional

# API URL (use environment variables with fallback to localhost)
import os
import sys

# Internal API URL for service-to-service communication
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8088")
API_URL = f"http://{API_HOST}:{API_PORT}"
API_PREFIX = "/api/v1"

# External API URL for browser access to documentation
# This should always use localhost or the public hostname, not the internal Docker network
EXTERNAL_API_URL = "http://localhost:8088"

# Print connection info to stderr for visibility in Docker logs
print(f"\n\n===> Connecting to API at: {API_URL}{API_PREFIX} <===\n\n", file=sys.stderr)

# Page configuration
st.set_page_config(
    page_title="Pokemon AI Agents",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #e53935;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        text-align: center;
        margin-bottom: 2rem;
    }
    .pokemon-card {
        background-color: #f5f5f5;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .pokemon-name {
        font-size: 1.8rem;
        color: #e53935;
        margin-bottom: 1rem;
    }
    .stat-label {
        font-weight: bold;
        color: #424242;
    }
    .battle-result {
        background-color: #e8f5e9;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }
    .winner {
        font-size: 1.5rem;
        color: #2e7d32;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>Pokemon AI Agents</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Research Pokemon and analyze battles using AI</p>", unsafe_allow_html=True)

# Create tabs including a Swagger tab
tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Battle Analysis", "Debug", "API Docs"])

def format_pokemon_data(pokemon_data: Dict[str, Any]):
    """Format and display Pokemon data in a nice card layout."""
    if not pokemon_data:
        return
    
    # Debug the data structure (commented out for production)
    # st.write("Debug - Pokemon data structure:")
    # st.json(pokemon_data)
    
    # Handle different possible structures
    pokemon = None
    
    # Case 1: Direct pokemon data
    if isinstance(pokemon_data, dict) and 'name' in pokemon_data:
        pokemon = pokemon_data
    
    # Case 2: ResearchPokemon wrapper
    elif isinstance(pokemon_data, dict) and "ResearchPokemon" in pokemon_data:
        pokemon = pokemon_data["ResearchPokemon"]
    
    # Case 3: Pokemon name as key in dictionary
    elif isinstance(pokemon_data, dict) and len(pokemon_data) > 0:
        # Try to find the first key that contains a dictionary with a 'name' field
        for key, value in pokemon_data.items():
            if isinstance(value, dict) and 'name' in value:
                pokemon = value
                break
    
    # If we couldn't extract the pokemon data, show an error
    if not pokemon or not isinstance(pokemon, dict) or 'name' not in pokemon:
        st.warning("Pokemon data is missing required fields")
        st.json(pokemon_data)
        return
    
    # Create a card for the Pokemon
    st.markdown(f"<div class='pokemon-card'>", unsafe_allow_html=True)
    st.markdown(f"<h2 class='pokemon-name'>{pokemon['name'].title()}</h2>", unsafe_allow_html=True)
    
    # Display types
    if pokemon.get('types'):
        types_str = ", ".join([t.title() for t in pokemon['types']])
        st.markdown(f"<p><span class='stat-label'>Types:</span> {types_str}</p>", unsafe_allow_html=True)
    
    # Display base stats
    if pokemon.get('base_stats'):
        st.markdown("<p><span class='stat-label'>Base Stats:</span></p>", unsafe_allow_html=True)
        stats = pokemon['base_stats']
        cols = st.columns(3)
        cols[0].metric("HP", stats.get('hp', 'N/A'))
        cols[1].metric("Attack", stats.get('attack', 'N/A'))
        cols[2].metric("Defense", stats.get('defense', 'N/A'))
        cols = st.columns(3)
        cols[0].metric("Sp. Attack", stats.get('special_attack', 'N/A'))
        cols[1].metric("Sp. Defense", stats.get('special_defense', 'N/A'))
        cols[2].metric("Speed", stats.get('speed', 'N/A'))
    
    # Display abilities
    if pokemon.get('abilities'):
        abilities_str = ", ".join(pokemon['abilities'])
        st.markdown(f"<p><span class='stat-label'>Abilities:</span> {abilities_str}</p>", unsafe_allow_html=True)
    
    # Display height and weight
    if pokemon.get('height') and pokemon.get('weight'):
        st.markdown(f"<p><span class='stat-label'>Height:</span> {pokemon['height']} m | <span class='stat-label'>Weight:</span> {pokemon['weight']} kg</p>", unsafe_allow_html=True)
    
    # Display details
    if pokemon.get('pokemon_details'):
        st.markdown("<p><span class='stat-label'>Details:</span></p>", unsafe_allow_html=True)
        for detail in pokemon['pokemon_details']:
            st.markdown(f"- {detail}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def display_battle_analysis(battle_data: Dict[str, Any]):
    """Display battle analysis results."""
    if not battle_data:
        return
    
    # Debug the battle data structure
    st.write("Debug - Battle data structure:")
    st.json(battle_data)
    
    # Extract the analysis data
    analysis = None
    
    # Case 1: Direct PokemonExpertAnalystAgent data
    if "PokemonExpertAnalystAgent" in battle_data:
        analysis = battle_data["PokemonExpertAnalystAgent"]
    
    # Case 2: Direct analysis data
    elif all(k in battle_data for k in ["pokemon_1", "pokemon_2", "winner"]):
        analysis = battle_data
    
    # Case 3: Nested structure
    elif isinstance(battle_data, dict) and len(battle_data) > 0:
        # Try to find nested analysis data
        for key, value in battle_data.items():
            if isinstance(value, dict) and "PokemonExpertAnalystAgent" in value:
                analysis = value["PokemonExpertAnalystAgent"]
                break
            elif isinstance(value, dict) and all(k in value for k in ["pokemon_1", "pokemon_2", "winner"]):
                analysis = value
                break
    
    if not analysis:
        st.warning("Battle analysis data is missing or in an unexpected format")
        return
    
    st.markdown("<div class='battle-result'>", unsafe_allow_html=True)
    st.markdown("<h3>Battle Analysis</h3>", unsafe_allow_html=True)
    
    st.markdown(f"<p>{analysis['analysis']}</p>", unsafe_allow_html=True)
    st.markdown("<h4>Reasoning</h4>", unsafe_allow_html=True)
    st.markdown(f"<p>{analysis['reasoning']}</p>", unsafe_allow_html=True)
    
    st.markdown(f"<p class='winner'>Winner: {analysis['winner']}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def call_chat_api(message: str):
    """Call the chat API endpoint."""
    try:
        response = requests.post(
            f"{API_URL}{API_PREFIX}/pokemon/chat",
            json={"message": message}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return None

def call_battle_api(pokemon1: str, pokemon2: str):
    """Call the battle API endpoint."""
    try:
        response = requests.get(
            f"{API_URL}{API_PREFIX}/pokemon/battle",
            params={"pokemon1": pokemon1, "pokemon2": pokemon2}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return None

# Chat tab content
with tab1:
    st.header("Chat with Pokemon AI")
    
    # User input
    user_message = st.text_input("Ask a question about Pokemon or anything:", placeholder="e.g., Tell me about Pikachu")
    
    if st.button("Send", key="send_chat"):
        if user_message:
            with st.spinner("Processing your request..."):
                # Call the API
                result = call_chat_api(user_message)
                
                if result:
                    # Check if the result is a direct Pokemon research response (new format)
                    # This happens when the API returns Pokemon data directly instead of wrapped in 'response'
                    if "response" in result and result["response"] is None and isinstance(result, dict):
                        # New format with Pokemon data directly in the result
                        st.markdown("### Pokemon Research")
                        
                        # Remove the 'response' key as it's None
                        pokemon_data = {k: v for k, v in result.items() if k != 'response'}
                        
                        # Display each Pokemon's data
                        for pokemon_name, pokemon_info in pokemon_data.items():
                            st.markdown(f"#### {pokemon_name}")
                            format_pokemon_data(pokemon_info)
                    else:
                        # Original format with wrapped response
                        # Display the supervisor's response if available
                        if "response" in result and isinstance(result["response"], dict) and "supervisor_result" in result["response"]:
                            supervisor = result["response"]["supervisor_result"]
                            st.markdown("### Response")
                            st.write(supervisor["answer"])
                            
                            # Display search queries if available
                            if "search_queries" in supervisor and supervisor["search_queries"]:
                                st.markdown("### Search Queries")
                                for query in supervisor["search_queries"]:
                                    st.markdown(f"- {query}")
                        
                        # Display Pokemon research if available in the original format
                        if "response" in result and isinstance(result["response"], dict) and "pokemon_research" in result["response"]:
                            research = result["response"]["pokemon_research"]
                            
                            # Check if research is not empty
                            if research and (isinstance(research, dict) or isinstance(research, list)):
                                st.markdown("### Pokemon Research")
                                
                                if isinstance(research, dict):
                                    # Single Pokemon research
                                    if research:  # Make sure it's not empty
                                        format_pokemon_data(research)
                                    else:
                                        st.info("No Pokemon research data available.")
                                elif isinstance(research, list):
                                    # Multiple Pokemon research
                                    if research:  # Make sure it's not empty
                                        for pokemon in research:
                                            format_pokemon_data(pokemon)
                                    else:
                                        st.info("No Pokemon research data available.")
                        else:
                            st.info("No Pokemon research data available.")
                    
                    # Battle Analysis has been removed from the chat tab
                    # It is now only available in the dedicated Battle Analysis tab
        else:
            st.warning("Please enter a message.")

# Debug tab content
with tab3:
    st.header("API Connection Debug")
    st.write(f"Attempting to connect to API at: {API_URL}{API_PREFIX}")
    
    if st.button("Test API Connection"):
        try:
            # Try to connect to the API
            response = requests.get(f"{API_URL}/docs")
            st.success(f"Connection successful! Status code: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            st.info("Check the following:")
            st.info("1. Is the API container running?")
            st.info("2. Are the environment variables set correctly?")
            st.info("3. Is the network configured properly?")
    
    # Show environment variables
    st.subheader("Environment Variables")
    env_vars = {
        "API_HOST": os.getenv("API_HOST", "Not set"),
        "API_PORT": os.getenv("API_PORT", "Not set"),
        "STREAMLIT_HOST": os.getenv("STREAMLIT_HOST", "Not set"),
        "STREAMLIT_PORT": os.getenv("STREAMLIT_PORT", "Not set")
    }
    st.json(env_vars)

# Battle tab content
with tab2:
    st.header("Pokemon Battle Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pokemon1 = st.text_input("First Pokemon:", placeholder="e.g., Pikachu")
    
    with col2:
        pokemon2 = st.text_input("Second Pokemon:", placeholder="e.g., Bulbasaur")
    
    if st.button("Analyze Battle", key="analyze_battle"):
        if pokemon1 and pokemon2:
            with st.spinner("Analyzing battle..."):
                # Call the API
                result = call_battle_api(pokemon1, pokemon2)
                
                if result:
                    # Display the Pokemon data
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"### {pokemon1.title()}")
                        format_pokemon_data(result.get("pokemon1", {}))
                    
                    with col2:
                        st.markdown(f"### {pokemon2.title()}")
                        format_pokemon_data(result.get("pokemon2", {}))
                    
                    # Display battle analysis
                    display_battle_analysis(result.get("battle_analysis", {}))
        else:
            st.warning("Please enter both Pokemon names.")

# API Docs tab content
with tab4:
    st.header("API Documentation")
    
    st.markdown("""
    Access the interactive API documentation to explore and test all available endpoints.
    Choose between Swagger UI (interactive) or ReDoc (reference style) documentation.
    """)
    
    col1, col2 = st.columns(2)
    
    # Swagger UI button
    swagger_url = f"{EXTERNAL_API_URL}/docs"
    with col1:
        st.markdown(f"""
        <a href='{swagger_url}' target='_blank'>
            <button style='background-color: #e53935; color: white; border: none; 
            border-radius: 8px; padding: 1rem; font-size: 1.2rem; 
            cursor: pointer; width: 100%; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            📚 Open Swagger UI<br>
            <small style='font-size: 0.8rem;'>Interactive Documentation</small>
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    # ReDoc button
    redoc_url = f"{EXTERNAL_API_URL}/redoc"
    with col2:
        st.markdown(f"""
        <a href='{redoc_url}' target='_blank'>
            <button style='background-color: #3B4CCA; color: white; border: none; 
            border-radius: 8px; padding: 1rem; font-size: 1.2rem; 
            cursor: pointer; width: 100%; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            📖 Open ReDoc<br>
            <small style='font-size: 0.8rem;'>Reference Documentation</small>
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    st.markdown("""    
    ### Available Endpoints
    
    - **Chat Endpoint**: `/api/v1/pokemon/chat` - Ask questions about Pokemon
    - **Battle Endpoint**: `/api/v1/pokemon/battle` - Analyze battles between two Pokemon
    - **Health Check**: `/api/v1/health` - Check API status
    """)
