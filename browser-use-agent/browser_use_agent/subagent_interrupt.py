"""Subagent interrupt forwarding layer.

Catches GraphInterrupt from subagents and stores them in parent state
so they can be surfaced to the frontend for human response.
"""

import time
import uuid
from typing import Any, Dict, Optional, TypedDict, List

from langgraph.types import Interrupt


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


def execute_subagent_with_interrupt_capture(
    subagent,
    input_data: Dict[str, Any],
    parent_state: Dict[str, Any],
    subagent_name: str = "Subagent"
) -> Dict[str, Any]:
    """Execute subagent and capture any interrupts.

    Args:
        subagent: The subagent graph to execute
        input_data: Input for the subagent
        parent_state: Parent agent's state (will be modified)
        subagent_name: Human-readable name for the subagent

    Returns:
        Dict with success status and either result or interrupt info
    """
    subagent_id = str(uuid.uuid4())

    try:
        result = subagent.invoke(input_data)
        return {"success": True, "result": result}

    except Exception as e:
        # Check if this is a GraphInterrupt (or similar interrupt exception)
        # GraphInterrupt may be raised directly or wrapped
        interrupt_value = None

        # Try to extract interrupt data from various exception formats
        if hasattr(e, 'args') and e.args:
            first_arg = e.args[0]
            # Handle tuple of Interrupt objects
            if isinstance(first_arg, tuple) and first_arg:
                if hasattr(first_arg[0], 'value'):
                    interrupt_value = first_arg[0].value
            # Handle single Interrupt object
            elif hasattr(first_arg, 'value'):
                interrupt_value = first_arg.value
            # Handle dict directly
            elif isinstance(first_arg, dict):
                interrupt_value = first_arg

        # If we couldn't extract interrupt data, re-raise the exception
        if interrupt_value is None:
            raise

        interrupt_info: SubagentInterrupt = {
            "id": str(uuid.uuid4()),
            "subagent_id": subagent_id,
            "subagent_name": subagent_name,
            "interrupt_type": interrupt_value.get("type", "guidance") if isinstance(interrupt_value, dict) else "guidance",
            "interrupt_data": interrupt_value if isinstance(interrupt_value, dict) else {"value": interrupt_value},
            "created_at": int(time.time()),
            "status": "pending"
        }

        # Initialize list if needed
        if "pending_subagent_interrupts" not in parent_state:
            parent_state["pending_subagent_interrupts"] = []

        # Store in parent state
        parent_state["pending_subagent_interrupts"].append(interrupt_info)

        question = interrupt_value.get("question", "Unknown question") if isinstance(interrupt_value, dict) else str(interrupt_value)

        return {
            "success": False,
            "waiting_for_human": True,
            "interrupt_id": interrupt_info["id"],
            "message": f"Subagent '{subagent_name}' needs human assistance: {question}"
        }


def check_and_resume_subagents(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Check for responded subagent interrupts and prepare resume info.

    Args:
        state: Current agent state

    Returns:
        Dict with resume info if a subagent should be resumed, None otherwise
    """
    pending_interrupts: List[SubagentInterrupt] = state.get("pending_subagent_interrupts", [])

    for interrupt in pending_interrupts:
        if interrupt.get("status") == "responded":
            # Mark as resumed
            interrupt["status"] = "resumed"

            return {
                "resume_subagent_id": interrupt["subagent_id"],
                "resume_value": interrupt.get("response"),
                "interrupt_id": interrupt["id"]
            }

    return None


def respond_to_subagent_interrupt(
    state: Dict[str, Any],
    interrupt_id: str,
    response: Any
) -> bool:
    """Store response for a subagent interrupt.

    Args:
        state: Current agent state
        interrupt_id: ID of the interrupt to respond to
        response: Human's response

    Returns:
        True if interrupt was found and updated, False otherwise
    """
    pending_interrupts: List[SubagentInterrupt] = state.get("pending_subagent_interrupts", [])

    for interrupt in pending_interrupts:
        if interrupt["id"] == interrupt_id:
            interrupt["status"] = "responded"
            interrupt["response"] = response
            return True

    return False
