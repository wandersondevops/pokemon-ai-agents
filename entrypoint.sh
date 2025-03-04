#!/bin/bash
set -e

# Default to API service if not specified
SERVICE=${SERVICE:-api}

# Run the specified service
if [ "$SERVICE" = "api" ]; then
    echo "Starting Pokemon AI Agents API..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
elif [ "$SERVICE" = "streamlit" ]; then
    echo "Starting Pokemon AI Agents Streamlit Frontend..."
    exec streamlit run app/frontend/streamlit/app.py --server.port 8501 --server.address 0.0.0.0
else
    echo "Unknown service: $SERVICE"
    echo "Valid options are: api, streamlit"
    exit 1
fi
