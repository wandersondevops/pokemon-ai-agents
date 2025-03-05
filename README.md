# Pokemon AI Agents

A system of AI agents that can research Pokemon and analyze battles between them.

## Features

- **Supervisor Agent**: Processes user queries and delegates to specialized agents
- **Research Agent**: Researches Pokemon and provides detailed information
- **Expert Agent**: Analyzes battles between Pokemon and predicts winners
- **FastAPI Interface**: Exposes the agents through a REST API
- **Streamlit UI**: User-friendly interface for interacting with the AI agents
- **Docker Support**: Containerized deployment for consistent environments

## Project Structure

The project follows a clean architecture with proper separation of concerns:

```
pokemon-ai-agents/
├── app/                  # Main application code
│   ├── api/              # API layer
│   │   ├── middleware/   # Custom middleware components
│   │   ├── models/       # Pydantic models for API requests/responses
│   │   ├── openapi/      # OpenAPI schema and Swagger UI customization
│   │   └── routers/      # FastAPI route definitions
│   ├── core/             # Core application modules
│   │   ├── config.py     # Configuration settings
│   │   └── dependencies.py # Dependency injection
│   ├── data/             # Data layer
│   │   ├── repositories/ # Data access components
│   │   └── schemas/      # Pydantic schemas for internal data models
│   ├── frontend/         # Frontend applications
│   │   └── streamlit/    # Streamlit UI application
│   ├── services/         # Service layer
│   │   ├── agents/       # AI agent implementations
│   │   └── pokemon/      # Pokemon-specific services
│   └── utils/            # Utility modules
│       └── helpers/      # Helper functions and classes
├── tests/                # Test suite
├── static/               # Static files for the application
├── Dockerfile            # Docker configuration for building the image
├── docker-compose.yml    # Docker Compose configuration for services
├── entrypoint.sh         # Script to determine which service to start
├── Makefile              # Convenient commands for development and deployment
└── requirements.txt      # Python dependencies
```

## Installation

### Local Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys. Here's an example of what it should contain:

```
# API Configuration
API_HOST=0.0.0.0
API_PORT=8088
API_DEBUG=True

# Streamlit Configuration
STREAMLIT_HOST=0.0.0.0
STREAMLIT_PORT=8501

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4o

# Search Configuration
TAVILY_API_KEY=your_tavily_api_key

# LangSmith Configuration (optional)
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY="your_langsmith_api_key"
LANGSMITH_PROJECT="pokemon-ai-agents"
```

## Docker Implementation

The project has been fully Dockerized with a multi-service architecture to provide consistent deployment across different environments.

### Docker Architecture

1. **Single Dockerfile**: A unified Dockerfile that uses an entrypoint script to determine which service to run.

2. **Multi-Service Composition**: Docker Compose configuration that defines and connects multiple services:
   - **API Service**: Runs the FastAPI backend on port 8088
   - **Streamlit Service**: Runs the Streamlit frontend on port 8501

3. **Shared Network**: Both services communicate over an internal Docker network.

4. **Volume Mounts**: Development-friendly configuration with code mounted as volumes for quick iterations.

5. **Environment Configuration**: Flexible environment variable handling for different deployment scenarios.

### Docker Components

- **Dockerfile**: Uses Python 3.11 slim as the base image with optimized layer caching.

- **docker-compose.yml**: Defines services, networks, volumes, and environment variables.

- **entrypoint.sh**: A bash script that determines which service to start based on the SERVICE environment variable.

- **.dockerignore**: Excludes unnecessary files from the Docker build context for faster builds.

### Docker Installation

1. Clone the repository
2. Create a `.env` file with your API keys (as shown above)
3. Build and start the Docker containers:
   ```
   make docker-build
   make docker-up
   ```
4. The services will be available at:
   - API: http://localhost:8088
   - Streamlit UI: http://localhost:8501
5. To stop the containers:
   ```
   make docker-down
   ```
6. To view logs:
   ```
   make docker-logs
   ```

### Docker Configuration Details

#### Environment Variables

The Docker setup supports the following environment variables:

