# Production-Grade Browser-Use Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the browser-use agent into a production-grade system with 6 architectural layers: tools, backend/storage, memory/learning, middleware, skills, and enhanced UI.

**Architecture:** Layer-based design inspired by Claude Code CLI, using DeepAgents framework with progressive enhancement from basic browser automation to production-grade system with learning and adaptive capabilities.

**Tech Stack:**
- Backend: Python 3.11+, LangGraph, DeepAgents, LangSmith
- Database: SQLite (dev) / PostgreSQL (production)
- Browser: agent-browser CLI
- Frontend: Next.js, TypeScript, TailwindCSS
- LLM: GPT-5 / o4-mini via ChatOpenAI

---

## Phase 1: Enhanced Tool Layer (Foundation)

**Goal:** Expand from 18 to 25+ browser tools, add comprehensive observation tools, and establish tool approval system.

### Task 1.1: Add Navigation Control Tools

**Files:**
- Modify: `browser-use-agent/browser_use_agent/tools.py`
- Test: Manual testing with agent-browser CLI

**Step 1: Add browser_back tool**

```python
@tool
def browser_back(config: RunnableConfig) -> str:
    """Go back to the previous page in browser history.

    Args:
        config: Runtime configuration with thread_id

    Returns:
        Success message or error
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    _update_browser_session(thread_id, update_last_activity=True)

    result = _run_browser_command(thread_id, ["back"])
    if result["success"]:
        return f"✓ Navigated back in browser history\n{result['output']}"
    return f"✗ Failed to navigate back: {result['error']}"
```

**Step 2: Add browser_forward tool**

```python
@tool
def browser_forward(config: RunnableConfig) -> str:
    """Go forward to the next page in browser history.

    Args:
        config: Runtime configuration with thread_id

    Returns:
        Success message or error
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    _update_browser_session(thread_id, update_last_activity=True)

    result = _run_browser_command(thread_id, ["forward"])
    if result["success"]:
        return f"✓ Navigated forward in browser history\n{result['output']}"
    return f"✗ Failed to navigate forward: {result['error']}"
```

**Step 3: Add browser_reload tool**

```python
@tool
def browser_reload(config: RunnableConfig) -> str:
    """Reload the current page.

    Args:
        config: Runtime configuration with thread_id

    Returns:
        Success message or error
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    _update_browser_session(thread_id, update_last_activity=True)

    result = _run_browser_command(thread_id, ["reload"])
    if result["success"]:
        return f"✓ Page reloaded\n{result['output']}"
    return f"✗ Failed to reload page: {result['error']}"
```

**Step 4: Add tools to BROWSER_TOOLS list**

In `tools.py`, update the BROWSER_TOOLS list:

```python
BROWSER_TOOLS = [
    # ... existing tools ...
    browser_back,
    browser_forward,
    browser_reload,
]
```

**Step 5: Test navigation tools**

Run: `cd browser-use-agent && uv run python agent.py --task "Navigate to example.com, then go back, then forward"`

Expected: Agent successfully uses navigation tools

**Step 6: Commit navigation tools**

```bash
git add browser-use-agent/browser_use_agent/tools.py
git commit -m "feat: add browser navigation controls (back, forward, reload)

- Add browser_back tool for navigating to previous page
- Add browser_forward tool for navigating to next page
- Add browser_reload tool for reloading current page
- All tools use thread-scoped sessions

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 1.2: Add Advanced Interaction Tools

**Files:**
- Modify: `browser-use-agent/browser_use_agent/tools.py`

**Step 1: Add browser_hover tool**

```python
@tool
def browser_hover(ref: str, config: RunnableConfig) -> str:
    """Hover over an element.

    Args:
        ref: Element reference (@e1, @e2, etc.) from browser_snapshot
        config: Runtime configuration with thread_id

    Returns:
        Success message or error
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    _update_browser_session(thread_id, update_last_activity=True)

    result = _run_browser_command(thread_id, ["hover", ref])
    if result["success"]:
        return f"✓ Hovered over element {ref}\n{result['output']}"
    return f"✗ Failed to hover over {ref}: {result['error']}"
```

**Step 2: Add browser_check tool**

```python
@tool
def browser_check(ref: str, config: RunnableConfig) -> str:
    """Check a checkbox element.

    Args:
        ref: Checkbox element reference (@e1, @e2, etc.)
        config: Runtime configuration with thread_id

    Returns:
        Success message or error
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    _update_browser_session(thread_id, update_last_activity=True)

    result = _run_browser_command(thread_id, ["check", ref])
    if result["success"]:
        return f"✓ Checked checkbox {ref}\n{result['output']}"
    return f"✗ Failed to check {ref}: {result['error']}"
```

**Step 3: Add browser_uncheck tool**

```python
@tool
def browser_uncheck(ref: str, config: RunnableConfig) -> str:
    """Uncheck a checkbox element.

    Args:
        ref: Checkbox element reference (@e1, @e2, etc.)
        config: Runtime configuration with thread_id

    Returns:
        Success message or error
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    _update_browser_session(thread_id, update_last_activity=True)

    result = _run_browser_command(thread_id, ["uncheck", ref])
    if result["success"]:
        return f"✓ Unchecked checkbox {ref}\n{result['output']}"
    return f"✗ Failed to uncheck {ref}: {result['error']}"
```

**Step 4: Add browser_select tool**

```python
@tool
def browser_select(ref: str, value: str, config: RunnableConfig) -> str:
    """Select an option from a dropdown.

    Args:
        ref: Dropdown element reference (@e1, @e2, etc.)
        value: Option value or text to select
        config: Runtime configuration with thread_id

    Returns:
        Success message or error
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    _update_browser_session(thread_id, update_last_activity=True)

    result = _run_browser_command(thread_id, ["select", ref, value])
    if result["success"]:
        return f"✓ Selected '{value}' in dropdown {ref}\n{result['output']}"
    return f"✗ Failed to select option in {ref}: {result['error']}"
```

**Step 5: Add tools to BROWSER_TOOLS list**

**Step 6: Test interaction tools**

Run: `cd browser-use-agent && uv run python agent.py --task "Go to a form page, hover over an input, check a checkbox, select a dropdown option"`

Expected: Agent uses new interaction tools successfully

**Step 7: Commit interaction tools**

```bash
git add browser-use-agent/browser_use_agent/tools.py
git commit -m "feat: add advanced browser interaction tools

- Add browser_hover for hovering over elements
- Add browser_check/uncheck for checkbox operations
- Add browser_select for dropdown selections
- All tools support thread-scoped sessions

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 1.3: Add Enhanced Observation Tools

**Files:**
- Modify: `browser-use-agent/browser_use_agent/tools.py`

**Step 1: Add browser_wait tool**

```python
@tool
def browser_wait(
    condition: str,
    value: str,
    timeout: int = 30,
    config: RunnableConfig = None
) -> str:
    """Wait for a condition to be met.

    Args:
        condition: Type of wait ('element', 'text', 'url', 'load', 'time')
        value: Value to wait for (element ref, text, URL pattern, or seconds for time)
        timeout: Maximum wait time in seconds (default 30)
        config: Runtime configuration with thread_id

    Returns:
        Success message or error

    Examples:
        browser_wait('element', '@e1', 10) - Wait up to 10s for element @e1
        browser_wait('text', 'Success', 5) - Wait up to 5s for text "Success"
        browser_wait('load', 'domcontentloaded', 30) - Wait for page load
        browser_wait('time', '2', 2) - Wait for 2 seconds
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    _update_browser_session(thread_id, update_last_activity=True)

    # Build wait command
    cmd = ["wait", f"--{condition}", value, f"--timeout={timeout}"]

    result = _run_browser_command(thread_id, cmd)
    if result["success"]:
        return f"✓ Wait condition met: {condition}={value}\n{result['output']}"
    return f"✗ Wait timeout or error: {result['error']}"
```

