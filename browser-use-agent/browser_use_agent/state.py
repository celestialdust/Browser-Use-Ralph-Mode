"""State definitions for browser automation agent."""

from typing import TypedDict, List, Dict, Optional, Any
from langchain_core.messages import BaseMessage


class BrowserSession(TypedDict, total=False):
    """Browser session information."""
    sessionId: str
    streamUrl: Optional[str]
    isActive: bool


class BrowserCommand(TypedDict, total=False):
    """Browser command for approval."""
    id: str
    command: str
    args: Dict[str, Any]
    requiresApproval: bool


class TodoItem(TypedDict, total=False):
    """Todo item for task tracking."""
    id: str
    content: str
    status: str  # pending, in_progress, completed


class ThoughtProcess(TypedDict, total=False):
    """Agent's thought process."""
    content: str
    timestamp: int
    isComplete: bool


class AgentState(TypedDict, total=False):
    """State for the browser automation agent."""
    messages: List[BaseMessage]
    todos: List[TodoItem]
    files: Dict[str, str]
    browser_session: Optional[BrowserSession]
    approval_queue: List[BrowserCommand]
    current_thought: Optional[ThoughtProcess]
    thread_id: str


def create_initial_state(thread_id: str) -> AgentState:
    """Create initial agent state for a thread.
    
    Args:
        thread_id: Unique thread identifier
        
    Returns:
        AgentState: Initial state
    """
    return {
        "messages": [],
        "todos": [],
        "files": {},
        "browser_session": None,
        "approval_queue": [],
        "current_thought": None,
        "thread_id": thread_id,
    }