- **SERVICE**: Determines which service to run (api or streamlit)
- **API_HOST**: Host for the API service (default: 0.0.0.0)
- **API_PORT**: Port for the API service (default: 8088)
- **API_DEBUG**: Enable debug mode for the API (default: True)
- **STREAMLIT_HOST**: Host for the Streamlit service (default: 0.0.0.0)
- **STREAMLIT_PORT**: Port for the Streamlit service (default: 8501)
- **OPENAI_API_KEY**: Your OpenAI API key
- **LLM_MODEL**: The language model to use (default: gpt-4o)
- **TAVILY_API_KEY**: Your Tavily search API key
- **LANGSMITH_TRACING**: Enable LangSmith tracing (default: false)

#### Makefile Commands

The Makefile provides convenient commands for Docker operations:

- `make docker-build`: Build Docker images
- `make docker-up`: Start Docker containers
- `make docker-down`: Stop Docker containers
- `make docker-logs`: View Docker logs

## Usage

### Running with Docker

```
make docker-up
```

The API will be available at `http://localhost:8088` and the Streamlit UI at `http://localhost:8501`.

### API Documentation

Once the API is running, you can access the interactive documentation at:
- Swagger UI: `http://localhost:8088/docs`

### API Endpoints

#### POST /api/v1/pokemon/chat

This endpoint exposes the supervisor agent, which can handle general queries and Pokemon-related queries.

Example request:
```json
{
  "message": "Your message here"
}
```

#### GET /api/v1/pokemon/battle

This endpoint analyzes a battle between two Pokemon.

Example request:
```
GET /api/v1/pokemon/battle?pokemon1=pokemon_name_1&pokemon2=pokemon_name_2
```

### Testing the API

You can run the test script to verify that the API endpoints work correctly:

```
python test_api.py
```

## Development

### Adding New Agents

To add a new agent:

1. Define a schema in `app/data/schemas/`
2. Create a prompt template in `app/services/agents/prompts.py`
3. Implement the agent logic in the appropriate service module
4. Add the agent to the API by creating or updating a router

### Modifying Existing Agents

To modify an existing agent:

1. Update the schema in `app/data/schemas/` if needed
2. Modify the prompt template in `app/services/agents/prompts.py`
3. Update the agent logic in the appropriate service module

### Project Architecture

The project follows a clean architecture with proper separation of concerns:

1. **API Layer**: Handles HTTP requests and responses
   - Routers define the endpoints and route handlers
   - Models define the request and response data structures

2. **Service Layer**: Contains the business logic
   - Agent services handle the AI agent interactions
   - Pokemon services handle Pokemon-specific logic

3. **Data Layer**: Handles data access and persistence
   - Repositories handle external API calls
   - Schemas define the internal data structures

4. **Core**: Contains application-wide configurations and dependencies

5. **Utils**: Contains utility functions and helpers

6. **Frontend**: Contains user interface applications
   - Streamlit application for interactive UI

## Testing

### Running Tests

The project uses pytest for testing. To run the tests:

```bash
# Run all tests
python -m pytest

# Run tests with coverage report
python -m pytest --cov=app

# Generate HTML coverage report
python -m pytest --cov=app --cov-report=html
```

### Test Coverage

Current test coverage is at 71% across the project. Key modules with high coverage include:

- **Pokemon Research Service**: 100% coverage
- **Pokemon Models**: 100% coverage
- **Pokemon Repository**: 100% coverage
- **API Routers**: 94-100% coverage

Areas for test coverage improvement:

- **OpenAPI Schema**: 10% coverage
- **Tool Executor**: 17% coverage
- **Supervisor Agent**: 41% coverage

### Test Structure

Tests are organized following the same structure as the application code:

```
tests/
├── unit/                 # Unit tests
│   ├── api/              # API layer tests
│   │   ├── models/       # Model tests
│   │   └── routers/      # Router tests
│   ├── data/             # Data layer tests
│   │   └── repositories/ # Repository tests
│   └── services/         # Service layer tests
│       └── pokemon/      # Pokemon service tests
└── conftest.py          # Common test fixtures
```

