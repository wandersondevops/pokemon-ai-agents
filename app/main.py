"""
Main FastAPI application.

This module contains the main FastAPI application and its configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from app.core.config import settings
from app.api.routers import general, pokemon
from app.api.openapi.schema import custom_openapi
from app.api.openapi.routes import create_docs_router

# Create the FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for interacting with Pokemon AI Agents",
    version="1.0.0",
    docs_url=None,  # Disable default docs URL
    redoc_url=None,  # Disable default redoc URL
    contact={
        "name": "Pokemon AI Agents Team",
        "url": "https://github.com/yourusername/pokemon-ai-agents",
        "email": "example@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path(__file__).parent.parent / "static"
os.makedirs(static_dir, exist_ok=True)  # Create the directory if it doesn't exist
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(general.router)
app.include_router(pokemon.router, prefix=settings.API_V1_STR)

# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# Include documentation routes
app.include_router(create_docs_router(app))
