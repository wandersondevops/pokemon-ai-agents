"""
OpenAPI schema customization for the FastAPI application.

This module contains the custom OpenAPI schema definition for the API.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import settings

def custom_openapi(app: FastAPI) -> dict:
    """
    Generate a custom OpenAPI schema for the application.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        dict: Custom OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="""## Pokemon AI Agents API

This API provides endpoints to interact with the Pokemon AI Agents system powered by LLMs. 

### Features

- **Chat Endpoint**: Process general queries and Pokemon-related queries using AI
- **Battle Endpoint**: Analyze battles between two Pokemon with detailed statistics and reasoning
- **Health Check**: Verify the API is running correctly

### Technical Details

- Built with FastAPI and LangChain
- Uses OpenAI's GPT models for natural language processing
- Integrates with PokeAPI for accurate Pokemon data
- Implements Tavily Search API for general knowledge queries

### Authentication

No authentication is required to use this API.

### Rate Limiting

Please be mindful of usage as the API uses OpenAI's API which has rate limits and costs associated with it.

### Error Handling

The API returns standard HTTP status codes:
- 200: Success
- 404: Resource not found
- 422: Validation error
- 500: Server error

### Example Usage

```python
import requests
import json

# Chat endpoint
response = requests.post(
    "http://localhost:8088/api/v1/pokemon/chat",
    json={"message": "Your message here"}
)
print(json.dumps(response.json(), indent=2))

# Battle endpoint
response = requests.get(
    "http://localhost:8088/api/v1/pokemon/battle?pokemon1=pokemon_name_1&pokemon2=pokemon_name_2"
)
print(json.dumps(response.json(), indent=2))
```
        """,
        routes=app.routes,
    )
    
    # Add custom tags metadata
    openapi_schema["tags"] = [
        {
            "name": "Pokemon",
            "description": "Endpoints for Pokemon research and battle analysis using AI",
            "externalDocs": {
                "description": "Pokemon API Documentation",
                "url": "https://pokeapi.co/docs/v2"
            }
        },
        {
            "name": "General",
            "description": "General endpoints for the application including health checks and documentation"
        },
    ]
    
    # Add examples to schema
    if "paths" in openapi_schema:
        # Chat endpoint examples
        if f"{settings.API_V1_STR}/pokemon/chat" in openapi_schema["paths"]:
            chat_path = openapi_schema["paths"][f"{settings.API_V1_STR}/pokemon/chat"]
            
            if "post" in chat_path:
                post_op = chat_path["post"]
                
                # Remove all examples from chat endpoint request
                if "requestBody" in post_op and "content" in post_op["requestBody"]:
                    # Remove example field to avoid hardcoded message in schema
                    if "example" in post_op["requestBody"]["content"]["application/json"]:
                        del post_op["requestBody"]["content"]["application/json"]["example"]
                    
                    # Remove examples field to avoid hardcoded Pokemon examples in UI
                    if "examples" in post_op["requestBody"]["content"]["application/json"]:
                        del post_op["requestBody"]["content"]["application/json"]["examples"]
                    
                    # Modify schema to use a generic format
                    if "schema" in post_op["requestBody"]["content"]["application/json"]:
                        post_op["requestBody"]["content"]["application/json"]["schema"] = {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "User's message or query"
                                }
                            },
                            "required": ["message"]
                        }
                
                # Add generic schema for response
                if "responses" in post_op and "200" in post_op["responses"]:
                    post_op["responses"]["200"]["content"] = {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "response": {
                                        "type": "object",
                                        "properties": {
                                            "supervisor_result": {
                                                "type": "object"
                                            },
                                            "pokemon_research": {
                                                "type": "object"
                                            },
                                            "battle_analysis": {
                                                "type": "object",
                                                "nullable": True
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
        
        # Battle endpoint examples
        if f"{settings.API_V1_STR}/pokemon/battle" in openapi_schema["paths"]:
            battle_path = openapi_schema["paths"][f"{settings.API_V1_STR}/pokemon/battle"]
            
            if "get" in battle_path:
                get_op = battle_path["get"]
                
                # Remove all examples from battle endpoint parameters
                if "parameters" in get_op:
                    for param in get_op["parameters"]:
                        # Remove example field to avoid hardcoded Pokemon in schema
                        if "example" in param:
                            del param["example"]
                        
                        # Remove examples field to avoid hardcoded Pokemon examples in UI
                        if "examples" in param:
                            del param["examples"]
                        
                        # Add generic schema property
                        if param["name"] in ["pokemon1", "pokemon2"]:
                            param["schema"] = {"type": "string"}
                
                # Add example responses
                # Remove response examples from battle endpoint
                if "responses" in get_op and "200" in get_op["responses"]:
                    # Remove examples and replace with generic schema
                    if "content" in get_op["responses"]["200"]:
                        get_op["responses"]["200"]["content"] = {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "pokemon1": {
                                            "type": "object",
                                            "description": "First Pokemon details"
                                        },
                                        "pokemon2": {
                                            "type": "object",
                                            "description": "Second Pokemon details"
                                        },
                                        "battle_analysis": {
                                            "type": "object",
                                            "properties": {
                                                "pokemon_1": {"type": "string"},
                                                "pokemon_2": {"type": "string"},
                                                "analysis": {"type": "string"},
                                                "reasoning": {"type": "string"},
                                                "winner": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                
                # Add error responses
                if "responses" in get_op:
                    get_op["responses"]["404"] = {
                        "description": "Pokemon not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "detail": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                    
                    get_op["responses"]["422"] = {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "detail": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "loc": {"type": "array"},
                                                    "msg": {"type": "string"},
                                                    "type": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    get_op["responses"]["500"] = {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "examples": {
                                    "API Limit Exceeded": {
                                        "summary": "External API limit exceeded",
                                        "description": "When an external API rate limit is reached",
                                        "value": {
                                            "detail": "API rate limit exceeded. Please try again later."
                                        }
                                    },
                                    "Battle Analysis Error": {
                                        "summary": "Error during battle analysis",
                                        "description": "When the battle analysis fails",
                                        "value": {
                                            "detail": "An error occurred while analyzing the battle between the specified Pokemon."
                                        }
                                    },
                                    "Research Error": {
                                        "summary": "Error during Pokemon research",
                                        "description": "When Pokemon research fails",
                                        "value": {
                                            "detail": "An error occurred while researching Pokemon information."
                                        }
                                    }
                                }
                            }
                        }
                    }
    
    return openapi_schema
