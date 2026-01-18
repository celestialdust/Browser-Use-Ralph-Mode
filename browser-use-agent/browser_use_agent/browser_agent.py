"""Main browser automation agent implementation using DeepAgents library."""

import uuid
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage

try:
    from deepagents import create_deep_agent
except ImportError:
    print("Error: deepagents library not installed. Please run:")
    print("  pip install deepagents")
    raise

from browser_use_agent.configuration import get_llm, Config
from browser_use_agent.prompts import get_system_prompt, RALPH_MODE_REFLECTION_PROMPT
from browser_use_agent.state import AgentState, create_initial_state
from browser_use_agent.tools import BROWSER_TOOLS


def create_browser_agent(
    model: Any = None,
    system_prompt: str = None,
    tools: List[Any] = None,
    **kwargs
) -> Any:
    """Create a DeepAgents browser automation agent.
    
    The agent includes:
    - Planning capabilities (write_todos tool)
    - File system tools for context management
    - Subagent spawning for task delegation
    - Browser automation tools
    - State and memory management
    
    Args:
        model: Language model to use (defaults to Azure OpenAI from config)
        system_prompt: System prompt for the agent (defaults to BROWSER_AGENT_SYSTEM_PROMPT)
        tools: List of tools available to the agent (defaults to BROWSER_TOOLS)
        **kwargs: Additional arguments for create_deep_agent
        
    Returns:
        Compiled LangGraph agent
    """
    # Use provided model or default to Azure OpenAI
    if model is None:
        model = get_llm()
    
    # Get system prompt
    prompt = get_system_prompt(system_prompt)
    
    # Use provided tools or default to browser tools
    if tools is None:
        tools = BROWSER_TOOLS
    
    # Create agent using DeepAgents library
    # The create_deep_agent function handles:
    # - Planning and task decomposition (write_todos tool)
    # - File system tools for context management  
    # - Subagent spawning (task tool)
    # - State management
    # - Checkpoint/memory management
    agent = create_deep_agent(
        model=model,
        system_prompt=prompt,
        tools=tools,
        **kwargs
    )
    
    return agent


def run_ralph_mode(
    task: str,
    max_iterations: int = None,
    thread_id: str = None,
    agent: Any = None,
    **kwargs
) -> Dict[str, Any]:
    """Run agent in Ralph Mode with iterative refinement.
    
    Ralph Mode runs the agent in a loop, allowing it to:
    - Iterate on the task multiple times
    - Refine its approach based on previous results
    - Use filesystem for persistent memory between iterations
    - Detect and correct mistakes
    
    This is inspired by the LangChain DeepAgents Ralph Mode pattern.
    
    Args:
        task: The task description for the agent
        max_iterations: Maximum number of iterations (defaults to Config.DEFAULT_MAX_ITERATIONS)
        thread_id: Optional thread ID for session isolation
        agent: Optional pre-created agent (will create new one if not provided)
        **kwargs: Additional configuration
        
    Returns:
        Final result after all iterations
    """
    if max_iterations is None:
        max_iterations = Config.DEFAULT_MAX_ITERATIONS
    
    if thread_id is None:
        thread_id = str(uuid.uuid4())
    
    if agent is None:
        agent = create_browser_agent()
    
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    # Initial state
    initial_state = create_initial_state(thread_id)
    initial_state["messages"] = [HumanMessage(content=task)]
    
    print(f"\n{'='*60}")
    print(f"Ralph Mode: Starting task with {max_iterations} iterations")
    print(f"Task: {task}")
    print(f"Thread ID: {thread_id}")
    print(f"{'='*60}\n")
    
    results = []
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration}/{max_iterations} ---\n")
        
        try:
            # Run agent for this iteration
            result = agent.invoke(initial_state, config)
            results.append(result)
            
            # Check if task is complete
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                content = getattr(last_message, "content", "")
                
                # Simple completion check
                completion_words = ["complete", "done", "finished", "success", "completed"]
                if any(word in content.lower() for word in completion_words):
                    print(f"\n✓ Task completed in iteration {iteration}")
                    break
            
            # Prepare for next iteration if needed
            if iteration < max_iterations:
                # Add reflection prompt for next iteration
                reflection = HumanMessage(content=RALPH_MODE_REFLECTION_PROMPT)
                initial_state["messages"].append(reflection)
                
        except Exception as e:
            print(f"✗ Error in iteration {iteration}: {e}")
            if iteration == max_iterations:
                raise
            continue
    
    print(f"\n{'='*60}")
    print(f"Ralph Mode: Completed after {len(results)} iterations")
    print(f"{'='*60}\n")
    
    # Return final result
    return results[-1] if results else {}


# Create the main agent instance
# This will be imported by langgraph.json
graph = create_browser_agent()