**Step 2: Add browser_is_checked tool**

```python
@tool
def browser_is_checked(ref: str, config: RunnableConfig) -> str:
    """Check if a checkbox or radio button is checked.

    Args:
        ref: Element reference (@e1, @e2, etc.)
        config: Runtime configuration with thread_id

    Returns:
        "true" if checked, "false" if not checked, or error message
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    result = _run_browser_command(thread_id, ["is", "checked", ref])
    if result["success"]:
        output = result["output"].strip().lower()
        return "true" if "true" in output or "checked" in output else "false"
    return f"✗ Failed to check state: {result['error']}"
```

**Step 3: Add browser_console tool**

```python
@tool
def browser_console(config: RunnableConfig) -> str:
    """Get browser console logs (errors, warnings, logs).

    Args:
        config: Runtime configuration with thread_id

    Returns:
        Console output or error message
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    result = _run_browser_command(thread_id, ["console"])
    if result["success"]:
        return f"Console logs:\n{result['output']}"
    return f"✗ Failed to get console logs: {result['error']}"
```

**Step 4: Add tools to BROWSER_TOOLS list**

**Step 5: Test observation tools**

Run: Manual test with various wait conditions and console logging

Expected: Tools correctly wait for conditions and retrieve console logs

**Step 6: Commit observation tools**

```bash
git add browser-use-agent/browser_use_agent/tools.py
git commit -m "feat: add enhanced browser observation tools

- Add browser_wait with support for element, text, url, load, time conditions
- Add browser_is_checked for checkbox/radio state checking
- Add browser_console for retrieving browser console logs
- Improve debugging and synchronization capabilities

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 1.4: Update Tool Approval Configuration

**Files:**
- Modify: `browser-use-agent/browser_use_agent/configuration.py`

**Step 1: Update auto-approved tools list**

```python
class Config:
    # ... existing config ...

    # Auto-approved tools (read-only operations)
    AUTO_APPROVED_TOOLS = [
        "browser_snapshot",
        "browser_screenshot",
        "browser_get_info",
        "browser_is_visible",
        "browser_is_enabled",
        "browser_is_checked",  # NEW
        "browser_get_url",
        "browser_console",  # NEW
        # DeepAgents built-in tools
        "ls",
        "read_file",
        "glob",
        "grep",
    ]

    # Approval-required tools (actions that modify state)
    APPROVAL_REQUIRED_TOOLS = [
        "browser_navigate",
        "browser_click",
        "browser_fill",
        "browser_type",
        "browser_press_key",
        "browser_eval",
        "browser_back",  # NEW
        "browser_forward",  # NEW
        "browser_reload",  # NEW
        "browser_hover",  # NEW
        "browser_check",  # NEW
        "browser_uncheck",  # NEW
        "browser_select",  # NEW
        "browser_close",
        # DeepAgents built-in tools
        "write_file",
        "edit_file",
        "execute",
    ]
```

**Step 2: Add tool categorization helper**

```python
class Config:
    # ... existing ...

    @classmethod
    def is_auto_approved(cls, tool_name: str) -> bool:
        """Check if a tool is auto-approved (read-only)."""
        return tool_name in cls.AUTO_APPROVED_TOOLS

    @classmethod
    def requires_approval(cls, tool_name: str) -> bool:
        """Check if a tool requires human approval."""
        return tool_name in cls.APPROVAL_REQUIRED_TOOLS
```

**Step 3: Test configuration**

Run: `cd browser-use-agent && uv run python -c "from browser_use_agent.configuration import Config; print('Auto:', Config.AUTO_APPROVED_TOOLS); print('Approval:', Config.APPROVAL_REQUIRED_TOOLS)"`

Expected: Prints updated tool lists correctly

**Step 4: Commit configuration**

```bash
git add browser-use-agent/browser_use_agent/configuration.py
git commit -m "feat: update tool approval configuration for new tools

- Add new tools to approval categories
- Add helper methods for checking tool approval status
- Categorize observation tools as auto-approved
- Categorize interaction/navigation tools as requiring approval

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Backend & Storage Layer

**Goal:** Implement dual database support (SQLite/PostgreSQL), integrate DeepAgents FilesystemBackend, and establish directory structure.

### Task 2.1: Create Storage Configuration Module

**Files:**
- Create: `browser-use-agent/browser_use_agent/storage/__init__.py`
- Create: `browser-use-agent/browser_use_agent/storage/config.py`
- Create: `browser-use-agent/browser_use_agent/storage/checkpoint.py`

**Step 1: Create storage package**

```bash
mkdir -p browser-use-agent/browser_use_agent/storage
```

**Step 2: Write storage configuration**

File: `browser-use-agent/browser_use_agent/storage/config.py`

```python
"""Storage configuration for browser agent."""

import os
from pathlib import Path
from typing import Optional


class StorageConfig:
    """Configuration for storage backends."""

    # Database type: 'sqlite' or 'postgres'
    DB_TYPE: str = os.getenv("CHECKPOINT_DB_TYPE", "sqlite")

    # SQLite configuration
    SQLITE_PATH: str = os.getenv(
        "SQLITE_PATH",
        ".browser-agent/checkpoints/browser_agent.db"
    )

    # PostgreSQL configuration
    POSTGRES_URI: str = os.getenv("DATABASE_URL", "")
    POSTGRES_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))

    # Supabase-specific (optional alternative to raw PostgreSQL)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Filesystem paths
    PROJECT_ROOT: Optional[Path] = None  # Auto-detected git root
    AGENT_DIR: str = ".browser-agent"

    @classmethod
    def get_agent_dir(cls) -> Path:
        """Get the .browser-agent directory path.

        Returns path relative to git root if detected, otherwise cwd.
        """
        if cls.PROJECT_ROOT is None:
            cls.PROJECT_ROOT = cls._detect_git_root()

        agent_dir = cls.PROJECT_ROOT / cls.AGENT_DIR
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    @classmethod
    def _detect_git_root(cls) -> Path:
        """Detect git repository root, fallback to cwd."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            return Path.cwd()

    @classmethod
    def get_checkpoint_path(cls) -> Path:
        """Get full path to SQLite checkpoint file."""
        if cls.DB_TYPE != "sqlite":
            raise ValueError("get_checkpoint_path only valid for sqlite DB_TYPE")

        checkpoint_path = cls.get_agent_dir() / "checkpoints" / "browser_agent.db"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        return checkpoint_path
```

**Step 3: Write checkpoint saver factory**

File: `browser-use-agent/browser_use_agent/storage/checkpoint.py`

