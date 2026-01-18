"""Browser automation tools using agent-browser CLI."""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from browser_use_agent.utils import stream_manager

# Global storage for browser session state (thread-safe using dict keyed by thread_id)
_browser_sessions: Dict[str, Dict[str, Any]] = {}


def _run_browser_command(
    thread_id: str,
    command: List[str],
    set_stream_port: bool = False
) -> Dict[str, Any]:
    """Execute agent-browser CLI command with proper session and streaming setup.
    
    Args:
        thread_id: Unique thread identifier for session isolation
        command: Command parts to execute (without agent-browser prefix)
        set_stream_port: Whether to set AGENT_BROWSER_STREAM_PORT env var
        
    Returns:
        Dict with command output and status
    """
    # Prepare command with session
    full_command = ["agent-browser", "--session", thread_id] + command
    
    # Set up environment
    env = os.environ.copy()
    if set_stream_port:
        port = stream_manager.get_port_for_thread(thread_id)
        env["AGENT_BROWSER_STREAM_PORT"] = str(port)
    
    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Command timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }


def _update_browser_session(thread_id: str, is_active: bool = True):
    """Update browser session state for the thread.
    
    Args:
        thread_id: Thread identifier
        is_active: Whether the session is active
    """
    stream_url = stream_manager.get_stream_url(thread_id) if is_active else None
    _browser_sessions[thread_id] = {
        "sessionId": thread_id,
        "streamUrl": stream_url,
        "isActive": is_active
    }


def get_browser_session(thread_id: str) -> Optional[Dict[str, Any]]:
    """Get browser session state for a thread.
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        Browser session dict or None
    """
    return _browser_sessions.get(thread_id)


@tool
def browser_navigate(url: str, thread_id: str) -> str:
    """Navigate browser to a URL and start streaming.
    
    Args:
        url: The URL to navigate to
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Navigation result and stream URL
    """
    # This is usually the first command, so set stream port
    result = _run_browser_command(
        thread_id,
        ["open", url],
        set_stream_port=True
    )
    
    if result["success"]:
        stream_url = stream_manager.get_stream_url(thread_id)
        # Mark session as active
        _update_browser_session(thread_id, is_active=True)
        return f"Successfully navigated to {url}. Browser stream available at {stream_url}"
    else:
        return f"Failed to navigate: {result['error']}"


@tool
def browser_snapshot(thread_id: str, interactive_only: bool = True) -> str:
    """Get page snapshot with accessibility tree and element references.
    
    Args:
        thread_id: Thread identifier for session isolation
        interactive_only: If True, only return interactive elements
        
    Returns:
        str: JSON snapshot with element refs (@e1, @e2, etc.)
    """
    command = ["snapshot", "--json"]
    if interactive_only:
        command.append("-i")
    
    result = _run_browser_command(thread_id, command)
    
    if result["success"]:
        try:
            # Parse JSON to pretty print
            snapshot_data = json.loads(result["output"])
            return json.dumps(snapshot_data, indent=2)
        except json.JSONDecodeError:
            return result["output"]
    else:
        return f"Failed to get snapshot: {result['error']}"


@tool
def browser_click(ref: str, thread_id: str) -> str:
    """Click an element by its reference from snapshot.
    
    Args:
        ref: Element reference (e.g., "@e1", "@e2")
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Click result
    """
    result = _run_browser_command(thread_id, ["click", ref])
    
    if result["success"]:
        return f"Successfully clicked {ref}"
    else:
        return f"Failed to click {ref}: {result['error']}"


@tool
def browser_fill(ref: str, text: str, thread_id: str) -> str:
    """Fill an input element with text (clears first, then types).
    
    Args:
        ref: Element reference (e.g., "@e1")
        text: Text to fill into the element
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Fill result
    """
    result = _run_browser_command(thread_id, ["fill", ref, text])
    
    if result["success"]:
        return f"Successfully filled {ref} with text"
    else:
        return f"Failed to fill {ref}: {result['error']}"


