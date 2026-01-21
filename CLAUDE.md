# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

- **Always use `uv` for Python operations** - Never use `pip` directly. Use `uv pip install`, `uv run`, `uv venv`, etc.
- **Credential handling**: Agent can use credentials provided directly in chat. Only use `request_credentials` tool if user hasn't provided them in the conversation.
- **README structure**: Do NOT include a "Recent Updates" or changelog section in README.md. Instead, document all features in the Features section. Keep the README focused on current capabilities, not version history.

## Project Overview

Browser Use is a full-stack browser automation system combining LangChain DeepAgents with agent-browser CLI. The system features Ralph Mode for iterative refinement and a Claude-inspired UI.

**Key Components:**
- **Backend (browser-use-agent/)**: Python agent using DeepAgents library with browser automation tools
- **Frontend (deep-agents-ui/)**: Next.js application with real-time browser preview and Claude-style UI
- **Browser Control**: agent-browser CLI for browser automation with WebSocket streaming

## Common Commands

### Backend (Python Agent)

```bash
# Setup
cd browser-use-agent
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Configure environment (required)
# Edit .env with Azure OpenAI credentials:
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_API_KEY
# - DEPLOYMENT_NAME (GPT-4/5 deployment)

# Run LangGraph server (primary backend)
langgraph dev --port 2024

# Optional: Use CDP mode to connect to existing Chrome browser
# First start Chrome: google-chrome --remote-debugging-port=9222
USE_CDP=true CDP_PORT=9222 langgraph dev --port 2024

# CLI usage
python agent.py --task "Navigate to example.com"
python agent.py --ralph --task "Research topic" --iterations 5
```

### Frontend (Next.js UI)

```bash
# Setup
cd deep-agents-ui
cp .env.local.example .env.local  # Configure environment
yarn install

# Development
yarn dev              # Start dev server (http://localhost:3000)
yarn build            # Build for production
yarn lint             # Run ESLint
yarn lint:fix         # Fix linting issues
yarn format           # Format with Prettier
yarn format:check     # Check formatting
```

### Browser Automation (agent-browser)

```bash
# Install globally (required)
npm install -g agent-browser

# Common workflow
agent-browser open <url>          # Navigate to URL
agent-browser snapshot -i         # Get interactive elements with @refs
agent-browser click @e1           # Click element by ref
agent-browser fill @e2 "text"     # Fill input
agent-browser screenshot          # Take screenshot
agent-browser close               # Close browser
```

See `skills/SKILL.md` for comprehensive agent-browser command reference.

## Architecture

### DeepAgents Integration

The backend uses the `deepagents` library (create_deep_agent) which provides:
- **Planning**: `write_todos` tool for task decomposition
- **File System Tools**: Context management across agent invocations
- **Subagent Spawning**: `task` tool for delegating specialized work
- **State Management**: Persistent memory via LangGraph checkpoints

### Agent State Flow

**State Schema** (browser_use_agent/state.py):
- `messages`: Conversation history (BaseMessage[])
- `todos`: Task tracking with status (pending/in_progress/completed)
- `files`: File system state for context management
- `browser_session`: Browser session metadata (sessionId, streamUrl, isActive)
- `approval_queue`: Commands awaiting user approval
- `current_thought`: Real-time thinking process
- `thread_id`: Unique conversation identifier

### Ralph Mode (Iterative Refinement)

Ralph Mode runs the agent in a loop for complex tasks:
1. Agent attempts task
2. Reviews result against original request
3. Iterates with reflection prompt if incomplete
4. Uses file system for persistent memory between iterations
5. Max iterations configurable (default: 5)

Triggered via CLI `--ralph` flag or UI toggle.

### Browser Session Management

Each conversation thread gets an isolated browser session:
- **Session ID**: `{thread_id}` for isolation
- **WebSocket Streaming**: Live viewport preview on port `9223 + offset`
- **Session Lifecycle**: Created on first browser command, persists per thread
- **State Persistence**: Cookies, localStorage maintained across agent calls

### Tool Approval System

Tools categorized in `configuration.py`:

**Auto-approved (read-only)**:
- browser_snapshot, browser_screenshot, browser_get_info
- browser_is_visible, browser_is_enabled, browser_get_url

**Require approval (actions)**:
- browser_navigate, browser_click, browser_fill
- browser_type, browser_press_key, browser_eval

UI presents approval dialog before executing action tools.

### Frontend Architecture

**3-Panel Layout**:
- **Left**: Thread list sidebar (15-30% width)
- **Center**: Chat interface with message streaming (50-80% width)
- **Right**: Persistent browser preview panel (20-50% width)