```python
"""Checkpoint saver factory for dual database support."""

from typing import Union
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from browser_use_agent.storage.config import StorageConfig


async def get_checkpoint_saver() -> BaseCheckpointSaver:
    """Create checkpoint saver based on configuration.

    Returns:
        AsyncSqliteSaver for local development
        AsyncPostgresSaver for production

    Environment Variables:
        CHECKPOINT_DB_TYPE: 'sqlite' (default) or 'postgres'
        SQLITE_PATH: Path to SQLite database (default: .browser-agent/checkpoints/browser_agent.db)
        DATABASE_URL: PostgreSQL connection string
        DB_POOL_SIZE: PostgreSQL pool size (default: 10)
    """
    if StorageConfig.DB_TYPE == "postgres":
        if not StorageConfig.POSTGRES_URI:
            raise ValueError(
                "DATABASE_URL environment variable required for postgres DB_TYPE"
            )

        print(f"[Storage] Using PostgreSQL checkpoint saver")
        print(f"[Storage] Database: {StorageConfig.POSTGRES_URI.split('@')[-1]}")  # Hide credentials

        return AsyncPostgresSaver.from_conn_string(
            StorageConfig.POSTGRES_URI,
            pool_size=StorageConfig.POSTGRES_POOL_SIZE
        )
    else:
        checkpoint_path = StorageConfig.get_checkpoint_path()
        print(f"[Storage] Using SQLite checkpoint saver")
        print(f"[Storage] Database: {checkpoint_path}")

        return AsyncSqliteSaver.from_conn_string(str(checkpoint_path))


async def init_checkpoint_db():
    """Initialize checkpoint database tables.

    Must be called before using checkpoint saver.
    """
    saver = await get_checkpoint_saver()

    # Tables are auto-created on first use by LangGraph
    # This just ensures the connection works
    print(f"[Storage] Checkpoint database initialized successfully")

    return saver
```

**Step 4: Write storage package init**

File: `browser-use-agent/browser_use_agent/storage/__init__.py`

```python
"""Storage backends for browser agent."""

from browser_use_agent.storage.config import StorageConfig
from browser_use_agent.storage.checkpoint import (
    get_checkpoint_saver,
    init_checkpoint_db,
)

__all__ = [
    "StorageConfig",
    "get_checkpoint_saver",
    "init_checkpoint_db",
]
```

**Step 5: Test storage configuration**

Run: `cd browser-use-agent && uv run python -c "from browser_use_agent.storage import StorageConfig; print(StorageConfig.get_agent_dir())"`

Expected: Prints `.browser-agent` directory path

**Step 6: Commit storage configuration**

```bash
git add browser-use-agent/browser_use_agent/storage/
git commit -m "feat: add dual database storage configuration

- Create storage package with config and checkpoint modules
- Support SQLite (dev) and PostgreSQL (production) via env vars
- Auto-detect git root for project-aware storage
- Factory pattern for checkpoint saver creation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 2.2: Integrate FilesystemBackend from DeepAgents

**Files:**
- Modify: `browser-use-agent/browser_use_agent/browser_agent.py`
- Create: `browser-use-agent/browser_use_agent/middleware/__init__.py`

**Step 1: Create middleware package**

```bash
mkdir -p browser-use-agent/browser_use_agent/middleware
touch browser-use-agent/browser_use_agent/middleware/__init__.py
```

**Step 2: Update browser agent to use FilesystemBackend**

File: `browser-use-agent/browser_use_agent/browser_agent.py`

```python
"""Main browser automation agent implementation using DeepAgents library."""

import uuid
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage

try:
    from deepagents import create_deep_agent
    from deepagents.backend.filesystem import FilesystemBackend
    from deepagents.middleware.filesystem import FilesystemMiddleware
except ImportError:
    print("Error: deepagents library not installed. Please run:")
    print("  uv pip install deepagents")
    raise

from browser_use_agent.configuration import get_llm, Config
from browser_use_agent.prompts import get_system_prompt, RALPH_MODE_REFLECTION_PROMPT
from browser_use_agent.state import AgentState, create_initial_state
from browser_use_agent.tools import BROWSER_TOOLS
from browser_use_agent.storage import get_checkpoint_saver, StorageConfig


def create_browser_agent(
    model: Any = None,
    system_prompt: str = None,
    tools: List[Any] = None,
    checkpointer: Any = None,
    **kwargs
) -> Any:
    """Create a DeepAgents browser automation agent with filesystem backend.

    The agent includes:
    - Planning capabilities (write_todos tool)
    - File system tools for context management (ls, read_file, write_file, edit_file)
    - Subagent spawning for task delegation
    - Browser automation tools
    - State and memory management with checkpointing

    Args:
        model: Language model to use (defaults to Azure OpenAI from config)
        system_prompt: System prompt for the agent (defaults to BROWSER_AGENT_SYSTEM_PROMPT)
        tools: List of tools available to the agent (defaults to BROWSER_TOOLS)
        checkpointer: Checkpoint saver for persistence (defaults to storage config)
        **kwargs: Additional arguments for create_deep_agent

    Returns:
        Compiled LangGraph agent
    """
    # Use provided model or default to Azure OpenAI
    if model is None:
        model = get_llm()

    # Get system prompt
    prompt = get_system_prompt(system_prompt)

    # Use provided tools or default to browser tools
    if tools is None:
        tools = BROWSER_TOOLS

    # Get checkpoint saver if not provided
    if checkpointer is None:
        # Note: get_checkpoint_saver is async, but create_deep_agent expects sync
        # We'll handle async initialization separately in server.py
        print("[Agent] Using in-memory checkpointer (call init_checkpoint_db() for persistence)")
        checkpointer = None  # Will use InMemorySaver by default

    # Create filesystem backend
    # This provides the underlying file operations for FilesystemMiddleware
    agent_dir = StorageConfig.get_agent_dir()
    print(f"[Agent] Filesystem backend: {agent_dir}")

    filesystem_backend = FilesystemBackend(
        working_dir=str(agent_dir)
    )

    # Create filesystem middleware with custom backend
    filesystem_middleware = FilesystemMiddleware(
        backend=filesystem_backend
    )

    # Create agent using DeepAgents library
    # The create_deep_agent function includes:
    # - TodoListMiddleware (planning)
    # - FilesystemMiddleware (file ops - we override with custom backend)
    # - SubAgentMiddleware (task delegation)
    # - SummarizationMiddleware (context management)
    # - AnthropicPromptCachingMiddleware (caching)
    agent = create_deep_agent(
        model=model,
        system_prompt=prompt,
        tools=tools,
        middleware=[filesystem_middleware],  # Override default filesystem middleware
        checkpointer=checkpointer,
        **kwargs
    )

    return agent


# ... rest of file unchanged ...
```

**Step 3: Update server.py to initialize checkpoint database**

File: `browser-use-agent/server.py` (modify imports and initialization)

```python
# At top of file, add:
import asyncio
from browser_use_agent.storage import init_checkpoint_db

# Before creating the graph, add:
async def setup_storage():
    """Initialize storage backends."""
    checkpointer = await init_checkpoint_db()
    return checkpointer

# In main execution, update:
checkpointer = asyncio.run(setup_storage())
graph = create_browser_agent(checkpointer=checkpointer)
```

**Step 4: Test filesystem integration**

Run: `cd browser-use-agent && uv run python -c "from browser_use_agent.browser_agent import create_browser_agent; agent = create_browser_agent(); print('Agent created successfully')"`

Expected: Agent created with filesystem backend

**Step 5: Commit filesystem integration**

```bash
git add browser-use-agent/browser_use_agent/browser_agent.py browser-use-agent/browser_use_agent/middleware/ browser-use-agent/server.py
git commit -m "feat: integrate DeepAgents FilesystemBackend

