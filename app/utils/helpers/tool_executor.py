"""
Tool executor for executing tools in the Pokemon AI Agents system.

This module contains the ToolExecutor class and related functions for executing tools.
"""

from typing import List, Dict, Any
import requests
import json
from collections import defaultdict
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage, HumanMessage, ToolCall
from langgraph.prebuilt import ToolNode

class ToolExecutor:
    """Custom ToolExecutor implementation."""
    
    def __init__(self, tools):
        """Initialize the ToolExecutor with a list of tools."""
        self.tools = {}
        for i, tool in enumerate(tools):
            # For TavilySearchAPIWrapper
            if hasattr(tool, 'run') and not hasattr(tool, 'name'):
                self.tools["tavily_search_api_wrapper"] = tool
            # For tools with name attribute
            elif hasattr(tool, 'name'):
                self.tools[tool.name] = tool
            # Fallback
            else:
                self.tools[f"tool_{i}"] = tool
    
    def invoke(self, tool_invocation):
        """Invoke a tool with the given input."""
        tool_name = tool_invocation.get("tool")
        tool_input = tool_invocation.get("tool_input")
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            # Handle different tool interfaces
            if hasattr(tool, 'invoke'):
                return tool.invoke(tool_input)
            elif hasattr(tool, 'run'):
                return tool.run(**tool_input)
            else:
                raise ValueError(f"Tool {tool_name} has no invoke or run method")
        else:
            raise ValueError(f"Tool {tool_name} not found")
            
    def batch(self, tool_invocations):
        """Execute multiple tool invocations in batch."""
        return [self.invoke(invocation) for invocation in tool_invocations]

def execute_tools(state: List[BaseMessage], tool_executor) -> List[ToolMessage]:
    """Execute tools based on the current state."""
    tool_invocation : AIMessage = state[-1]
    
    # Simple parsing of tool calls from the AIMessage
    if hasattr(tool_invocation, 'tool_calls') and tool_invocation.tool_calls:
        parsed_tool_calls = tool_invocation.tool_calls
    elif hasattr(tool_invocation, 'content') and isinstance(tool_invocation.content, str):
        # Try to extract tool calls from content if available
        try:
            content = tool_invocation.content
            if '"search_queries"' in content:
                parsed_tool_calls = [json.loads(content)]
            else:
                return []
        except:
            return []
    else:
        return []

    ids = []
    tool_invocations = []

    for parsed_call in parsed_tool_calls:
        args = parsed_call.get('args', {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except:
                continue
                
        if "search_queries" in args:
            for query in args["search_queries"]:
                tool_invocations.append({
                    "tool": "tavily_search_api_wrapper",
                    "tool_input": {"query": query}
                })
            ids.append(parsed_call.get("id", ""))
    
    if not tool_invocations:
        return []
        
    outputs = tool_executor.batch(tool_invocations)

    outputs_map = defaultdict(dict)
    for id_, output, invocation in zip(ids, outputs, tool_invocations):
        outputs_map[id_][invocation["tool_input"]["query"]] = output

    tool_messages = []
    for id_, mapped_output in outputs_map.items():
        tool_messages.append(ToolMessage(
            content=mapped_output,
            tool_call_id=id_
        ))

    return tool_messages
