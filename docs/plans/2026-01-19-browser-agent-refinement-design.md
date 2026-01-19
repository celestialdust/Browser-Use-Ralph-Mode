# Browser Agent Refinement Design

**Date**: 2026-01-19
**Status**: Approved

## Overview

This document outlines 8 tasks to refine the Browser Use agent system, covering frontend UI changes, error handling, prompt refinement, reflection/skill creation, structured tool output, and image upload capabilities.

---

## Task 1: Remove Status from ThreadList

### Changes
- **Remove**: Status filter dropdown ("All", "Idle", "Busy", "Interrupted", "Error")
- **Remove**: Colored status dots next to each thread
- **Remove**: "Requiring Attention" grouping for interrupted threads
- **Keep**: Thread list with title, date grouping (Today, Yesterday, This Week, Older)

### Files
- `deep-agents-ui/src/app/components/ThreadList.tsx`

---

## Task 2: Reasoning Display Markdown Rendering

### Changes
- **Remove**: Sparkling star icon from "Show thinking process" header
- **Add**: Markdown rendering using `react-markdown` for both components
- **Keep**: Collapsible behavior, streaming support

### Files
- `deep-agents-ui/src/app/components/ThoughtProcess.tsx`
- `deep-agents-ui/src/app/components/ReasoningDisplay.tsx`

---

## Task 3: Recursion Limit & Stop Mechanisms

### Changes
- **Remove**: ConfigDialog input field for recursion limit
- **Hardcode**: High value (5000) in config
- **Stop Triggers**:
  1. User clicks stop button
  2. Error occurs → immediate stop
  3. Recursion limit reached → stop with message

### Error-Triggered Stop Behavior
- Display error message in chat
- Halt agent execution immediately
- Offer retry option

### Files
- `deep-agents-ui/src/lib/config.ts`
- `deep-agents-ui/src/app/components/ConfigDialog.tsx`
- `deep-agents-ui/src/hooks/useChat.ts`

---

## Task 4: Prompt Refinement & Context Loading

### Context Loading Order (Before Agent Initiates)
1. **AGENTS.md** - Synthesized rules (as `<project_memory>`)
2. **agent.md** - Technical reference (as `<agent_memory>`)
3. **Skills metadata** - Progressive disclosure list

### Revised XML Prompt Structure

```xml
<system>
  <role>Browser automation agent with visual and DOM capabilities</role>

  <agent_memory>
    <!-- agent.md content injected here -->
  </agent_memory>

  <project_memory>
    <!-- AGENTS.md synthesized rules injected here -->
  </project_memory>

  <task_management>
    When using write_todos:
    1. Keep todo list MINIMAL - aim for 3-6 items maximum
    2. Only create todos for complex, multi-step tasks
    3. Break down work into clear, actionable items without over-fragmenting
    4. For simple tasks (1-2 steps), just do them directly
    5. When first creating a todo list, ALWAYS ask user if plan looks good before starting
    6. Update todo status promptly as you complete each item
  </task_management>

  <file_management>
    When reading files, use pagination to prevent context overflow:
    - First scan: read_file(path, limit=100) - See structure
    - Targeted read: read_file(path, offset=100, limit=200) - Specific sections
    - Full read: Only when necessary for editing

    All file paths must be absolute (start with /).
  </file_management>

  <subagents>
    When delegating to subagents:
    - Use filesystem for large I/O (>500 words) - communicate via files
    - Parallelize independent work - spawn parallel subagents
    - Clear specifications - tell subagent exact format/structure needed
    - Main agent synthesizes - subagents gather/execute, main integrates
  </subagents>

  <browser_tools>
    <approach>
      DOM-first with visual fallback:
      1. Try browser_snapshot (DOM approach) first
      2. If snapshot fails/unusable, fall back to browser_screenshot(filepath)
      3. Process screenshot visually using GPT-5/o4-mini to decide next moves
    </approach>

    <tools>
      Core: navigate, snapshot, click, fill, type, press_key, screenshot, scroll
      Navigation: back, forward, reload
      Info: get_info, console
      Lifecycle: close
    </tools>

    <output_format>
      All browser tools return structured output:
      - action: What was performed
      - observation: What was observed
      - next_step: Suggested next action
      - filepath: Path to full output file
    </output_format>
  </browser_tools>

  <human_tools>
    request_human_guidance, request_credentials, request_confirmation
  </human_tools>

  <skills>
    <!-- Progressive disclosure: names + descriptions loaded here -->

    How to use skills:
    1. Recognize when a skill applies to the task
    2. Read full skill instructions when needed
    3. Follow step-by-step workflows
    4. Access supporting files via absolute paths
  </skills>

  <workflow>
    1. Check filesystem for existing context/skills
    2. Plan with write_todos (if complex task)
    3. Execute browser commands (DOM-first, visual fallback)
    4. Handle obstacles (retry, human guidance, visual approach)
    5. On completion: close browser → trigger reflection
  </workflow>

  <constraints>
    - Never store/log credentials
    - Request human confirmation for financial operations
    - Request human confirmation for irreversible actions
    - Always close browser when task complete
  </constraints>

  <reflection>
    After browser_close:
    1. Call reflection tool to analyze session
    2. Identify patterns worth saving as skills
    3. Update AGENTS.md with learnings
  </reflection>
</system>
```