- Use FilesystemBackend for file operations
- Configure working directory in .browser-agent/
- Initialize checkpoint database on server startup
- Add middleware package for future extensions

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 2.3: Create Directory Structure Initialization

**Files:**
- Create: `browser-use-agent/browser_use_agent/storage/init.py`

**Step 1: Write directory initialization script**

```python
"""Initialize .browser-agent directory structure."""

from pathlib import Path
from browser_use_agent.storage.config import StorageConfig


def init_agent_directories():
    """Create the standard .browser-agent directory structure.

    Creates:
        .browser-agent/
        ├── checkpoints/           # SQLite checkpoints (if local)
        ├── memory/                # Agent memory files
        │   ├── AGENTS.md
        │   ├── USER_PREFERENCES.md
        │   └── domains/           # Per-domain knowledge
        ├── skills/                # Auto-generated and custom skills
        ├── settings/              # Agent configuration
        │   ├── config.json
        │   └── credentials.json   # Encrypted credentials
        ├── artifacts/             # Session artifacts
        │   ├── screenshots/
        │   └── sessions/
        └── traces/                # Cached LangSmith traces
    """
    agent_dir = StorageConfig.get_agent_dir()

    # Create subdirectories
    subdirs = [
        "checkpoints",
        "memory",
        "memory/domains",
        "skills",
        "settings",
        "artifacts/screenshots",
        "artifacts/sessions",
        "traces",
    ]

    for subdir in subdirs:
        (agent_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Create initial memory files if they don't exist
    agents_md = agent_dir / "memory" / "AGENTS.md"
    if not agents_md.exists():
        agents_md.write_text("""# Browser Agent Memory

Last updated: (auto-updated on reflection)

## Learned Best Practices

(Auto-populated from reflection on LangSmith traces and diary entries)

## Domain-Specific Patterns

(Auto-populated with site-specific behaviors)

## Common Failure Patterns

(Auto-populated from error analysis)

## Skill Prerequisites

(Auto-populated when skills require credentials or data)
""")

    user_prefs_md = agent_dir / "memory" / "USER_PREFERENCES.md"
    if not user_prefs_md.exists():
        user_prefs_md.write_text("""# User Preferences

Max tokens: 2000 (enforced by UserPreferencesManager)

## UI Preferences

(User's preferred browser settings, viewport size, etc.)

## Workflow Preferences

(Common workflows and patterns)
""")

    # Create .gitignore in agent directory
    gitignore = agent_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("""# Ignore sensitive and generated files
settings/credentials.json
artifacts/sessions/
traces/
checkpoints/*.db
checkpoints/*.db-*

# Keep directory structure
!.gitkeep
""")

    print(f"[Storage] Initialized directory structure at {agent_dir}")
    return agent_dir


def get_or_create_user_agent_dir() -> Path:
    """Get or create user-level ~/.browser-agent directory.

    Creates:
        ~/.browser-agent/
        ├── memory/
        │   ├── AGENTS.md
        │   └── USER_PREFERENCES.md
        ├── skills/
        └── settings/
            └── global_config.json
    """
    user_dir = Path.home() / ".browser-agent"
    user_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (user_dir / "memory").mkdir(exist_ok=True)
    (user_dir / "skills").mkdir(exist_ok=True)
    (user_dir / "settings").mkdir(exist_ok=True)

    # Create initial files
    agents_md = user_dir / "memory" / "AGENTS.md"
    if not agents_md.exists():
        agents_md.write_text("# User-Level Agent Memory\n\n")

    user_prefs = user_dir / "memory" / "USER_PREFERENCES.md"
    if not user_prefs.exists():
        user_prefs.write_text("# Global User Preferences\n\n")

    return user_dir
```

**Step 2: Add init to storage package**

Modify `browser-use-agent/browser_use_agent/storage/__init__.py`:

```python
"""Storage backends for browser agent."""

from browser_use_agent.storage.config import StorageConfig
from browser_use_agent.storage.checkpoint import (
    get_checkpoint_saver,
    init_checkpoint_db,
)
from browser_use_agent.storage.init import (
    init_agent_directories,
    get_or_create_user_agent_dir,
)

__all__ = [
    "StorageConfig",
    "get_checkpoint_saver",
    "init_checkpoint_db",
    "init_agent_directories",
    "get_or_create_user_agent_dir",
]
```

**Step 3: Call initialization in browser_agent.py**

At the top of `create_browser_agent`:

```python
def create_browser_agent(...):
    # Initialize directory structure
    from browser_use_agent.storage import init_agent_directories
    init_agent_directories()

    # ... rest of function ...
```

**Step 4: Test directory creation**

Run: `cd browser-use-agent && uv run python -c "from browser_use_agent.storage import init_agent_directories; d = init_agent_directories(); print(f'Created: {d}')"`

Expected: Directory structure created with initial files

**Step 5: Commit directory initialization**