### Mocking Strategy

The tests use pytest's patching mechanism to mock external dependencies:

- **LangChain Components**: Mock templates, chains, and LLM responses
- **External APIs**: Mock API responses for PokeAPI and other external services
- **Pydantic Models**: Use actual Pydantic models for type safety in tests

## Innovative Approaches

The Pokemon AI Agents project implements several innovative approaches to ensure accuracy, reliability, and user experience:

### Battle Analysis System

The battle analysis system uses a sophisticated approach to determine the likely winner in a Pokemon battle:

- **Type Advantage Calculation**: Analyzes the complex type relationships between Pokemon
- **Stat Comparison**: Evaluates base stats to determine strengths and weaknesses
- **Ability Consideration**: Takes into account how abilities might affect battle outcomes
- **Speed Prioritization**: Considers which Pokemon would likely attack first based on speed stats

### Name Correction Mechanism

To ensure accuracy in Pokemon analysis, the system implements a robust name correction mechanism:

```python
# Verify that the correct Pokémon were analyzed
if result and len(result) > 0:
    # Check if the Pokémon names in the result match the expected names
    result_pokemon_1 = result[0].pokemon_1.lower()
    result_pokemon_2 = result[0].pokemon_2.lower()
    
    # If the names don't match, correct them
    if result_pokemon_1 != pokemon_1.lower():
        result[0].pokemon_1 = pokemon_1
    if result_pokemon_2 != pokemon_2.lower():
        result[0].pokemon_2 = pokemon_2
```

This ensures that even if the LLM somehow references incorrect Pokemon names, the system will automatically correct them to the intended Pokemon.

### Contextual Research

The research agent adapts its analysis based on the context:

- **Single Pokemon Research**: Provides comprehensive details about a single Pokemon
- **Comparison Mode**: When researching Pokemon for a battle, focuses on battle-relevant attributes
- **Adaptive Prompting**: Modifies the system message based on the research context
- **Contextual Data Enrichment**: Ensures all relevant data is included for the specific use case

### Enhanced Swagger UI

The API documentation features a custom Pokemon-themed Swagger UI:

- **Pokemon Color Scheme**: Custom styling with Pokemon branding
- **Interactive Examples**: Pre-populated examples for popular Pokemon
- **Battle Scenario Testing**: Ready-to-use battle analysis examples
- **Improved Visual Hierarchy**: Better organization of endpoints and models

### Robust Error Handling

The system implements comprehensive error handling throughout:

- **API Error Responses**: Proper HTTP status codes with descriptive messages
- **LLM Fallback Mechanisms**: Graceful handling of LLM failures
- **Data Validation**: Thorough validation of inputs and outputs
- **Pokemon Name Normalization**: Case-insensitive handling of Pokemon names
- **Comprehensive Exception Handling**: Detailed error messages for debugging

### Advanced Pokemon Research Tool

The project features a sophisticated research tool that leverages AI to gather and synthesize Pokemon information:

- **Multi-Source Research**: Combines data from official Pokemon databases, community wikis, and game mechanics resources
- **Contextual Information Retrieval**: Intelligently determines what information is most relevant based on the query context
- **Adaptive Detail Level**: Provides concise summaries for general queries and in-depth analysis for specific questions
- **Cross-Reference Verification**: Cross-checks information across multiple sources to ensure accuracy
- **Semantic Understanding**: Goes beyond keyword matching to understand the intent behind research queries
- **Memory System**: Remembers previously researched Pokemon to provide faster responses and comparative insights
- **Structured Data Extraction**: Converts unstructured text into structured data for consistent formatting
- **Evolution Chain Analysis**: Tracks complete evolution paths and compares stats across evolutionary stages
- **Move Set Optimization**: Analyzes optimal move combinations based on Pokemon types and stats

The research tool is implemented using a combination of vector databases, semantic search, and LLM-powered information extraction to provide comprehensive and accurate Pokemon information.

### Interactive Streamlit Frontend

The project includes a user-friendly Streamlit frontend that makes the Pokemon AI Agents accessible to users of all technical levels:

