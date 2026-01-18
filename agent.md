# DeepAgents Browser-Use Agent Reference

This document contains key technical references for building a full-stack browser automation agent using LangChain DeepAgents, Ralph Mode, agent-browser streaming, and the DeepAgents UI.

## Table of Contents

1. [DeepAgents Overview](#deepagents-overview)
2. [Ralph Mode](#ralph-mode)
3. [Browser Streaming](#browser-streaming)
4. [Browser-Use Skills](#browser-use-skills)
5. [DeepAgents UI](#deepagents-ui)
6. [UI Design - Claude Style](#ui-design---claude-style)
7. [Integration Architecture](#integration-architecture)
8. [Environment Variables](#environment-variables)

---

## DeepAgents Overview

**Source**: [LangChain DeepAgents Docs](https://docs.langchain.com/oss/python/deepagents/overview)

### Purpose
DeepAgents is a standalone library for building agents that can tackle complex, multi-step tasks. Built on LangGraph and inspired by applications like Claude Code, Deep Research, and Manus.

### Core Capabilities

1. **Planning and Task Decomposition**
   - Built-in `write_todos` tool enables agents to break down complex tasks into discrete steps
   - Track progress and adapt plans as new information emerges

2. **Context Management**
   - File system tools: `ls`, `read_file`, `write_file`, `edit_file`
   - Allow agents to offload large context to memory
   - Prevents context window overflow
   - Enables work with variable-length tool results

3. **Subagent Spawning**
   - Built-in `task` tool enables spawning specialized subagents
   - Provides context isolation
   - Keeps main agent's context clean while going deep on specific subtasks

4. **Long-term Memory**
   - Extend agents with persistent memory across threads using LangGraph's Store
   - Agents can save and retrieve information from previous conversations

### When to Use Deep Agents

Use deep agents when you need agents that can:
- Handle complex, multi-step tasks requiring planning and decomposition
- Manage large amounts of context through file system tools
- Delegate work to specialized subagents for context isolation
- Persist memory across conversations and threads

### Technology Stack

- **LangGraph**: Provides underlying graph execution and state management
- **LangChain**: Tools and model integrations work seamlessly
- **LangSmith**: Observability, evaluation, and deployment

---

## Ralph Mode

**Sources**: 
- [LangChain DeepAgents Ralph Mode Example](https://github.com/langchain-ai/deepagents/tree/master/examples/ralph_mode)
- [LangChain LinkedIn Post](https://www.linkedin.com/posts/langchain-oss_ralph-mode-for-deep-agents-what-if-activity-7414709373324849153-h-wX)
- [Alibaba Cloud Blog](https://www.alibabacloud.com/blog/602799)

### What is Ralph Mode?

Ralph Mode is a looping paradigm that allows an agent to repeatedly attempt to fulfill a task over multiple iterations until completion or until reaching a maximum iteration threshold.

### Key Characteristics

- **Fresh Context Each Iteration**: Uses filesystem as memory between iterations
- **Iterative Improvement**: Agent can detect mistakes and correct them over time
- **Reduced Hallucination**: Multiple passes improve result quality
- **Long-horizon Tasks**: Suited for complex tasks requiring multiple refinement passes

### Usage Example

```bash
# Run agent in Ralph mode with 5 iterations
uv run deepagents --ralph "Build a Python programming course" --ralph-iterations 5
```

### Benefits

- Improves depth of responses
- Can correct mistakes over time
- Better for tasks like:
  - Improving drafts
  - Fixing bugs iteratively
  - Refining designs
  - Complex browser automation workflows

### Ralph Mode Workflow

1. Agent receives task
2. Plans approach and executes
3. Reflects on results
4. Updates state on disk (files/memory)
5. Loops back to step 2 until:
   - Success criteria met
   - Max iterations reached
   - Stopping condition triggered

---

## Browser Streaming

**Sources**: 
- [agent-browser Streaming Documentation](https://agent-browser.dev/streaming)
- [agent-browser GitHub Repository](https://github.com/vercel-labs/agent-browser)

### Overview

Streaming allows live preview or "pair browsing" where a human can watch and interact alongside an AI agent. The browser viewport is streamed via WebSocket with bidirectional communication.

### Enabling Streaming

Set the `AGENT_BROWSER_STREAM_PORT` environment variable before launching:

```bash
AGENT_BROWSER_STREAM_PORT=9223 agent-browser open example.com
```

This starts a WebSocket server on port 9223 that:
- Streams viewport frames (base64-encoded images)
- Accepts input events (mouse, keyboard, touch)

### WebSocket Protocol

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:9223');
```

#### Frame Messages

The server sends frame messages with base64-encoded images:

```json
{
  "type": "frame",
  "data": "<base64-encoded-jpeg>",
  "metadata": {
    "deviceWidth": 1280,
    "deviceHeight": 720,
    "pageScaleFactor": 1,
    "offsetTop": 0,
    "scrollOffsetX": 0,
    "scrollOffsetY": 0
  }
}
```

#### Status Messages

Connection and screencast status:

```json
{
  "type": "status",
  "connected": true,
  "screencasting": true,
  "viewportWidth": 1280,
  "viewportHeight": 720
}
```

### Input Injection

#### Mouse Events

```javascript
// Click
{
  "type": "input_mouse",
  "eventType": "mousePressed",
  "x": 100,
  "y": 200,
  "button": "left",
  "clickCount": 1
}

// Release
{
  "type": "input_mouse",
  "eventType": "mouseReleased",
  "x": 100,
  "y": 200,
  "button": "left"
}

// Move
{
  "type": "input_mouse",
  "eventType": "mouseMoved",
  "x": 150,
  "y": 250
}

// Scroll
{
  "type": "input_mouse",
  "eventType": "mouseWheel",
  "x": 100,
  "y": 200,
  "deltaX": 0,
  "deltaY": 100
}
```

#### Keyboard Events

```javascript
// Key down
{
  "type": "input_keyboard",
  "eventType": "keyDown",
  "key": "Enter",
  "code": "Enter"
}

// Key up
{
  "type": "input_keyboard",
  "eventType": "keyUp",
  "key": "Enter",
  "code": "Enter"
}

// Type character
{
  "type": "input_keyboard",
  "eventType": "char",
  "text": "a"
}

// With modifiers (1=Alt, 2=Ctrl, 4=Meta, 8=Shift)
{
  "type": "input_keyboard",
  "eventType": "keyDown",
  "key": "c",
  "code": "KeyC",
  "modifiers": 2
}
```

#### Touch Events

```javascript
// Touch start
{
  "type": "input_touch",
  "eventType": "touchStart",
  "touchPoints": [{ "x": 100, "y": 200 }]
}

// Touch move
{
  "type": "input_touch",
  "eventType": "touchMove",
  "touchPoints": [{ "x": 150, "y": 250 }]
}

// Touch end
{
  "type": "input_touch",
  "eventType": "touchEnd",
  "touchPoints": []
}

// Multi-touch (pinch zoom)
{
  "type": "input_touch",
  "eventType": "touchStart",
  "touchPoints": [
    { "x": 100, "y": 200, "id": 0 },
    { "x": 200, "y": 200, "id": 1 }
  ]
}
```

### Programmatic API

For advanced control via TypeScript:

```typescript
import { BrowserManager } from 'agent-browser';

const browser = new BrowserManager();
await browser.launch({ headless: true });
await browser.navigate('https://example.com');

// Start screencast with callback
await browser.startScreencast((frame) => {
  console.log('Frame:', frame.metadata.deviceWidth, 'x', frame.metadata.deviceHeight);
  // frame.data is base64-encoded image
}, {
  format: 'jpeg',  // or 'png'
  quality: 80,     // 0-100, jpeg only
  maxWidth: 1280,
  maxHeight: 720,
  everyNthFrame: 1
});

// Inject mouse event
await browser.injectMouseEvent({
  type: 'mousePressed',
  x: 100,
  y: 200,
  button: 'left',
  clickCount: 1
});

// Inject keyboard event
await browser.injectKeyboardEvent({
  type: 'keyDown',
  key: 'Enter',
  code: 'Enter'
});

// Inject touch event
await browser.injectTouchEvent({
  type: 'touchStart',
  touchPoints: [{ x: 100, y: 200 }]
});

// Check if screencasting
console.log('Active:', browser.isScreencasting());

// Stop screencast
await browser.stopScreencast();
```

### Use Cases

- **Pair browsing**: Human watches and assists AI agent in real-time
- **Remote preview**: View browser output in a separate UI
- **Recording**: Capture frames for video generation
- **Mobile testing**: Inject touch events for mobile emulation
- **Accessibility testing**: Manual interaction during automated tests

---

## Browser-Use Skills

**Sources**: 
- [Local SKILL.md](skills/SKILL.md)
- [agent-browser.dev](https://agent-browser.dev/)

### Skill Structure

Skills are modular capabilities stored in folders with a `SKILL.md` file containing:
- YAML frontmatter (name, description, triggers)
- Markdown documentation with commands and examples

### Core Workflow

1. **Navigate**: `agent-browser open <url>`
2. **Snapshot**: `agent-browser snapshot -i` (returns elements with refs like `@e1`, `@e2`)
3. **Interact**: Use refs from the snapshot
4. **Re-snapshot**: After navigation or significant DOM changes

### Key Commands by Category

#### Navigation
```bash
agent-browser open <url>      # Navigate to URL
agent-browser back            # Go back
agent-browser forward         # Go forward
agent-browser reload          # Reload page
agent-browser close           # Close browser
```

#### Snapshot (Page Analysis)
```bash
agent-browser snapshot            # Full accessibility tree
agent-browser snapshot -i         # Interactive elements only (recommended)
agent-browser snapshot -c         # Compact output
agent-browser snapshot -d 3       # Limit depth to 3
agent-browser snapshot -s "#main" # Scope to CSS selector
```

#### Interactions (use @refs from snapshot)
```bash
agent-browser click @e1           # Click
agent-browser fill @e2 "text"     # Clear and type
agent-browser type @e2 "text"     # Type without clearing
agent-browser press Enter         # Press key
agent-browser hover @e1           # Hover
agent-browser check @e1           # Check checkbox
agent-browser select @e1 "value"  # Select dropdown
agent-browser scroll down 500     # Scroll page
```

#### Information Retrieval
```bash
agent-browser get text @e1        # Get element text
agent-browser get html @e1        # Get innerHTML
agent-browser get value @e1       # Get input value
agent-browser get attr @e1 href   # Get attribute
agent-browser get title           # Get page title
agent-browser get url             # Get current URL
```

#### Screenshots & Recording
```bash
agent-browser screenshot          # Screenshot to stdout
agent-browser screenshot path.png # Save to file
agent-browser screenshot --full   # Full page
agent-browser pdf output.pdf      # Save as PDF
```

#### Video Recording
```bash
agent-browser record start ./demo.webm    # Start recording
agent-browser click @e1                   # Perform actions
agent-browser record stop                 # Stop and save video
```

#### Sessions (Parallel Browsers)
```bash
agent-browser --session test1 open site-a.com
agent-browser --session test2 open site-b.com
agent-browser session list
```

### Why Refs?

The `snapshot` command returns an accessibility tree where each element has a unique ref like `@e1`, `@e2`. This provides:

- **Deterministic**: Ref points to exact element from snapshot
- **Fast**: No DOM re-query needed
- **AI-friendly**: LLMs can reliably parse and use refs

---

## DeepAgents UI

**Source**: [DeepAgents UI GitHub](https://github.com/langchain-ai/deep-agents-ui)

### Overview

A Next.js application for interacting with DeepAgents via a web interface.

### Features

- Chat interface with agent (user messages ↔ agent replies)
- View agent's files/state through LangGraph state
- Multi-thread support with thread history
- Debug Mode for step-by-step execution
- Real-time streaming of agent actions

### Setup

```bash
# Clone and install
git clone https://github.com/langchain-ai/deep-agents-ui.git
cd deep-agents-ui
yarn install
yarn dev
```

### Configuration

Required settings (via UI or environment variables):

- **Deployment URL**: The URL for the LangGraph deployment (e.g., `http://127.0.0.1:2024`)
- **Assistant ID**: The ID of the assistant/agent (from `langgraph.json`)
- **LangSmith API Key** (optional): Format `lsv2_pt_...` (env var: `NEXT_PUBLIC_LANGSMITH_API_KEY`)

### Usage Modes

1. **Normal Mode**: Run agent end-to-end
2. **Debug Mode**: Execute agent step-by-step for development

### State Management

Uses LangGraph SDK's `useStream` hook with state type:

```typescript
export type StateType = {
  messages: Message[];
  todos: TodoItem[];
  files: Record<string, string>;
  email?: { id?: string; subject?: string; page_content?: string; };
  ui?: any;
};
```

---

## UI Design - Claude Style

**Design Philosophy**: Clean, minimal, thoughtful - inspired by Anthropic's Claude interface

### Core Aesthetic Principles

1. **Minimalism**: Remove unnecessary visual elements, focus on content
2. **Clarity**: Clear hierarchy, readable typography, purposeful spacing
3. **Thoughtfulness**: Show AI reasoning process transparently
4. **Responsiveness**: Smooth transitions, immediate feedback

### Color Palette

```css
/* Base Colors - Light Mode */
--background: #ffffff;
--surface: #f5f5f5;
--surface-secondary: #ebebeb;
--border: #e5e5e5;
--text-primary: #1a1a1a;
--text-secondary: #666666;
--text-muted: #999999;
--accent: #2f6868;
--accent-hover: #254f4f;

/* Semantic Colors */
--success: #16a34a;
--warning: #ea580c;
--error: #dc2626;
--info: #0284c7;
```

### Typography

```css
/* Font Stack */
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", 
             "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", 
             sans-serif;
--font-mono: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, 
             "Courier New", monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

### Key Components

#### 1. Thought Process Display

**Purpose**: Show agent's internal reasoning in real-time (like Claude's thinking display)

**Visual Design**:
- Collapsible section with subtle background (`--surface`)
- Expandable/collapsible with smooth animation
- Arrow indicator (▼ expanded, ▶ collapsed)
- Muted text color for reasoning steps
- Appears above agent's response

**Component Structure**:
```tsx
<ThoughtProcess>
  <ThoughtHeader>
    <Icon /> Thought process
    <ExpandIcon />
  </ThoughtHeader>
  <ThoughtContent>
    {/* Real-time streaming of agent's reasoning */}
    <ThoughtStep>Let me think about how to connect these:</ThoughtStep>
    <ThoughtList>
      <ThoughtItem>1. Analyze the user's request</ThoughtItem>
      <ThoughtItem>2. Plan browser navigation steps</ThoughtItem>
      <ThoughtItem>3. Execute commands with approval</ThoughtItem>
    </ThoughtList>
  </ThoughtContent>
</ThoughtProcess>
```

**CSS Styling**:
```css
.thought-process {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.thought-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
}

.thought-header:hover {
  background: var(--surface-secondary);
}

.thought-content {
  padding: 0 16px 16px 16px;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

.thought-step {
  margin-bottom: 12px;
  font-style: italic;
}

.thought-list {
  list-style: none;
  padding: 0;
}

.thought-item {
  padding: 4px 0;
  padding-left: 20px;
  position: relative;
}

.thought-item::before {
  content: "•";
  position: absolute;
  left: 8px;
  color: var(--text-muted);
}
```

#### 2. Chat Message Layout

**Structure**:
```tsx
<Message role={role}>
  {role === 'assistant' && thoughtProcess && (
    <ThoughtProcess content={thoughtProcess} />
  )}
  <MessageContent>
    {content}
  </MessageContent>
  {toolCalls && <ToolCallsDisplay calls={toolCalls} />}
  {browserPreview && <BrowserPreview streamUrl={streamUrl} />}
</Message>
```

**Styling**:
```css
.message {
  padding: 24px 0;
  border-bottom: 1px solid var(--border);
}

.message-content {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--text-primary);
}

.message-user {
  background: transparent;
}

.message-assistant {
  background: var(--surface);
  padding: 24px;
  border-radius: 8px;
}
```

#### 3. Browser Preview Card

**Design**:
- Clean card with subtle shadow
- Connection status indicator (green dot for active)
- Responsive image container
- Minimal controls

```css
.browser-preview {
  margin-top: 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--surface);
}

.browser-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  background: white;
}

.browser-preview-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
}

.browser-preview-image {
  width: 100%;
  height: auto;
  display: block;
}
```

#### 4. Approval Dialog

**Design**: Modal overlay with clear action buttons

```css
.approval-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
              0 10px 10px -5px rgba(0, 0, 0, 0.04);
  padding: 24px;
  max-width: 500px;
  width: 90%;
  z-index: 1000;
}

.approval-title {
  font-size: var(--text-lg);
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.approval-command {
  background: var(--surface);
  padding: 12px;
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  margin-bottom: 16px;
  border: 1px solid var(--border);
}

.approval-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.button-approve {
  background: var(--accent);
  color: white;
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.button-approve:hover {
  background: var(--accent-hover);
}

.button-reject {
  background: transparent;
  color: var(--text-secondary);
  padding: 10px 20px;
  border-radius: 6px;
  border: 1px solid var(--border);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.button-reject:hover {
  background: var(--surface);
  border-color: var(--text-secondary);
}
```

### Real-Time Streaming Implementation

**Thought Process Streaming**:
```typescript
// In ChatMessage component
const [thoughtProcess, setThoughtProcess] = useState<string>('');
const [isThinking, setIsThinking] = useState(false);

useEffect(() => {
  if (message.type === 'assistant' && message.metadata?.thinking) {
    setIsThinking(true);
    // Stream thinking text character by character for effect
    streamText(message.metadata.thinking, setThoughtProcess);
  }
}, [message]);

function streamText(text: string, setter: (value: string) => void) {
  let index = 0;
  const interval = setInterval(() => {
    if (index < text.length) {
      setter(text.slice(0, index + 1));
      index++;
    } else {
      clearInterval(interval);
      setIsThinking(false);
    }
  }, 10); // 10ms per character
}
```

**Agent State Updates**:
- Show todos being created/completed in real-time
- Display file operations as they happen
- Stream browser command execution status

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  Header (App Title, Settings, New Thread)               │
├──────────────┬──────────────────────────────────────────┤
│              │                                           │
│  Thread      │  Chat Messages                            │
│  List        │  ┌─────────────────────────────────────┐ │
│  (Sidebar)   │  │ User Message                        │ │
│              │  └─────────────────────────────────────┘ │
│              │  ┌─────────────────────────────────────┐ │
│              │  │ [Thought Process] ▼                 │ │
│              │  │ Let me navigate to...               │ │
│              │  │ 1. Open browser                     │ │
│              │  │ 2. Navigate to URL                  │ │
│              │  ├─────────────────────────────────────┤ │
│              │  │ Assistant Response                  │ │
│              │  │ I'll help you with that...          │ │
│              │  │ [Browser Preview]                   │ │
│              │  │ [Screenshot Image]                  │ │
│              │  └─────────────────────────────────────┘ │
│              │                                           │
├──────────────┴──────────────────────────────────────────┤
│  Input Area (Message input + Send button)               │
└─────────────────────────────────────────────────────────┘
```

### Animation Guidelines

```css
/* Smooth transitions */
* {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Fade in */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-enter {
  animation: fadeIn 0.3s ease;
}

/* Expand/collapse */
.thought-content {
  transition: max-height 0.3s ease, opacity 0.2s ease;
}

.thought-content.collapsed {
  max-height: 0;
  opacity: 0;
}

.thought-content.expanded {
  max-height: 500px;
  opacity: 1;
}
```

### Accessibility

- Use semantic HTML (`<article>`, `<section>`, `<button>`)
- ARIA labels for icon buttons
- Keyboard navigation support (Tab, Enter, Escape)
- Focus indicators for interactive elements
- Screen reader friendly status updates

### Responsive Design

```css
/* Mobile (< 768px) */
@media (max-width: 768px) {
  .thread-sidebar {
    position: fixed;
    left: -100%;
    transition: left 0.3s ease;
  }
  
  .thread-sidebar.open {
    left: 0;
  }
  
  .chat-main {
    width: 100%;
  }
}

/* Tablet (768px - 1024px) */
@media (min-width: 768px) and (max-width: 1024px) {
  .thread-sidebar {
    width: 280px;
  }
}

/* Desktop (> 1024px) */
@media (min-width: 1024px) {
  .thread-sidebar {
    width: 320px;
  }
}
```

---

## Integration Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                   │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │   Chat UI  │  │   Browser    │  │    Approval     │ │
│  │            │  │   Preview    │  │      UI         │ │
│  └────────────┘  └──────────────┘  └─────────────────┘ │
└─────────────┬───────────┬─────────────────┬─────────────┘
              │           │                 │
         HTTP │           │ WebSocket       │ HTTP
              │           │                 │
┌─────────────▼───────────▼─────────────────▼─────────────┐
│              Backend (Python + LangGraph)                │
│  ┌──────────────────────────────────────────────────┐   │
│  │         DeepAgents (Ralph Mode)                  │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────┐  │   │
│  │  │  Planning  │  │   Browser    │  │ Approval│  │   │
│  │  │   (todos)  │  │    Skills    │  │  Logic  │  │   │
│  │  └────────────┘  └──────────────┘  └─────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│                           │                              │
│                           ▼                              │
│                  ┌─────────────────┐                     │
│                  │  Azure OpenAI   │                     │
│                  │    (GPT-5)      │                     │
│                  └─────────────────┘                     │
└───────────────────────────┬──────────────────────────────┘
                            │
                            │ subprocess calls
                            │
┌───────────────────────────▼──────────────────────────────┐
│              agent-browser CLI + Browser                 │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Browser   │  │   Session    │  │   WebSocket     │  │
│  │  Commands  │  │  Management  │  │    Streaming    │  │
│  └────────────┘  └──────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User sends command** → Chat UI → Backend DeepAgent
2. **Agent plans** → Uses `write_todos` to break down task
3. **Agent executes browser skill** → Calls `agent-browser` CLI with session ID
4. **Browser streams viewport** → WebSocket to Frontend Browser Preview
5. **Action commands trigger approval** → Backend sends interrupt → Approval UI
6. **User approves/rejects** → Frontend sends `resumeInterrupt` → Backend continues/aborts
7. **Results returned** → Chat UI displays response

### Thread Isolation

- Each thread gets unique ID
- Browser session uses `--session {thread_id}` for isolation
- Separate WebSocket stream per thread (port = base_port + hash(thread_id))
- Independent state, files, and memory per thread

---

## Environment Variables

### Python Backend

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
OPENAI_API_VERSION=2024-02-15-preview

# LangSmith (for observability)
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_TRACING_V2=true

# Browser Streaming
AGENT_BROWSER_STREAM_PORT=9223

# Optional: Browser-Use Skills API
BROWSER_USE_API_KEY=your_browser_use_key
```

### Frontend (Next.js)

```bash
# Optional: Pre-configure LangSmith API Key
NEXT_PUBLIC_LANGSMITH_API_KEY=lsv2_pt_...
```

### LangChain Model Configuration

```python
from langchain_openai import AzureChatOpenAI

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    deployment_name="gpt-5",  # or your deployment name
    temperature=0,
    model_kwargs={
        "top_p": 0.95,
    }
)
```

---

## Command Reference Quick Guide

### DeepAgents CLI

```bash
# Run agent with Ralph mode
deepagents --ralph "Your task description" --ralph-iterations 5

# List available skills
deepagents skills list

# Run agent with specific skills
deepagents --skills browser-use "Navigate to example.com"
```

### agent-browser Commands

```bash
# Basic navigation with session and streaming
AGENT_BROWSER_STREAM_PORT=9223 agent-browser --session thread_123 open example.com

# Get interactive elements
agent-browser --session thread_123 snapshot -i --json

# Interact with elements
agent-browser --session thread_123 click @e1
agent-browser --session thread_123 fill @e2 "text input"

# Get information
agent-browser --session thread_123 get text @e1
agent-browser --session thread_123 screenshot output.png

# Close session
agent-browser --session thread_123 close
```

### LangGraph Development

```bash
# Start local development server
langgraph dev --port 2024

# Deploy to LangGraph Cloud
langgraph deploy

# Test deployed agent
langgraph test
```

---

## Development Workflow

### 1. Backend Setup

```bash
# Create Python project
mkdir browser-use-agent
cd browser-use-agent

# Initialize with uv or pip
uv init  # or python -m venv .venv

# Install dependencies
uv add deepagents langchain-openai langgraph

# Install agent-browser globally
npm install -g agent-browser

# Create .env file with credentials
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### 2. Frontend Setup

```bash
# Navigate to deep-agents-ui
cd deep-agents-ui

# Install dependencies
yarn install

# Start development server
yarn dev
```

### 3. Running the System

```bash
# Terminal 1: Start backend
cd browser-use-agent
langgraph dev --port 2024

# Terminal 2: Start frontend
cd deep-agents-ui
yarn dev

# Terminal 3: Verify agent-browser
agent-browser --version

# Browser: Open http://localhost:3000
# Configure: Deployment URL = http://127.0.0.1:2024
#            Assistant ID = browser-agent
```

---

## Testing Scenarios

### Basic Browser Navigation

```
User: "Navigate to example.com and tell me the title"
Expected:
1. Agent plans task
2. Executes: agent-browser open example.com
3. Executes: agent-browser get title
4. Returns: "Example Domain"
```

### Interactive Form Filling (with approval)

```
User: "Go to contact form and fill in name 'John Doe'"
Expected:
1. Agent navigates to page
2. Gets snapshot to find form elements
3. **Requests approval** for fill command
4. User approves in UI
5. Agent fills form
6. Returns confirmation
```

### Multi-step Research with Ralph Mode

```
User: "Research the top 3 features of Next.js from their docs"
Expected:
1. Agent plans research approach (writes todos)
2. Iteration 1: Navigates to Next.js docs, takes screenshots
3. Iteration 2: Reads specific sections, extracts text
4. Iteration 3: Summarizes findings, creates file
5. Returns: List of top 3 features with sources
```

---

## Troubleshooting

### Browser Session Issues

```bash
# List active sessions
agent-browser session list

# Close stuck session
agent-browser --session thread_123 close

# Clear all sessions
pkill -f "agent-browser"
```

### Streaming Connection Issues

```bash
# Check if WebSocket port is listening
lsof -i :9223

# Test WebSocket connection
curl --include --no-buffer \
  --header "Connection: Upgrade" \
  --header "Upgrade: websocket" \
  http://localhost:9223/
```

### DeepAgents Debugging

```bash
# Enable debug logging
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
export LANGCHAIN_PROJECT="browser-agent-debug"

# Run with verbose output
langgraph dev --verbose
```

---

## Additional Resources

- [LangChain DeepAgents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [agent-browser Documentation](https://agent-browser.dev/)
- [DeepAgents UI GitHub](https://github.com/langchain-ai/deep-agents-ui)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Platform](https://smith.langchain.com/)

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Maintained By**: Browser-Use Agent Development Team