```bash
git add browser-use-agent/browser_use_agent/storage/init.py browser-use-agent/browser_use_agent/storage/__init__.py browser-use-agent/browser_use_agent/browser_agent.py
git commit -m "feat: add directory structure initialization

- Create .browser-agent/ directory tree
- Generate initial memory files (AGENTS.md, USER_PREFERENCES.md)
- Support both project-level and user-level directories
- Add .gitignore for sensitive files

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: Memory & Learning Layer

**Goal:** Implement LangSmith trace collection, session diary, reflection engine, and domain knowledge management.

### Task 3.1: LangSmith Trace Fetcher

**Files:**
- Create: `browser-use-agent/browser_use_agent/memory/__init__.py`
- Create: `browser-use-agent/browser_use_agent/memory/traces.py`

**Step 1: Create memory package**

```bash
mkdir -p browser-use-agent/browser_use_agent/memory
touch browser-use-agent/browser_use_agent/memory/__init__.py
```

**Step 2: Write LangSmith trace fetcher**

File: `browser-use-agent/browser_use_agent/memory/traces.py`

```python
"""LangSmith trace collection for learning from agent executions."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from langsmith import Client
except ImportError:
    print("Warning: langsmith not installed. Run: uv pip install langsmith")
    Client = None

from browser_use_agent.storage import StorageConfig


class LangSmithTraceFetcher:
    """Fetches and caches agent traces from LangSmith."""

    def __init__(self, project_name: str = "browser-agent"):
        """Initialize trace fetcher.

        Args:
            project_name: LangSmith project name
        """
        if Client is None:
            raise ImportError("langsmith package required. Run: uv pip install langsmith")

        self.client = Client()
        self.project_name = project_name
        self.cache_dir = StorageConfig.get_agent_dir() / "traces"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_recent_traces(
        self,
        hours: int = 24,
        filter_tags: Optional[List[str]] = None,
        min_feedback_score: float = 0.7
    ) -> List[Dict]:
        """Fetch successful traces from last N hours.

        Args:
            hours: Look back period
            filter_tags: Only fetch traces with these tags
            min_feedback_score: Minimum user feedback score (0-1)

        Returns:
            List of trace data dictionaries
        """
        end = datetime.now()
        start = end - timedelta(hours=hours)

        # Build filter query
        filter_query = f'and(eq(status, "success"), gt(feedback_score, {min_feedback_score}))'
        if filter_tags:
            tag_filters = " or ".join([f'eq(tags, "{tag}")' for tag in filter_tags])
            filter_query = f"and({filter_query}, or({tag_filters}))"

        print(f"[Traces] Fetching from LangSmith project: {self.project_name}")
        print(f"[Traces] Filter: {filter_query}")

        runs = self.client.list_runs(
            project_name=self.project_name,
            start_time=start,
            filter=filter_query
        )

        traces = []
        for run in runs:
            # Check cache first
            trace_path = self.cache_dir / f"{run.id}.json"
            if trace_path.exists():
                trace_data = json.loads(trace_path.read_text())
            else:
                # Extract and cache
                trace_data = self._extract_trace_data(run)
                trace_path.write_text(json.dumps(trace_data, indent=2))

            traces.append(trace_data)

        print(f"[Traces] Fetched {len(traces)} traces")
        return traces

    def _extract_trace_data(self, run) -> Dict:
        """Extract relevant data from LangSmith run."""
        return {
            "run_id": str(run.id),
            "task": run.inputs.get("task", ""),
            "steps": self._extract_steps(run),
            "success": run.status == "success",
            "feedback_score": run.feedback_stats.get("score", 0) if run.feedback_stats else 0,
            "duration_ms": run.total_tokens if hasattr(run, "total_tokens") else 0,
            "timestamp": run.start_time.isoformat() if run.start_time else "",
            "tags": run.tags or [],
            "metadata": run.extra or {},
        }

    def _extract_steps(self, run) -> List[Dict]:
        """Extract execution steps from run."""
        steps = []

        # Extract tool calls from run outputs
        if hasattr(run, "outputs") and run.outputs:
            messages = run.outputs.get("messages", [])
            for msg in messages:
                if hasattr(msg, "additional_kwargs"):
                    tool_calls = msg.additional_kwargs.get("tool_calls", [])
                    for tool_call in tool_calls:
                        steps.append({
                            "tool": tool_call.get("name", "unknown"),
                            "args": tool_call.get("args", {}),
                            "result": tool_call.get("result", ""),
                        })

        return steps

    def clear_cache(self, older_than_days: int = 30):
        """Remove cached traces older than N days.

        Args:
            older_than_days: Remove traces older than this many days
        """
        cutoff = datetime.now() - timedelta(days=older_than_days)
        removed = 0

        for trace_file in self.cache_dir.glob("*.json"):
            if trace_file.stat().st_mtime < cutoff.timestamp():
                trace_file.unlink()
                removed += 1

        print(f"[Traces] Removed {removed} cached traces older than {older_than_days} days")
```

**Step 3: Add dependencies**

Update `browser-use-agent/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "langsmith>=0.1.0",
]
```

**Step 4: Test trace fetcher**

Run: `cd browser-use-agent && uv pip install langsmith && uv run python -c "from browser_use_agent.memory.traces import LangSmithTraceFetcher; print('Trace fetcher imported successfully')"`

Expected: No errors, langsmith installed

**Step 5: Commit trace fetcher**

```bash
git add browser-use-agent/browser_use_agent/memory/ browser-use-agent/pyproject.toml
git commit -m "feat: add LangSmith trace fetcher for learning

- Implement LangSmithTraceFetcher for collecting successful traces
- Cache traces locally to avoid repeated API calls
- Filter by feedback score and tags
- Extract steps and metadata for analysis

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 3.2: Session Diary System

**Files:**
- Create: `browser-use-agent/browser_use_agent/memory/diary.py`

**Step 1: Write session diary implementation**

```python
"""Session diary for recording agent experiences."""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from browser_use_agent.storage import StorageConfig


class SessionDiary:
    """Records session experiences for later reflection."""

    def __init__(self):
        """Initialize session diary."""
        self.diary_dir = StorageConfig.get_agent_dir() / "memory" / "diary"
        self.diary_dir.mkdir(parents=True, exist_ok=True)
        self.processed_log = self.diary_dir / "processed.log"

    async def create_entry(
        self,
        session_id: str,
        accomplishments: List[str],
        challenges: List[str],
        design_decisions: Dict[str, str],
        user_feedback: Optional[str] = None
    ) -> Path:
        """Create a diary entry from session experience.

        Called automatically on session end or via explicit command.

        Args:
            session_id: Unique session identifier
            accomplishments: List of what was accomplished
            challenges: List of challenges encountered
            design_decisions: Dict of design decisions and rationale
            user_feedback: Optional user feedback

        Returns:
            Path to created diary entry file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        entry_file = self.diary_dir / f"{session_id}_{timestamp}.md"

        content = f"""# Session Diary Entry

**Session ID**: {session_id}
**Date**: {datetime.now().isoformat()}

## Accomplishments
{self._format_list(accomplishments)}

## Challenges Encountered
{self._format_list(challenges)}

## Design Decisions
{self._format_dict(design_decisions)}

## User Feedback
{user_feedback or "None provided"}

## Tags
{self._extract_tags(accomplishments, challenges)}
"""

        entry_file.write_text(content)
        print(f"[Diary] Created entry: {entry_file}")
        return entry_file

    def get_unprocessed_entries(self) -> List[Path]:
        """Get diary entries that haven't been reflected upon.

        Returns:
            List of unprocessed diary entry paths
        """
        processed = set()
        if self.processed_log.exists():
            processed = set(self.processed_log.read_text().splitlines())

        all_entries = list(self.diary_dir.glob("*.md"))
        return [e for e in all_entries if str(e) not in processed]

    def mark_processed(self, entry_path: Path):
        """Mark entry as processed to avoid re-analysis.

        Args:
            entry_path: Path to diary entry
        """
        with self.processed_log.open("a") as f:
            f.write(f"{entry_path}\n")
        print(f"[Diary] Marked as processed: {entry_path.name}")

    def _format_list(self, items: List[str]) -> str:
        """Format list as markdown."""
        if not items:
            return "- (None)\n"
        return "\n".join([f"- {item}" for item in items])

    def _format_dict(self, items: Dict[str, str]) -> str:
        """Format dict as markdown."""
        if not items:
            return "- (None)\n"
        return "\n".join([f"- **{k}**: {v}" for k, v in items.items()])

    def _extract_tags(self, accomplishments: List[str], challenges: List[str]) -> str:
        """Extract tags from accomplishments and challenges."""
        tags = set()

        # Extract domain from accomplishments/challenges
        all_text = " ".join(accomplishments + challenges).lower()

        # Common domains
        domains = ["google", "linkedin", "github", "amazon", "facebook"]
        for domain in domains:
            if domain in all_text:
                tags.add(domain)

        # Common task types
        if any(word in all_text for word in ["login", "auth", "signin"]):
            tags.add("authentication")
        if any(word in all_text for word in ["form", "fill", "submit"]):
            tags.add("form-filling")
        if any(word in all_text for word in ["search", "query"]):
            tags.add("search")
        if any(word in all_text for word in ["scrape", "extract", "data"]):
            tags.add("data-extraction")

        return ", ".join(sorted(tags)) if tags else "general"
```

**Step 2: Test diary system**

Run: `cd browser-use-agent && uv run python -c "import asyncio; from browser_use_agent.memory.diary import SessionDiary; d = SessionDiary(); asyncio.run(d.create_entry('test', ['Task 1'], ['Challenge 1'], {'Decision': 'Rationale'}))"`

Expected: Diary entry created in .browser-agent/memory/diary/

**Step 3: Commit diary system**

```bash
git add browser-use-agent/browser_use_agent/memory/diary.py
git commit -m "feat: add session diary system

- Implement SessionDiary for recording session experiences
- Track accomplishments, challenges, and design decisions
- Auto-extract tags from session content
- Support marking entries as processed for reflection

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 3.3: Reflection Engine