### Key Patterns (from DeepAgents CLI)
- Task management: 3-6 todos max, ask approval before starting
- File pagination: limit/offset pattern for large files
- Subagent delegation: filesystem for large I/O, parallelize independent work
- Skills progressive disclosure: metadata first, full content on-demand
- Absolute paths: All file operations use absolute paths

### Files
- `browser-use-agent/browser_use_agent/prompts.py`
- `browser-use-agent/browser_use_agent/browser_agent.py`

---

## Task 5: Error Handling Reinforcement

### WebSocket Error Handling
- Show visible error banner when WebSocket disconnects
- Exponential backoff for reconnection (1s, 2s, 4s, 8s, 16s)
- Clear "Reconnecting..." status in BrowserPanel
- After max retries, show "Connection lost" with manual retry button
- Auto-stop agent execution if stream is critical to task

### LangGraph API Error Handling
- Catch and display specific error types (timeout, 500, 401, network)
- Show user-friendly error messages in chat
- Auto-stop agent on fatal errors (auth, server down)
- Add request timeout handling (configurable, default 60s)
- Retry transient errors (503, network) with backoff

### Error State UI
- Consistent error banner component
- States: Warning (yellow), Error (red), Info (blue)
- Actions: Retry, Dismiss, View Details

### Files
- `deep-agents-ui/src/app/components/BrowserPanel.tsx`
- `deep-agents-ui/src/hooks/useChat.ts`
- `deep-agents-ui/src/app/components/ChatInterface.tsx`

---

## Task 6: Reflection & Skill Creation

### Reflection Trigger Flow
```
browser_close called
    ↓
Agent calls reflect_on_session tool
    ↓
Reflection tool:
  1. Analyzes session diary entries
  2. Identifies patterns, learnings, potential skills
  3. Updates AGENTS.md with new rules
    ↓
If skill opportunity identified:
    ↓
Trigger skill creator (from LangChain deepagents)
    ↓
Save new skill to .browser-agent/skills/
```

### New Reflection Tool
```python
@tool
def reflect_on_session(thread_id: str) -> ReflectionOutput:
    """
    Analyze the current session and extract learnings.
    Called after browser_close to capture insights.
    """
    # Returns structured output:
    # - accomplishments: List[str]
    # - challenges: List[str]
    # - learnings: List[str]
    # - skill_opportunities: List[SkillOpportunity]
    # - rules_to_add: List[str]
```

### Skill Creator Integration
- **Source**: https://github.com/langchain-ai/deepagents/tree/master/libs/deepagents-cli/examples/skills/skill-creator
- **Trigger**: When `reflect_on_session` identifies a `skill_opportunity`
- **Output**: New `.md` skill file + optional supporting files

### Frontend Skill Management UI
Location: ConfigDialog (Settings) - compact section

```
┌─────────────────────────────────────┐
│ Skills                              │
│ ┌─────────────────────────────────┐ │
│ │ ☑ linkedin-login    [×]         │ │
│ │   Login to LinkedIn and...      │ │
│ ├─────────────────────────────────┤ │
│ │ ☑ google-search     [×]         │ │
│ │   Search Google effe...         │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

- Description truncated with ellipsis at ~50 chars
- Inline delete button (×)
- Enable/disable toggle
- Compact row height

### Files
- `browser-use-agent/browser_use_agent/tools.py` (new reflection tool)
- `browser-use-agent/browser_use_agent/reflection.py` (integrate skill creator)
- `deep-agents-ui/src/app/components/ConfigDialog.tsx` (skill management UI)

---

## Task 7: Structured Browser Tool Output

### Pydantic Model
```python
from pydantic import BaseModel, Field