**Key UI Components** (deep-agents-ui/src/app/components/):
- `ChatInterface.tsx`: Main chat with message handling
- `ThoughtProcess.tsx`: Waterfall display of agent reasoning (hierarchical, nested)
- `BrowserPanel.tsx`: Persistent WebSocket browser preview
- `BrowserPreview.tsx`: Live viewport rendering
- `BrowserCommandApproval.tsx`: Action approval dialogs
- `ConfigDialog.tsx`: Settings (LangGraph URL, Ralph mode, stream port)
- `ThreadList.tsx`: Thread management sidebar

**State Management**:
- `ChatProvider.tsx`: LangGraph SDK client, thread state, streaming
- Environment variables from `.env.local` populate default settings
- Settings override via ConfigDialog stored in localStorage

## Development Workflow

### Adding Browser Tools

1. Define tool function in `browser_use_agent/tools.py`
2. Wrap with `@tool` decorator, provide clear description
3. Add to `BROWSER_TOOLS` list
4. Categorize in `Config.APPROVAL_REQUIRED_TOOLS` or `Config.AUTO_APPROVED_TOOLS`
5. Tool automatically available to DeepAgents via `create_browser_agent()`

### Modifying Agent Behavior

**System Prompt**: Edit `browser_use_agent/prompts.py`
- `BROWSER_AGENT_SYSTEM_PROMPT`: Main agent instructions
- `RALPH_MODE_REFLECTION_PROMPT`: Reflection between iterations

**LLM Configuration**: Edit `browser_use_agent/configuration.py`
- Azure OpenAI endpoint, API key, deployment
- Temperature, model parameters
- Stream port ranges

### UI Customization

**Styling**: Anthropic-inspired design system
- Colors defined in `tailwind.config.ts` and component styles
- Muted palette: `#2f6868` (primary), `#f5f5f5` (surface), `#e5e5e5` (border)
- 200ms cubic-bezier transitions for smooth animations

**Environment Variables**: `deep-agents-ui/.env.local`
- `NEXT_PUBLIC_DEPLOYMENT_URL`: LangGraph backend URL
- `NEXT_PUBLIC_ASSISTANT_ID`: Graph name from langgraph.json
- `NEXT_PUBLIC_RALPH_MODE_ENABLED`: Enable Ralph mode by default
- `NEXT_PUBLIC_BROWSER_STREAM_PORT`: WebSocket port for streaming

## Important Implementation Details

### Thread Isolation

Each thread must use unique identifiers:
- Thread ID passed via `config={"configurable": {"thread_id": thread_id}}`
- Browser sessions scoped to thread ID
- LangGraph checkpoints maintain state per thread
- File system operations within DeepAgents scoped to agent context

### WebSocket Browser Streaming

- agent-browser supports `--cdp` flag for Chrome DevTools Protocol
- Frontend connects to `ws://localhost:${BROWSER_STREAM_PORT}` per session
- Port offset prevents conflicts: `BASE_STREAM_PORT + hash(thread_id) % MAX_PORT_OFFSET`
- Stream URL format: `ws://localhost:9223?sessionId={thread_id}`

### Error Handling

- Browser commands may fail if elements not found (agent should snapshot first)
- LangGraph SDK errors surface in UI via error states
- Ralph Mode continues iterations on error (unless max iterations reached)
- WebSocket reconnection logic in BrowserPanel handles stream interruptions

### Element References (@refs)

agent-browser uses `@e1`, `@e2`, etc. for element references:
- Obtained via `agent-browser snapshot -i` (interactive elements only)
- Valid within current page state only
- Must re-snapshot after navigation or DOM changes
- Agent should always snapshot before interactions

## Configuration Files

- `browser-use-agent/.env`: Azure OpenAI credentials (required, not in git)
- `browser-use-agent/langgraph.json`: LangGraph server config, defines `browser-agent` graph
- `deep-agents-ui/.env.local`: Frontend environment (optional, overrides defaults)
- `browser-use-agent/pyproject.toml`: Python dependencies via uv/pip

## Testing & Debugging

**Backend Testing**:
```bash
# Test agent directly
cd browser-use-agent
source .venv/bin/activate
python agent.py --task "test task"

# Test Ralph mode
python agent.py --ralph --task "complex task" --iterations 3
```

**Frontend Integration**:
1. Start backend: `langgraph dev --port 2024`
2. Start frontend: `yarn dev` (in deep-agents-ui/)
3. Open http://localhost:3000
4. Create new thread and test scenarios

**Browser Automation**:
- Use `--headed` flag to see browser window: `agent-browser open <url> --headed`
- Check console: `agent-browser console`
- Record sessions: `agent-browser record start ./debug.webm`

## External Resources

- [DeepAgents Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [agent-browser Docs](https://agent-browser.dev/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- Skills reference: `skills/SKILL.md`
- Technical reference: `agent.md`
