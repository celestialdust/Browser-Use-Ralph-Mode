# Browser Agent Refinement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 8 refinement tasks covering structured tool output, prompt refinement with detailed workflow, UI cleanup, error handling, reflection/skills, and image upload.

**Architecture:** The browser agent uses DeepAgents library with LangGraph backend. Frontend is Next.js with LangGraph SDK for streaming. Changes span Python tools/prompts, TypeScript components, and configuration.

**Tech Stack:** Python (LangChain/DeepAgents), TypeScript/React (Next.js), LangGraph SDK, WebSocket streaming

---

## Task 7: Structured Browser Tool Output (Foundation)

This task establishes the foundation for all other changes by standardizing tool output format.

**Files:**
- Create: `browser-use-agent/browser_use_agent/models.py`
- Modify: `browser-use-agent/browser_use_agent/tools.py:1-750`

### Step 1: Write the failing test for BrowserToolOutput model

```python
# tests/test_models.py
import pytest
from browser_use_agent.models import BrowserToolOutput

def test_browser_tool_output_all_fields():
    output = BrowserToolOutput(
        action="Navigated to https://example.com",
        observation="Page loaded successfully with title 'Example Domain'",
        next_step="Take browser_snapshot to see available elements",
        filepath="/Users/test/.browser-agent/artifacts/tool_outputs/navigate_abc123_20260119_120000.txt"
    )
    assert output.action == "Navigated to https://example.com"
    assert output.observation == "Page loaded successfully with title 'Example Domain'"
    assert output.next_step == "Take browser_snapshot to see available elements"
    assert output.filepath.endswith(".txt")

def test_browser_tool_output_to_string():
    output = BrowserToolOutput(
        action="Clicked @e1",
        observation="Button was clicked, page state changed",
        next_step="Take snapshot to verify result",
        filepath="/path/to/output.txt"
    )
    result = output.to_string()
    assert "Action:" in result
    assert "Clicked @e1" in result
    assert "Observation:" in result
    assert "Next Step:" in result
```

### Step 2: Run test to verify it fails

Run: `cd browser-use-agent && uv run pytest tests/test_models.py -v`
Expected: FAIL with "No module named 'browser_use_agent.models'"

### Step 3: Create BrowserToolOutput Pydantic model

```python
# browser-use-agent/browser_use_agent/models.py
"""Pydantic models for browser agent structured outputs."""

from pydantic import BaseModel, Field


class BrowserToolOutput(BaseModel):
    """Structured output for all browser tool calls.

    This provides consistent, predictable output format that:
    1. Tells the agent what happened (action)
    2. Describes current state (observation)
    3. Suggests what to do next (next_step)
    4. Points to full output if needed (filepath)
    """

    action: str = Field(
        description="The action that was performed"
    )
    observation: str = Field(
        description="What was observed after the action"
    )
    next_step: str = Field(
        description="Suggested next step based on observation"
    )
    filepath: str = Field(
        description="Absolute path to file containing full command output"
    )

    def to_string(self) -> str:
        """Convert to human-readable string format."""
        return (
            f"Action: {self.action}\n"
            f"Observation: {self.observation}\n"
            f"Next Step: {self.next_step}\n"
            f"Full Output: {self.filepath}"
        )
```

### Step 4: Run test to verify it passes

Run: `cd browser-use-agent && uv run pytest tests/test_models.py -v`
Expected: PASS

### Step 5: Write test for browser_scroll tool

```python
# tests/test_tools.py (add to existing or create)
import pytest
from unittest.mock import patch, MagicMock

def test_browser_scroll_down():
    from browser_use_agent.tools import browser_scroll

    with patch('browser_use_agent.tools._run_browser_command') as mock_cmd:
        mock_cmd.return_value = {"success": True, "output": "Scrolled down 500px"}

        result = browser_scroll.invoke({
            "direction": "down",
            "amount": 500,
            "thread_id": "test-thread"
        })

        assert "Action:" in result
        assert "Scrolled down" in result
        mock_cmd.assert_called()

def test_browser_scroll_to_top():
    from browser_use_agent.tools import browser_scroll

    with patch('browser_use_agent.tools._run_browser_command') as mock_cmd:
        mock_cmd.return_value = {"success": True, "output": "Scrolled to top"}

        result = browser_scroll.invoke({
            "direction": "top",
            "thread_id": "test-thread"
        })

        assert "top" in result.lower()
```

### Step 6: Run test to verify it fails

Run: `cd browser-use-agent && uv run pytest tests/test_tools.py::test_browser_scroll_down -v`
Expected: FAIL with "browser_scroll not defined"

### Step 7: Add browser_scroll tool to tools.py

In `browser-use-agent/browser_use_agent/tools.py`, add after the browser_wait function (around line 524):

```python
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
```

### Step 8: Run test to verify it passes

Run: `cd browser-use-agent && uv run pytest tests/test_tools.py::test_browser_scroll_down tests/test_tools.py::test_browser_scroll_to_top -v`
Expected: PASS

### Step 9: Update existing tools to use BrowserToolOutput