class BrowserToolOutput(BaseModel):
    """Structured output for all browser tool calls."""

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
```

### Output File Structure
- **Location**: `.browser-agent/artifacts/tool_outputs/`
- **Filename**: `{tool_name}_{timestamp}.txt`
- **Content**: Full raw output from agent-browser command

### Tools to Keep (14 total)

**Core (8)**:
- `browser_navigate` → action: "Navigated to {url}"
- `browser_snapshot` → action: "Captured DOM snapshot"
- `browser_click` → action: "Clicked {ref}"
- `browser_fill` → action: "Filled {ref} with text"
- `browser_type` → action: "Typed into {ref}"
- `browser_press_key` → action: "Pressed {key}"
- `browser_screenshot` → action: "Captured screenshot" (filepath required)
- `browser_scroll` → action: "Scrolled {direction}" *(new)*

**Navigation (3)**:
- `browser_back` → action: "Navigated back"
- `browser_forward` → action: "Navigated forward"
- `browser_reload` → action: "Reloaded page"

**Info (2)**:
- `browser_get_info` → action: "Retrieved {info_type}"
- `browser_console` → action: "Retrieved console logs"

**Lifecycle (1)**:
- `browser_close` → action: "Closed browser session"

### Tools to Remove (4 total)
- ~~`browser_wait`~~ - removed
- ~~`browser_is_visible`~~ - removed
- ~~`browser_is_enabled`~~ - removed
- ~~`browser_is_checked`~~ - removed

### New browser_scroll Tool
```python
@tool
def browser_scroll(
    direction: str = Field(description="Scroll direction: 'up', 'down', 'top', 'bottom'"),
    amount: int = Field(default=500, description="Pixels to scroll (ignored for top/bottom)"),
    thread_id: str = Field(description="Browser session ID")
) -> BrowserToolOutput:
    """Scroll the page to load dynamic content or reach elements."""
```

### Files
- `browser-use-agent/browser_use_agent/tools.py`
- `browser-use-agent/browser_use_agent/prompts.py`

---

## Task 8: Image Upload & Visual Processing

### Chat Input Layout
```
┌─────────────────────────────────────────────────┐
│ [📎]  Type your message...              [Send →]│
└─────────────────────────────────────────────────┘
  ↑                                            ↑
  Upload (left)                        Send (right)
```

### Image Preview (Expands Upward)
```
┌─────────────────────────────────────────────────┐
│ [Existing filesystem preview - if present]      │
├─────────────────────────────────────────────────┤
│ [Image preview - if image attached]       [×]   │
├─────────────────────────────────────────────────┤
│ [📎]  Type your message...              [Send →]│
└─────────────────────────────────────────────────┘
```

### Constraints
- **One image per send** - Upload button disabled when image attached
- **Remove with ×** - Clear image to upload a different one
- **Separate from file preview** - Image preview renders in its own container

### Upload Button Behavior
- **Click**: Opens file picker (one image: jpg, png, gif, webp)
- **State**: Disabled when image already attached
- **Clear**: × button removes image, re-enables upload

### Backend Integration
- Images sent as base64 in message content (multimodal)
- **Visual processing model**: GPT-5 or o4-mini (required for image/screenshot analysis)
- Agent can reference uploaded images for visual analysis
- Works alongside browser screenshots for visual fallback
- When visual fallback is triggered (screenshot), route to GPT-5/o4-mini for processing

### Files
- `deep-agents-ui/src/app/components/ChatInput.tsx` (or equivalent)
- `deep-agents-ui/src/app/components/ChatMessage.tsx`
- `deep-agents-ui/src/context/ChatProvider.tsx`

---

## Implementation Order

Suggested order based on dependencies:

1. **Task 7**: Structured browser tool output (foundation for other changes)
2. **Task 4**: Prompt refinement (depends on tool structure)
3. **Task 1**: Remove status from ThreadList (independent UI change)
4. **Task 2**: Reasoning markdown rendering (independent UI change)
5. **Task 3**: Recursion limit & stop mechanisms
6. **Task 5**: Error handling reinforcement
7. **Task 6**: Reflection & skill creation
8. **Task 8**: Image upload & visual processing
