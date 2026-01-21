# Browser Use - Full-Stack Agent with DeepAgents & Ralph Mode

A complete browser automation system combining [LangChain DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) with [agent-browser](https://agent-browser.dev/), featuring Ralph Mode for iterative refinement and a Claude-inspired UI.

![Browser Use Agent](https://img.shields.io/badge/Status-Alpha-yellow)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)
![Node 18+](https://img.shields.io/badge/Node-18+-green)
![License MIT](https://img.shields.io/badge/License-MIT-lightgrey)

## Overview

Browser Use is a full-stack browser automation agent that can:
- **Plan and execute** complex multi-step browser tasks
- **Self-correct** using Ralph Mode's iterative refinement
- **Control browsers** via `agent-browser` CLI
- **Stream live** browser viewport via WebSocket
- **Show thinking** in real-time like Claude
- **Request approval** for sensitive actions
- **Isolate sessions** per conversation thread

## Features

### DeepAgents Integration
- **Planning & Decomposition**: Built-in `write_todos` tool with parallel vs sequential task identification
- **File System Tools**: Manage large context with filesystem
- **Parallel Subagents**: Spawn multiple subagents concurrently for independent tasks
- **File-Based Results**: Subagents write results to files and return paths to avoid context bloat
- **Long-term Memory**: Persistent state across conversations

### Skills System
- **Document Skills**: PDF, PPTX, DOCX manipulation
- **Browser Skills**: Automated browser interactions
- **Skill Creator**: Guide for building custom skills
- **Settings Integration**: View and manage skills in UI

### Memory Management
- **AGENTS.md**: Store learned patterns with enforced structure
- **USER_PREFERENCES.md**: Store user preferences with standardized sections
- **Diary**: Record task completions and learnings
- **Skills**: Create reusable workflows

### Human-in-the-Loop
- **Guidance Requests**: Agent can ask for help when stuck
- **Credential Requests**: Secure credential input form in UI
- **Confirmation Dialogs**: Approve/reject risky actions
- **Subagent Support**: Interrupts from subagents surface to UI

### Bash Execution
- **Script Execution**: Run Python/Node scripts
- **Package Installation**: pip/npm install commands
- **Security Tiers**: Auto-approve safe, require approval for others, block dangerous
- **Unified Root**: All paths resolve relative to `.browser-agent/`

### Ralph Mode
- **Iterative Refinement**: Agent retries with improvements
- **Self-Reflection**: Reviews mistakes and adapts approach
- **Persistent Memory**: Uses filesystem between iterations
- **Configurable Iterations**: Set max attempts per task

### Browser Automation
- **Full Browser Control**: Navigate, click, fill, type, screenshot
- **Element Refs**: Clean `@e1` syntax for interactions
- **Session Isolation**: Each thread gets its own browser
- **Live Streaming**: WebSocket viewport streaming

### Claude-Style UI
- **Waterfall Thought Process**: Hierarchical, nested display of reasoning
- **3-Panel Layout**: Resizable threads, chat, and browser panels
- **Persistent Browser Preview**: Right-side panel with live streaming
- **Clean Design**: Anthropic-inspired minimal color palette
- **Smooth Animations**: 200ms transitions

### Selective Approval
**Auto-approved (read-only)**:
- `browser_snapshot`, `browser_screenshot`, `browser_get_info`
- `browser_is_visible`, `browser_is_enabled`

**Require approval (actions)**:
- `browser_navigate`, `browser_click`, `browser_fill`
- `browser_type`, `browser_press_key`, `browser_eval`

## Quick Start

### Prerequisites

- **Python 3.11+** with `uv` or `pip`
- **Node.js 18+** with `yarn` or `npm`
- **Azure OpenAI** API access with GPT-4/5 deployment
- **agent-browser**: `npm install -g agent-browser`

### 1. Clone Repository

```bash
git clone <repository-url>
cd Browser-Use
```

### 2. Backend Setup

```bash
cd browser-use-agent

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

**`.env` configuration**:
```env
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
OPENAI_API_VERSION=2025-01-01-preview
DEPLOYMENT_NAME=your-gpt-deployment-name
TEMPERATURE=1.0
```

### 3. Frontend Setup

```bash
cd ../deep-agents-ui

# Configure environment variables (recommended)
cp .env.local.example .env.local
# Edit .env.local with your settings

# Install dependencies
yarn install

# Start development server
yarn dev
```

### 4. Start Backend

In a separate terminal:

```bash
cd browser-use-agent
source .venv/bin/activate
langgraph dev --port 2024
```

### 5. Open UI

Navigate to http://localhost:3000 and start chatting!

## Configuration

### Backend Configuration

**Environment Variables** (`browser-use-agent/.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | *Required* |
| `AZURE_OPENAI_API_KEY` | API key | *Required* |
| `OPENAI_API_VERSION` | API version | `2025-01-01-preview` |
| `DEPLOYMENT_NAME` | Model deployment name | `gsds-gpt-5` |
| `TEMPERATURE` | Model temperature | `1.0` |
| `AGENT_BROWSER_STREAM_PORT` | Base WebSocket port | `9223` |

### Frontend Configuration

**Environment Variables** (`.env.local`):
```env
NEXT_PUBLIC_DEPLOYMENT_URL=http://127.0.0.1:2024
NEXT_PUBLIC_ASSISTANT_ID=browser-agent
NEXT_PUBLIC_RALPH_MODE_ENABLED=false
NEXT_PUBLIC_RALPH_MAX_ITERATIONS=5
NEXT_PUBLIC_BROWSER_STREAM_PORT=9223
```

## Usage Examples

### Web UI Chat

**Simple Navigation**:
```
Navigate to example.com and tell me the main heading
```

**Form Interaction**:
```
Go to https://httpbin.org/forms/post, fill in the customer name
as "John Doe", fill in the telephone as "555-1234", and submit the form
```

**Research Task (Ralph Mode)**:
```
Research the latest features in Next.js 15 and create a summary
with the top 3 most important improvements
```

### CLI Usage

```bash
# Standard mode
python agent.py --task "Navigate to google.com and search for 'LangChain'"

# Ralph Mode (iterative)
python agent.py --ralph --task "Research browser automation tools" --iterations 5
```

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                              │
│  ┌─────────────┐  ┌──────────────────┐  ┌─────────────────────────────────┐ │
│  │   Thread    │  │   Chat Interface │  │       Browser Panel             │ │
│  │   Sidebar   │  │  ┌────────────┐  │  │  ┌───────────────────────────┐  │ │
│  │             │  │  │ Messages   │  │  │  │   Live Viewport Stream    │  │ │
│  │  - Today    │  │  │ ┌────────┐ │  │  │  │                           │  │ │
│  │  - Yesterday│  │  │ │Thought │ │  │  │  │   WebSocket Connection    │  │ │
│  │  - Older    │  │  │ │Process │ │  │  │  │   ws://localhost:9223     │  │ │
│  │             │  │  │ └────────┘ │  │  │  │                           │  │ │
│  │             │  │  │ ┌────────┐ │  │  │  └───────────────────────────┘  │ │
│  │             │  │  │ │Tool    │ │  │  │                                 │ │
│  │             │  │  │ │Calls   │ │  │  │  Auto-expand on session start   │ │
│  │             │  │  │ └────────┘ │  │  │  Auto-collapse on session end   │ │
│  └─────────────┘  │  └────────────┘  │  └─────────────────────────────────┘ │
│        15%        │       50%        │              35%                     │
└───────────────────┴──────────────────┴──────────────────────────────────────┘
                                    │
                    HTTP/SSE Stream (LangGraph SDK)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (LangGraph + Python)                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        LangGraph Server (:2024)                         ││
│  │  ┌───────────────┐  ┌────────────────┐  ┌────────────────────────────┐ ││
│  │  │ State Manager │  │ Checkpoint DB  │  │    Thread Isolation        │ ││
│  │  │               │  │   (SQLite)     │  │                            │ ││
│  │  │ - messages    │  │                │  │  thread_id → browser_session│ ││
│  │  │ - todos       │  │  Persistent    │  │  thread_id → memory_context │ ││
│  │  │ - files       │  │  across        │  │  thread_id → checkpoint     │ ││
│  │  │ - browser     │  │  restarts      │  │                            │ ││
│  │  └───────────────┘  └────────────────┘  └────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  ┌─────────────────────────────────┴─────────────────────────────────────┐  │
│  │                         DeepAgents Graph                               │  │
│  │  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────────┐   │  │
│  │  │  Plan   │───▶│ Execute  │───▶│ Reflect  │───▶│ Ralph Iteration │   │  │
│  │  │(Todos)  │    │ (Tools)  │    │(Memory)  │    │   (if enabled)  │   │  │
│  │  └─────────┘    └──────────┘    └──────────┘    └─────────────────┘   │  │
│  │       │              │               │                   │            │  │
│  │       ▼              ▼               ▼                   ▼            │  │
│  │  write_todos   Browser Tools   AGENTS.md          Max iterations      │  │
│  │               + Bash Tools    USER_PREFS.md       then return         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │
                    subprocess (agent-browser CLI)
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BROWSER LAYER (agent-browser)                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      Chromium Instance (Headless)                       ││
│  │  ┌───────────────────┐  ┌────────────────────┐  ┌────────────────────┐ ││
│  │  │   Page Control    │  │  Element Refs      │  │  Screencast Stream │ ││
│  │  │                   │  │                    │  │                    │ ││
│  │  │  - navigate(url)  │  │  @e1, @e2, @e3...  │  │  JPEG frames →     │ ││
│  │  │  - click(@ref)    │  │  from snapshot -i  │  │  WebSocket :9223   │ ││
│  │  │  - fill(@ref)     │  │                    │  │                    │ ││
│  │  │  - screenshot()   │  │  Valid per page    │  │  30fps streaming   │ ││
│  │  └───────────────────┘  └────────────────────┘  └────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input                                                    Browser Viewport
    │                                                               ▲
    ▼                                                               │
┌─────────┐   HTTP POST    ┌─────────────┐   subprocess   ┌─────────────────┐
│ Next.js │ ─────────────▶ │  LangGraph  │ ────────────▶  │  agent-browser  │
│   UI    │                │   Server    │                │      CLI        │
└─────────┘                └─────────────┘                └─────────────────┘
    ▲                            │                               │
    │         SSE Stream         │                               │
    │  (messages, todos, tools,  │                               │
    │   thought, browser_session)│                               │
    └────────────────────────────┘                               │
                                                                 │
    ┌────────────────────────────────────────────────────────────┘
    │  WebSocket Stream (ws://localhost:9223)
    │  - JPEG frames (base64)
    │  - viewport metadata
    ▼
┌─────────────────┐
│  BrowserPanel   │
│  Live Preview   │
└─────────────────┘
```

### Component Interactions

#### Frontend Components

```
page.tsx (Main Layout)
    │
    ├── ChatProvider (Context)
    │   └── useChat hook
    │       ├── LangGraph SDK client
    │       ├── Thread state management
    │       ├── Message streaming
    │       ├── Browser session detection
    │       └── Error handling
    │
    ├── ThreadList
    │   ├── SWR infinite loading
    │   ├── Time-based grouping
    │   └── Interrupt count badge
    │
    ├── ChatInterface
    │   ├── ChatMessage[]
    │   │   ├── ThoughtProcess (waterfall display)
    │   │   ├── ToolCallBox (collapsible)
    │   │   └── SubAgentIndicator
    │   ├── TodoList (grouped by status)
    │   ├── FileExplorer
    │   └── InputArea
    │
    └── ChatWithBrowserPanel
        ├── ResizablePanel (chat)
        └── ResizablePanel (browser)
            └── BrowserPanelContent
                └── WebSocket → img[src=base64]
```

#### Backend Components

```
browser_agent.py (Graph Definition)
    │
    ├── create_browser_agent()
    │   └── create_deep_agent()
    │       ├── Planning node (write_todos)
    │       ├── Execution node (tools)
    │       ├── Reflection node (memory)
    │       └── Subagent spawning (task tool)
    │
    ├── Tools
    │   ├── BROWSER_TOOLS (tools.py)
    │   │   ├── browser_navigate
    │   │   ├── browser_click
    │   │   ├── browser_fill
    │   │   ├── browser_snapshot
    │   │   └── ... (30+ tools)
    │   │
    │   ├── BASH_TOOLS (bash_tool.py)
    │   │   └── bash_execute (with security tiers)
    │   │
    │   ├── HUMAN_TOOLS (human_loop.py)
    │   │   ├── request_guidance
    │   │   ├── request_credentials
    │   │   └── request_confirmation
    │   │
    │   └── REFLECTION_TOOLS (reflection.py)
    │       ├── read_memory
    │       ├── update_agents_file
    │       └── update_user_preferences
    │
    └── State (state.py)
        ├── messages: BaseMessage[]
        ├── todos: Todo[]
        ├── files: dict
        ├── browser_session: BrowserSession
        ├── current_thought: ThoughtProcess
        └── approval_queue: ApprovalRequest[]
```

### Filesystem Architecture

The `.browser-agent/` directory serves as the unified root for all agent operations:

```
.browser-agent/                    # Agent's "home directory"
│
├── artifacts/                     # Generated outputs
│   ├── file_outputs/             # User-requested files (PDFs, CSVs, etc.)
│   ├── screenshots/              # Browser screenshots
│   └── tool_outputs/             # Large tool results
│
├── memory/                        # Persistent memory
│   ├── AGENTS.md                 # Learned patterns (website, task, error recovery)
│   ├── USER_PREFERENCES.md       # User preferences and settings
│   └── diary/                    # Session completion logs
│
├── skills/                        # Reusable skill definitions
│   ├── agent-browser/            # Browser automation skill
│   ├── pdf.md                    # PDF manipulation
│   ├── pptx.md                   # PowerPoint creation
│   └── docx.md                   # Word document handling
│
├── checkpoints/                   # LangGraph state persistence
│   └── browser_agent.db          # SQLite checkpoint database
│
└── traces/                        # Debug traces (optional)
```

**Path Resolution:**

Both the DeepAgents `FilesystemBackend` and `bash_execute` tool use `.browser-agent/` as root:

```python
# DeepAgents FilesystemBackend
write_file("/artifacts/report.pdf", content)  # → .browser-agent/artifacts/report.pdf

# bash_execute (cwd defaults to .browser-agent/)
bash_execute("python artifacts/script.py")    # Runs from .browser-agent/
```

### State Management

#### Thread Isolation

Each conversation thread maintains isolated state:

```python
thread_id = "abc-123"

# Isolated per thread:
- Browser session (sessionId, streamUrl, isActive)
- LangGraph checkpoint (messages, todos, files)
- WebSocket port (9223 + hash(thread_id) % 100)

# Shared across threads:
- Memory files (AGENTS.md, USER_PREFERENCES.md)
- Skills definitions
- Configuration
```

#### State Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph State                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  messages: BaseMessage[]                                   │  │
│  │    - HumanMessage (user input)                            │  │
│  │    - AIMessage (agent response + tool_calls)              │  │
│  │    - ToolMessage (tool results)                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  todos: Todo[]                                             │  │
│  │    - content: string                                       │  │
│  │    - status: "pending" | "in_progress" | "completed"       │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  browser_session: BrowserSession | null                    │  │
│  │    - sessionId: string (thread_id)                        │  │
│  │    - streamUrl: string (ws://localhost:9223)              │  │
│  │    - isActive: boolean                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  current_thought: ThoughtProcess | null                    │  │
│  │    - content: string (streaming)                          │  │
│  │    - isComplete: boolean                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Checkpoint on each node
                              ▼
                    ┌─────────────────┐
                    │   SQLite DB     │
                    │  (persistent)   │
                    └─────────────────┘
```

### WebSocket Streaming Architecture

```
┌─────────────────┐                      ┌─────────────────┐
│  agent-browser  │                      │    Frontend     │
│    (backend)    │                      │  BrowserPanel   │
└────────┬────────┘                      └────────┬────────┘
         │                                        │
         │  Start screencast                      │
         │  on browser_navigate                   │
         ▼                                        │
┌─────────────────┐     WebSocket      ┌─────────────────┐
│  Screencast     │ ─────────────────▶ │   WebSocket     │
│  Server :9223   │   JPEG frames      │   Client        │
└─────────────────┘   (base64)         └─────────────────┘
         │                                        │
         │  Frame message:                        │
         │  {                                     │
         │    type: "frame",                      │
         │    data: "base64...",                  │
         │    metadata: {                         │
         │      deviceWidth,                      │
         │      deviceHeight,                     │
         │      ...                               │
         │    }                                   │
         │  }                                     │
         │                                        ▼
         │                              ┌─────────────────┐
         │                              │  <img src=      │
         │                              │   data:image/   │
         │                              │   jpeg;base64>  │
         │                              └─────────────────┘
         │
         │  On browser_close:
         │  - Stop screencast
         │  - Close WebSocket
         │  - Frontend auto-collapses panel
         ▼
```

### Interrupt Flow (Human-in-the-Loop)

```
Agent encounters need for human input
                │
                ▼
┌─────────────────────────────────────┐
│  langgraph.types.interrupt({        │
│    type: "guidance" | "credentials" │
│          | "confirmation",          │
│    question: "...",                 │
│    context: "..."                   │
│  })                                 │
└──────────────────┬──────────────────┘
                   │
                   │ Stream interrupted state
                   ▼
┌─────────────────────────────────────┐
│  Frontend detects interrupt         │
│  stream.interrupt !== null          │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Render appropriate UI:             │
│  - HumanLoopInterrupt (guidance)    │
│  - CredentialsForm (credentials)    │
│  - ConfirmationDialog (confirm)     │
└──────────────────┬──────────────────┘
                   │
                   │ User responds
                   ▼
┌─────────────────────────────────────┐
│  resumeInterrupt(response)          │
│  → stream.submit(response)          │
└──────────────────┬──────────────────┘
                   │
                   │ Graph resumes
                   ▼
        Agent continues execution
```

## Project Structure

```
Browser-Use/
├── browser-use-agent/          # Python Backend (DeepAgents)
│   ├── browser_use_agent/     # Core agent package
│   │   ├── browser_agent.py   # Main agent + Ralph Mode
│   │   ├── configuration.py   # Azure OpenAI config
│   │   ├── tools.py          # Browser automation tools
│   │   ├── bash_tool.py      # Bash execution with security tiers
│   │   ├── human_loop.py     # Human-in-the-loop tools
│   │   ├── subagent_interrupt.py  # Subagent interrupt forwarding
│   │   ├── state.py          # State definitions
│   │   ├── prompts.py        # System prompts + memory management
│   │   ├── reflection.py     # Memory read/write tools
│   │   ├── storage/          # Checkpoint and config
│   │   ├── skills/           # Skill loader
│   │   └── utils.py          # StreamManager
│   ├── agent.py              # CLI entry point
│   ├── server.py             # Optional FastAPI wrapper + skills API
│   └── langgraph.json        # LangGraph config
│
├── deep-agents-ui/            # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/skills/       # Skills API route
│   │   │   ├── components/       # UI components
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── BrowserPanel.tsx
│   │   │   │   ├── ThoughtProcess.tsx
│   │   │   │   ├── ToolCallBox.tsx
│   │   │   │   ├── ThreadList.tsx
│   │   │   │   └── ...
│   │   │   ├── hooks/
│   │   │   │   ├── useChat.ts    # Main chat hook
│   │   │   │   └── useThreads.ts # Thread list hook
│   │   │   ├── providers/
│   │   │   │   ├── ChatProvider.tsx
│   │   │   │   └── ClientProvider.tsx
│   │   │   └── types/
│   │   └── components/ui/        # shadcn/ui components
│   └── .env.local.example
│
├── .browser-agent/            # Agent memory and artifacts
│   ├── artifacts/            # Generated files
│   ├── memory/               # Persistent memory
│   ├── skills/               # Skill definitions
│   └── checkpoints/          # State persistence
│
├── agent.md                  # Technical reference
├── CLAUDE.md                 # AI assistant instructions
└── README.md                 # This file
```

## Documentation

- [Backend README](./browser-use-agent/README.md) - Python agent details
- [agent.md](./agent.md) - Technical reference & implementation
- Skills: `.browser-agent/skills/` - PDF, PPTX, DOCX, browser automation

### External Resources
- [DeepAgents Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [agent-browser Docs](https://agent-browser.dev/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)

---

Built with DeepAgents and agent-browser