Modify `browser_navigate` in tools.py (around line 289):

```python
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

    result = _run_browser_command(
        thread_id,
        ["open", url],
        set_stream_port=True
    )

    if result["success"]:
        stream_url = stream_manager.get_stream_url(thread_id)

        # Wait for stream server to be ready
        port = stream_manager.get_port_for_thread(thread_id)
        stream_ready = _wait_for_stream_ready(port, timeout_seconds=5)

        if not stream_ready:
            print(f"[Browser Navigate] Warning: Stream server not ready within timeout")

        _update_browser_session(thread_id, is_active=True, update_last_activity=True)

        # Save full output
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
```

### Step 10: Update browser_snapshot to use BrowserToolOutput

```python
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

            # Create preview (first 500 chars or summary)
            preview = output_str[:500] + "..." if len(output_str) > 500 else output_str

            output = BrowserToolOutput(
                action="Captured DOM snapshot",
                observation=f"Found {element_count} interactive elements. Elements have @refs like @e1, @e2.",
                next_step="Use @refs to interact: browser_click(@e1), browser_fill(@e2, 'text')",
                filepath=filepath
            )
            return output.to_string() + f"\n\nPreview:\n{preview}"
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
```

### Step 11: Update browser_click to use BrowserToolOutput

```python
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
```

### Step 12: Update remaining core tools (browser_fill, browser_type, browser_press_key)

Apply similar pattern to browser_fill, browser_type, browser_press_key. Each should:
1. Import BrowserToolOutput
2. Save output to file
3. Return structured output with appropriate action/observation/next_step

### Step 13: Remove deprecated tools

Remove these tools from tools.py and BROWSER_TOOLS list:
- `browser_wait` (lines 473-523)
- `browser_is_visible` (lines 645-657)
- `browser_is_enabled` (lines 660-672)
- `browser_is_checked` (lines 675-690)

Update BROWSER_TOOLS list (around line 719) to add browser_scroll and remove deprecated tools:

```python
BROWSER_TOOLS = [
    # Core commands
    browser_navigate,
    browser_snapshot,
    browser_click,
    browser_fill,
    browser_type,
    browser_press_key,
    browser_screenshot,
    browser_scroll,  # New
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
]
```

### Step 14: Run full test suite

Run: `cd browser-use-agent && uv run pytest tests/ -v`
Expected: All tests pass

### Step 15: Commit Task 7

```bash
git add browser-use-agent/browser_use_agent/models.py browser-use-agent/browser_use_agent/tools.py tests/
git commit -m "$(cat <<'EOF'
feat: add structured browser tool output with BrowserToolOutput model

- Add BrowserToolOutput Pydantic model with action/observation/next_step/filepath
- Add browser_scroll tool for page scrolling
- Update browser_navigate, browser_snapshot, browser_click to use structured output
- Remove deprecated tools: browser_wait, browser_is_visible, browser_is_enabled, browser_is_checked
- All tools now save full output to .browser-agent/artifacts/tool_outputs/

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Prompt Refinement & Context Loading

This task adds detailed workflow instructions and context loading to the system prompt.

**Files:**
- Modify: `browser-use-agent/browser_use_agent/prompts.py:1-320`
- Modify: `browser-use-agent/browser_use_agent/browser_agent.py:1-212`

### Step 1: Write test for prompt generation

```python
# tests/test_prompts.py
def test_system_prompt_contains_required_sections():
    from browser_use_agent.prompts import BROWSER_AGENT_SYSTEM_PROMPT

    required_sections = [
        "<role>",
        "<task_management>",
        "<file_management>",
        "<browser_tools>",
        "<workflow>",
        "<constraints>",
    ]

    for section in required_sections:
        assert section in BROWSER_AGENT_SYSTEM_PROMPT, f"Missing section: {section}"

def test_workflow_section_has_planning_step():
    from browser_use_agent.prompts import BROWSER_AGENT_SYSTEM_PROMPT

    # Workflow should instruct agent to plan before doing
    assert "plan" in BROWSER_AGENT_SYSTEM_PROMPT.lower()
    assert "write_todos" in BROWSER_AGENT_SYSTEM_PROMPT
