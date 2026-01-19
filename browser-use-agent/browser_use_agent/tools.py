"""Browser automation tools using agent-browser CLI."""

import json
import os
import socket
import subprocess
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from browser_use_agent.utils import stream_manager

# Global storage for browser session state (thread-safe using dict keyed by thread_id)
_browser_sessions: Dict[str, Dict[str, Any]] = {}

# Timeout configuration (in seconds)
BROWSER_TIMEOUT_SECONDS = 300  # 5 minutes

# Background cleanup thread
_cleanup_thread: Optional[threading.Thread] = None
_cleanup_running = False


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


def _update_browser_session(thread_id: str, is_active: bool = True, update_last_activity: bool = True):
    """Update browser session state for the thread.
    
    Args:
        thread_id: Thread identifier
        is_active: Whether the session is active
        update_last_activity: Whether to update the last activity timestamp
    """
    stream_url = stream_manager.get_stream_url(thread_id) if is_active else None
    
    session_data = {
        "sessionId": thread_id,
        "streamUrl": stream_url,
        "isActive": is_active
    }
    
    if update_last_activity and is_active:
        session_data["lastActivity"] = datetime.now()
    elif thread_id in _browser_sessions and "lastActivity" in _browser_sessions[thread_id]:
        # Preserve existing last activity if not updating
        session_data["lastActivity"] = _browser_sessions[thread_id]["lastActivity"]
    
    _browser_sessions[thread_id] = session_data


def get_browser_session(thread_id: str) -> Optional[Dict[str, Any]]:
    """Get browser session state for a thread.
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        Browser session dict or None (without lastActivity timestamp)
    """
    session = _browser_sessions.get(thread_id)
    if session:
        # Return copy without lastActivity (internal field)
        return {
            "sessionId": session["sessionId"],
            "streamUrl": session["streamUrl"],
            "isActive": session["isActive"]
        }
    return None


def _cleanup_inactive_sessions():
    """Background task to close inactive browser sessions."""
    global _cleanup_running
    _cleanup_running = True
    
    print("[Browser Timeout] Cleanup thread started")
    
    while _cleanup_running:
        try:
            now = datetime.now()
            inactive_threads = []
            
            # Find inactive sessions
            for thread_id, session in list(_browser_sessions.items()):
                if not session.get("isActive", False):
                    continue
                    
                last_activity = session.get("lastActivity")
                if last_activity:
                    inactive_duration = now - last_activity
                    if inactive_duration.total_seconds() > BROWSER_TIMEOUT_SECONDS:
                        inactive_threads.append(thread_id)
                        print(f"[Browser Timeout] Session {thread_id} inactive for {inactive_duration.total_seconds():.0f}s")
            
            # Close inactive sessions
            for thread_id in inactive_threads:
                print(f"[Browser Timeout] Auto-closing session {thread_id}")
                result = _run_browser_command(thread_id, ["close"])
                stream_manager.release_port(thread_id)
                _update_browser_session(thread_id, is_active=False, update_last_activity=False)
                
                if result["success"]:
                    print(f"[Browser Timeout] Session {thread_id} closed successfully")
                else:
                    print(f"[Browser Timeout] Failed to close session {thread_id}: {result.get('error')}")
            
            # Sleep for 10 seconds before next check
            time.sleep(10)
            
        except Exception as e:
            print(f"[Browser Timeout] Error in cleanup thread: {e}")
            time.sleep(10)
    
    print("[Browser Timeout] Cleanup thread stopped")


def _start_cleanup_thread():
    """Start the background cleanup thread if not already running."""
    global _cleanup_thread, _cleanup_running
    
    if _cleanup_thread is None or not _cleanup_thread.is_alive():
        _cleanup_thread = threading.Thread(target=_cleanup_inactive_sessions, daemon=True)
        _cleanup_thread.start()
        print(f"[Browser Timeout] Started automatic session cleanup (timeout: {BROWSER_TIMEOUT_SECONDS}s)")


def _stop_cleanup_thread():
    """Stop the background cleanup thread."""
    global _cleanup_running
    _cleanup_running = False


def _wait_for_stream_ready(port: int, timeout_seconds: int = 5, check_interval: float = 0.1) -> bool:
    """Wait for WebSocket stream server to be ready.
    
    Args:
        port: Port number to check
        timeout_seconds: Maximum time to wait
        check_interval: Time between checks in seconds
        
    Returns:
        bool: True if stream is ready, False if timeout
    """
    start_time = time.time()
    attempts = 0
    
    while time.time() - start_time < timeout_seconds:
        attempts += 1
        try:
            # Try to connect to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is open and accepting connections
                elapsed = time.time() - start_time
                print(f"[Stream Ready] Port {port} ready after {elapsed:.2f}s ({attempts} attempts)")
                return True
        except Exception as e:
            pass
        
        time.sleep(check_interval)
    
    print(f"[Stream Timeout] Port {port} not ready after {timeout_seconds}s")
    return False


@tool
def browser_navigate(url: str, thread_id: str) -> str:
    """Navigate browser to a URL and start streaming.
    
    Args:
        url: The URL to navigate to
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Navigation result and stream URL
    """
    # Start cleanup thread if not running
    _start_cleanup_thread()
    
    # This is usually the first command, so set stream port
    result = _run_browser_command(
        thread_id,
        ["open", url],
        set_stream_port=True
    )
    
    if result["success"]:
        stream_url = stream_manager.get_stream_url(thread_id)
        
        # Wait for stream server to be ready before returning
        port = stream_manager.get_port_for_thread(thread_id)
        stream_ready = _wait_for_stream_ready(port, timeout_seconds=5)
        
        if not stream_ready:
            print(f"[Browser Navigate] Warning: Stream server not ready within timeout, but navigation succeeded")
        
        # Mark session as active and update last activity
        _update_browser_session(thread_id, is_active=True, update_last_activity=True)
        print(f"[Browser Navigate] Session {thread_id[:8]}... → Stream: {stream_url}")
        return f"Successfully navigated to {url}. Browser stream available at {stream_url}"
    else:
        return f"Failed to navigate: {result['error']}"


