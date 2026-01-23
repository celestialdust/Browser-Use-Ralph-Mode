"""State definitions for browser automation agent."""

from typing import TypedDict, List, Dict, Optional, Any, Literal
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


class SubagentInterrupt(TypedDict, total=False):
    """Pending interrupt from a subagent."""
    id: str                    # Unique interrupt ID
    subagent_id: str           # Which subagent is waiting
    subagent_name: str         # Human-readable name
    interrupt_type: str        # guidance, credentials, confirmation
    interrupt_data: Dict       # Full interrupt value
    response: Any              # Human's response (when responded)
    created_at: int            # Timestamp
    status: str                # pending, responded, resumed


class SubagentStatus(TypedDict, total=False):
    """Status of a running or completed subagent.

    Used for polling-based subagent visibility in the UI.
    """
    subagent_id: str                                                    # Unique subagent identifier
    subagent_type: str                                                  # Type of subagent (e.g., "research", "browser")
    prompt: str                                                         # The prompt given to the subagent
    status: Literal["pending", "running", "completed", "error", "cancelled"]  # Current status
    started_at: str                                                     # ISO timestamp when started
    completed_at: Optional[str]                                         # ISO timestamp when completed
    tool_calls_count: int                                               # Number of tool calls made
    last_activity: Optional[str]                                        # Brief description of current action
    result_summary: Optional[str]                                       # First 200 chars of result
    error: Optional[str]                                                # Error message if status is "error"


class PresentedFile(TypedDict):
    """A file presented to the user in the chat UI.

    Created when the agent calls present_file tool to show a file artifact.
    """
    id: str                     # Unique file ID
    file_path: str              # Relative path within .browser-agent directory
    display_name: str           # Human-readable name shown in UI
    description: Optional[str]  # Optional description of file contents
    file_type: str              # File type (PDF, DOCX, Markdown, etc.)
    file_size: int              # File size in bytes
    presented_at: str           # ISO timestamp when presented
    message_id: Optional[str]   # Associated message ID (if any)


class AgentState(TypedDict, total=False):
    """State for the browser automation agent."""
    messages: List[BaseMessage]
    todos: List[TodoItem]
    files: Dict[str, str]
    browser_session: Optional[BrowserSession]
    approval_queue: List[BrowserCommand]
    current_thought: Optional[ThoughtProcess]
    thread_id: str
    pending_subagent_interrupts: List[SubagentInterrupt]
    active_subagents: Optional[Dict[str, SubagentStatus]]  # Polling-based subagent visibility
    presented_files: Optional[List[PresentedFile]]  # File artifacts presented to user


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
        "pending_subagent_interrupts": [],
        "active_subagents": None,
        "presented_files": [],
    }