```

### Step 2: Run test to verify current state

Run: `cd browser-use-agent && uv run pytest tests/test_prompts.py -v`
Expected: May fail if sections don't exist

### Step 3: Rewrite BROWSER_AGENT_SYSTEM_PROMPT with detailed workflow

Replace the entire BROWSER_AGENT_SYSTEM_PROMPT in prompts.py with:

```python
BROWSER_AGENT_SYSTEM_PROMPT = """<system>
<role>Browser automation agent with visual and DOM capabilities, memory, and learning.</role>

<task_management>
When using write_todos for planning:
1. Keep todo list MINIMAL - aim for 3-6 items maximum
2. Only create todos for complex, multi-step tasks
3. Break down work into clear, actionable items without over-fragmenting
4. For simple tasks (1-2 steps), just do them directly
5. When first creating a todo list, ALWAYS ask user if plan looks good before starting
6. Update todo status promptly as you complete each item
7. Only one task should be in_progress at a time
</task_management>

<file_management>
When reading files, use pagination to prevent context overflow:
- First scan: read_file(path, limit=100) - See structure
- Targeted read: read_file(path, offset=100, limit=200) - Specific sections
- Full read: Only when necessary for editing

All file paths must be absolute (start with /).
</file_management>

<subagents>
When delegating to subagents via task tool:
- Use filesystem for large I/O (>500 words) - communicate via files
- Parallelize independent work - spawn parallel subagents
- Clear specifications - tell subagent exact format/structure needed
- Main agent synthesizes - subagents gather/execute, main integrates
</subagents>

<browser_tools>
<approach>
DOM-first with visual fallback:
1. Try browser_snapshot (DOM approach) first - returns @refs for elements
2. If snapshot fails/unusable, take browser_screenshot(filepath) for visual analysis
3. All tools return structured output: action, observation, next_step, filepath
</approach>

<tools>
Core (8):
- browser_navigate(url) - Go to URL, starts browser session
- browser_snapshot() - Get DOM elements with @refs (@e1, @e2)
- browser_click(ref) - Click element by @ref
- browser_fill(ref, text) - Clear and fill input
- browser_type(ref, text) - Type without clearing
- browser_press_key(key) - Press keyboard key (Enter, Tab, Escape)
- browser_screenshot(filepath) - Take screenshot for visual analysis
- browser_scroll(direction, amount) - Scroll page (up/down/top/bottom)

Navigation (3):
- browser_back() - Go back in history
- browser_forward() - Go forward in history
- browser_reload() - Reload current page

Info (2):
- browser_get_info(type, ref?) - Get text/html/value/url/title
- browser_console() - Get console logs for debugging

Lifecycle (1):
- browser_close() - MUST call when task complete

Human-in-the-loop (3):
- request_human_guidance(question) - When stuck, ask for help
- request_credentials(service) - NEVER guess passwords
- request_confirmation(action) - Before risky/financial operations
</tools>

<critical_patterns>
1. ALWAYS snapshot after navigation to get fresh @refs
2. @refs become stale after navigation or DOM changes - re-snapshot
3. NEVER guess credentials - always use request_credentials
4. ALWAYS close browser when task is complete
</critical_patterns>
</browser_tools>

<workflow>
Follow this workflow for every task:

**Phase 1: Understand**
1. Parse the user's request - what is the specific goal?
2. Identify any implicit requirements (credentials, confirmations)
3. Check if task is simple (1-2 steps) or complex (3+ steps)

**Phase 2: Plan (for complex tasks only)**
4. Use write_todos to create a minimal plan (3-6 items max)
5. Ask user: "Here's my plan - does this look good?"
6. Wait for user approval before executing

**Phase 3: Execute**
7. Check filesystem for existing context/skills:
   - ls .browser-agent/ to see available resources
   - Read AGENTS.md for learned patterns
   - Check skills/ for relevant workflows
8. Start browser session: browser_navigate(url)
9. Take snapshot: browser_snapshot() to get @refs
10. Execute actions using @refs from snapshot
11. Verify results after each action - snapshot again if needed

**Phase 4: Handle Obstacles**
12. Element not found → Take fresh snapshot, try alternative text
13. Login required → Use request_credentials (never guess)
14. Unclear instructions → Use request_human_guidance
15. Risky action (financial/delete) → Use request_confirmation

**Phase 5: Complete**
16. Verify task objectives are met
17. Call browser_close() to clean up session
18. Summarize what was accomplished
</workflow>

<constraints>
HARD LIMITS - Never violate these:
- Never store/log/guess credentials
- Request human confirmation for financial operations
- Request human confirmation for irreversible actions (delete, submit payment)
- Always close browser when task complete
- Re-snapshot after any navigation or DOM change
- Session isolation: each thread_id gets isolated browser
</constraints>

<error_recovery>
When things go wrong:

**Element not found:**
1. Take fresh snapshot (elements may have loaded async)
2. Search for alternative text/attributes
3. Try scrolling to load dynamic content
4. After 2-3 failures, use request_human_guidance

**Page not loading:**
1. Check browser_console for errors
2. Try browser_reload
3. Verify URL is correct

**Action has no effect:**
1. Snapshot to verify element state
2. Try alternative interaction (type vs fill, hover before click)
3. Check if page requires specific order of operations

**Don't keep trying blindly** - After 2-3 failed attempts with same approach, ask for help or try fundamentally different approach.
</error_recovery>
</system>"""
```

### Step 4: Run test to verify it passes

Run: `cd browser-use-agent && uv run pytest tests/test_prompts.py -v`
Expected: PASS

### Step 5: Update browser_agent.py to load context files

Add context loading before agent creation. Modify create_browser_agent function:

```python
def create_browser_agent(
    model: Any = None,
    system_prompt: str = None,
    tools: List[Any] = None,
    checkpointer: Any = None,
    **kwargs
) -> Any:
    """Create a DeepAgents browser automation agent with filesystem backend."""
    # Initialize directory structure
    from browser_use_agent.storage import init_agent_directories
    init_agent_directories()

    # Use provided model or default
    if model is None:
        model = get_llm()

    # Build system prompt with context loading
    base_prompt = get_system_prompt(system_prompt)

    # Load context files if they exist
    agent_dir = StorageConfig.get_agent_dir()

    # Load AGENTS.md (project memory - synthesized rules)
    agents_md_path = agent_dir / "memory" / "AGENTS.md"
    project_memory = ""
    if agents_md_path.exists():
        try:
            content = agents_md_path.read_text()
            project_memory = f"\n<project_memory>\n{content}\n</project_memory>\n"
            print(f"[Agent] Loaded project memory from {agents_md_path}")
        except Exception as e:
            print(f"[Agent] Failed to load AGENTS.md: {e}")

    # Load agent.md (technical reference)
    agent_md_path = agent_dir / "agent.md"
    agent_memory = ""
    if agent_md_path.exists():
        try:
            content = agent_md_path.read_text()
            agent_memory = f"\n<agent_memory>\n{content}\n</agent_memory>\n"
            print(f"[Agent] Loaded agent memory from {agent_md_path}")
        except Exception as e:
            print(f"[Agent] Failed to load agent.md: {e}")

    # Load skills metadata (names and descriptions only)
    skills_dir = agent_dir / "skills"
    skills_metadata = ""
    if skills_dir.exists():
        skill_entries = []
        for skill_file in skills_dir.glob("*/SKILL.md"):
            try:
                content = skill_file.read_text()
                # Parse YAML frontmatter for name and description
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        import yaml
                        frontmatter = yaml.safe_load(content[3:end])
                        name = frontmatter.get("name", skill_file.parent.name)
                        desc = frontmatter.get("description", "No description")
                        skill_entries.append(f"- {name}: {desc}")
            except Exception as e:
                print(f"[Agent] Failed to parse skill {skill_file}: {e}")

        if skill_entries:
            skills_list = "\n".join(skill_entries)
            skills_metadata = f"\n<skills>\nAvailable skills:\n{skills_list}\n\nTo use a skill: read_file(.browser-agent/skills/[name]/SKILL.md) for full instructions.\n</skills>\n"
            print(f"[Agent] Loaded {len(skill_entries)} skill metadata entries")

    # Combine prompt with context
    full_prompt = base_prompt + project_memory + agent_memory + skills_metadata

    # Use provided tools or default
    if tools is None:
        tools = BROWSER_TOOLS

    # Get checkpoint saver
    if checkpointer is None:
        print("[Agent] Using in-memory checkpointer")
        checkpointer = None

    # Create filesystem backend
    print(f"[Agent] Filesystem backend: {agent_dir}")
    filesystem_backend = FilesystemBackend(root_dir=str(agent_dir))

    # Create agent
    agent = create_deep_agent(
        model=model,
        system_prompt=full_prompt,
        tools=tools,
        backend=filesystem_backend,
        checkpointer=checkpointer,
        **kwargs
    )

    return agent