@tool
def browser_type(ref: str, text: str, thread_id: str) -> str:
    """Type text into an element without clearing it first.
    
    Args:
        ref: Element reference (e.g., "@e1")
        text: Text to type
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Type result
    """
    result = _run_browser_command(thread_id, ["type", ref, text])
    
    if result["success"]:
        return f"Successfully typed into {ref}"
    else:
        return f"Failed to type into {ref}: {result['error']}"


@tool
def browser_press_key(key: str, thread_id: str) -> str:
    """Press a keyboard key (e.g., "Enter", "Escape", "Tab").
    
    Args:
        key: Key to press
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Key press result
    """
    result = _run_browser_command(thread_id, ["press", key])
    
    if result["success"]:
        return f"Successfully pressed {key}"
    else:
        return f"Failed to press {key}: {result['error']}"


@tool
def browser_get_info(info_type: str, thread_id: str, ref: Optional[str] = None) -> str:
    """Get information from the browser or an element.
    
    Args:
        info_type: Type of info (text, html, value, attr, title, url, count)
        thread_id: Thread identifier for session isolation
        ref: Optional element reference (required for text, html, value, attr)
        
    Returns:
        str: Requested information
    """
    command = ["get", info_type]
    if ref:
        command.append(ref)
    
    result = _run_browser_command(thread_id, command)
    
    if result["success"]:
        return result["output"].strip()
    else:
        return f"Failed to get {info_type}: {result['error']}"


@tool
def browser_screenshot(thread_id: str, filename: Optional[str] = None) -> str:
    """Take a screenshot of the current page.
    
    Args:
        thread_id: Thread identifier for session isolation
        filename: Optional filename to save to (if None, returns base64)
        
    Returns:
        str: Screenshot result or base64 data
    """
    command = ["screenshot"]
    if filename:
        command.append(filename)
    else:
        command.append("--json")
    
    result = _run_browser_command(thread_id, command)
    
    if result["success"]:
        if filename:
            return f"Screenshot saved to {filename}"
        else:
            try:
                data = json.loads(result["output"])
                return f"Screenshot captured (base64): {data.get('data', '')[:100]}..."
            except json.JSONDecodeError:
                return result["output"]
    else:
        return f"Failed to take screenshot: {result['error']}"


@tool
def browser_is_visible(ref: str, thread_id: str) -> str:
    """Check if an element is visible.
    
    Args:
        ref: Element reference
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: "true" or "false"
    """
    result = _run_browser_command(thread_id, ["is", "visible", ref])
    return result["output"].strip() if result["success"] else "false"


@tool
def browser_is_enabled(ref: str, thread_id: str) -> str:
    """Check if an element is enabled.
    
    Args:
        ref: Element reference
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: "true" or "false"
    """
    result = _run_browser_command(thread_id, ["is", "enabled", ref])
    return result["output"].strip() if result["success"] else "false"


@tool
def browser_wait(thread_id: str, condition: str, value: str) -> str:
    """Wait for a condition to be met.
    
    Args:
        thread_id: Thread identifier for session isolation
        condition: Condition type (text, url, load, etc.)
        value: Value to wait for
        
    Returns:
        str: Wait result
    """
    command = ["wait", f"--{condition}", value]
    result = _run_browser_command(thread_id, command)
    
    if result["success"]:
        return f"Condition met: {condition} = {value}"
    else:
        return f"Wait timeout: {result['error']}"


@tool
def browser_close(thread_id: str) -> str:
    """Close the browser session and stop streaming.
    
    Args:
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Close result
    """
    result = _run_browser_command(thread_id, ["close"])
    
    # Release the stream port
    stream_manager.release_port(thread_id)
    
    # Mark session as inactive
    _update_browser_session(thread_id, is_active=False)
    
    if result["success"]:
        return "Browser session closed successfully"
    else:
        return f"Failed to close browser: {result['error']}"


# Export all tools
BROWSER_TOOLS = [
    browser_navigate,
    browser_snapshot,
    browser_click,
    browser_fill,
    browser_type,
    browser_press_key,
    browser_get_info,
    browser_screenshot,
    browser_is_visible,
    browser_is_enabled,
    browser_wait,
    browser_close,
]