def _update_activity(thread_id: str):
    """Update last activity timestamp for a browser session."""
    if thread_id in _browser_sessions and _browser_sessions[thread_id].get("isActive"):
        _browser_sessions[thread_id]["lastActivity"] = datetime.now()


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
    _update_activity(thread_id)
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
    _update_activity(thread_id)
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
    _update_activity(thread_id)
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
    _update_activity(thread_id)
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
def browser_set_viewport(width: int, height: int, thread_id: str) -> str:
    """Set browser viewport size to mimic real desktop/mobile devices.
    
    CRITICAL for avoiding bot detection - headless browsers have unusual viewport sizes.
    Recommended: 1920x1080 for desktop, 390x844 for mobile.
    
    Args:
        width: Viewport width in pixels (e.g., 1920, 1366, 1280)
        height: Viewport height in pixels (e.g., 1080, 768, 720)
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Success or error message
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["set", "viewport", str(width), str(height)])
    
    if result["success"]:
        return f"Successfully set viewport to {width}x{height}"
    else:
        return f"Failed to set viewport: {result['error']}"


@tool
def browser_set_headers(headers_json: str, thread_id: str) -> str:
    """Set custom HTTP headers including User-Agent.
    
    CRITICAL for bypassing user-agent detection. Most sites check for realistic Chrome/Firefox user agents.
    
    Args:
        headers_json: JSON string of headers 
                     e.g., '{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}'
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Success or error message
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["set", "headers", headers_json])
    
    if result["success"]:
        return "Successfully set custom headers"
    else:
        return f"Failed to set headers: {result['error']}"


@tool
def browser_cookies_get(thread_id: str) -> str:
    """Get all cookies from current page. Save these to restore sessions later and avoid re-triggering CAPTCHA.
    
    Use this after successful interactions to save session state.
    
    Args:
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: JSON array of cookie objects
    """
    result = _run_browser_command(thread_id, ["cookies", "get", "--json"])
    
    if result["success"]:
        return result["output"]
    else:
        return f"Failed to get cookies: {result['error']}"


@tool
def browser_cookies_set(cookies_json: str, thread_id: str) -> str:
    """Set cookies for the current domain. Use to restore sessions and avoid repeated CAPTCHAs.
    
    CRITICAL for session persistence. Once CAPTCHA is solved, save cookies and reuse them.
    
    Args:
        cookies_json: JSON string of cookie array 
                     e.g., '[{"name":"session","value":"abc123","domain":".example.com"}]'
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Success or error message
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["cookies", "set", cookies_json])
    
    if result["success"]:
        return "Successfully set cookies"
    else:
        return f"Failed to set cookies: {result['error']}"


@tool
def browser_wait_time(milliseconds: int, thread_id: str) -> str:
    """Wait for specified time. Add human-like delays between actions.
    
    IMPORTANT: Bot detection often checks action speed. Add 500-2000ms delays between major actions.
    
    Args:
        milliseconds: Time to wait in ms (recommend 500-2000ms between actions)
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Success message
    """
    result = _run_browser_command(thread_id, ["wait", str(milliseconds)])
    
    if result["success"]:
        return f"Waited {milliseconds}ms"
    else:
        return f"Wait failed: {result['error']}"


@tool
def browser_hover(ref: str, thread_id: str) -> str:
    """Hover over an element before clicking (human-like behavior).
    
    More human-like than direct clicks. Some sites track mouse movement patterns.
    
    Args:
        ref: Element reference from snapshot (e.g., "@e1")
        thread_id: Thread identifier for session isolation
        
    Returns:
        str: Success or error message
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["hover", ref])
    
    if result["success"]:
        return f"Successfully hovered over {ref}"
    else:
        return f"Failed to hover: {result['error']}"


@tool
def browser_back(thread_id: str) -> str:
    """Go back to the previous page in browser history.

    Args:
        thread_id: Thread identifier for session isolation

    Returns:
        str: Navigation result
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["back"])

    if result["success"]:
        return "Successfully navigated back in browser history"
    else:
        return f"Failed to navigate back: {result['error']}"


@tool
def browser_forward(thread_id: str) -> str:
    """Go forward to the next page in browser history.

    Args:
        thread_id: Thread identifier for session isolation

    Returns:
        str: Navigation result
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["forward"])

    if result["success"]:
        return "Successfully navigated forward in browser history"
    else:
        return f"Failed to navigate forward: {result['error']}"


@tool
def browser_reload(thread_id: str) -> str:
    """Reload the current page.

    Args:
        thread_id: Thread identifier for session isolation

    Returns:
        str: Reload result
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["reload"])

    if result["success"]:
        return "Successfully reloaded the page"
    else:
        return f"Failed to reload page: {result['error']}"


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
    browser_set_viewport,
    browser_set_headers,
    browser_cookies_get,
    browser_cookies_set,
    browser_wait_time,
    browser_hover,
    browser_back,
    browser_forward,
    browser_reload,
    browser_close,
]