```

### Step 6: Add yaml to dependencies if needed

Check pyproject.toml and add pyyaml if not present:

```toml
dependencies = [
    # ... existing deps
    "pyyaml>=6.0",
]
```

### Step 7: Run full test suite

Run: `cd browser-use-agent && uv run pytest tests/ -v`
Expected: All tests pass

### Step 8: Commit Task 4

```bash
git add browser-use-agent/browser_use_agent/prompts.py browser-use-agent/browser_use_agent/browser_agent.py browser-use-agent/pyproject.toml
git commit -m "$(cat <<'EOF'
feat: refine prompts with detailed workflow and context loading

- Rewrite system prompt with XML structure for clarity
- Add detailed 5-phase workflow: Understand → Plan → Execute → Handle Obstacles → Complete
- Add task_management section with planning guidelines (3-6 todos max, ask approval)
- Add file_management section with pagination pattern
- Add subagent delegation guidelines
- Load AGENTS.md, agent.md, and skills metadata at agent creation
- Progressive skill disclosure: only names/descriptions loaded initially

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 1: Remove Status from ThreadList

**Files:**
- Modify: `deep-agents-ui/src/app/components/ThreadList.tsx`

### Step 1: Identify elements to remove

In ThreadList.tsx, locate and mark for removal:
- Status filter dropdown (Select component with "All", "Idle", "Busy", "Interrupted", "Error")
- `statusFilter` state variable
- `getThreadColor()` function
- Colored status dots in thread items
- "Requiring Attention" grouping logic

### Step 2: Remove status filter state and dropdown

Remove the statusFilter state:
```typescript
// REMOVE THIS:
const [statusFilter, setStatusFilter] = useState<string>("all");
```

Remove the status filter Select component (the dropdown with All/Idle/Busy/Interrupted/Error options).

### Step 3: Remove getThreadColor function

Remove the entire `getThreadColor()` function that maps status to colors.

### Step 4: Remove status dots from thread items

In the thread item rendering, remove the colored dot indicator:
```tsx
// REMOVE status dot span:
<span className={`w-2 h-2 rounded-full ${getThreadColor(thread.status)}`} />
```

