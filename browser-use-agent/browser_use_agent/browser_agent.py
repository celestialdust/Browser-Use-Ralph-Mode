"""Main browser automation agent implementation using DeepAgents library."""

import uuid
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from browser_use_agent.configuration import get_llm, Config
from browser_use_agent.prompts import get_system_prompt, RALPH_MODE_REFLECTION_PROMPT
from browser_use_agent.state import AgentState, create_initial_state
from browser_use_agent.tools import BROWSER_TOOLS
from browser_use_agent.storage import get_checkpoint_saver, StorageConfig


def _load_context_files(agent_dir) -> str:
    """Load context files and return them as formatted string sections.

    Loads:
    - AGENTS.md as <project_memory>
    - agent.md as <agent_memory>
    - Skills metadata (names/descriptions only) as <skills>

    Args:
        agent_dir: Path to the .browser-agent directory

    Returns:
        Formatted context string to append to system prompt
    """
    import yaml
    from pathlib import Path

    context_sections = []

    # Load AGENTS.md (project memory - synthesized rules)
    agents_md_path = agent_dir / "memory" / "AGENTS.md"
    if agents_md_path.exists():
        try:
            content = agents_md_path.read_text()
            # Only include if there's actual content beyond the template
            if content.strip() and len(content) > 200:
                context_sections.append(f"<project_memory>\n{content}\n</project_memory>")
                print(f"[Agent] Loaded project memory from {agents_md_path}")
        except Exception as e:
            print(f"[Agent] Failed to load AGENTS.md: {e}")

    # Load agent.md (technical reference) - look in project root
    # Try multiple locations
    project_root = agent_dir.parent
    agent_md_paths = [
        project_root / "agent.md",
        agent_dir / "agent.md",
    ]
    for agent_md_path in agent_md_paths:
        if agent_md_path.exists():
            try:
                content = agent_md_path.read_text()
                # Truncate if too long (keep first 2000 chars)
                if len(content) > 2000:
                    content = content[:2000] + "\n\n[...truncated for brevity...]"
                context_sections.append(f"<agent_memory>\n{content}\n</agent_memory>")
                print(f"[Agent] Loaded agent memory from {agent_md_path}")
                break
            except Exception as e:
                print(f"[Agent] Failed to load agent.md from {agent_md_path}: {e}")

    # Load skills metadata (names and descriptions only)
    skills_dir = agent_dir / "skills"
    if skills_dir.exists():
        skill_entries = []
        for skill_folder in skills_dir.iterdir():
            if skill_folder.is_dir():
                skill_file = skill_folder / "SKILL.md"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text()
                        # Parse YAML frontmatter for name and description
                        if content.startswith("---"):
                            end = content.find("---", 3)
                            if end > 0:
                                try:
                                    frontmatter = yaml.safe_load(content[3:end])
                                    name = frontmatter.get("name", skill_folder.name)
                                    desc = frontmatter.get("description", "No description")
                                    skill_entries.append(f"- {name}: {desc}")
                                except yaml.YAMLError:
                                    # Fall back to folder name
                                    skill_entries.append(f"- {skill_folder.name}: (no description)")
                    except Exception as e:
                        print(f"[Agent] Failed to parse skill {skill_file}: {e}")

        if skill_entries:
            skills_list = "\n".join(skill_entries)
            context_sections.append(
                f"<skills>\nAvailable skills:\n{skills_list}\n\n"
                f"To use a skill: read_file(skills/[name]/SKILL.md) for full instructions.\n</skills>"
            )
            print(f"[Agent] Loaded {len(skill_entries)} skill metadata entries")

    return "\n".join(context_sections)


def create_browser_agent(
    model: Any = None,
    system_prompt: str = None,
    tools: List[Any] = None,
    checkpointer: Any = None,
    **kwargs
) -> Any:
    """Create a DeepAgents browser automation agent with filesystem backend.

    The agent includes:
    - Planning capabilities (write_todos tool)
    - File system tools for context management (ls, read_file, write_file, edit_file)
    - Subagent spawning for task delegation
    - Browser automation tools
    - State and memory management with checkpointing
    - Context loading from AGENTS.md, agent.md, and skills

    Args:
        model: Language model to use (defaults to Azure OpenAI from config)
        system_prompt: System prompt for the agent (defaults to BROWSER_AGENT_SYSTEM_PROMPT)
        tools: List of tools available to the agent (defaults to BROWSER_TOOLS)
        checkpointer: Checkpoint saver for persistence (defaults to storage config)
        **kwargs: Additional arguments for create_deep_agent

    Returns:
        Compiled LangGraph agent
    """
    # Initialize directory structure
    from browser_use_agent.storage import init_agent_directories
    init_agent_directories()

    # Use provided model or default to Azure OpenAI
    if model is None:
        model = get_llm()

    # Get base system prompt
    base_prompt = get_system_prompt(system_prompt)

    # Create filesystem backend
    agent_dir = StorageConfig.get_agent_dir()
    print(f"[Agent] Filesystem backend: {agent_dir}")

    # Load context files (AGENTS.md, agent.md, skills metadata)
    context = _load_context_files(agent_dir)

    # Combine base prompt with context
    if context:
        full_prompt = base_prompt + "\n\n" + context
    else:
        full_prompt = base_prompt

    # Use provided tools or default to browser tools
    if tools is None:
        tools = BROWSER_TOOLS

    # Get checkpoint saver if not provided
    if checkpointer is None:
        # Note: get_checkpoint_saver is async, but create_deep_agent expects sync
        # We'll handle async initialization separately in server.py
        print("[Agent] Using in-memory checkpointer (call init_checkpoint_db() for persistence)")
        checkpointer = None  # Will use InMemorySaver by default

    filesystem_backend = FilesystemBackend(
        root_dir=str(agent_dir)
    )

    # Create agent using DeepAgents library
    # The create_deep_agent function includes:
    # - TodoListMiddleware (planning)
    # - FilesystemMiddleware (file ops - configured via backend parameter)
    # - SubAgentMiddleware (task delegation)
    # - SummarizationMiddleware (context management)
    # NOTE: Using GPT-5 which doesn't use Anthropic prompt caching
    agent = create_deep_agent(
        model=model,
        system_prompt=full_prompt,
        tools=tools,
        backend=filesystem_backend,  # Configure custom filesystem backend
        checkpointer=checkpointer,
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


# Lazy initialization for the main agent instance
# This avoids blocking calls during module import in ASGI servers
_graph = None


def get_graph(config=None):
    """Get or create the browser agent (lazy initialization).

    This defers directory creation and agent setup until first use,
    avoiding blocking calls during module import in async contexts.

    Args:
        config: Optional RunnableConfig (accepted for LangGraph compatibility)

    Returns:
        Compiled LangGraph agent
    """
    global _graph
    if _graph is None:
        _graph = create_browser_agent()
    return _graph


# For langgraph.json compatibility, expose as callable
# LangGraph will call this function to get the graph instance
graph = get_graph
