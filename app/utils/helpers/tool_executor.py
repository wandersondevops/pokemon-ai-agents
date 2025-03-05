from typing import List, Dict, Any, Annotated
import json
from collections import defaultdict
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage, HumanMessage, ToolCall
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.chat_models import ChatOpenAI
from typing_extensions import TypedDict

class ToolExecutor:
    """Custom ToolExecutor implementation."""
    
    def __init__(self, tools):
        """Initialize the ToolExecutor with a list of tools."""
        self.tools = {}
        for i, tool in enumerate(tools):
            # Handle TavilySearchAPIWrapper specifically
            if 'TavilySearchAPIWrapper' in str(type(tool)):
                self.tools["tavily_search_api_wrapper"] = tool
                # Also register it as tool_0 for fallback
                self.tools[f"tool_{i}"] = tool
            elif hasattr(tool, 'name'):
                self.tools[tool.name] = tool
            else:
                self.tools[f"tool_{i}"] = tool
    
    def invoke(self, tool_invocation):
        """Invoke a tool with the given input."""
        tool_name = tool_invocation.get("tool")
        tool_input = tool_invocation.get("tool_input")
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            
            # Special case for TavilySearchAPIWrapper
            if 'TavilySearchAPIWrapper' in str(type(tool)):
                query = tool_input.get("query", "")
                try:
                    # TavilySearchAPIWrapper has a results method that takes a query parameter
                    return tool.results(query)
                except Exception:
                    return []
            elif hasattr(tool, 'invoke'):
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
    tool_invocation: AIMessage = state[-1]
    
    # Find the original question from earlier messages
    original_question = None
    for message in state:
        if isinstance(message, HumanMessage) and hasattr(message, 'content'):
            original_question = message.content
            break
    
    if not original_question:
        return []
    
    parsed_tool_calls = None
    
    if hasattr(tool_invocation, 'tool_calls') and tool_invocation.tool_calls:
        parsed_tool_calls = tool_invocation.tool_calls
    elif hasattr(tool_invocation, 'content') and isinstance(tool_invocation.content, str):
        try:
            content = tool_invocation.content
            
            # Try to parse the content as JSON
            parsed_content = json.loads(content)
            
            # Check for needs_search in the parsed content
            if isinstance(parsed_content, dict) and parsed_content.get("needs_search", False):
                print("Found needs_search=True in content")
                parsed_tool_calls = [parsed_content]
            elif '"search_queries"' in content or '"needs_search"' in content:
                print("Found search_queries or needs_search in content string")
                parsed_tool_calls = [parsed_content]
            else:
                print("No search indicators found in content")
                return []
        except Exception as e:
            print(f"Error parsing message content: {e}")
            return []
    else:
        print("Message has no tool_calls or content")
        return []

    if not parsed_tool_calls:
        print("No parsed tool calls found")
        return []

    print("Parsed tool calls:", parsed_tool_calls)
    
    ids = []
    tool_invocations = []
    
    for parsed_call in parsed_tool_calls:
        print("Processing parsed call:", parsed_call)
        args = parsed_call.get('args', {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
                print("Parsed args from string:", args)
            except Exception as e:
                print(f"Error parsing args string: {e}")
                continue
        
        print("Args type:", type(args))
        print("Args content:", args)
                
        # Check for either search_queries or needs_search field
        needs_search = False
        if "needs_search" in parsed_call and parsed_call.get("needs_search", False):
            needs_search = True
            print("Found needs_search=True in parsed_call directly")
        elif "needs_search" in args and args.get("needs_search", False):
            needs_search = True
            print("Found needs_search=True in args")
        elif "search_queries" in args:
            needs_search = True
            print("Found search_queries in args")
            
        if needs_search and original_question:
            print("Creating tool invocation for search with query:", original_question)
            # Use the original question for search
            tool_invocations.append({
                "tool": "tavily_search_api_wrapper",
                "tool_input": {"query": original_question}
            })
            ids.append(parsed_call.get("id", "search_id"))
            # Only add the original question once
            break
    
    if not tool_invocations:
        print("No tool invocations created")
        return []
    
    print("\n*** Executing tool invocations ***")
    print("Tool invocations:", tool_invocations)
    print("IDs:", ids)
        
    try:
        outputs = tool_executor.batch(tool_invocations)
        print("\n*** Tool execution completed ***")
        print("Outputs type:", type(outputs))
        print("Outputs length:", len(outputs))
        print("Outputs content:", outputs)
    except Exception as e:
        print(f"\n*** Error executing tools: {e} ***")
        import traceback
        traceback.print_exc()
        return []

    outputs_map = defaultdict(dict)
    try:
        for id_, output, invocation in zip(ids, outputs, tool_invocations):
            print(f"Processing output for ID: {id_}")
            print(f"Output type: {type(output)}")
            print(f"Output content: {output}")
            outputs_map[id_][invocation["tool_input"]["query"]] = output
    except Exception as e:
        print(f"\n*** Error mapping outputs: {e} ***")
        import traceback
        traceback.print_exc()
        return []

    tool_messages = []
    try:
        for id_, mapped_output in outputs_map.items():
            print(f"Creating ToolMessage for ID: {id_}")
            print(f"Mapped output: {mapped_output}")
            tool_messages.append(ToolMessage(
                content=mapped_output,
                tool_call_id=id_
            ))
    except Exception as e:
        print(f"\n*** Error creating tool messages: {e} ***")
        import traceback
        traceback.print_exc()
        return []

    print("\n*** Returning tool messages ***")
    print("Tool messages length:", len(tool_messages))
    print("Tool messages content:", tool_messages)
    return tool_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

tool = TavilySearchResults(max_results=2)
tools = [tool]
llm = ChatOpenAI(model_name='gpt-4o', temperature=0.7)
llm_with_tools = llm.bind(tools=tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile()