### Step 5: Remove "Requiring Attention" grouping

Remove any grouping logic that separates interrupted threads into a special section.

### Step 6: Keep date grouping

Ensure date grouping remains (Today, Yesterday, This Week, Older).

### Step 7: Verify UI builds

Run: `cd deep-agents-ui && yarn build`
Expected: Build succeeds with no errors

### Step 8: Commit Task 1

```bash
git add deep-agents-ui/src/app/components/ThreadList.tsx
git commit -m "$(cat <<'EOF'
refactor: remove status indicators from ThreadList

- Remove status filter dropdown
- Remove colored status dots next to threads
- Remove "Requiring Attention" grouping
- Keep date grouping (Today, Yesterday, This Week, Older)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Reasoning Display Markdown Rendering

**Files:**
- Modify: `deep-agents-ui/src/app/components/ThoughtProcess.tsx`
- Modify: `deep-agents-ui/src/app/components/ReasoningDisplay.tsx`

### Step 1: Install react-markdown if not present

Run: `cd deep-agents-ui && yarn add react-markdown`

### Step 2: Update ThoughtProcess.tsx to use react-markdown

Import and use react-markdown for content rendering:

```tsx
import ReactMarkdown from 'react-markdown';

// In the component, replace plain text rendering with:
<ReactMarkdown className="prose prose-sm max-w-none">
  {content}
</ReactMarkdown>
```

### Step 3: Remove sparkles icon from header

Find the header with the sparkles/star icon and remove the icon:

```tsx
// Change from:
<Sparkles className="w-4 h-4" />
<span>Show thinking process</span>

// To:
<span>Show thinking process</span>
```

### Step 4: Update ReasoningDisplay.tsx similarly

Apply same changes:
1. Import react-markdown
2. Use ReactMarkdown for summary text rendering
3. Remove sparkles icon

### Step 5: Verify styles work with prose class

Ensure tailwind typography plugin is configured. Check tailwind.config.ts for `@tailwindcss/typography` plugin.

### Step 6: Build and verify

Run: `cd deep-agents-ui && yarn build`
Expected: Build succeeds

### Step 7: Commit Task 2

```bash
git add deep-agents-ui/src/app/components/ThoughtProcess.tsx deep-agents-ui/src/app/components/ReasoningDisplay.tsx deep-agents-ui/package.json deep-agents-ui/yarn.lock
git commit -m "$(cat <<'EOF'
feat: add markdown rendering to reasoning displays

- Add react-markdown for ThoughtProcess content
- Add react-markdown for ReasoningDisplay summaries
- Remove sparkles icon from headers
- Keep collapsible behavior and streaming support

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Recursion Limit & Stop Mechanisms

**Files:**
- Modify: `deep-agents-ui/src/lib/config.ts`
- Modify: `deep-agents-ui/src/app/components/ConfigDialog.tsx`
- Modify: `deep-agents-ui/src/app/hooks/useChat.ts`

### Step 1: Hardcode high recursion limit in config.ts

In config.ts, change the default recursion limit:

```typescript
// Change from:
recursionLimit: parseInt(localStorage.getItem('recursionLimit') ||
  process.env.NEXT_PUBLIC_RECURSION_LIMIT || '200')

// To:
recursionLimit: 5000  // Hardcoded high value
```

### Step 2: Remove recursion limit input from ConfigDialog

In ConfigDialog.tsx, remove the input field for recursion limit. Keep other settings (deploymentUrl, assistantId, ralphMode, browserStreamPort).

### Step 3: Add error-triggered stop in useChat.ts

In useChat.ts, add error handling that stops the stream on errors:

```typescript
// In the stream error handler:
const handleStreamError = (error: Error) => {
  console.error('[useChat] Stream error:', error);

  // Stop stream immediately on error
  stopStream();

  // Add error message to chat
  // This will be displayed to user
  setErrorMessage(error.message || 'An error occurred');
};
```

### Step 4: Add recursion limit reached message

```typescript
// When recursion limit is reached, show message:
if (error.message.includes('recursion') || error.message.includes('limit')) {
  setErrorMessage('Agent reached maximum iterations. You can retry or provide more guidance.');
}
```

### Step 5: Ensure stop button works

Verify stopStream() properly cancels the active stream.

### Step 6: Build and verify

Run: `cd deep-agents-ui && yarn build`
Expected: Build succeeds

### Step 7: Commit Task 3

```bash
git add deep-agents-ui/src/lib/config.ts deep-agents-ui/src/app/components/ConfigDialog.tsx deep-agents-ui/src/app/hooks/useChat.ts
git commit -m "$(cat <<'EOF'
feat: hardcode recursion limit and improve stop mechanisms

- Hardcode recursion limit to 5000 (remove from config dialog)
- Add error-triggered stop behavior
- Show user-friendly message when recursion limit reached
- Offer retry option on errors

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Error Handling Reinforcement

**Files:**
- Modify: `deep-agents-ui/src/app/components/BrowserPanel.tsx`
- Modify: `deep-agents-ui/src/app/hooks/useChat.ts`
- Create: `deep-agents-ui/src/app/components/ErrorBanner.tsx`

### Step 1: Create ErrorBanner component

```tsx
// deep-agents-ui/src/app/components/ErrorBanner.tsx
import React from 'react';