**Files:**
- Create: `browser-use-agent/browser_use_agent/memory/reflection.py`

**Step 1: Write reflection engine**

```python
"""Reflection engine for updating agent memory from experiences."""

import json
from pathlib import Path
from typing import List, Dict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from browser_use_agent.memory.diary import SessionDiary
from browser_use_agent.storage import StorageConfig


class ReflectionEngine:
    """Reflects on diary entries and updates procedural memory."""

    def __init__(self):
        """Initialize reflection engine."""
        self.diary = SessionDiary()
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.agents_md_path = StorageConfig.get_agent_dir() / "memory" / "AGENTS.md"
        self.reflection_dir = StorageConfig.get_agent_dir() / "memory" / "reflections"
        self.reflection_dir.mkdir(parents=True, exist_ok=True)

    async def reflect(self, force: bool = False) -> str:
        """Analyze unprocessed diary entries and update AGENTS.md.

        Similar to Claude Code's /reflect command:
        1. Load unprocessed diary entries
        2. Analyze each entry against existing rules
        3. Identify violations, patterns, new learnings
        4. Update AGENTS.md with synthesized rules
        5. Mark entries as processed

        Args:
            force: Force reflection even if no unprocessed entries

        Returns:
            Summary message
        """
        entries = self.diary.get_unprocessed_entries()
        if not entries and not force:
            return "[Reflection] No unprocessed diary entries"

        print(f"[Reflection] Processing {len(entries)} diary entries")

        # Load current rules
        current_rules = ""
        if self.agents_md_path.exists():
            current_rules = self.agents_md_path.read_text()

        all_insights = []

        # Analyze each entry
        for entry_path in entries:
            entry_content = entry_path.read_text()

            print(f"[Reflection] Analyzing: {entry_path.name}")
            analysis = await self._analyze_entry(entry_content, current_rules)
            all_insights.append(analysis)

            # Save individual reflection
            reflection_path = self.reflection_dir / f"{entry_path.stem}_reflection.md"
            reflection_path.write_text(self._format_reflection(analysis))

            # Mark processed
            self.diary.mark_processed(entry_path)

        # Synthesize all insights into rule updates
        print("[Reflection] Synthesizing insights into updated rules")
        updated_rules = await self._synthesize_rules(current_rules, all_insights)

        # Update AGENTS.md
        self.agents_md_path.write_text(updated_rules)
        print(f"[Reflection] Updated {self.agents_md_path}")

        return f"[Reflection] Reflected on {len(entries)} entries, updated AGENTS.md"

    async def _analyze_entry(self, entry: str, current_rules: str) -> Dict:
        """Analyze diary entry against existing rules.

        Args:
            entry: Diary entry content
            current_rules: Current AGENTS.md content

        Returns:
            Analysis dict with findings
        """
        prompt = f"""Analyze this session diary entry against existing agent rules:

CURRENT RULES:
{current_rules}

DIARY ENTRY:
{entry}

Identify:
1. **Rule Violations**: Did the session violate any existing rules?
2. **Weak Guidelines**: Are any rules too vague or not enforced?
3. **New Patterns**: Any recurring patterns not captured in rules?
4. **Domain Knowledge**: Site-specific learnings to document?
5. **Skill Opportunities**: Repeatable workflows to extract as skills?

Return JSON with analysis:
{{
  "rule_violations": [{{ "rule": "...", "violation": "..." }}],
  "weak_guidelines": [{{ "guideline": "...", "issue": "..." }}],
  "new_patterns": ["pattern1", "pattern2"],
  "domain_knowledge": {{ "domain": "...", "insights": ["..."] }},
  "skill_opportunities": [{{ "name": "...", "description": "..." }}]
}}
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            return {
                "rule_violations": [],
                "weak_guidelines": [],
                "new_patterns": [],
                "domain_knowledge": {},
                "skill_opportunities": []
            }

    async def _synthesize_rules(self, current_rules: str, insights: List[Dict]) -> str:
        """Synthesize insights into updated AGENTS.md content.

        Args:
            current_rules: Current AGENTS.md content
            insights: List of analysis results

        Returns:
            Updated AGENTS.md content
        """
        prompt = f"""Update agent memory rules based on reflection insights:

CURRENT RULES:
{current_rules}

INSIGHTS FROM SESSIONS:
{json.dumps(insights, indent=2)}

Generate updated AGENTS.md that:
1. Strengthens weak guidelines
2. Adds new patterns discovered
3. Documents domain-specific knowledge
4. Removes outdated rules
5. Maintains clear, actionable format

Keep token count under 5000.
Return ONLY the updated markdown content.
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    def _format_reflection(self, analysis: Dict) -> str:
        """Format analysis as markdown reflection.

        Args:
            analysis: Analysis dict

        Returns:
            Formatted markdown
        """
        return f"""# Reflection Analysis

## Rule Violations
{self._format_violations(analysis.get("rule_violations", []))}

## Weak Guidelines
{self._format_weak(analysis.get("weak_guidelines", []))}

## New Patterns
{self._format_list(analysis.get("new_patterns", []))}

## Domain Knowledge
{self._format_domain(analysis.get("domain_knowledge", {}))}

## Skill Opportunities
{self._format_skills(analysis.get("skill_opportunities", []))}
"""

    def _format_violations(self, violations: List[Dict]) -> str:
        if not violations:
            return "- (None detected)\n"
        return "\n".join([f"- **{v['rule']}**: {v['violation']}" for v in violations])

    def _format_weak(self, weak: List[Dict]) -> str:
        if not weak:
            return "- (None identified)\n"
        return "\n".join([f"- **{w['guideline']}**: {w['issue']}" for w in weak])

    def _format_list(self, items: List[str]) -> str:
        if not items:
            return "- (None)\n"
        return "\n".join([f"- {item}" for item in items])

    def _format_domain(self, domain: Dict) -> str:
        if not domain:
            return "- (None)\n"
        domain_name = domain.get("domain", "unknown")
        insights = domain.get("insights", [])
        return f"**{domain_name}**:\n" + "\n".join([f"- {i}" for i in insights])

    def _format_skills(self, skills: List[Dict]) -> str:
        if not skills:
            return "- (None)\n"
        return "\n".join([f"- **{s['name']}**: {s['description']}" for s in skills])
```

**Step 2: Test reflection engine**

Run: Manual test after creating a diary entry

Expected: Reflection analyzes entry and updates AGENTS.md

**Step 3: Commit reflection engine**

```bash
git add browser-use-agent/browser_use_agent/memory/reflection.py
git commit -m "feat: add reflection engine for memory updates

- Implement ReflectionEngine for analyzing diary entries
- Update AGENTS.md with synthesized learnings
- Identify rule violations, patterns, and skill opportunities
- Save individual reflection analyses

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 4: Middleware Stack

**Goal:** Implement browser-specific and production middleware for session management, human approval, trajectory logging, and error recovery.

### Task 4.1: Browser Session Middleware

**Files:**
- Create: `browser-use-agent/browser_use_agent/middleware/browser_session.py`

**Step 1: Write browser session middleware**

```python
"""Browser session middleware for managing session lifecycle."""

from typing import Any, Dict, Callable
from langchain.agents.middleware import AgentMiddleware
from langgraph.types import Command

from browser_use_agent.tools import (
    _update_browser_session,
    get_browser_session,
)


