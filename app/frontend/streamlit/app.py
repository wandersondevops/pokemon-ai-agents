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

# Chat Tab
with tab1:
    st.header("Chat with Pokemon AI")
    user_message = st.text_input("Ask something about Pokemon:", placeholder="e.g., Tell me about Pikachu")
    if st.button("Send"):
        if user_message:
            with st.spinner("Thinking..."):
                result = call_chat_api(user_message)
                if result:
                    st.json(result)
        else:
            st.warning("Please enter a message.")

# Battle Analysis Tab
with tab2:
    st.header("Pokemon Battle Analysis")
    col1, col2 = st.columns(2)
    with col1:
        pokemon1 = st.text_input("First Pokemon:", placeholder="e.g., Pikachu")
    with col2:
        pokemon2 = st.text_input("Second Pokemon:", placeholder="e.g., Charizard")
    if st.button("Analyze Battle"):
        if pokemon1 and pokemon2:
            with st.spinner("Analyzing battle..."):
                result = call_battle_api(pokemon1, pokemon2)
                if result:
                    st.json(result)
        else:
            st.warning("Please enter both Pokemon names.")

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
