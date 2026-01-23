"""Middleware for presented files state management."""

from typing import Annotated, NotRequired, List, Optional
from langchain.agents.middleware.types import AgentMiddleware, AgentState


def _presented_files_reducer(
    left: Optional[List[dict]],
    right: Optional[List[dict]]
) -> List[dict]:
    """Reducer that appends presented files to the list.

    Args:
        left: Existing list of presented files
        right: New files to add

    Returns:
        Combined list of all presented files
    """
    if left is None:
        return right if right is not None else []
    if right is None:
        return left
    return left + right


class PresentedFilesState(AgentState):
    """State extension for presented files tracking."""
    presented_files: Annotated[NotRequired[List[dict]], _presented_files_reducer]


class PresentedFilesMiddleware(AgentMiddleware):
    """Middleware that adds presented_files state field with append reducer.

    This middleware enables the present_file tool to update state using Command,
    with new files being appended to the list rather than replacing it.
    """

    state_schema = PresentedFilesState
    tools = []  # No tools, just state extension