type ErrorType = 'warning' | 'error' | 'info';

interface ErrorBannerProps {
  type: ErrorType;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  onViewDetails?: () => void;
}

export function ErrorBanner({
  type,
  message,
  onRetry,
  onDismiss,
  onViewDetails
}: ErrorBannerProps) {
  const colors = {
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };

  return (
    <div className={`p-3 border rounded-md ${colors[type]} flex items-center justify-between`}>
      <span className="text-sm">{message}</span>
      <div className="flex gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-sm underline hover:no-underline"
          >
            Retry
          </button>
        )}
        {onViewDetails && (
          <button
            onClick={onViewDetails}
            className="text-sm underline hover:no-underline"
          >
            Details
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-sm underline hover:no-underline"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
```

### Step 2: Add WebSocket error handling to BrowserPanel

In BrowserPanel.tsx, enhance error handling:

```typescript
// Add exponential backoff constants
const INITIAL_RETRY_DELAY = 1000;  // 1s
const MAX_RETRY_DELAY = 16000;     // 16s
const MAX_RETRIES = 5;

// In WebSocket error handler:
const handleWebSocketError = () => {
  const delay = Math.min(INITIAL_RETRY_DELAY * Math.pow(2, reconnectAttempts), MAX_RETRY_DELAY);

  if (reconnectAttempts < MAX_RETRIES) {
    setConnectionError(`Reconnecting in ${delay/1000}s...`);
    setTimeout(() => {
      setReconnectAttempts(prev => prev + 1);
      connectWebSocket();
    }, delay);
  } else {
    setConnectionError('Connection lost. Click to retry.');
  }
};
```

### Step 3: Add LangGraph API error handling to useChat

```typescript
// Add request timeout handling
const STREAM_TIMEOUT = 60000; // 60s default

// Wrap stream submission with timeout
const submitWithTimeout = async (input: any) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), STREAM_TIMEOUT);

  try {
    await stream.submit(input, { signal: controller.signal });
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. The server may be busy.');
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
};

// Handle specific error types
const handleApiError = (error: Error) => {
  if (error.message.includes('401')) {
    setErrorMessage('Authentication failed. Check your API key.');
  } else if (error.message.includes('500')) {
    setErrorMessage('Server error. Please try again.');
  } else if (error.message.includes('503')) {
    // Retry transient errors
    retryWithBackoff();
  } else {
    setErrorMessage(error.message);
  }
};
```

### Step 4: Integrate ErrorBanner in ChatInterface

Import and display ErrorBanner when errors occur.

### Step 5: Build and verify

Run: `cd deep-agents-ui && yarn build`
Expected: Build succeeds

### Step 6: Commit Task 5

```bash
git add deep-agents-ui/src/app/components/ErrorBanner.tsx deep-agents-ui/src/app/components/BrowserPanel.tsx deep-agents-ui/src/app/hooks/useChat.ts deep-agents-ui/src/app/components/ChatInterface.tsx
git commit -m "$(cat <<'EOF'
feat: reinforce error handling across frontend

- Add ErrorBanner component with warning/error/info states
- Add exponential backoff for WebSocket reconnection
- Add request timeout handling for LangGraph API
- Show user-friendly error messages
- Add retry and dismiss actions

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Reflection & Skill Creation

**Files:**
- Create: `browser-use-agent/browser_use_agent/reflection.py`
- Modify: `browser-use-agent/browser_use_agent/tools.py`
- Modify: `deep-agents-ui/src/app/components/ConfigDialog.tsx`

### Step 1: Write test for reflection tool

```python
# tests/test_reflection.py
def test_reflect_on_session_returns_output():
    from browser_use_agent.reflection import reflect_on_session

    # Mock thread_id with existing diary
    result = reflect_on_session.invoke({"thread_id": "test-thread"})

    assert "accomplishments" in result.lower() or "no diary" in result.lower()
```

### Step 2: Run test to verify it fails

Run: `cd browser-use-agent && uv run pytest tests/test_reflection.py -v`
Expected: FAIL with module not found

### Step 3: Create reflection.py with reflect_on_session tool

