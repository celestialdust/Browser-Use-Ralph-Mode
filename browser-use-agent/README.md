# Browser Use Agent

A browser automation agent built with [DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) and [agent-browser](https://agent-browser.dev/), featuring Ralph Mode for iterative task refinement.

## Features

- 🤖 **DeepAgents Integration**: Built on LangChain's DeepAgents framework
- 🔄 **Ralph Mode**: Iterative refinement and self-correction
- 🌐 **Browser Automation**: Full browser control via `agent-browser` CLI
- ☁️ **Browserbase Support**: Cloud browser infrastructure for serverless deployments
- 📊 **Planning & Decomposition**: Built-in task breakdown with `write_todos`
- 💾 **Context Management**: File system tools for large context handling
- 🎯 **Subagent Spawning**: Delegate specialized tasks to subagents
- 🔐 **Selective Approval**: User approval for sensitive browser actions
- 📺 **Live Streaming**: WebSocket-based browser viewport streaming
- 📄 **File Presentation**: Present generated files (PDF, DOCX, XLSX, images) to users with preview
- 🧵 **Multi-threading**: Isolated browser sessions per thread
- 🧹 **Daemon Lifecycle Management**: Automatic cleanup of stale daemon processes

## Architecture

```
browser-use-agent/
├── browser_use_agent/          # Core agent package
│   ├── __init__.py            # Package initialization
│   ├── configuration.py       # Configuration and LLM setup
│   ├── browser_agent.py       # Main agent implementation with Ralph Mode
│   ├── prompts.py            # System prompts + memory management
│   ├── state.py              # State definitions and data models
│   ├── tools.py              # Browser automation tools
│   ├── models.py             # Pydantic models for structured output
│   ├── skills/               # Skill loader
│   │   ├── __init__.py
│   │   └── loader.py         # Load skills from .browser-agent/skills/
│   └── utils.py              # Utility functions (StreamManager)
├── agent.py                   # CLI entry point
├── langgraph.json            # LangGraph configuration
├── pyproject.toml            # Project configuration
└── .env                      # Environment variables (not committed)

../.browser-agent/              # Agent memory and skills (project root)
├── skills/                    # Skill files
│   ├── agent-browser/        # Browser automation skill
│   ├── skill-creator.md      # Guide for creating skills
│   ├── pdf.md               # PDF manipulation
│   ├── pptx.md              # PowerPoint creation/editing
│   └── docx.md              # Word document handling
├── memory/                   # Agent memory files
└── artifacts/               # Generated files
```

## Installation

### Prerequisites

- Python 3.11+
- Node.js (for `agent-browser` CLI)
- OpenAI API or Azure OpenAI access

### Setup

1. **Install `agent-browser` CLI**:
```bash
npm install -g agent-browser
```

2. **Create and activate virtual environment**:
```bash
cd browser-use-agent
uv venv
source .venv/bin/activate
```

3. **Install Python dependencies**:
```bash
uv pip install -e .
```

4. **Configure environment variables**:
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

**OpenAI:**
```env
USE_AZURE=false
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-5"
TEMPERATURE="1.0"
```

**Azure OpenAI:**
```env
USE_AZURE=true
AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-api-key"
DEPLOYMENT_NAME="gpt-5"
```

## Usage

### CLI Usage

#### Standard Mode
```bash
python agent.py --task "Navigate to example.com and get the title"
```

#### Ralph Mode (Iterative Refinement)
```bash
python agent.py --ralph --task "Research the top 3 features of Next.js" --iterations 3
```

#### Custom Thread ID
```bash
python agent.py --thread-id my-session --task "Fill out a form on example.com"
```

### LangGraph Server

Start the LangGraph development server:
```bash
source .venv/bin/activate
langgraph dev --port 2024 --allow-blocking
```

**Note:** The `--allow-blocking` flag is required because the agent uses synchronous blocking calls (e.g., for git operations in `StorageConfig`). Without this flag, LangGraph will detect blocking I/O and fail to start.

The agent will be available at `http://127.0.0.1:2024` with graph ID `browser-agent`.

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

# Ralph mode
result = run_ralph_mode(
    task="Research browser automation",
    max_iterations=5,
    agent=agent
)
```

## Browser Tools

All browser tools run in an isolated sandbox and are **auto-approved** (no user approval required):

### Navigation
- `browser_navigate` - Navigate to URL
- `browser_back` / `browser_forward` - Navigate history
- `browser_reload` - Reload page

### Interaction
- `browser_click` - Click an element
- `browser_fill` - Fill input field
- `browser_type` - Type text
- `browser_press_key` - Press keyboard key

### Observation
- `browser_snapshot` - Get page structure with interactive elements
- `browser_screenshot` - Capture page screenshot
- `browser_get_info` - Get element information
- `browser_console` - Get console logs
- `browser_is_visible` / `browser_is_enabled` / `browser_is_checked` - Check element states

### Advanced
- `browser_eval` - Execute JavaScript
- `browser_wait` - Wait for condition
- `browser_close` - Close browser session

### File Presentation
- `present_file` - Present a generated file to the user in the UI
  - Displays file as a clickable card with preview and download
  - Supports PDF, DOCX, XLSX, images, Markdown, text, JSON, CSV, HTML

## Ralph Mode

Ralph Mode enables iterative refinement where the agent:
1. Attempts the task
2. Reviews results
3. Reflects on mistakes
4. Tries again with improvements
5. Repeats until success or max iterations

Inspired by the [LangChain Ralph Mode example](https://github.com/langchain-ai/deepagents/tree/master/examples/ralph_mode).

## Browser Streaming

Each thread gets an isolated browser session with WebSocket streaming:
- **Port allocation**: Hash-based port from thread ID
- **Stream URL**: `ws://localhost:{port}`
- **Frame format**: Base64-encoded JPEG images
- **Input support**: Mouse, keyboard, touch events

Set `AGENT_BROWSER_STREAM_PORT` environment variable to customize the base port (default: 9223).

## DeepAgents Features

The agent automatically includes DeepAgents capabilities:
- **Planning**: `write_todos` tool for task decomposition
- **File System**: `read_file`, `write_file`, `edit_file`, `ls` for context management
- **Subagents**: `task` tool for spawning specialized agents
- **Memory**: Persistent state across conversations
- **Checkpointing**: Resume interrupted tasks

## Skills System

Skills are modular packages that extend agent capabilities. Located in `.browser-agent/skills/`:

### Available Skills
- **agent-browser**: Browser automation commands and patterns
- **skill-creator**: Guide for creating new skills
- **pdf**: PDF manipulation (extract, merge, split, create)
- **pptx**: PowerPoint creation and editing
- **docx**: Word document creation with tracked changes

### Skills API

The FastAPI server exposes skills endpoints:
```bash
# List all skills
GET /skills

# Get specific skill content
GET /skills/{skill_name}
```

### Loading Skills
```python
from browser_use_agent.skills.loader import SkillLoader

loader = SkillLoader()
skills = loader.list_skills()  # Get metadata
content = loader.load_skill("pdf")  # Get full content
```

## Memory Management

The agent maintains persistent memory for learning:

- **AGENTS.md**: Learned website patterns and navigation quirks
- **diary.md**: Task completions and learnings
- **skills/**: Reusable workflows

Memory update guidelines are in the system prompt.

## Development

### Run Tests
```bash
pytest tests/
```

### Lint Code
```bash
ruff check .
black .
```

### Type Checking
```bash
mypy browser_use_agent/
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_AZURE` | Use Azure OpenAI | `true` |
| `OPENAI_API_KEY` | OpenAI API key (when USE_AZURE=false) | - |
| `OPENAI_MODEL` | OpenAI model name | `gpt-5` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | - |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - |
| `DEPLOYMENT_NAME` | Azure deployment name | `gpt-5` |
| `TEMPERATURE` | Model temperature | `1.0` |
| `REASONING_ENABLED` | Enable reasoning API | `true` |
| `REASONING_EFFORT` | Reasoning effort level | `medium` |
| `AGENT_BROWSER_STREAM_PORT` | Base WebSocket port | `9223` |
| `BROWSERBASE_API_KEY` | Browserbase API key (cloud browser) | - |
| `BROWSERBASE_PROJECT_ID` | Browserbase project ID | - |
| `USE_CDP` | Use Chrome DevTools Protocol | `false` |
| `CDP_PORT` | CDP port (when USE_CDP=true) | `9222` |

### Browserbase (Cloud Browser)

[Browserbase](https://browserbase.com/) provides cloud browser infrastructure for running the agent in serverless environments where a local browser isn't available.

**Setup:**

1. Get your API key and project ID from the [Browserbase Dashboard](https://browserbase.com/overview)

2. Add to your `.env` file:
```env
BROWSERBASE_API_KEY=your-api-key
BROWSERBASE_PROJECT_ID=your-project-id
```

When both variables are set, `agent-browser` automatically connects to a Browserbase session instead of launching a local browser. All commands work identically.

**When to use Browserbase:**
- Serverless deployments (Vercel, AWS Lambda, etc.)
- CI/CD pipelines
- Environments without browser access
- Scaling browser automation workloads

### CDP Mode (Chrome DevTools Protocol)

Connect to an existing Chrome browser instead of launching isolated sessions:

```bash
# 1. Start Chrome with remote debugging enabled
google-chrome --remote-debugging-port=9222

# 2. Configure backend to use CDP
USE_CDP=true CDP_PORT=9222 langgraph dev --port 2024
```

**When to use CDP mode:**
- Debugging browser automation issues
- Reusing authenticated browser sessions
- Connecting to a Chrome instance with specific extensions
- Manual intervention during automation

**Note:** In CDP mode, all threads share the same browser instance. For isolation, use the default session mode.

### Configuration Class

```python
from browser_use_agent.configuration import Config

# Access settings
Config.AZURE_OPENAI_ENDPOINT
Config.DEFAULT_MAX_ITERATIONS
Config.APPROVAL_REQUIRED_TOOLS

# Validate configuration
Config.validate()
```

## Troubleshooting

### "Daemon failed to start" Error
This error occurs when `agent-browser` cannot start its daemon process, usually due to:
- **Too many daemon processes**: The system automatically cleans up excess daemons (keeps max 3), but you can manually check: `pgrep -f "agent-browser.*daemon"`
- **Stale processes**: Kill all daemons and retry: `pkill -f "agent-browser.*daemon"`
- **Port conflicts**: Check if ports are in use: `lsof -i :9222-9230`

### Browser Not Starting
- Verify `agent-browser` is installed: `agent-browser --help`
- Check port availability: `lsof -i :9223`

### Import Errors
- Activate virtual environment: `source .venv/bin/activate`
- Reinstall dependencies: `uv pip install -e .`

### Azure OpenAI Errors
- Verify `.env` configuration
- Check API key and endpoint
- Ensure deployment name matches your Azure resource

## Resources

- [DeepAgents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [agent-browser Documentation](https://agent-browser.dev/)
- [Browserbase Documentation](https://docs.browserbase.com/)
- [LangChain Documentation](https://docs.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## License

MIT License - See LICENSE file for details
