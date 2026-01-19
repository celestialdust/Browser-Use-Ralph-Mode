# Task 2.2: Integrate FilesystemBackend from DeepAgents

**Status:** ✅ Completed
**Commit:** 0e0a5bd - "feat: integrate DeepAgents FilesystemBackend"
**Date:** 2026-01-19

## Overview

Integrated DeepAgents' `FilesystemBackend` to provide file system operations for the browser agent, enabling persistent context management across agent invocations.

## Files Modified

- `browser-use-agent/browser_use_agent/browser_agent.py`
  - Added `FilesystemBackend` initialization in `create_browser_agent()`
  - Configured backend to use `.browser-agent/` directory

## Implementation Details

### FilesystemBackend Configuration

**Location in Code:**
```python
def create_browser_agent(...):
    # Create filesystem backend
    agent_dir = StorageConfig.get_agent_dir()
    print(f"[Agent] Filesystem backend: {agent_dir}")

    filesystem_backend = FilesystemBackend(
        root_dir=str(agent_dir)
    )

    # Pass to create_deep_agent
    agent = create_deep_agent(
        model=model,
        system_prompt=prompt,
        tools=tools,
        backend=filesystem_backend,
        checkpointer=checkpointer,
        **kwargs
    )
```

### DeepAgents Middleware Stack

The `create_deep_agent()` function automatically includes:

1. **TodoListMiddleware** - Planning with `write_todos` tool
2. **FilesystemMiddleware** - File operations (configured via `backend` parameter)
   - `ls` - List directory contents
   - `read_file` - Read file contents
   - `write_file` - Write files
   - `edit_file` - Edit existing files
3. **SubAgentMiddleware** - Task delegation with `task` tool
4. **SummarizationMiddleware** - Context management

### File Operations Available to Agent

**Tools Provided by FilesystemMiddleware:**
- `ls(path)` - List files and directories
- `read_file(file_path)` - Read file contents
- `write_file(file_path, content)` - Create or overwrite files
- `edit_file(file_path, old_text, new_text)` - Edit existing files

**Root Directory:**
- All file operations scoped to `.browser-agent/` directory
- Agent cannot access files outside this sandbox
- Provides safe, isolated workspace for agent operations

## Integration with Storage System

**Storage Hierarchy:**
```
.browser-agent/                    # FilesystemBackend root
├── checkpoints/                   # Checkpoint storage
├── memory/                        # Agent memory files
│   ├── AGENTS.md                 # Editable by agent
│   └── USER_PREFERENCES.md       # Editable by agent
├── skills/                        # Custom skills
├── settings/                      # Configuration
├── artifacts/                     # Session artifacts
│   ├── screenshots/
│   └── sessions/
└── traces/                        # Cached traces
```

## Use Cases

### 1. Persistent Memory
Agent can write to `memory/AGENTS.md` to record learned patterns:
```python
# Agent action
edit_file("memory/AGENTS.md", "## Learned Best Practices",
          "## Learned Best Practices\n\n- Always snapshot before clicking")
```

### 2. Session Notes
Agent can create diary entries:
```python
write_file("artifacts/sessions/session-123.md", "# Session Notes\n\n...")
```

### 3. Skill Discovery
Agent can read available skills:
```python
skills = ls("skills/")
skill_content = read_file("skills/login.md")
```

## Testing

```bash
cd browser-use-agent
uv run python -c "
from browser_use_agent.browser_agent import create_browser_agent
agent = create_browser_agent()
print('Agent created with FilesystemBackend')
"
# Output: [Agent] Filesystem backend: /path/to/project/.browser-agent
```

## Prompt Caching Note

**Related Fix (commit f163fa2):**
- Disabled Anthropic prompt caching in `create_deep_agent()` call
- Added parameter: `use_prompt_caching=False`
- Reason: GPT-5 model doesn't support Anthropic's caching mechanism
- Prevents `TypeError: create_deep_agent() got an unexpected keyword argument 'use_prompt_caching'`

## Impact

- ✅ Agent can persist context across invocations
- ✅ File-based memory system for learned patterns
- ✅ Safe sandbox for agent file operations
- ✅ Foundation for reflection system (Task 3.x)
- ✅ Enables skill-based workflows

## Next Steps

- Task 2.3: Create directory structure initialization
- Task 3.2: Session diary system using file operations
- Task 5.1: Skill loader with progressive disclosure
