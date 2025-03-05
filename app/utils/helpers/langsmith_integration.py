"""
LangSmith integration for the Pokemon AI Agents.

This module contains functions for integrating with LangSmith.
"""

import os
import datetime
import logging
from typing import Dict, Any, Optional, List, Union, Callable

from langchain_openai import ChatOpenAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.smith import RunEvalConfig, run_on_dataset
# EvaluationResult is no longer available in langchain.smith.evaluation
# Using Dict[str, Any] as a replacement type
# run_llm_with_tracing is deprecated, using direct Client approach
from langchain_core.runnables import RunnableConfig
from langsmith import Client
import langsmith.utils

from app.core.config import settings
from app.utils.helpers.langgraph_nodes import create_pokemon_agent_graph, State

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("langsmith_integration")


def configure_langsmith():
    """
    Configure LangSmith environment variables.
    
    This function sets the necessary environment variables for LangSmith integration.
    """
    # Set LangSmith environment variables
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if settings.LANGSMITH_TRACING else "false"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    
    # Ensure we're using the correct LangSmith API key
    if not settings.LANGSMITH_API_KEY:
        logger.warning("LANGSMITH_API_KEY is not set in environment variables")
        return False
    
    # Log the configuration (without sensitive data)
    logger.info(f"LangSmith configured with project: {settings.LANGSMITH_PROJECT}")
    logger.info(f"LangSmith tracing enabled: {settings.LANGSMITH_TRACING}")
    logger.info(f"LangSmith endpoint: {settings.LANGSMITH_ENDPOINT}")
    
    return True


def create_langsmith_agent(llm: ChatOpenAI, search_wrapper: TavilySearchAPIWrapper):
    """
    Create a LangSmith-enabled Pokemon agent.
    
    Args:
        llm: The language model to use
        search_wrapper: The search wrapper to use
        
    Returns:
        The LangSmith-enabled Pokemon agent
    """
    # Configure LangSmith
    configure_langsmith()
    
    # Create the Pokemon agent graph
    graph = create_pokemon_agent_graph(llm, search_wrapper)
    
    # Return the graph
    return graph


def run_with_langsmith(
    agent,
    query: str,
    metadata: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    auto_create_dataset: bool = True
) -> Dict[str, Any]:
    """
    Run the Pokemon agent with LangSmith tracing.
    
    Args:
        agent: The Pokemon agent to run
        query: The user query
        metadata: Additional metadata to include in the trace
        config: Additional configuration for the run
        auto_create_dataset: Whether to automatically add this query to a dataset
        
    Returns:
        Dict[str, Any]: The agent's response
    """
    # Configure LangSmith
    if not configure_langsmith():
        logger.warning("LangSmith not properly configured, running without tracing")
        return agent.invoke({"messages": [{"role": "human", "content": query}]})
    
    # Create the initial state with all required keys
    initial_state = {
        "messages": [{"role": "human", "content": query}],
        "pokemon_research_data": {},
        "battle_analysis_result": None,
        "search_results": None
    }
    
    # Create the config with additional metadata
    run_metadata = {
        "query": query,
        "timestamp": str(datetime.datetime.now()),
        "api_version": "v1"
    }
    
    # Add user-provided metadata
    if metadata:
        run_metadata.update(metadata)
    
    # Create the config
    run_config = RunnableConfig(
        callbacks=None,  # LangSmith will automatically add callbacks
        tags=["pokemon-ai-agents", "production", "autonomous"],
        metadata=run_metadata
    )
    
    # Run the agent with tracing
    try:
        # Use the LangSmith API key from settings
        if not settings.LANGSMITH_API_KEY:
            logger.warning("LANGSMITH_API_KEY is not set, tracing may not work")
        
        # Set up tracing via environment variables
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        
        # Create a unique run ID for this invocation
        run_id = f"pokemon-ai-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(query) % 10000}"
        os.environ["LANGCHAIN_RUN_ID"] = run_id
        
        # Set up the config with tags and metadata
        run_config = RunnableConfig(
            tags=["pokemon-ai-agents", "production", "autonomous"],
            metadata=run_metadata
        )
        
        # Run the agent with the config
        result = agent.invoke(initial_state, config=run_config)
        
        # Automatically add to dataset if enabled
        if auto_create_dataset and result:
            try:
                # Add to the auto dataset
                add_to_auto_dataset(query, result)
            except Exception as e:
                logger.error(f"Error adding to auto dataset: {e}")
        
        return result
    except Exception as e:
        logger.error(f"Error running agent with LangSmith tracing: {e}")
        import traceback
        traceback.print_exc()
        # Fall back to running without tracing
        return agent.invoke(initial_state)


