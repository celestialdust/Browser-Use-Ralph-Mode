# Bash Tool for Code Execution Design

**Date:** 2026-01-20
**Status:** Approved
**Issue:** Agent can't execute code files to generate PDFs, process data, etc.

## Overview

Add a bash execution tool with mixed security model:
- Auto-approved: Safe commands (python scripts, npm/pip install, read-only operations)
- Approval required: Potentially dangerous commands
- Blocked: Dangerous commands (sudo, rm -rf /, etc.)

## Backend Implementation

**File:** `browser-use-agent/browser_use_agent/bash_tool.py` (new file)

```python
"""Bash execution tool with mixed security model.

Safe commands run automatically, others require human approval.
"""

import re
import subprocess
from typing import Optional
from langchain_core.tools import tool
from langgraph.types import interrupt

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

    # Execute command
    print(f"[Bash] Executing: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir,
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
```

**Integration in `tools.py`:**

```python
# Add import
from browser_use_agent.bash_tool import BASH_TOOLS

# Add to exports
BROWSER_TOOLS = [
    # ... existing tools ...
    *BASH_TOOLS,
]
```

**Note on DeepAgents file tools vs bash commands:**
DeepAgents provides separate LangChain tools for file operations (`read_file`, `write_file`, `edit_file`, `ls`) that the agent calls directly. These are **not bash commands** and don't go through `bash_execute`. The bash tool's auto-approved patterns (`cat`, `ls`, `head`, `tail`) are for cases where the agent needs shell-level file access (e.g., piping, complex file operations).

## Frontend Implementation

### Update HumanLoopInterrupt Component

**File:** `deep-agents-ui/src/app/components/HumanLoopInterrupt.tsx`

Add Terminal icon import and bash_approval case:

```typescript
import { HelpCircle, KeyRound, AlertTriangle, Terminal } from "lucide-react";

// Update props interface
interface HumanLoopInterruptProps {
  type: "guidance" | "credentials" | "confirmation" | "bash_approval";
  data: {
    // ... existing fields ...
    command?: string;  // For bash_approval
  };
  subagentName?: string;
  onRespond: (response: any) => void;
}

// Add bash_approval case before the final return null
if (type === "bash_approval") {
  return (
    <div className="border rounded-lg p-4 bg-orange-50 border-orange-200 dark:bg-orange-950 dark:border-orange-800">
      <div className="flex items-center gap-2 mb-2">
        <Terminal size={20} className="text-orange-600 dark:text-orange-400" />
        <h3 className="font-semibold text-orange-800 dark:text-orange-200">
          {subagentName ? `${subagentName} wants to run a command` : "Command approval needed"}
        </h3>
      </div>
      <pre className="bg-gray-900 text-green-400 p-3 rounded mt-3 overflow-x-auto text-sm font-mono">
        $ {data.command}
      </pre>
      <div className="flex gap-2 mt-4">
        <Button
          onClick={() => onRespond("approved")}
          className="bg-orange-600 hover:bg-orange-700"
        >
          Allow
        </Button>
        <Button
          variant="outline"
          onClick={() => onRespond("rejected")}
        >
          Deny
        </Button>
      </div>
    </div>
  );
}
```

### Update Interrupt Detection

**File:** `deep-agents-ui/src/app/components/ChatInterface.tsx`

```typescript
const humanLoopInterrupt = useMemo(() => {
  const value = interrupt?.value as any;
  if (!value?.type) return null;
  if (['guidance', 'credentials', 'confirmation', 'bash_approval'].includes(value.type)) {
    return value;
  }
  return null;
}, [interrupt]);
```

## Prompt Addition

**File:** `browser-use-agent/browser_use_agent/prompts.py`

Add to system prompt:

```
<bash_execution>
Use bash_execute tool to run code and scripts:
- Python scripts: bash_execute("python script.py", thread_id)
- Node scripts: bash_execute("node script.js", thread_id)
- Install packages: bash_execute("pip install package", thread_id)

**Auto-approved (no human confirmation needed):**
- python/python3 script execution
- node script execution
- pip/npm install
- Read-only: cat, ls, head, tail, pwd, wc
- mkdir

**Requires approval:**
- File modifications (rm, mv, cp)
- Network commands (curl, wget)
- Any command not in the auto-approved list

**Blocked (will not run):**
- sudo commands
- Destructive operations (rm -rf /, dd)
- Piped downloads (curl | bash)

**Workflow for generating files (PDF, reports):**
1. Write script to artifacts/file_outputs/generate_{name}.py
2. Run with bash_execute("python artifacts/file_outputs/generate_{name}.py", thread_id)
3. Script should save output to artifacts/file_outputs/
4. Return output file path to user
</bash_execution>
```

## Files to Create/Modify

**Create:**
1. `browser-use-agent/browser_use_agent/bash_tool.py` - New bash execution tool

**Modify:**
1. `browser-use-agent/browser_use_agent/tools.py` - Import and export BASH_TOOLS
2. `browser-use-agent/browser_use_agent/prompts.py` - Add bash_execution section
3. `deep-agents-ui/src/app/components/HumanLoopInterrupt.tsx` - Add bash_approval type
4. `deep-agents-ui/src/app/components/ChatInterface.tsx` - Update interrupt detection

## Security Considerations

1. **Sandboxing**: Commands run in the same process as the agent. Consider Docker isolation for production.
2. **Timeout**: 5-minute default timeout prevents runaway processes.
3. **Working directory**: Can be restricted to .browser-agent/ for additional safety.
4. **Audit log**: Consider logging all bash commands for review.

## Testing

1. Run auto-approved command:
   - `bash_execute("python --version", thread_id)` or `bash_execute("python script.py", thread_id)`
   - Should return output without approval prompt

2. Run command requiring approval:
   - `bash_execute("curl https://example.com", thread_id)`
   - Should show approval dialog in frontend
   - Allow → command runs
   - Deny → command rejected

3. Run blocked command:
   - `bash_execute("sudo rm -rf /", thread_id)`
   - Should return blocked message, no prompt

4. Generate a file:
   - Agent writes Python script to generate PDF
   - Agent runs script with bash_execute
   - PDF created in artifacts/file_outputs/

## Future Enhancements

- Docker-based sandboxed execution
- Per-user command allowlists
- Resource limits (CPU, memory)
- Command history/audit log
- Cancellation support for long-running commands
