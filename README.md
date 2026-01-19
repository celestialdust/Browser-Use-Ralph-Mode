# Browser Use - Full-Stack Agent with DeepAgents & Ralph Mode

A complete browser automation system combining [LangChain DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) with [agent-browser](https://agent-browser.dev/), featuring Ralph Mode for iterative refinement and a Claude-inspired UI.

![Browser Use Agent](https://img.shields.io/badge/Status-Alpha-yellow)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)
![Node 18+](https://img.shields.io/badge/Node-18+-green)
![License MIT](https://img.shields.io/badge/License-MIT-lightgrey)

## 🎯 Overview

Browser Use is a full-stack browser automation agent that can:
- 🤖 **Plan and execute** complex multi-step browser tasks
- 🔄 **Self-correct** using Ralph Mode's iterative refinement
- 🌐 **Control browsers** via `agent-browser` CLI
- 📺 **Stream live** browser viewport via WebSocket
- 🧠 **Show thinking** in real-time like Claude
- 🔐 **Request approval** for sensitive actions
- 🧵 **Isolate sessions** per conversation thread

## 🏗️ Architecture

```
Browser-Use/
├── browser-use-agent/          # Python Backend (DeepAgents)
│   ├── browser_use_agent/     # Core agent package
│   │   ├── browser_agent.py   # Main agent + Ralph Mode
│   │   ├── configuration.py   # Azure OpenAI config
│   │   ├── tools.py          # Browser automation tools
│   │   ├── state.py          # State definitions
│   │   ├── prompts.py        # System prompts + memory management
│   │   ├── skills/           # Skill loader
│   │   └── utils.py          # StreamManager
│   ├── agent.py              # CLI entry point
│   ├── server.py             # Optional FastAPI wrapper + skills API
│   └── langgraph.json        # LangGraph config
│
├── deep-agents-ui/            # Next.js Frontend
│   ├── src/app/
│   │   ├── api/skills/       # Skills API route
│   │   ├── components/       # UI components
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── BrowserPanel.tsx         # Persistent browser panel
│   │   │   ├── BrowserPreview.tsx
│   │   │   ├── ThoughtProcess.tsx       # Waterfall display
│   │   │   ├── ReasoningDisplay.tsx     # OpenAI reasoning summary
│   │   │   ├── ConfigDialog.tsx         # Settings + skills display
│   │   │   └── BrowserCommandApproval.tsx
│   │   ├── hooks/           # React hooks
│   │   ├── providers/       # Context providers
│   │   └── types/          # TypeScript definitions
│   ├── .env.local.example   # Environment variables template
│   └── ...
│
├── .browser-agent/            # 📚 Agent memory and skills
│   ├── skills/               # Skill files
│   │   ├── agent-browser/    # Browser automation skill
│   │   ├── skill-creator.md  # Guide for creating skills
│   │   ├── pdf.md           # PDF manipulation
│   │   ├── pptx.md          # PowerPoint creation/editing
│   │   └── docx.md          # Word document handling
│   ├── memory/              # Agent memory files
│   └── artifacts/           # Generated files
│
├── agent.md                  # 📖 Technical reference
└── README.md                 # This file
```

## ✨ Features

### DeepAgents Integration
- **Planning & Decomposition**: Built-in `write_todos` tool
- **File System Tools**: Manage large context with filesystem
- **Subagent Spawning**: Delegate tasks to specialized agents
- **Long-term Memory**: Persistent state across conversations

### Skills System
- **Document Skills**: PDF, PPTX, DOCX manipulation
- **Browser Skills**: Automated browser interactions
- **Skill Creator**: Guide for building custom skills
- **Settings Integration**: View and manage skills in UI

### Memory Management
- **AGENTS.md**: Store learned website patterns
- **Diary**: Record task completions and learnings
- **Skills**: Create reusable workflows

### Ralph Mode
- **Iterative Refinement**: Agent retries with improvements
- **Self-Reflection**: Reviews mistakes and adapts approach
- **Persistent Memory**: Uses filesystem between iterations
- **Configurable Iterations**: Set max attempts per task

### Browser Automation
- **Full Browser Control**: Navigate, click, fill, type, screenshot
- **Element Refs**: Clean `@e1` syntax for interactions
- **Session Isolation**: Each thread gets its own browser
- **Streaming**: Live WebSocket viewport streaming

### Claude-Style UI
- **Waterfall Thought Process**: Hierarchical, nested display of reasoning
- **3-Panel Layout**: Resizable threads, chat, and browser panels
- **Persistent Browser Preview**: Right-side panel with live WebSocket streaming
- **Clean Design**: Anthropic-inspired minimal color palette
- **Smooth Animations**: Character-by-character streaming with 200ms transitions
- **Interactive Approvals**: Review actions before execution

### Selective Approval
**Auto-approved (read-only)**:
- `browser_snapshot`, `browser_screenshot`, `browser_get_info`
- `browser_is_visible`, `browser_is_enabled`

**Require approval (actions)**:
- `browser_navigate`, `browser_click`, `browser_fill`
- `browser_type`, `browser_press_key`, `browser_eval`

## 🚀 Quick Start

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

### 5. Configure UI

**Option A: Environment Variables** (Recommended)
- Settings auto-populate from `.env.local`
- No manual configuration needed

**Option B: Settings Dialog**
1. Open http://localhost:3000
2. Click Settings (⚙️) in top right
3. Configure:
   - **Deployment URL**: `http://127.0.0.1:2024`
   - **Assistant ID**: `browser-agent`
   - **Ralph Mode**: Enable/disable iterative refinement
   - **Max Iterations**: Set refinement passes (1-20)
   - **Browser Stream Port**: WebSocket port (default: 9223)
4. Click Save

## 📖 Usage Examples

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

**Standard Mode**:
```bash
cd browser-use-agent
source .venv/bin/activate
python agent.py --task "Navigate to google.com and search for 'LangChain'"
```

**Ralph Mode (Iterative)**:
```bash
python agent.py --ralph \
  --task "Research browser automation tools and compare their features" \
  --iterations 5
```

**Custom Thread ID**:
```bash
python agent.py --thread-id my-research-session \
  --task "Find pricing information for cloud services"
```

### Python API

```python
from browser_use_agent import create_browser_agent, run_ralph_mode
from langchain_core.messages import HumanMessage

# Create agent
agent = create_browser_agent()

# Standard mode
result = agent.invoke({
    "messages": [HumanMessage(content="Navigate to example.com")],
    "thread_id": "my-thread"
}, config={"configurable": {"thread_id": "my-thread"}})

# Ralph mode for complex tasks
result = run_ralph_mode(
    task="Research and compare top 3 web frameworks",
    max_iterations=5,
    agent=agent
)

print(result["messages"][-1].content)
```

## 🔧 Configuration

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

**Python Config Class**:
```python
from browser_use_agent.configuration import Config

# Access settings
Config.AZURE_OPENAI_ENDPOINT
Config.DEFAULT_MAX_ITERATIONS  # Ralph Mode iterations
Config.APPROVAL_REQUIRED_TOOLS  # Actions requiring approval

# Validate
Config.validate()
```

### Frontend Configuration

**Environment Variables** (`.env.local`) - Recommended:
```env
# LangGraph Backend
NEXT_PUBLIC_DEPLOYMENT_URL=http://127.0.0.1:2024
NEXT_PUBLIC_ASSISTANT_ID=browser-agent

# LangSmith (Optional)
NEXT_PUBLIC_LANGSMITH_API_KEY=

# Ralph Mode Configuration
NEXT_PUBLIC_RALPH_MODE_ENABLED=false
NEXT_PUBLIC_RALPH_MAX_ITERATIONS=5

# Browser Streaming
NEXT_PUBLIC_BROWSER_STREAM_PORT=9223
```

**Settings UI** (Overrides env variables):
- Deployment URL (backend API)
- Assistant ID (graph name)
- LangSmith API Key (optional)
- Ralph Mode toggle and max iterations
- Browser stream port

## 🎨 UI Design Philosophy

Inspired by [Anthropic's Claude](https://claude.ai/):

- **Minimalist**: Clean, uncluttered interface with 3-panel layout
- **Waterfall Thinking**: Hierarchical display of reasoning steps
- **Persistent Browser**: Resizable right panel for live viewport streaming
- **Muted Colors**: Soft grays, subtle accents matching Anthropic's palette
- **Smooth Animations**: 200ms cubic-bezier transitions, character streaming
- **Contextual**: Show agent thinking with nested structure, hide complexity
- **Responsive**: Mobile-friendly, adaptive layouts with panel management

**Color Palette**:
- Background: `#ffffff` (light) / `#1a1a1a` (dark)
- Surface: `#f5f5f5` / `#2a2a2a`
- Border: `#e5e5e5` / `#404040`
- Primary: `#2f6868` / `#4db6ac`
- Text: `#1a1a1a`, `#666666`, `#999999` / `#f0f0f0`, `#a0a0a0`

**Layout Structure**:
```
┌─────────────┬────────────────┬─────────────┐
│  Threads    │     Chat       │   Browser   │
│  Sidebar    │   Messages     │   Panel     │
│  (15-30%)   │   (50-80%)     │   (20-50%)  │
└─────────────┴────────────────┴─────────────┘
```

## 📚 Documentation

- [Backend README](./browser-use-agent/README.md) - Python agent details
- [Frontend README](./deep-agents-ui/README.md) - Next.js UI details
- [agent.md](./agent.md) - Technical reference & implementation
- Skills: `.browser-agent/skills/` - PDF, PPTX, DOCX, browser automation

### External Resources
- [DeepAgents Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [agent-browser Docs](https://agent-browser.dev/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Ralph Mode Example](https://github.com/langchain-ai/deepagents/tree/master/examples/ralph_mode)

### Integration Testing

1. Start backend: `langgraph dev --port 2024`
2. Start frontend: `yarn dev`
3. Open http://localhost:3000
4. Verify environment variables loaded (check settings)
5. Create new thread
6. Test scenarios:
   - Simple navigation
   - Form interaction
   - Approval flow
   - Waterfall thought process display
   - Persistent browser panel (resizable, reconnection)
   - 3-panel layout responsiveness
   - Ralph mode configuration
   - Multi-step tasks
---

Built with using DeepAgents and agent-browser