def create_langsmith_dataset(name: str, description: str, data: list):
    """
    Create a LangSmith dataset.
    
    Args:
        name: The name of the dataset
        description: The description of the dataset
        data: The data for the dataset
        
    Returns:
        The created dataset
    """
    # Configure LangSmith
    if not configure_langsmith():
        logger.error("LangSmith not properly configured, cannot create dataset")
        return None
    
    # Create the client with explicit API key from settings
    client = Client(
        api_key=settings.LANGSMITH_API_KEY,
        api_url=settings.LANGSMITH_ENDPOINT
    )
    
    # Create the dataset
    try:
        dataset = client.create_dataset(name=name, description=description)
        
        # Add examples to the dataset
        for example in data:
            client.create_example(
                inputs=example["inputs"],
                outputs=example.get("outputs", {}),
                dataset_id=dataset.id
            )
        
        logger.info(f"Successfully created dataset '{name}' with {len(data)} examples")
        return dataset
    except Exception as e:
        logger.error(f"Error creating LangSmith dataset: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_evaluation(
    agent,
    dataset_name: str,
    evaluation_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run an evaluation on a LangSmith dataset.
    
    Args:
        agent: The Pokemon agent to evaluate
        dataset_name: The name of the dataset to evaluate on
        evaluation_config: Additional configuration for the evaluation
        
    Returns:
        Dict[str, Any]: The evaluation results
    """
    # Configure LangSmith
    if not configure_langsmith():
        logger.error("LangSmith not properly configured, cannot run evaluation")
        return None
    
    # Create the client with explicit API key from settings
    client = Client(
        api_key=settings.LANGSMITH_API_KEY,
        api_url=settings.LANGSMITH_ENDPOINT
    )
    
    # Create the evaluation config
    eval_config = RunEvalConfig(
        evaluators=["criteria", "correctness", "helpfulness"],
        custom_evaluators=[],
        **(evaluation_config or {})
    )
    
    # Run the evaluation
    try:
        evaluation_result = run_on_dataset(
            client=client,  # Use our configured client
            dataset_name=dataset_name,
            llm_or_chain_factory=lambda: agent,
            evaluation=eval_config,
            project_name=f"{settings.LANGSMITH_PROJECT}-eval",
            tags=["evaluation", "pokemon-ai-agents", "production", "autonomous"]
        )
        
        logger.info(f"Successfully ran evaluation on dataset '{dataset_name}'")
        return evaluation_result
    except Exception as e:
        logger.error(f"Error running LangSmith evaluation: {e}")
        import traceback
        traceback.print_exc()
        return None


def add_to_auto_dataset(query: str, result: Any) -> None:
    """
    Automatically add a query and result to a dataset for future evaluation.
    
    Args:
        query: The user query
        result: The agent's response
    """
    # Get the auto dataset name
    dataset_name = f"{settings.LANGSMITH_PROJECT}-auto-dataset"
    
    # Create the client
    client = Client(
        api_key=settings.LANGSMITH_API_KEY,
        api_url=settings.LANGSMITH_ENDPOINT
    )
    
    try:
        # Check if the dataset exists
        try:
            datasets = client.list_datasets()
            dataset = next((d for d in datasets if d.name == dataset_name), None)
        except Exception as e:
            logger.warning(f"Error listing datasets: {e}")
            dataset = None
        
        # Create the dataset if it doesn't exist
        if not dataset:
            try:
                # The API has changed, now we need to pass dataset_name as a parameter
                dataset = client.create_dataset(
                    dataset_name=dataset_name,
                    description=f"Automatically generated dataset for {settings.LANGSMITH_PROJECT}"
                )
                logger.info(f"Created auto dataset '{dataset_name}'")
            except langsmith.utils.LangSmithConflictError:
                # Dataset already exists but wasn't found in the list_datasets call
                # This can happen due to caching or race conditions
                logger.info(f"Dataset '{dataset_name}' already exists, retrieving it")
                datasets = client.list_datasets(force_refresh=True)
                dataset = next((d for d in datasets if d.name == dataset_name), None)
                
                if not dataset:
                    # If we still can't find it, try to get it directly by name
                    try:
                        all_datasets = client.list_datasets(force_refresh=True)
                        dataset = next((d for d in all_datasets if d.name == dataset_name), None)
                    except Exception as e:
                        logger.error(f"Error retrieving dataset by name: {e}")
                        raise
        
        if not dataset:
            logger.error(f"Could not create or find dataset '{dataset_name}'")
            return
            
        # Add the example to the dataset
        client.create_example(
            inputs={"query": query},
            outputs={"result": result},
            dataset_id=dataset.id
        )
        
        logger.info(f"Added query to auto dataset: '{query[:50]}...'" if len(query) > 50 else query)
    except Exception as e:
        logger.error(f"Error adding to auto dataset: {e}")
        # Only print traceback for non-conflict errors to reduce log noise
        if not isinstance(e, langsmith.utils.LangSmithConflictError):
            import traceback
            traceback.print_exc()


def schedule_auto_evaluation(frequency_hours: int = 24) -> None:
    """
    Schedule automatic evaluations to run periodically.
    
    Args:
        frequency_hours: How often to run evaluations (in hours)
    """
    if not settings.LANGSMITH_API_KEY:
        logger.error("Cannot schedule auto evaluation: LANGSMITH_API_KEY not set")
        return
    
    # This is a placeholder for scheduling logic
    # In a real implementation, you would use a task scheduler like Celery or APScheduler
    logger.info(f"Auto evaluation scheduled to run every {frequency_hours} hours")
    
    # For now, we'll just log a message
    logger.info("To implement scheduled evaluations, add a proper task scheduler to the project")


def get_recent_runs(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent runs from LangSmith.
    
    Args:
        limit: Maximum number of runs to return
        
    Returns:
        List of recent runs
    """
    if not configure_langsmith():
        logger.error("LangSmith not properly configured, cannot get recent runs")
        return []
    
    # Create the client
    client = Client(
        api_key=settings.LANGSMITH_API_KEY,
        api_url=settings.LANGSMITH_ENDPOINT
    )
    
    try:
        # Get recent runs
        runs = client.list_runs(
            project_name=settings.LANGSMITH_PROJECT,
            execution_order=1,  # Most recent first
            limit=limit
        )
        
        # Convert runs to a more usable format
        result = []
        for run in runs:
            run_data = {
                "id": str(run.id) if hasattr(run, 'id') else 'unknown',
                "name": run.name if hasattr(run, 'name') else 'unknown',
                "start_time": str(run.start_time) if hasattr(run, 'start_time') else None,
                "end_time": str(run.end_time) if hasattr(run, 'end_time') else None,
                "status": run.status if hasattr(run, 'status') else 'unknown',
                "error": run.error if hasattr(run, 'error') else None,
            }
            
            # Safely add inputs and outputs if they exist
            if hasattr(run, 'inputs'):
                run_data["inputs"] = run.inputs
            if hasattr(run, 'outputs'):
                run_data["outputs"] = run.outputs
            
            result.append(run_data)
        
        return result
    except Exception as e:
        logger.error(f"Error getting recent runs: {e}")
        import traceback
        traceback.print_exc()
        return []


def run_llm_with_tracing(llm, inputs, project_name=None, api_key=None, config=None):
    """
    Run an LLM with LangSmith tracing.
    
    Args:
        llm: The LLM to run
        inputs: The inputs to the LLM
        project_name: The name of the project to trace under
        api_key: The LangSmith API key
        config: Additional configuration for the run
        
    Returns:
        The LLM's response
    """
    # Configure LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if project_name:
        os.environ["LANGCHAIN_PROJECT"] = project_name
    if api_key:
        os.environ["LANGCHAIN_API_KEY"] = api_key
    
    # Add run ID to metadata if not present
    if config and "metadata" in config:
        if "run_id" not in config["metadata"]:
            config["metadata"]["run_id"] = f"run_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{id(llm)}"
    
    # Run the LLM with tracing
    result = llm.invoke(inputs, config=config)
    
    return result