- **Intuitive Chat Interface**: Simple chat-like interface for interacting with the Pokemon agents
- **Real-time Pokemon Research**: Instantly view detailed Pokemon information with visualized stats
- **Interactive Battle Analysis**: Compare any two Pokemon with detailed battle outcome predictions
- **Visual Stat Comparisons**: Radar charts and bar graphs for comparing Pokemon stats
- **Pokemon Card Display**: Beautiful Pokemon card-style display of research results
- **Responsive Design**: Works on desktop and mobile devices
- **Debug Mode**: Optional debug panel for viewing the raw API responses

The Streamlit frontend communicates with the FastAPI backend via HTTP requests, providing a seamless user experience while maintaining a clean separation of concerns in the architecture.

## API Documentation

The API is fully documented using Swagger UI and ReDoc, providing comprehensive and interactive documentation for all endpoints.

### Enhanced Swagger UI

Access the Swagger UI documentation at `/docs` endpoint when the API is running. Our enhanced Pokémon-themed Swagger UI provides an interactive interface with the following features:

- **Interactive Testing**: Test API calls directly from the browser with a user-friendly interface
- **Pokémon-Themed Design**: Custom styling with Pokémon color scheme and branding
- **Rich Examples**: Comprehensive examples for different Pokémon and battle scenarios
- **Dropdown Example Selection**: Quick-select from various predefined examples for testing
- **Visual Enhancements**: Improved visual hierarchy, animations, and responsive design
- **Guided Help Section**: Step-by-step instructions for using the API documentation

#### Swagger UI Features

- **Expanded Documentation**: All operations are expanded by default for better visibility
- **Persistent Authorization**: Authentication tokens are remembered between page refreshes
- **Request Duration Display**: Shows how long each API request takes
- **Endpoint Filtering**: Easily filter endpoints to find what you need
- **Vendor Extensions Display**: Shows vendor and common extensions

#### Testing Examples

The Swagger UI includes a variety of examples for testing:

**Chat Endpoint Examples:**
- **Pokémon Research**: Pikachu, Charizard, Mewtwo
- **Pokémon Battle Comparisons**: Pikachu vs Bulbasaur, Charizard vs Blastoise
- **General Queries**: Exercise benefits, General knowledge questions

**Battle Endpoint Examples:**
- Pikachu vs Bulbasaur
- Charizard vs Blastoise
- Mewtwo vs Dragonite

### ReDoc

Access the ReDoc documentation at `/redoc` endpoint for a more readable, reference-style documentation with Google Fonts integration for better readability.

### Documentation Features

- **Comprehensive API Description**: Detailed overview of the API's features, technical details, and example usage
- **Enhanced Tag Metadata**: Organized endpoints with external documentation links
- **Rich Request Examples**: Multiple examples for each endpoint showing different use cases
- **Detailed Response Examples**: Complete response examples showing the structure and content
- **Schema Definitions**: Detailed schema definitions for all request and response models
- **Error Documentation**: Comprehensive documentation of error responses with examples
- **Interactive Try-It**: Test endpoints directly from the documentation

## Troubleshooting

### Docker Connection Issues

1. **API Connection Errors**:
   - Verify both containers are running: `docker ps`
   - Check API health: `curl http://localhost:8088/api/v1/pokemon/health`
   - Ensure the Streamlit container is using the correct API_HOST environment variable
   - Check Docker network: `docker network inspect pokemon-ai-agents_pokemon-network`

2. **Environment Variables**:
   - Make sure all required environment variables are set in the `.env` file
   - Verify that the Docker containers have access to these variables
   - Use the Debug tab in the Streamlit UI to check environment variables

3. **Container Logs**:
   - Check API logs: `docker logs pokemon-ai-api`
   - Check Streamlit logs: `docker logs pokemon-ai-streamlit`
   - Look for connection errors or other issues

4. **Restarting Services**:
   - Restart individual containers: `docker restart <container-name>`
   - Restart all services: `docker-compose down && docker-compose up -d`


## License

This project is licensed under the MIT License - see the LICENSE file for details.
