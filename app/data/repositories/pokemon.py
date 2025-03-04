"""
Pokemon repository for fetching Pokemon data from external APIs.

This module contains functions for fetching Pokemon data from the PokeAPI.
"""

from typing import Dict, Any
import requests

from app.core.config import settings

def fetch_pokemon_data(pokemon_name: str) -> Dict[str, Any]:
    """
    Fetch Pokemon data from the PokeAPI.
    
    Args:
        pokemon_name (str): The name of the Pokemon to fetch data for
        
    Returns:
        Dict[str, Any]: A dictionary containing the Pokemon data
    """
    try:
        # Convert pokemon name to lowercase for API compatibility
        pokemon_name = pokemon_name.lower().strip()
        
        # Make the API request
        response = requests.get(f"{settings.POKEMON_API_BASE_URL}/{pokemon_name}")
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the JSON response
        pokemon_data = response.json()
        
        # Extract relevant information
        processed_data = {
            "name": pokemon_data["name"],
            "base_stats": {
                "hp": pokemon_data["stats"][0]["base_stat"],
                "attack": pokemon_data["stats"][1]["base_stat"],
                "defense": pokemon_data["stats"][2]["base_stat"],
                "special_attack": pokemon_data["stats"][3]["base_stat"],
                "special_defense": pokemon_data["stats"][4]["base_stat"],
                "speed": pokemon_data["stats"][5]["base_stat"]
            },
            "types": [t["type"]["name"] for t in pokemon_data["types"]],
            "abilities": [a["ability"]["name"] for a in pokemon_data["abilities"]],
            "height": pokemon_data["height"] / 10,  # Convert to meters
            "weight": pokemon_data["weight"] / 10,  # Convert to kg
            "sprite_url": pokemon_data["sprites"]["front_default"]
        }
        
        return processed_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Pokemon data: {e}")
        return {"error": f"Failed to fetch data for {pokemon_name}: {str(e)}"}
    except (KeyError, IndexError) as e:
        print(f"Error processing Pokemon data: {e}")
        return {"error": f"Failed to process data for {pokemon_name}: {str(e)}"}
