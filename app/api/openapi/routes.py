"""
Routes for OpenAPI documentation.

This module contains the routes for the OpenAPI documentation endpoints.
"""

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse

from app.api.openapi.swagger_ui import get_custom_swagger_ui_html, get_custom_redoc_html

def create_docs_router(app: FastAPI = None) -> APIRouter:
    """
    Create a router for the OpenAPI documentation endpoints.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        APIRouter: Router for the OpenAPI documentation endpoints
    """
    router = APIRouter(tags=["Documentation"])
    
    # Create closures that capture the app instance
    def get_swagger_ui():
        return get_custom_swagger_ui_html(app)
    
    def get_redoc():
        return get_custom_redoc_html(app)
    
    # Add routes with the closures as handlers
    router.add_api_route("/docs", get_swagger_ui, methods=["GET"], include_in_schema=False)
    router.add_api_route("/redoc", get_redoc, methods=["GET"], include_in_schema=False)
    
    return router
