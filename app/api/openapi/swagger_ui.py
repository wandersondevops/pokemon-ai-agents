"""
Swagger UI customization for the FastAPI application.

This module contains the custom Swagger UI HTML template for the API documentation.
"""

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse

def get_custom_swagger_ui_html(app: FastAPI) -> HTMLResponse:
    """
    Generate a custom Swagger UI HTML response.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        HTMLResponse: Custom Swagger UI HTML response
    """
    # Get the default Swagger UI HTML response
    swagger_ui = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Interactive API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        init_oauth=None,
        swagger_ui_parameters={
            "docExpansion": "list",  # Show operations as expanded by default
            "defaultModelsExpandDepth": 3,  # Expand models to show all properties
            "defaultModelExpandDepth": 3,  # Expand nested models
            "tryItOutEnabled": True,  # Enable Try it out by default
            "persistAuthorization": True,  # Remember auth between page refreshes
            "filter": True,  # Enable filtering operations
            "displayRequestDuration": True,  # Show request duration
            "showExtensions": True,  # Show vendor extensions
            "showCommonExtensions": True,  # Show common extensions
        }
    )
    
    # Add custom CSS to the HTML content
    pokemon_css = """
    <style>
        /* Pokemon-themed color scheme */
        :root {
            --pokemon-red: #EE1515;
            --pokemon-blue: #3B4CCA;
            --pokemon-yellow: #FFDE00;
            --pokemon-light-blue: #7FCCEC;
            --pokemon-light-yellow: #FFF4B2;
            --pokemon-light-red: #FFACAC;
            --pokemon-gray: #424242;
            --pokemon-light-gray: #F5F5F5;
        }
        
        /* Main layout and typography */
        body {
            font-family: 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .swagger-ui .topbar { 
            background-color: var(--pokemon-red);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .swagger-ui .info .title {
            color: var(--pokemon-blue);
            font-size: 36px;
            font-weight: 700;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        .swagger-ui .info {
            margin: 30px 0;
            padding: 20px;
            background-color: var(--pokemon-light-gray);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .swagger-ui .info p {
            font-size: 16px;
            line-height: 1.6;
            color: var(--pokemon-gray);
        }
        
        /* Operation blocks styling */
        .swagger-ui .opblock {
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        
        .swagger-ui .opblock:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        .swagger-ui .opblock.opblock-post {
            border-color: var(--pokemon-blue);
            background: rgba(59, 76, 202, 0.05);
        }
        
        .swagger-ui .opblock.opblock-get {
            border-color: var(--pokemon-yellow);
            background: rgba(255, 222, 0, 0.05);
        }
        
        /* Buttons */
        .swagger-ui .btn {
            border-radius: 20px;
            transition: all 0.2s ease;
        }
        
        .swagger-ui .btn.execute {
            background-color: var(--pokemon-red);
            color: white;
            border-color: var(--pokemon-red);
            font-weight: bold;
            font-size: 14px;
            padding: 10px 25px;
            box-shadow: 0 2px 5px rgba(238, 21, 21, 0.3);
        }
        
        .swagger-ui .btn.execute:hover {
            background-color: #d10000;
            border-color: #d10000;
            box-shadow: 0 4px 8px rgba(238, 21, 21, 0.4);
            transform: translateY(-1px);
        }
        
        .swagger-ui .btn.try-out__btn {
            background-color: var(--pokemon-blue);
            color: white;
            border-color: var(--pokemon-blue);
        }
        
        .swagger-ui .btn.try-out__btn:hover {
            background-color: #2a3aa9;
            border-color: #2a3aa9;
        }
        
        /* Tables and parameters */
        .swagger-ui table {
            box-shadow: 0 1px 5px rgba(0,0,0,0.05);
            border-radius: 5px;
            overflow: hidden;
        }
        
        .swagger-ui table tbody tr td {
            padding: 15px 10px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .swagger-ui table thead tr th {
            background-color: var(--pokemon-light-gray);
            padding: 12px 10px;
            font-weight: 600;
        }
        
        .swagger-ui .parameter__name {
            font-weight: bold;
            font-size: 14px;
            color: var(--pokemon-blue);
        }
        
        .swagger-ui .parameter__in {
            font-size: 12px;
            font-style: italic;
            color: #777;
        }
        
        /* Examples section */
        .swagger-ui select {
            border-radius: 4px;
            border: 1px solid #ddd;
            padding: 8px 10px;
            background-color: white;
        }
        
        /* Response section */
        .swagger-ui .responses-wrapper {
            background-color: var(--pokemon-light-gray);
            border-radius: 5px;
            padding: 5px;
            margin-top: 15px;
        }
        
        .swagger-ui .response-col_status {
            font-weight: bold;
            color: var(--pokemon-blue);
        }
        
        .swagger-ui .response-col_status .response-undocumented {
            font-weight: normal;
            color: #777;
        }
        
        .swagger-ui .responses-inner h4 {
            font-size: 16px;
            margin: 15px 0;
            color: var(--pokemon-gray);
        }
        
        /* Tabs */
        .swagger-ui .tab {
            padding: 0;
        }
        
        .swagger-ui .tab li {
            font-size: 14px;
            padding: 10px 15px;
        }
        
        .swagger-ui .tab li.active {
            background-color: var(--pokemon-light-blue);
        }
        
        /* Models section */
        .swagger-ui section.models {
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 30px 0;
        }
        
        .swagger-ui section.models h4 {
            font-size: 18px;
            color: var(--pokemon-blue);
        }
        
        /* Help section */
        .swagger-help {
            background-color: var(--pokemon-light-yellow);
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
            border-left: 5px solid var(--pokemon-yellow);
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .swagger-help h3 {
            margin-top: 0;
            color: var(--pokemon-red);
            font-size: 22px;
            font-weight: 600;
        }
        
        .swagger-help ol {
            padding-left: 25px;
        }
        
        .swagger-help li {
            margin-bottom: 12px;
            line-height: 1.5;
        }
        
        .swagger-help strong {
            color: var(--pokemon-blue);
        }
        
        .swagger-help .tip {
            background-color: white;
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 3px solid var(--pokemon-red);
            margin-top: 15px;
            font-weight: 500;
        }
        
        /* Pokemon logo */
        .pokemon-logo {
            text-align: center;
            margin: 20px 0;
        }
        
        .pokemon-logo img {
            max-width: 250px;
            height: auto;
        }
    </style>
    <div class="pokemon-logo">
        <img src="https://upload.wikimedia.org/wikipedia/commons/9/98/International_Pok%C3%A9mon_logo.svg" alt="Pokemon Logo">
    </div>
    <div class="swagger-help">
        <h3>How to Test the Pokemon AI API</h3>
        <ol>
            <li>Expand an endpoint by clicking on it (either <strong>POST /chat</strong> or <strong>GET /battle</strong>)</li>
            <li>Click the <strong>"Try it out"</strong> button to enable interactive testing</li>
            <li>For the <strong>chat</strong> endpoint, enter your message in the request body</li>
            <li>For the <strong>battle</strong> endpoint, enter two Pokemon names as query parameters</li>
            <li>Click <strong>"Execute"</strong> to send the request to the API</li>
            <li>View the detailed response below, including Pokemon research and battle analysis</li>
        </ol>
        <div class="tip">
            <strong>Tip:</strong> Try different Pokemon combinations to see detailed battle analysis results!
        </div>
    </div>
    """
    
    # Get the HTML content from the response
    html_content = swagger_ui.body.decode("utf-8")
    
    # Insert the custom CSS and HTML before the closing </body> tag
    html_content = html_content.replace("</body>", f"{pokemon_css}</body>")
    
    # Create a new response with the modified HTML content
    return HTMLResponse(content=html_content)

def get_custom_redoc_html(app: FastAPI) -> HTMLResponse:
    """
    Generate a custom ReDoc HTML response.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        HTMLResponse: Custom ReDoc HTML response
    """
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        with_google_fonts=True
    )
