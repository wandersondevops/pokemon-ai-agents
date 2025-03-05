"""
Streamlit frontend for the Pokemon AI Agents API with ngrok support.
"""

import streamlit as st
import requests
import os
import sys

# ✅ Move `st.set_page_config()` to the first Streamlit command!
st.set_page_config(
    page_title="Pokemon AI Agents",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better text display
st.markdown("""
<style>
    .stTextArea textarea {
        font-family: monospace;
        font-size: 14px;
        line-height: 1.5;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .snippet-container {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        padding: 10px;
        border-radius: 5px;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# Fetch API URL from environment variables (ngrok-friendly)
API_URL = os.getenv("API_URL", None)
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8088")

# Use ngrok if available, otherwise fall back to local API
if API_URL is None:
    API_URL = f"http://{API_HOST}:{API_PORT}"

API_PREFIX = "/api/v1"

# External API URL for browser access (Swagger, ReDoc, etc.)
EXTERNAL_API_URL = API_URL

# Debugging: Log API connection info
print(f"\n\n===> Connecting to API at: {API_URL}{API_PREFIX} <===\n\n", file=sys.stderr)
st.write(f"🔗 Connecting to API at: {API_URL}{API_PREFIX}")

# Header
st.markdown("<h1 style='text-align: center; color: #e53935;'>Pokemon AI Agents</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Research Pokemon and analyze battles using AI</p>", unsafe_allow_html=True)

# Create UI tabs
tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Battle Analysis", "Debug", "API Docs"])

def call_chat_api(message: str):
    """Call the chat API endpoint."""
    try:
        response = requests.post(f"{API_URL}{API_PREFIX}/pokemon/chat", json={"message": message})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return None

def call_battle_api(pokemon1: str, pokemon2: str):
    """Call the battle API endpoint."""
    try:
        response = requests.get(f"{API_URL}{API_PREFIX}/pokemon/battle", params={"pokemon1": pokemon1, "pokemon2": pokemon2})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return None


def display_formatted_snippet(snippet, key_prefix):
    """Display a formatted snippet with better handling for long text.
    
    Args:
        snippet (str): The text snippet to display
        key_prefix (str): Prefix for the component keys
    """
    # Format the snippet for better readability
    if len(snippet) > 500:
        # For very long snippets, create a tabbed view
        tab1, tab2 = st.tabs(["Formatted View", "Raw Text"])
        
        with tab1:
            # Split into paragraphs for better readability
            paragraphs = snippet.split('\n')
            for i, para in enumerate(paragraphs):
                if para.strip():
                    st.markdown(f"<div style='margin-bottom: 10px;'>{para}</div>", unsafe_allow_html=True)
        
        with tab2:
            st.text_area("", snippet, height=350, key=f"{key_prefix}_raw")
    else:
        # For shorter snippets, just use a text area
        st.text_area("", snippet, height=300, key=f"{key_prefix}_text")
    
    # Add a copy button
    if st.button("Copy Snippet", key=f"{key_prefix}_copy"):
        st.session_state[f"{key_prefix}_copied"] = True
        st.success("Snippet copied to clipboard!")

# Initialize session state variables if not already defined
if 'chat_submitted' not in st.session_state:
    st.session_state.chat_submitted = False

# Function to handle form submission
def submit_chat_form():
    st.session_state.chat_submitted = True

# Chat Tab
with tab1:
    st.header("Chat with Pokemon AI")
    
    # Use a form to capture Enter key press
    with st.form(key="chat_form", clear_on_submit=False):
        user_message = st.text_input("Ask something about Pokemon:", placeholder="e.g., Tell me about Pikachu", key="chat_input")
        submit_button = st.form_submit_button("Send", on_click=submit_chat_form)
    
    # Process the form submission
    if st.session_state.chat_submitted and user_message:
        if user_message:
            with st.spinner("Thinking..."):
                result = call_chat_api(user_message)
                if result:
                    # Display the result in a more readable format
                    if isinstance(result, dict):
                        # Check if there are search results
                        if "sources" in result and result["sources"]:
                            st.subheader("Search Results")
                            for i, source in enumerate(result["sources"]):
                                with st.expander(f"{source.get('title', 'No title')}"):
                                    st.write(f"**URL:** {source.get('url', 'No URL')}")
                                    st.write("**Snippet:**")
                                    # Use our custom function for better snippet display
                                    display_formatted_snippet(source.get('snippet', 'No content'), f"snippet_{i}")
                        
                        # Display the full JSON for debugging
                        with st.expander("View Raw JSON"):
                            st.json(result)
                    else:
                        st.json(result)
                    
                    # Reset the submission state to allow for another submission
                    st.session_state.chat_submitted = False
        else:
            st.warning("Please enter a message.")
            st.session_state.chat_submitted = False

# Initialize battle form submission state
if 'battle_submitted' not in st.session_state:
    st.session_state.battle_submitted = False

# Function to handle battle form submission
def submit_battle_form():
    st.session_state.battle_submitted = True

# Battle Analysis Tab
with tab2:
    st.header("Pokemon Battle Analysis")
    
    # Use a form to capture Enter key press
    with st.form(key="battle_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            pokemon1 = st.text_input("First Pokemon:", placeholder="e.g., Pikachu", key="pokemon1_input")
        with col2:
            pokemon2 = st.text_input("Second Pokemon:", placeholder="e.g., Charizard", key="pokemon2_input")
        submit_button = st.form_submit_button("Analyze Battle", on_click=submit_battle_form)
    
    # Process the form submission
    if st.session_state.battle_submitted and pokemon1 and pokemon2:
        if pokemon1 and pokemon2:
            with st.spinner("Analyzing battle..."):
                result = call_battle_api(pokemon1, pokemon2)
                if result:
                    # Display the result in a more readable format
                    with st.expander("View Battle Analysis", expanded=True):
                        st.json(result)
                    
                    # Reset the submission state to allow for another submission
                    st.session_state.battle_submitted = False
        else:
            st.warning("Please enter both Pokemon names.")
            st.session_state.battle_submitted = False

# Debug Tab
with tab3:
    st.header("API Connection Debug")
    st.write(f"Attempting to connect to API at: {API_URL}{API_PREFIX}")
    if st.button("Test API Connection"):
        try:
            response = requests.get(f"{API_URL}/docs")
            st.success(f"Connection successful! Status code: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            st.info("1. Is the API running?")
            st.info("2. Are environment variables set correctly?")
            st.info("3. Is networking properly configured?")
    st.subheader("Environment Variables")
    st.json({
        "API_URL": API_URL,
        "API_HOST": API_HOST,
        "API_PORT": API_PORT
    })

# API Documentation Tab
with tab4:
    st.header("API Documentation")
    st.markdown(f"""
    - **Chat Endpoint**: `{API_URL}/api/v1/pokemon/chat`
    - **Battle Endpoint**: `{API_URL}/api/v1/pokemon/battle`
    - **Swagger UI**: [Open Swagger Docs]({API_URL}/docs)
    - **ReDoc**: [Open ReDoc Docs]({API_URL}/redoc)
    """)
