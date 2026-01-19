"""Browser automation tools using agent-browser CLI.

This module provides only the essential core commands from agent-browser.
For advanced commands, the agent can use the Bash tool to execute
agent-browser commands directly after consulting agent-browser --help.
"""

import json
import os
import socket
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from langchain.tools import tool
from browser_use_agent.utils import stream_manager
from browser_use_agent.configuration import Config

# Maximum output size before saving to filesystem (in characters)
MAX_OUTPUT_SIZE = 1000


def _save_large_output(content: str, thread_id: str, output_type: str) -> str:
    """Save large output to filesystem and return a reference.

    Args:
        content: The large content to save
        thread_id: Thread identifier for organizing files
        output_type: Type of output (e.g., 'snapshot', 'console')

    Returns:
        Message with file path reference
    """
    from browser_use_agent.storage.config import StorageConfig

    # Create artifacts directory
    agent_dir = StorageConfig.get_agent_dir()
    artifacts_dir = agent_dir / "artifacts" / "tool_outputs"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_type}_{thread_id[:8]}_{timestamp}.json"
    filepath = artifacts_dir / filename

    # Save content
    filepath.write_text(content)

    return str(filepath)


def _handle_output(content: str, thread_id: str, output_type: str) -> str:
    """Handle tool output - return directly if small, save to file if large.

    Args:
        content: The content to handle
        thread_id: Thread identifier
        output_type: Type of output for filename

    Returns:
        Content directly if small, or file reference if large
    """
    if len(content) <= MAX_OUTPUT_SIZE:
        return content

    filepath = _save_large_output(content, thread_id, output_type)
    # Return file reference only
    return f"[Output saved to file: {filepath}]\nUse read_file tool to access full content."

# Global storage for browser session state (thread-safe using dict keyed by thread_id)
_browser_sessions: Dict[str, Dict[str, Any]] = {}

# Timeout configuration (in seconds)
BROWSER_TIMEOUT_SECONDS = 300  # 5 minutes

# Background cleanup thread
_cleanup_thread: Optional[threading.Thread] = None
_cleanup_running = False

# Daemon management
_daemon_cleanup_lock = threading.Lock()
_last_daemon_cleanup: Optional[datetime] = None
DAEMON_CLEANUP_INTERVAL_SECONDS = 60  # Only cleanup once per minute max


