"""
General router for the FastAPI application.

This module contains general routes for the application, such as the root endpoint.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from pathlib import Path
import os

# Create router
router = APIRouter(
    tags=["General"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """
    Root endpoint to serve the HTML page.
    
    Returns:
        HTMLResponse: The HTML content for the root page
    """
    try:
        static_dir = Path(__file__).parent.parent.parent.parent / "static"
        os.makedirs(static_dir, exist_ok=True)  # Create the directory if it doesn't exist
        
        # Check if index.html exists, if not create a simple one
        index_path = static_dir / "index.html"
        if not index_path.exists():
            with open(index_path, "w") as f:
                f.write("""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Pokemon AI Agents API</title>
                    <style>
                        body {
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 800px;
                            margin: 0 auto;
                            padding: 20px;
                        }
                        h1 {
                            color: #e91e63;
                            border-bottom: 2px solid #e91e63;
                            padding-bottom: 10px;
                        }
                        h2 {
                            color: #0277bd;
                            margin-top: 30px;
                        }
                        code {
                            background-color: #f5f5f5;
                            padding: 2px 5px;
                            border-radius: 3px;
                            font-family: 'Courier New', Courier, monospace;
                        }
                        pre {
                            background-color: #f5f5f5;
                            padding: 15px;
                            border-radius: 5px;
                            overflow-x: auto;
                        }
                        .endpoint {
                            background-color: #e3f2fd;
                            padding: 15px;
                            border-radius: 5px;
                            margin-bottom: 20px;
                            border-left: 5px solid #0277bd;
                        }
                        .method {
                            font-weight: bold;
                            color: #0277bd;
                        }
                    </style>
                </head>
                <body>
                    <h1>Pokemon AI Agents API</h1>
                    <p>Welcome to the Pokemon AI Agents API. This API provides endpoints to interact with the Pokemon AI Agents system.</p>
                    
                    <h2>API Documentation</h2>
                    <p>For detailed API documentation, please visit the <a href="/docs">Swagger UI</a>.</p>
                    
                    <h2>Available Endpoints</h2>
                    
                    <div class="endpoint">
                        <p><span class="method">POST</span> <code>/api/v1/pokemon/chat</code></p>
                        <p>Process a chat message using the supervisor agent. This endpoint handles general queries as well as Pokémon-specific queries.</p>
                        <p>Example request:</p>
                        <pre>
                {
                    "message": "Your message here"
                }
                        </pre>
                    </div>
                    
                    <div class="endpoint">
                        <p><span class="method">GET</span> <code>/api/v1/pokemon/battle?pokemon1=pokemon_name_1&pokemon2=pokemon_name_2</code></p>
                        <p>Analyze a battle between two Pokemon. This endpoint researches both Pokemon and analyzes a potential battle between them.</p>
                    </div>
                    
                    <h2>GitHub Repository</h2>
                    <p>The source code for this API is available on <a href="https://github.com/yourusername/pokemon-ai-agents">GitHub</a>.</p>
                </body>
                </html>
                """)
        
        with open(index_path) as f:
            return f.read()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while serving the root page: {str(e)}"
        )
