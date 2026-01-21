"""Bash execution tool with mixed security model.

Safe commands run automatically, others require human approval.
"""

import re
import subprocess
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool
from langgraph.types import interrupt
from browser_use_agent.storage.config import StorageConfig


def _get_default_working_dir() -> str:
    """Get the default working directory (.browser-agent/).

    All bash commands run relative to .browser-agent/ by default,
    matching the FilesystemBackend root used by DeepAgents.
    """
    agent_dir = StorageConfig.get_agent_dir()
    return str(agent_dir)


def _resolve_working_dir(working_dir: Optional[str]) -> str:
    """Resolve working directory path relative to .browser-agent/.

    Handles paths like:
    - /artifacts/file_outputs -> .browser-agent/artifacts/file_outputs
    - artifacts/file_outputs -> .browser-agent/artifacts/file_outputs
    - None -> .browser-agent/ (default root)
    """
    # Get .browser-agent/ directory as base
    agent_dir = StorageConfig.get_agent_dir()

    if working_dir is None:
        return str(agent_dir)

    # Strip leading slash and resolve relative to .browser-agent/
    clean_path = working_dir.lstrip("/")
    resolved = agent_dir / clean_path

    # Create directory if it doesn't exist
    if not resolved.exists():
        resolved.mkdir(parents=True, exist_ok=True)

    return str(resolved)


# Virtual path prefixes that should be converted to relative paths
VIRTUAL_PATH_PREFIXES = [
    "/artifacts",
    "/memory",
    "/skills",
    "/checkpoints",
    "/traces",
]


def _make_paths_relative(command: str) -> str:
    """Convert absolute virtual paths to relative paths.

    Since bash commands run with cwd=.browser-agent/, paths like
    /artifacts/file_outputs/script.py should become
    artifacts/file_outputs/script.py (relative to cwd).

    Args:
        command: The bash command with potential absolute virtual paths

    Returns:
        Command with virtual paths made relative
    """
    resolved_command = command
    for prefix in VIRTUAL_PATH_PREFIXES:
        # Replace /prefix with prefix (remove leading slash)
        if prefix in resolved_command:
            resolved_command = resolved_command.replace(prefix, prefix.lstrip("/"))

    return resolved_command

# Auto-approved command patterns (regex)
AUTO_APPROVED_PATTERNS = [
    r"^python\s+[\w\-_./]+\.py(\s+.*)?$",   # python script.py [args]
    r"^python3\s+[\w\-_./]+\.py(\s+.*)?$",  # python3 script.py [args]
    r"^python\s+--version$",                 # python --version
    r"^python3\s+--version$",                # python3 --version
    r"^node\s+[\w\-_./]+\.js(\s+.*)?$",     # node script.js [args]
    r"^pip\s+install\s+[\w\-_\[\]]+",       # pip install package[extras]
    r"^pip3\s+install\s+[\w\-_\[\]]+",      # pip3 install package[extras]
    r"^npm\s+install(\s+[\w\-_@/]+)?",      # npm install [package]
    r"^cat\s+[\w\-_./]+",                    # cat file
    r"^ls(\s+[\w\-_./-]*)?$",               # ls [dir]
    r"^head(\s+-n\s+\d+)?\s+[\w\-_./]+",    # head [-n N] file
    r"^tail(\s+-n\s+\d+)?\s+[\w\-_./]+",    # tail [-n N] file
    r"^pwd$",                                # pwd
    r"^echo\s+",                             # echo text
    r"^mkdir\s+-?p?\s+[\w\-_./]+",          # mkdir dir
    r"^wc(\s+-[lwc]+)?\s+[\w\-_./]+",       # wc [-lwc] file
]

# Always blocked patterns (regex)
BLOCKED_PATTERNS = [
    r"sudo",                           # No sudo
    r"rm\s+-rf\s+/",                  # No rm -rf /
    r"rm\s+-rf\s+~",                  # No rm -rf ~
    r">\s*/dev/",                     # No writing to /dev/
    r"mkfs",                          # No filesystem creation
    r"dd\s+if=",                      # No raw disk access
    r":\(\)\{",                       # No fork bombs
    r"chmod\s+777",                   # No 777 permissions
    r"curl.*\|\s*bash",              # No curl | bash
    r"wget.*\|\s*bash",              # No wget | bash
]


def is_command_auto_approved(command: str) -> bool:
    """Check if command matches auto-approved patterns."""
    command = command.strip()
    return any(re.match(pattern, command) for pattern in AUTO_APPROVED_PATTERNS)


def is_command_blocked(command: str) -> bool:
    """Check if command matches blocked patterns."""
    command = command.strip()
    return any(re.search(pattern, command) for pattern in BLOCKED_PATTERNS)


@tool
def bash_execute(
    command: str,
    thread_id: str,
    working_dir: Optional[str] = None,
    timeout: int = 300
) -> str:
    """Execute a bash command with safety controls.

    Safe commands (python/node scripts, pip/npm install, cat/ls) run automatically.
    Other commands require human approval via interrupt.
    Dangerous commands are blocked entirely.

    Args:
        command: The bash command to execute
        thread_id: Thread identifier for session context
        working_dir: Optional working directory (defaults to current directory)
        timeout: Command timeout in seconds (default: 300 = 5 minutes)

    Returns:
        Command output (stdout + stderr) or error message

    Examples:
        # Run a Python script (auto-approved)
        bash_execute("python generate_report.py", thread_id)

        # Install a package (auto-approved)
        bash_execute("pip install pandas", thread_id)

        # Run curl (requires approval)
        bash_execute("curl https://api.example.com/data", thread_id)
    """
    command = command.strip()

    # Check if command is blocked
    if is_command_blocked(command):
        return f"[BLOCKED] Command blocked for safety: {command}"

    # Check if command needs approval
    if not is_command_auto_approved(command):
        print(f"[Bash] Requesting approval for: {command}")

        # Use interrupt to request human approval
        response = interrupt({
            "type": "bash_approval",
            "thread_id": thread_id,
            "command": command,
            "question": f"Allow this command to run?",
        })

        if response != "approved":
            return f"[REJECTED] Command rejected by user: {command}"

        print(f"[Bash] Command approved: {command}")

    # Resolve working directory path (defaults to .browser-agent/)
    cwd = _resolve_working_dir(working_dir)

    # Convert absolute virtual paths to relative (e.g., /artifacts/ -> artifacts/)
    command = _make_paths_relative(command)

    # Execute command
    print(f"[Bash] Executing: {command} (cwd: {cwd})")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr

        if result.returncode != 0:
            output = f"[Exit code: {result.returncode}]\n{output}"

        return output if output else "(command completed with no output)"

    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Command timed out after {timeout} seconds: {command}"
    except Exception as e:
        return f"[ERROR] Failed to execute command: {str(e)}"


# Export for tools list
BASH_TOOLS = [bash_execute]
