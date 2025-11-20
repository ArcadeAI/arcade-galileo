"""
Arcade + Galileo Integration Demo

Demonstrates agentic workflow with Arcade tools and Galileo observability.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from arcadepy import Arcade
from langchain_openai import ChatOpenAI

from instrumentation import execute_tool_with_tracing, tracer

MAX_WORKFLOW_ROUNDS = 5
DEFAULT_LLM_MODEL = "gpt-4o"
DEFAULT_LLM_TEMPERATURE = 0.7

REQUIRED_ARCADE_TOOLS = [
    "Gmail_ListEmailsByHeader",
    "GoogleDocs_CreateDocumentFromText",
    "Gmail_SendEmail",
]


def validate_environment() -> None:
    """Validate required environment variables are set."""
    required = [
        "OPENAI_API_KEY",
        "ARCADE_API_KEY",
        "ARCADE_USER_ID",
        "GALILEO_API_KEY",
        "GALILEO_PROJECT_NAME",
    ]
    
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def load_arcade_tools() -> Tuple[List[Dict[str, Any]], Arcade, str]:
    """Load and filter Arcade tools in OpenAI format."""
    print("Loading Arcade tools (this takes ~30 seconds)...")
    
    api_key = os.getenv("ARCADE_API_KEY")
    user_id = os.getenv("ARCADE_USER_ID")
    arcade = Arcade(api_key=api_key)
    
    tools_page = arcade.tools.formatted.list(user_id=user_id, format="openai")
    all_tools = list(tools_page)
    
    tools = [
        tool for tool in all_tools 
        if any(name in tool['function']['name'] for name in REQUIRED_ARCADE_TOOLS)
    ]
    
    if not tools:
        raise RuntimeError(f"Required tools not found: {REQUIRED_ARCADE_TOOLS}")
    
    print(f"Loaded {len(tools)} tools: {', '.join(t['function']['name'] for t in tools)}")
    return tools, arcade, user_id


def create_agent(tools: List[Dict[str, Any]]) -> Any:
    """Create LangChain agent with tools."""
    llm = ChatOpenAI(
        model=DEFAULT_LLM_MODEL,
        temperature=DEFAULT_LLM_TEMPERATURE,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    return llm.bind_tools(tools)


def _execute_tool_call(
    tool_call: Dict[str, Any],
    arcade: Arcade,
    user_id: str,
    round_num: int
) -> Dict[str, Any]:
    """Execute a single tool call with tracing."""
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    
    print(f"[Round {round_num}] Executing: {tool_name}")
    
    result = execute_tool_with_tracing(
        tool_name=tool_name,
        tool_executor=lambda: arcade.tools.execute(
            tool_name=tool_name,
            input=tool_args,
            user_id=user_id
        ),
        inputs=tool_args
    )
    
    return {
        "tool_call_id": tool_call.get("id", ""),
        "role": "tool",
        "name": tool_name,
        "content": str(result)
    }


def _process_tool_calls(
    response: Any,
    arcade: Arcade,
    user_id: str,
    messages: List[Dict[str, Any]],
    round_num: int
) -> None:
    """Process all tool calls from agent response."""
    for tool_call in response.tool_calls:
        tool_result = _execute_tool_call(tool_call, arcade, user_id, round_num)
        messages.append(response)
        messages.append(tool_result)


def execute_workflow(agent: Any, arcade: Arcade, user_id: str) -> Optional[str]:
    """Execute email summary workflow with tracing."""
    task = """
    Complete this workflow:
    1. Check my emails from today
    2. Create a Google Doc titled "Email Summary - [Today's Date]" with a summary
    3. Send me an email with subject "Your Email Summary" containing the doc link
    """
    
    with tracer.start_as_current_span("email-summary-workflow"):
        messages = [{"role": "user", "content": task}]
        
        for round_num in range(1, MAX_WORKFLOW_ROUNDS + 1):
            response = agent.invoke(messages)
            
            if not response.tool_calls:
                return response.content
            
            _process_tool_calls(response, arcade, user_id, messages, round_num)
        
        print(f"Warning: Workflow incomplete after {MAX_WORKFLOW_ROUNDS} rounds", 
              file=sys.stderr)
        return None


def main() -> None:
    """Run the demo workflow."""
    print("=" * 60)
    print("Arcade + Galileo Integration Demo")
    print("=" * 60)
    print()
    
    validate_environment()
    
    try:
        tools, arcade, user_id = load_arcade_tools()
        agent = create_agent(tools)
        
        print("Executing workflow...\n")
        result = execute_workflow(agent, arcade, user_id)
        
        if result:
            print("\n" + "=" * 60)
            print("Workflow completed!")
            print("=" * 60)
            print(f"\n{result}")
        
        print(f"\n📊 View traces: https://app.galileo.ai")
        print(f"   Project: {os.getenv('GALILEO_PROJECT_NAME')}")
        
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