def _cleanup_stale_daemons(force: bool = False) -> None:
    """Clean up stale agent-browser daemon processes.

    This helps prevent "Daemon failed to start" errors caused by:
    - Orphaned daemon processes from previous sessions
    - Resource contention from too many running daemons
    - Socket file conflicts

    Args:
        force: If True, bypass the cleanup interval check
    """
    global _last_daemon_cleanup

    with _daemon_cleanup_lock:
        # Rate limit cleanup to avoid overhead
        if not force and _last_daemon_cleanup:
            elapsed = (datetime.now() - _last_daemon_cleanup).total_seconds()
            if elapsed < DAEMON_CLEANUP_INTERVAL_SECONDS:
                return

        try:
            # Find all agent-browser daemon processes
            result = subprocess.run(
                ["pgrep", "-f", "agent-browser.*daemon"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                daemon_count = len(pids)

                # If there are many daemons, clean up the oldest ones
                # Keep at most 3 daemon processes
                if daemon_count > 3:
                    print(f"[Daemon Cleanup] Found {daemon_count} daemon processes, cleaning up excess...")

                    # Get process info with start times
                    ps_result = subprocess.run(
                        ["ps", "-o", "pid,etime", "-p", ",".join(pids)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if ps_result.returncode == 0:
                        lines = ps_result.stdout.strip().split('\n')[1:]  # Skip header
                        processes = []
                        for line in lines:
                            parts = line.split()
                            if len(parts) >= 2:
                                pid = parts[0]
                                etime = parts[1]
                                processes.append((pid, etime))

                        # Sort by elapsed time (oldest first) and kill excess
                        # etime format: [[dd-]hh:]mm:ss
                        processes_to_kill = processes[:-3] if len(processes) > 3 else []

                        for pid, etime in processes_to_kill:
                            try:
                                subprocess.run(
                                    ["kill", "-TERM", pid],
                                    capture_output=True,
                                    timeout=2
                                )
                                print(f"[Daemon Cleanup] Terminated stale daemon PID {pid} (uptime: {etime})")
                            except Exception as e:
                                print(f"[Daemon Cleanup] Failed to kill PID {pid}: {e}")

                        if processes_to_kill:
                            # Give processes time to terminate gracefully
                            time.sleep(0.5)

            _last_daemon_cleanup = datetime.now()

        except subprocess.TimeoutExpired:
            print("[Daemon Cleanup] Timeout while checking daemon processes")
        except FileNotFoundError:
            # pgrep not available on this system
            pass
        except Exception as e:
            print(f"[Daemon Cleanup] Error during cleanup: {e}")


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
    # Prepare command - use CDP if configured, otherwise use session-based isolation
    if Config.USE_CDP:
        full_command = ["agent-browser", "--cdp", str(Config.CDP_PORT)] + command
    else:
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
        except Exception:
            pass

        time.sleep(check_interval)

    print(f"[Stream Timeout] Port {port} not ready after {timeout_seconds}s")
    return False


def _update_activity(thread_id: str):
    """Update last activity timestamp for a browser session."""
    if thread_id in _browser_sessions and _browser_sessions[thread_id].get("isActive"):
        _browser_sessions[thread_id]["lastActivity"] = datetime.now()


# ============================================================================
# Core Commands - agent-browser core commands
# ============================================================================

@tool
def browser_navigate(url: str, thread_id: str) -> str:
    """Navigate browser to a URL and start streaming.

    Args:
        url: The URL to navigate to
        thread_id: Thread identifier for session isolation

    Returns:
        Structured output with action, observation, next_step, filepath
    """
    from browser_use_agent.models import BrowserToolOutput

    # Start cleanup thread if not running
    _start_cleanup_thread()

    # Clean up stale daemon processes to prevent "Daemon failed to start" errors
    _cleanup_stale_daemons()

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

        # Save full output to file
        filepath = _save_large_output(
            f"Navigated to {url}\nStream URL: {stream_url}\nStream ready: {stream_ready}",
            thread_id,
            "navigate"
        )

        output = BrowserToolOutput(
            action=f"Navigated to {url}",
            observation=f"Page loaded. Browser stream available at {stream_url}",
            next_step="Take browser_snapshot to see available elements and their @refs",
            filepath=filepath
        )
        return output.to_string()
    else:
        return f"Failed to navigate: {result['error']}"


@tool
def browser_snapshot(thread_id: str, interactive_only: bool = True) -> str:
    """Get page snapshot with accessibility tree and element references.

    Args:
        thread_id: Thread identifier for session isolation
        interactive_only: If True, only return interactive elements

    Returns:
        Structured output with action, observation, next_step, filepath
    """
    from browser_use_agent.models import BrowserToolOutput

    command = ["snapshot", "--json"]
    if interactive_only:
        command.append("-i")

    result = _run_browser_command(thread_id, command)

    if result["success"]:
        try:
            snapshot_data = json.loads(result["output"])
            output_str = json.dumps(snapshot_data, indent=2)

            # Count elements
            element_count = len(snapshot_data) if isinstance(snapshot_data, list) else "unknown"

            # Save full snapshot to file
            filepath = _save_large_output(output_str, thread_id, "snapshot")

            output = BrowserToolOutput(
                action="Captured DOM snapshot",
                observation=f"Found {element_count} interactive elements. Elements have @refs like @e1, @e2.",
                next_step="Use @refs to interact: browser_click(@e1), browser_fill(@e2, 'text')",
                filepath=filepath
            )
            return output.to_string()
        except json.JSONDecodeError:
            filepath = _save_large_output(result["output"], thread_id, "snapshot")
            output = BrowserToolOutput(
                action="Captured DOM snapshot",
                observation="Snapshot captured but not in JSON format",
                next_step="Use read_file to examine full snapshot content",
                filepath=filepath
            )
            return output.to_string()
    else:
        return f"Failed to get snapshot: {result['error']}"


@tool
def browser_click(ref: str, thread_id: str) -> str:
    """Click an element by its reference from snapshot.

    Args:
        ref: Element reference (e.g., "@e1", "@e2")
        thread_id: Thread identifier for session isolation

    Returns:
        Structured output with action, observation, next_step, filepath
    """
    from browser_use_agent.models import BrowserToolOutput

    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["click", ref])

    filepath = _save_large_output(
        result["output"] if result["success"] else result["error"],
        thread_id,
        "click"
    )

    if result["success"]:
        output = BrowserToolOutput(
            action=f"Clicked {ref}",
            observation="Click successful. Page state may have changed.",
            next_step="Take browser_snapshot to see updated elements (refs may have changed)",
            filepath=filepath
        )
        return output.to_string()
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
        Fill result
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
        Type result
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
        Key press result
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["press", key])

    if result["success"]:
        return f"Successfully pressed {key}"
    else:
        return f"Failed to press {key}: {result['error']}"


@tool
def browser_screenshot(thread_id: str, filename: str = None) -> str:
    """Take a screenshot of the current page.

    Args:
        thread_id: Thread identifier for session isolation
        filename: Optional filename (without path). Screenshots are saved to .browser-agent/artifacts/screenshots/

    Returns:
        Screenshot result with file path
    """
    import os
    from datetime import datetime

    # Ensure screenshots directory exists
    screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".browser-agent", "artifacts", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"

    # Ensure .png extension
    if not filename.endswith('.png'):
        filename = f"{filename}.png"

    # Full path for screenshot
    screenshot_path = os.path.join(screenshots_dir, filename)

    command = ["screenshot", screenshot_path]
    result = _run_browser_command(thread_id, command)

    if result["success"]:
        return f"Screenshot saved to {screenshot_path}"
    else:
        return f"Failed to take screenshot: {result['error']}"


@tool
def browser_scroll(
    direction: str,
    thread_id: str,
    amount: int = 500
) -> str:
    """Scroll the page to load dynamic content or reach elements.

    Args:
        direction: Scroll direction - 'up', 'down', 'top', 'bottom'
        thread_id: Thread identifier for session isolation
        amount: Pixels to scroll (ignored for 'top'/'bottom')

    Returns:
        Structured output with action, observation, next_step, filepath
    """
    from browser_use_agent.models import BrowserToolOutput

    _update_activity(thread_id)

    # Map direction to agent-browser scroll command
    if direction == "top":
        cmd = ["eval", "window.scrollTo(0, 0)"]
    elif direction == "bottom":
        cmd = ["eval", "window.scrollTo(0, document.body.scrollHeight)"]
    elif direction == "down":
        cmd = ["eval", f"window.scrollBy(0, {amount})"]
    elif direction == "up":
        cmd = ["eval", f"window.scrollBy(0, -{amount})"]
    else:
        return f"Invalid direction: {direction}. Use: up, down, top, bottom"

    result = _run_browser_command(thread_id, cmd)

    if result["success"]:
        # Save full output to file
        filepath = _save_large_output(
            result["output"] or f"Scrolled {direction}",
            thread_id,
            "scroll"
        )

        output = BrowserToolOutput(
            action=f"Scrolled {direction}" + (f" {amount}px" if direction in ["up", "down"] else ""),
            observation="Page scrolled successfully. New content may have loaded.",
            next_step="Take browser_snapshot to see newly visible elements",
            filepath=filepath
        )
        return output.to_string()
    else:
        return f"Failed to scroll: {result['error']}"


@tool
def browser_close(thread_id: str) -> str:
    """Close the browser session and stop streaming.

    Args:
        thread_id: Thread identifier for session isolation

    Returns:
        Close result
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


# ============================================================================
# Navigation Commands
# ============================================================================

@tool
def browser_back(thread_id: str) -> str:
    """Go back to the previous page in browser history.

    Args:
        thread_id: Thread identifier for session isolation

    Returns:
        Navigation result
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
        Navigation result
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
        Reload result
    """
    _update_activity(thread_id)
    result = _run_browser_command(thread_id, ["reload"])

    if result["success"]:
        return "Successfully reloaded the page"
    else:
        return f"Failed to reload page: {result['error']}"


# ============================================================================
# Get Info Commands
# ============================================================================

@tool
def browser_get_info(info_type: str, thread_id: str, ref: Optional[str] = None) -> str:
    """Get information from the browser or an element.

    Args:
        info_type: Type of info (text, html, value, attr, title, url, count)
        thread_id: Thread identifier for session isolation
        ref: Optional element reference (required for text, html, value, attr)

    Returns:
        Requested information.
        If output is large (>1000 chars), saves to file and returns reference.
    """
    command = ["get", info_type]
    if ref:
        command.append(ref)

    result = _run_browser_command(thread_id, command)

    if result["success"]:
        output = result["output"].strip()
        return _handle_output(output, thread_id, f"get_{info_type}")
    else:
        return f"Failed to get {info_type}: {result['error']}"


# ============================================================================
# Debug Commands (console)
# ============================================================================

@tool
def browser_console(thread_id: str) -> str:
    """Get browser console logs (errors, warnings, logs).

    Args:
        thread_id: Thread identifier for session isolation

    Returns:
        Console output or error message.
        If output is large (>1000 chars), saves to file and returns reference.
    """
    result = _run_browser_command(thread_id, ["console"])
    if result["success"]:
        output = f"Console logs:\n{result['output']}"
        return _handle_output(output, thread_id, "console")
    return f"✗ Failed to get console logs: {result['error']}"


# Import human-in-the-loop tools
from browser_use_agent.human_loop import HUMAN_LOOP_TOOLS

# Import reflection tools
from browser_use_agent.reflection import REFLECTION_TOOLS

# Export all tools
BROWSER_TOOLS = [
    # Core commands
    browser_navigate,
    browser_snapshot,
    browser_click,
    browser_fill,
    browser_type,
    browser_press_key,
    browser_screenshot,
    browser_scroll,
    browser_close,
    # Navigation
    browser_back,
    browser_forward,
    browser_reload,
    # Get info
    browser_get_info,
    # Debug
    browser_console,
    # Human-in-the-loop tools
    *HUMAN_LOOP_TOOLS,
    # Reflection tools
    *REFLECTION_TOOLS,
]