```python
# browser-use-agent/browser_use_agent/reflection.py
"""Reflection tools for session analysis and skill creation."""

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
from browser_use_agent.storage.config import StorageConfig


class SkillOpportunity(BaseModel):
    """Identified opportunity for skill extraction."""
    name: str = Field(description="Proposed skill name")
    description: str = Field(description="What the skill does")
    steps: List[str] = Field(description="Key steps in the workflow")


class ReflectionOutput(BaseModel):
    """Output from session reflection."""
    accomplishments: List[str] = Field(description="What was accomplished")
    challenges: List[str] = Field(description="Obstacles encountered")
    learnings: List[str] = Field(description="Key learnings")
    skill_opportunities: List[SkillOpportunity] = Field(
        default_factory=list,
        description="Potential skills to extract"
    )
    rules_to_add: List[str] = Field(
        default_factory=list,
        description="Rules to add to AGENTS.md"
    )


@tool
def reflect_on_session(thread_id: str) -> str:
    """Analyze the current session and extract learnings.

    Called after browser_close to capture insights from the session.
    Reads diary entries and identifies patterns worth saving.

    Args:
        thread_id: Thread identifier for the session

    Returns:
        Reflection summary with accomplishments, challenges, learnings
    """
    agent_dir = StorageConfig.get_agent_dir()
    diary_dir = agent_dir / "memory" / "diary"

    # Find diary entries for this thread
    diary_entries = []
    if diary_dir.exists():
        for entry_file in diary_dir.glob(f"*{thread_id[:8]}*.md"):
            try:
                content = entry_file.read_text()
                diary_entries.append(content)
            except Exception:
                pass

    if not diary_entries:
        return (
            "No diary entries found for this session.\n"
            "To enable reflection, create diary entries during task execution:\n"
            "write_file(.browser-agent/memory/diary/YYYY-MM-DD-task-name.md, content)"
        )

    # Analyze diary entries (simple pattern extraction)
    combined = "\n".join(diary_entries)

    output = ReflectionOutput(
        accomplishments=_extract_section(combined, "accomplishments"),
        challenges=_extract_section(combined, "challenges"),
        learnings=_extract_section(combined, "learnings"),
        skill_opportunities=[],
        rules_to_add=[]
    )

    # Check for repeated patterns that could become skills
    if "login" in combined.lower() and "password" in combined.lower():
        output.skill_opportunities.append(SkillOpportunity(
            name="login-workflow",
            description="Automated login flow for web services",
            steps=["Navigate to login page", "Fill credentials", "Submit form", "Verify success"]
        ))

    # Format output
    result = "## Session Reflection\n\n"
    result += "### Accomplishments\n"
    for item in output.accomplishments or ["No accomplishments recorded"]:
        result += f"- {item}\n"

    result += "\n### Challenges\n"
    for item in output.challenges or ["No challenges recorded"]:
        result += f"- {item}\n"

    result += "\n### Learnings\n"
    for item in output.learnings or ["No learnings recorded"]:
        result += f"- {item}\n"

    if output.skill_opportunities:
        result += "\n### Skill Opportunities\n"
        for skill in output.skill_opportunities:
            result += f"- **{skill.name}**: {skill.description}\n"

    return result


def _extract_section(content: str, section_name: str) -> List[str]:
    """Extract bullet points from a markdown section."""
    items = []
    in_section = False

    for line in content.split("\n"):
        lower_line = line.lower()
        if section_name in lower_line and "#" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("#"):
                break
            if line.strip().startswith("-"):
                items.append(line.strip()[1:].strip())

    return items


# Export reflection tools
REFLECTION_TOOLS = [reflect_on_session]
```

### Step 4: Run test to verify it passes

Run: `cd browser-use-agent && uv run pytest tests/test_reflection.py -v`
Expected: PASS

### Step 5: Add reflection tools to BROWSER_TOOLS in tools.py

```python
# At the end of tools.py, add:
from browser_use_agent.reflection import REFLECTION_TOOLS

BROWSER_TOOLS = [
    # ... existing tools ...
    *REFLECTION_TOOLS,
]
```

### Step 6: Add skill management UI to ConfigDialog (compact)

In ConfigDialog.tsx, add a compact skills section:

```tsx
// Add skills state
const [skills, setSkills] = useState<{name: string, description: string, enabled: boolean}[]>([]);

// Add skills section in the dialog:
<div className="space-y-2">
  <label className="text-sm font-medium">Skills</label>
  <div className="border rounded-md divide-y max-h-40 overflow-y-auto">
    {skills.map((skill) => (
      <div key={skill.name} className="flex items-center justify-between p-2 text-sm">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={skill.enabled}
            onChange={() => toggleSkill(skill.name)}
          />
          <span className="font-medium">{skill.name}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500 truncate max-w-[200px]">
            {skill.description}
          </span>
          <button onClick={() => deleteSkill(skill.name)} className="text-red-500">
            ×
          </button>
        </div>
      </div>
    ))}
    {skills.length === 0 && (
      <div className="p-2 text-sm text-gray-500">No skills created yet</div>
    )}
  </div>
</div>
```

### Step 7: Build and verify

Run: `cd deep-agents-ui && yarn build`
Expected: Build succeeds

### Step 8: Commit Task 6

```bash
git add browser-use-agent/browser_use_agent/reflection.py browser-use-agent/browser_use_agent/tools.py deep-agents-ui/src/app/components/ConfigDialog.tsx tests/test_reflection.py
git commit -m "$(cat <<'EOF'
feat: add session reflection and skill management

- Add reflect_on_session tool for post-session analysis
- Extract accomplishments, challenges, learnings from diary
- Identify skill opportunities from patterns
- Add compact skill management UI to ConfigDialog
- Skills can be enabled/disabled and deleted

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Image Upload & Visual Processing

**Files:**
- Modify: `deep-agents-ui/src/app/components/ChatInterface.tsx`
- Modify: `deep-agents-ui/src/context/ChatProvider.tsx`

### Step 1: Add image upload state to ChatInterface

```tsx
// Add state for image upload
const [attachedImage, setAttachedImage] = useState<{
  data: string;  // base64
  name: string;
  type: string;
} | null>(null);