class BrowserSessionMiddleware(AgentMiddleware):
    """Manages browser session lifecycle and state."""

    async def before_agent(self, state: Dict, runtime: Any) -> Dict | Command:
        """Initialize browser session on agent start.

        Args:
            state: Agent state
            runtime: Runtime context

        Returns:
            Updated state or command
        """
        thread_id = runtime.config.get("configurable", {}).get("thread_id", "default")

        # Check if browser session exists
        session = get_browser_session(thread_id)
        if not session:
            # Initialize session metadata (browser not opened yet)
            _update_browser_session(thread_id, is_active=False, update_last_activity=False)
            print(f"[BrowserSession] Initialized session metadata for thread {thread_id}")
        else:
            print(f"[BrowserSession] Resuming existing session for thread {thread_id}")

        # Add session to state
        state["browser_session"] = get_browser_session(thread_id)
        return state

    async def after_agent(self, state: Dict, runtime: Any) -> Dict | Command:
        """Update browser session on agent end.

        Args:
            state: Agent state
            runtime: Runtime context

        Returns:
            Updated state or command
        """
        thread_id = runtime.config.get("configurable", {}).get("thread_id", "default")

        # Update last activity
        session = get_browser_session(thread_id)
        if session and session.get("isActive"):
            _update_browser_session(thread_id, is_active=True, update_last_activity=True)
            print(f"[BrowserSession] Updated last activity for thread {thread_id}")

        return state

    async def wrap_tool_call(
        self,
        state: Dict,
        runtime: Any,
        tool_call: Any,
        call_next: Callable
    ) -> Any:
        """Wrap tool calls to update session state.

        Args:
            state: Agent state
            runtime: Runtime context
            tool_call: Tool call details
            call_next: Next middleware in chain

        Returns:
            Tool result
        """
        tool_name = tool_call.get("name", "")
        thread_id = runtime.config.get("configurable", {}).get("thread_id", "default")

        # Track browser tool usage
        browser_tools = ["browser_navigate", "browser_click", "browser_fill", "browser_type"]
        if any(tool_name.startswith(bt) for bt in browser_tools):
            _update_browser_session(thread_id, is_active=True, update_last_activity=True)

        # Call next middleware
        result = await call_next()

        return result
```

**Step 2: Register middleware in browser_agent.py**

Update `create_browser_agent`:

```python
from browser_use_agent.middleware.browser_session import BrowserSessionMiddleware

def create_browser_agent(...):
    # ... existing code ...

    # Create middleware stack
    browser_session_mw = BrowserSessionMiddleware()

    agent = create_deep_agent(
        model=model,
        system_prompt=prompt,
        tools=tools,
        middleware=[
            filesystem_middleware,
            browser_session_mw,  # Add browser session middleware
        ],
        checkpointer=checkpointer,
        **kwargs
    )

    return agent
```

**Step 3: Test browser session middleware**

Run: Manual test with browser navigation

Expected: Session state tracked correctly

**Step 4: Commit browser session middleware**

```bash
git add browser-use-agent/browser_use_agent/middleware/browser_session.py browser-use-agent/browser_use_agent/browser_agent.py
git commit -m "feat: add browser session middleware

- Implement BrowserSessionMiddleware for session lifecycle
- Track session state and last activity
- Update session on browser tool usage
- Integrate with browser_agent

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 4.2: Human Approval Middleware

**Files:**
- Create: `browser-use-agent/browser_use_agent/middleware/human_approval.py`

**Step 1: Write human approval middleware**

```python
"""Human approval middleware for tool execution."""

from typing import Any, Dict, Callable
from langchain.agents.middleware import AgentMiddleware

from browser_use_agent.configuration import Config


class HumanApprovalMiddleware(AgentMiddleware):
    """Requires human approval for sensitive tool calls."""

    async def wrap_tool_call(
        self,
        state: Dict,
        runtime: Any,
        tool_call: Any,
        call_next: Callable
    ) -> Any:
        """Wrap tool calls to require approval for sensitive operations.

        Args:
            state: Agent state
            runtime: Runtime context
            tool_call: Tool call details
            call_next: Next middleware in chain

        Returns:
            Tool result
        """
        tool_name = tool_call.get("name", "")

        # Check if tool requires approval
        if Config.requires_approval(tool_name):
            # Queue for approval
            approval_item = {
                "tool": tool_name,
                "args": tool_call.get("args", {}),
                "status": "pending",
            }

            # Add to approval queue in state
            if "approval_queue" not in state:
                state["approval_queue"] = []
            state["approval_queue"].append(approval_item)

            print(f"[Approval] Queued for approval: {tool_name}")

            # In production, this would wait for human approval via UI
            # For now, we'll auto-approve in development
            # TODO: Implement actual approval mechanism
            approved = True

            if not approved:
                raise PermissionError(f"Tool {tool_name} requires human approval")

        # Call next middleware
        result = await call_next()

        return result
```

**Step 2: Add to middleware stack**

Update `create_browser_agent`:

```python
from browser_use_agent.middleware.human_approval import HumanApprovalMiddleware

def create_browser_agent(...):
    # ... existing code ...

    human_approval_mw = HumanApprovalMiddleware()

    agent = create_deep_agent(
        model=model,
        system_prompt=prompt,
        tools=tools,
        middleware=[
            filesystem_middleware,
            browser_session_mw,
            human_approval_mw,  # Add human approval middleware
        ],
        checkpointer=checkpointer,
        **kwargs
    )

    return agent
```

**Step 3: Test human approval middleware**

Run: Manual test with approval-required tool

Expected: Tool queued for approval

**Step 4: Commit human approval middleware**

```bash
git add browser-use-agent/browser_use_agent/middleware/human_approval.py browser-use-agent/browser_use_agent/browser_agent.py
git commit -m "feat: add human approval middleware

- Implement HumanApprovalMiddleware for sensitive operations
- Queue tools requiring approval
- Check against Config.APPROVAL_REQUIRED_TOOLS
- Placeholder for production approval mechanism

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 5: Skills System

**Goal:** Implement progressive skill loading (metadata → SKILL.md → supporting files) and skill discovery from successful traces.

### Task 5.1: Skill Loader with Progressive Disclosure

**Files:**
- Create: `browser-use-agent/browser_use_agent/skills/__init__.py`
- Create: `browser-use-agent/browser_use_agent/skills/loader.py`

**Step 1: Create skills package**

```bash
mkdir -p browser-use-agent/browser_use_agent/skills
```

**Step 2: Write skill loader**

File: `browser-use-agent/browser_use_agent/skills/loader.py`

```python
"""Skill loader with progressive disclosure."""

import json
from pathlib import Path
from typing import List, Dict, Optional

from browser_use_agent.storage import StorageConfig


