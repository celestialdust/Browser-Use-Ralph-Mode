"""Human-in-the-loop tools using LangGraph interrupt mechanism.

This module provides tools for the agent to request help from humans when:
- Both DOM and visual approaches fail (request guidance)
- Login credentials are needed (request credentials)
- Confirmation is needed for sensitive actions (request confirmation)

Uses LangGraph's interrupt() function for proper graph-based human intervention.
"""

from typing import Dict, Any, Optional
from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def request_human_guidance(thread_id: str, context: str, question: str, attempted_approaches: str) -> str:
    """Request guidance from a human when stuck.

    Use this tool when:
    - Both DOM-based and visual approaches have failed
    - You're unsure how to proceed with a task
    - You need clarification on user intent
    - You encounter an unexpected situation

    This tool uses LangGraph's interrupt mechanism to pause execution
    and wait for human response.

    Args:
        thread_id: Thread identifier for this session
        context: Describe the current situation and what you're trying to do
        question: Specific question for the human
        attempted_approaches: What approaches you've already tried

    Returns:
        Human's guidance response

    Example:
        guidance = request_human_guidance(
            thread_id="abc123",
            context="Trying to log into LinkedIn",
            question="I cannot find the login button. Where should I look?",
            attempted_approaches="Tried: snapshot with -i flag, searched for 'Sign In', checked top navigation"
        )
    """
    request_data = {
        "type": "guidance",
        "thread_id": thread_id,
        "context": context,
        "question": question,
        "attempted_approaches": attempted_approaches,
    }

    print(f"[HumanLoop] Requesting guidance for thread {thread_id}")
    print(f"[HumanLoop] Question: {question}")

    # Use LangGraph interrupt to pause and wait for human response
    response = interrupt(request_data)

    print(f"[HumanLoop] Received guidance: {response}")
    return response


@tool
def request_credentials(thread_id: str, service: str, credential_types: str, reason: str) -> Dict[str, str]:
    """Request login credentials from a human.

    Use this tool when you need credentials to log into a service.
    NEVER attempt to guess or generate credentials.

    This tool uses LangGraph's interrupt mechanism to pause execution
    and wait for credentials from the human.

    Args:
        thread_id: Thread identifier for this session
        service: Name of the service (e.g., "LinkedIn", "Gmail", "GitHub")
        credential_types: What credentials are needed (e.g., "username and password", "API key", "2FA code")
        reason: Why you need these credentials

    Returns:
        Dictionary with credentials (e.g., {"username": "...", "password": "..."})

    Example:
        creds = request_credentials(
            thread_id="abc123",
            service="LinkedIn",
            credential_types="username and password",
            reason="User asked me to check their LinkedIn messages"
        )
        username = creds["username"]
        password = creds["password"]
    """
    request_data = {
        "type": "credentials",
        "thread_id": thread_id,
        "service": service,
        "credential_types": credential_types,
        "reason": reason,
        "question": f"Please provide {credential_types} for {service}",
    }

    print(f"[HumanLoop] Requesting credentials for {service}")
    print(f"[HumanLoop] Reason: {reason}")

    # Use LangGraph interrupt to pause and wait for credentials
    credentials = interrupt(request_data)

    print(f"[HumanLoop] Received credentials for {service}")
    return credentials


@tool
def request_confirmation(thread_id: str, action: str, risks: str, alternatives: str = "None") -> str:
    """Request confirmation from human before taking a potentially risky action.

    Use this tool before:
    - Submitting forms with financial information
    - Deleting or modifying important data
    - Performing actions that cannot be undone
    - Actions with security or privacy implications

    This tool uses LangGraph's interrupt mechanism to pause execution
    and wait for user confirmation.

    Args:
        thread_id: Thread identifier for this session
        action: Describe the action you want to take
        risks: Potential risks or consequences
        alternatives: Alternative approaches (if any)

    Returns:
        "approved" if human approves, "rejected" with reason if denied

    Example:
        confirmation = request_confirmation(
            thread_id="abc123",
            action="Submit payment form with $500 amount",
            risks="This will charge the credit card on file",
            alternatives="Could save as draft instead"
        )

        if "approved" in confirmation.lower():
            # Proceed with action
            browser_click(submit_button_ref, thread_id)
        else:
            # Handle rejection
            return f"Action cancelled: {confirmation}"
    """
    request_data = {
        "type": "confirmation",
        "thread_id": thread_id,
        "action": action,
        "risks": risks,
        "alternatives": alternatives,
        "question": f"Should I proceed with: {action}?",
        "options": ["Approve", "Reject", "Suggest alternative"],
    }

    print(f"[HumanLoop] Requesting confirmation for action: {action}")
    print(f"[HumanLoop] Risks: {risks}")

    # Use LangGraph interrupt to pause and wait for confirmation
    decision = interrupt(request_data)

    print(f"[HumanLoop] Received decision: {decision}")
    return decision


# Tools list for export
HUMAN_LOOP_TOOLS = [
    request_human_guidance,
    request_credentials,
    request_confirmation,
]