const fileInputRef = useRef<HTMLInputElement>(null);
```

### Step 2: Add upload button to input area

```tsx
// Add to the left of the input textarea:
<button
  onClick={() => fileInputRef.current?.click()}
  disabled={attachedImage !== null}
  className={`p-2 ${attachedImage ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'}`}
>
  <Paperclip className="w-5 h-5" />
</button>

<input
  ref={fileInputRef}
  type="file"
  accept="image/jpeg,image/png,image/gif,image/webp"
  onChange={handleFileSelect}
  className="hidden"
/>
```

### Step 3: Add image preview above input

```tsx
// Above the input area, conditionally render:
{attachedImage && (
  <div className="border-t p-2 flex items-center gap-2">
    <img
      src={attachedImage.data}
      alt="Attached"
      className="h-20 w-auto object-contain rounded"
    />
    <button
      onClick={() => setAttachedImage(null)}
      className="text-gray-500 hover:text-red-500"
    >
      ×
    </button>
  </div>
)}
```

### Step 4: Implement handleFileSelect

```tsx
const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;

  // Validate file type
  if (!file.type.startsWith('image/')) {
    alert('Please select an image file');
    return;
  }

  // Convert to base64
  const reader = new FileReader();
  reader.onload = () => {
    setAttachedImage({
      data: reader.result as string,
      name: file.name,
      type: file.type,
    });
  };
  reader.readAsDataURL(file);

  // Clear input for re-selection
  e.target.value = '';
};
```

### Step 5: Modify sendMessage to include image

```tsx
const handleSubmit = () => {
  const trimmedInput = input.trim();
  if (!trimmedInput && !attachedImage) return;

  // Build message content
  let content: any = trimmedInput;

  if (attachedImage) {
    // Multimodal message format
    content = [
      { type: 'text', text: trimmedInput },
      {
        type: 'image_url',
        image_url: { url: attachedImage.data }
      }
    ];
  }

  sendMessage(content);
  setInput('');
  setAttachedImage(null);
};
```

### Step 6: Update ChatProvider to handle multimodal messages

In ChatProvider.tsx, ensure the stream.submit handles multimodal content properly.

### Step 7: Build and verify

Run: `cd deep-agents-ui && yarn build`
Expected: Build succeeds

### Step 8: Commit Task 8

```bash
git add deep-agents-ui/src/app/components/ChatInterface.tsx deep-agents-ui/src/context/ChatProvider.tsx
git commit -m "$(cat <<'EOF'
feat: add image upload for visual processing

- Add paperclip upload button (left side of input)
- Add image preview with remove button
- Limit to one image per message
- Support jpg, png, gif, webp formats
- Send images as base64 multimodal content
- Works with GPT-5/o4-mini for visual analysis

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Final Integration & Testing

### Step 1: Run all backend tests

Run: `cd browser-use-agent && uv run pytest tests/ -v`
Expected: All tests pass

### Step 2: Run frontend build

Run: `cd deep-agents-ui && yarn build`
Expected: Build succeeds with no errors

### Step 3: Start backend and verify

Run: `cd browser-use-agent && langgraph dev --port 2024`
Expected: Server starts, agent loads with new prompts

### Step 4: Start frontend and manual test

Run: `cd deep-agents-ui && yarn dev`
Test:
1. Thread list has no status dots
2. Thinking display renders markdown
3. Image upload works
4. Error banners appear on errors
5. Skills section visible in settings

### Step 5: Final commit

```bash
git add -A
git commit -m "$(cat <<'EOF'
chore: browser agent refinement complete

All 8 tasks implemented:
1. ThreadList status indicators removed
2. Markdown rendering in reasoning displays
3. Recursion limit hardcoded, error stops
4. Prompt refinement with detailed workflow
5. Error handling reinforcement
6. Reflection and skill management
7. Structured browser tool output
8. Image upload and visual processing

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Execution Summary

| Task | Files Changed | Type |
|------|--------------|------|
| 7 | models.py, tools.py | Backend |
| 4 | prompts.py, browser_agent.py | Backend |
| 1 | ThreadList.tsx | Frontend |
| 2 | ThoughtProcess.tsx, ReasoningDisplay.tsx | Frontend |
| 3 | config.ts, ConfigDialog.tsx, useChat.ts | Frontend |
| 5 | ErrorBanner.tsx, BrowserPanel.tsx, useChat.ts | Frontend |
| 6 | reflection.py, tools.py, ConfigDialog.tsx | Both |
| 8 | ChatInterface.tsx, ChatProvider.tsx | Frontend |

**Total: 15+ files across 8 tasks**