class SkillLoader:
    """Loads skills with progressive disclosure pattern."""

    def __init__(self):
        """Initialize skill loader."""
        self.skills_dir = StorageConfig.get_agent_dir() / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def list_skills(self) -> List[Dict]:
        """List all available skills (metadata only).

        Returns:
            List of skill metadata dicts
        """
        skills = []

        for skill_file in self.skills_dir.glob("*.md"):
            metadata = self._extract_metadata(skill_file)
            if metadata:
                skills.append(metadata)

        return skills

    def load_skill(self, skill_name: str) -> Optional[str]:
        """Load full skill content.

        Args:
            skill_name: Name of skill to load

        Returns:
            Full skill markdown content or None
        """
        skill_file = self.skills_dir / f"{skill_name}.md"
        if not skill_file.exists():
            return None

        return skill_file.read_text()

    def load_skill_supporting_files(self, skill_name: str) -> Dict[str, str]:
        """Load supporting files for a skill.

        Args:
            skill_name: Name of skill

        Returns:
            Dict mapping filename to content
        """
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            return {}

        files = {}
        for file_path in skill_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(skill_dir)
                files[str(rel_path)] = file_path.read_text()

        return files

    def _extract_metadata(self, skill_file: Path) -> Optional[Dict]:
        """Extract YAML frontmatter metadata from skill file.

        Args:
            skill_file: Path to skill markdown file

        Returns:
            Metadata dict or None
        """
        content = skill_file.read_text()

        # Extract YAML frontmatter
        if not content.startswith("---"):
            return None

        try:
            _, frontmatter, _ = content.split("---", 2)
            metadata = {}

            for line in frontmatter.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

            metadata["file"] = skill_file.name
            return metadata
        except ValueError:
            return None

    def save_skill(
        self,
        skill_name: str,
        content: str,
        supporting_files: Optional[Dict[str, str]] = None
    ) -> Path:
        """Save a skill to disk.

        Args:
            skill_name: Name of skill
            content: Skill markdown content with YAML frontmatter
            supporting_files: Optional dict of supporting files

        Returns:
            Path to saved skill file
        """
        skill_file = self.skills_dir / f"{skill_name}.md"
        skill_file.write_text(content)

        # Save supporting files if provided
        if supporting_files:
            skill_dir = self.skills_dir / skill_name
            skill_dir.mkdir(exist_ok=True)

            for filename, file_content in supporting_files.items():
                file_path = skill_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_content)

        print(f"[Skills] Saved skill: {skill_name}")
        return skill_file
```

**Step 3: Test skill loader**

Run: Manual test with sample skill file

Expected: Skill metadata extracted and loaded correctly

**Step 4: Commit skill loader**

```bash
git add browser-use-agent/browser_use_agent/skills/
git commit -m "feat: add skill loader with progressive disclosure

- Implement SkillLoader for managing skills
- Support metadata extraction from YAML frontmatter
- Progressive loading: list → load → supporting files
- Save skills and supporting files

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 6: Enhanced UI Layer

**Goal:** Replace AzureChatOpenAI with ChatOpenAI, add reasoning display, enhance browser preview auto-show/hide, and add multimodal image upload.

### Task 6.1: Replace Azure OpenAI with ChatOpenAI

**Files:**
- Modify: `browser-use-agent/browser_use_agent/configuration.py`

**Step 1: Update LLM configuration**

```python
"""Configuration for browser agent."""

import os
from typing import Any, Optional
from langchain_openai import ChatOpenAI


class Config:
    # ... existing config ...

    # LLM Configuration - ChatOpenAI with reasoning API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")  # or "o4-mini"

    # Reasoning configuration
    REASONING_ENABLED: bool = os.getenv("REASONING_ENABLED", "true").lower() == "true"
    REASONING_EFFORT: str = os.getenv("REASONING_EFFORT", "medium")  # low, medium, high
    REASONING_SUMMARY: str = os.getenv("REASONING_SUMMARY", "detailed")  # brief, detailed

    # Legacy Azure config (deprecated)
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    DEPLOYMENT_NAME: str = os.getenv("DEPLOYMENT_NAME", "")


def get_llm() -> ChatOpenAI:
    """Get configured language model with reasoning support.

    Returns:
        ChatOpenAI instance configured for reasoning API
    """
    # Check for OpenAI API key
    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable required")

    # Configure reasoning if enabled
    reasoning_config = None
    if Config.REASONING_ENABLED:
        reasoning_config = {
            "effort": Config.REASONING_EFFORT,
            "summary": Config.REASONING_SUMMARY,
        }

    # Create ChatOpenAI with reasoning support
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        api_key=Config.OPENAI_API_KEY,
        temperature=0.7,
        streaming=True,
        use_responses_api=True,  # Enable responses API for reasoning
        reasoning=reasoning_config if Config.REASONING_ENABLED else None,
    )

    print(f"[LLM] Using ChatOpenAI model: {Config.OPENAI_MODEL}")
    if Config.REASONING_ENABLED:
        print(f"[LLM] Reasoning enabled: effort={Config.REASONING_EFFORT}, summary={Config.REASONING_SUMMARY}")

    return llm
```

**Step 2: Update dependencies**

Update `pyproject.toml`:

```toml
[project]
dependencies = [
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",  # Update from langchain-azure-openai
    "langgraph>=0.1.0",
    "deepagents>=0.1.0",
    # ... other dependencies ...
]
```

**Step 3: Test ChatOpenAI configuration**

Run: `cd browser-use-agent && OPENAI_API_KEY=sk-... uv run python -c "from browser_use_agent.configuration import get_llm; llm = get_llm(); print(llm)"`

Expected: ChatOpenAI instance created with reasoning config

**Step 4: Commit ChatOpenAI migration**

```bash
git add browser-use-agent/browser_use_agent/configuration.py browser-use-agent/pyproject.toml
git commit -m "feat: replace Azure OpenAI with ChatOpenAI

- Migrate from AzureChatOpenAI to ChatOpenAI
- Add reasoning API support (GPT-5, o4-mini)
- Configure reasoning effort and summary levels
- Update dependencies

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 6.2: Add Reasoning Display Component (Frontend)

**Files:**
- Create: `deep-agents-ui/src/app/components/ReasoningDisplay.tsx`

**Step 1: Write reasoning display component**

```typescript
"use client";

import React, { useState } from "react";
import { Sparkles } from "lucide-react";

interface ReasoningDisplayProps {
  reasoning: string;
  summary?: string;
}

export function ReasoningDisplay({ reasoning, summary }: ReasoningDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!reasoning) return null;

  return (
    <div className="reasoning-container bg-muted/50 border border-border rounded-lg p-4 my-2">
      <div
        className="flex items-center gap-2 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Sparkles className="w-4 h-4 text-primary" />
        <span className="text-sm font-medium">
          {isExpanded ? "Hide" : "Show"} thinking process
        </span>
      </div>

      {!isExpanded && summary && (
        <p className="text-xs text-muted-foreground italic mt-2">
          {summary}
        </p>
      )}

      {isExpanded && (
        <div className="mt-3 text-sm text-foreground/90 whitespace-pre-wrap animate-fade-in">
          {reasoning}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Add to ChatInterface**

Update `deep-agents-ui/src/app/components/ChatInterface.tsx`:

```typescript
import { ReasoningDisplay } from "./ReasoningDisplay";

// In message rendering:
{message.reasoning && (
  <ReasoningDisplay
    reasoning={message.reasoning}
    summary={message.reasoningSummary}
  />
)}
```

**Step 3: Test reasoning display**

Run: `cd deep-agents-ui && yarn dev`

Navigate to UI and trigger reasoning

Expected: Reasoning displays with collapsible preview

**Step 4: Commit reasoning display**

```bash
git add deep-agents-ui/src/app/components/ReasoningDisplay.tsx deep-agents-ui/src/app/components/ChatInterface.tsx
git commit -m "feat: add reasoning display component

- Create ReasoningDisplay component with Claude-style UI
- Collapsible with Sparkles icon
- Show summary preview when collapsed
- Integrate with ChatInterface

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-01-19-production-browser-agent.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach would you like to use?**
