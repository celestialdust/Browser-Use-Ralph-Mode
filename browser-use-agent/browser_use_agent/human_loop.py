"""Human-in-the-loop tools for requesting human assistance.

This module provides tools for the agent to request help from humans when:
- Both DOM and visual approaches fail (request guidance)
- Login credentials are needed (request credentials)
- Confirmation is needed for sensitive actions (request confirmation)
"""

from datetime import datetime
from typing import Dict, Any, Optional
from langchain_core.tools import tool

# Global state for human interaction requests
_human_requests: Dict[str, Dict[str, Any]] = {}
_request_counter = 0


def _create_request(
    request_type: str,
    thread_id: str,
    context: str,
    question: str,
    options: Optional[list] = None
) -> Dict[str, Any]:
    """Create a human interaction request.

    Args:
        request_type: Type of request (guidance, credentials, confirmation)
        thread_id: Thread identifier
        context: Context about the situation
        question: Question to ask the human
        options: Optional list of suggested options

    Returns:
        Request data dict
    """
    global _request_counter
    _request_counter += 1
    request_id = f"{thread_id}_{request_type}_{_request_counter}"

    request = {
        "id": request_id,
        "type": request_type,
        "thread_id": thread_id,
        "context": context,
        "question": question,
        "options": options,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "response": None,
    }

    _human_requests[request_id] = request
    print(f"[HumanLoop] Created {request_type} request: {request_id}")
    return request


def get_pending_requests(thread_id: str) -> list:
    """Get all pending requests for a thread.

    Args:
        thread_id: Thread identifier

    Returns:
        List of pending request dicts
    """
    return [
        req for req in _human_requests.values()
        if req["thread_id"] == thread_id and req["status"] == "pending"
    ]


def get_request(request_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific request by ID.

    Args:
        request_id: Request identifier

    Returns:
        Request dict or None
    """
    return _human_requests.get(request_id)


def submit_response(request_id: str, response: Any) -> bool:
    """Submit a response to a pending request.

    Args:
        request_id: Request identifier
        response: The human's response

    Returns:
        True if successful, False otherwise
    """
    if request_id not in _human_requests:
        return False

    request = _human_requests[request_id]
    if request["status"] != "pending":
        return False

    request["response"] = response
    request["status"] = "completed"
    request["completed_at"] = datetime.now().isoformat()
    print(f"[HumanLoop] Response submitted for {request_id}")
    return True


@tool
def request_human_guidance(thread_id: str, context: str, question: str, attempted_approaches: str) -> str:
    """Request guidance from a human when stuck.

    Use this tool when:
    - Both DOM-based and visual approaches have failed
    - You're unsure how to proceed with a task
    - You need clarification on user intent
    - You encounter an unexpected situation

    Args:
        thread_id: Thread identifier for this session
        context: Describe the current situation and what you're trying to do
        question: Specific question for the human
        attempted_approaches: What approaches you've already tried

    Returns:
        Request ID to check for response later

    Example:
        request_human_guidance(
            thread_id="abc123",
            context="Trying to log into LinkedIn",
            question="I cannot find the login button using DOM selectors or visual detection. Where should I look?",
            attempted_approaches="Tried: snapshot with -i flag, searched for 'Sign In', checked top navigation"
        )
    """
    full_context = f"{context}\n\nAttempted approaches:\n{attempted_approaches}"

    request = _create_request(
        request_type="guidance",
        thread_id=thread_id,
        context=full_context,
        question=question,
        options=None
    )

    return f"Created guidance request: {request['id']}. Human will respond soon. You can continue with other tasks or wait for response."


@tool
def request_credentials(thread_id: str, service: str, credential_types: str, reason: str) -> str:
    """Request login credentials from a human.

    Use this tool when you need credentials to log into a service.
    NEVER attempt to guess or generate credentials.

    Args:
        thread_id: Thread identifier for this session
        service: Name of the service (e.g., "LinkedIn", "Gmail", "GitHub")
        credential_types: What credentials are needed (e.g., "username and password", "API key", "2FA code")
        reason: Why you need these credentials

    Returns:
        Request ID to check for response later

    Example:
        request_credentials(
            thread_id="abc123",
            service="LinkedIn",
            credential_types="username and password",
            reason="User asked me to check their LinkedIn messages"
        )
    """
    question = f"Please provide {credential_types} for {service}"
    context = f"Service: {service}\nNeeded: {credential_types}\nReason: {reason}"

    request = _create_request(
        request_type="credentials",
        thread_id=thread_id,
        context=context,
        question=question,
        options=None
    )

    return f"Created credentials request: {request['id']}. Waiting for human to provide credentials."


@tool
def request_confirmation(thread_id: str, action: str, risks: str, alternatives: str = "None") -> str:
    """Request confirmation from human before taking a potentially risky action.

    Use this tool before:
    - Submitting forms with financial information
    - Deleting or modifying important data
    - Performing actions that cannot be undone
    - Actions with security or privacy implications

    Args:
        thread_id: Thread identifier for this session
        action: Describe the action you want to take
        risks: Potential risks or consequences
        alternatives: Alternative approaches (if any)

    Returns:
        Request ID to check for response later

    Example:
        request_confirmation(
            thread_id="abc123",
            action="Submit payment form with $500 amount",
            risks="This will charge the credit card on file",
            alternatives="Could save as draft instead"
        )
    """
    question = f"Should I proceed with: {action}"
    context = f"Action: {action}\n\nRisks:\n{risks}\n\nAlternatives:\n{alternatives}"

    request = _create_request(
        request_type="confirmation",
        thread_id=thread_id,
        context=context,
        question=question,
        options=["Proceed", "Cancel", "Suggest alternative"]
    )

    return f"Created confirmation request: {request['id']}. Waiting for human approval."


@tool
def check_human_response(thread_id: str, request_id: str) -> str:
    """Check if a human has responded to a previous request.

    Args:
        thread_id: Thread identifier for this session
        request_id: ID of the request to check

    Returns:
        Status and response (if available)

    Example:
        check_human_response(
            thread_id="abc123",
            request_id="abc123_guidance_1"
        )
    """
    request = get_request(request_id)

    if not request:
        return f"Request {request_id} not found"

    if request["thread_id"] != thread_id:
        return f"Request {request_id} belongs to a different thread"

    if request["status"] == "pending":
        return f"Request {request_id} is still pending. Human has not responded yet."

    if request["status"] == "completed":
        response = request["response"]
        request_type = request["type"]

        if request_type == "credentials":
            # Format credentials response
            if isinstance(response, dict):
                creds_info = "\n".join([f"- {k}: {v}" for k, v in response.items()])
                return f"Credentials received:\n{creds_info}"
            return f"Credentials received: {response}"

        elif request_type == "confirmation":
            return f"Confirmation response: {response}"

        elif request_type == "guidance":
            return f"Guidance received: {response}"

    return f"Request {request_id} has status: {request['status']}"


# Tools list for export
HUMAN_LOOP_TOOLS = [
    request_human_guidance,
    request_credentials,
    request_confirmation,
    check_human_response,
]
