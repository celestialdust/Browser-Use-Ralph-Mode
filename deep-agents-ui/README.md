# Deep Agents UI - Browser Automation Frontend

A modern, Claude-inspired interface for interacting with the Browser Use Agent. Built with Next.js 15, React 19, and Tailwind CSS.

## Features

### Frontend Features
- 🎨 **Claude-Style Aesthetic**: Clean, minimal design with Anthropic-inspired color palette and sidebar
- 💬 **Multi-Thread Chat**: Create and manage multiple conversation threads with smart truncation
- 🧠 **Collapsible Thought Process**: Nested display with intelligent summaries when collapsed
- 🌐 **Always-Visible Browser Status Indicator**: Header-integrated status display
  - **Header Icon**: Monitor icon always visible in top-right corner (Claude-style)
  - **Red Icon (Idle)**: Shows when no browser session, disabled/not clickable
  - **Green Icon (Active)**: Shows when browser session running
  - **Status-Only**: Icon is purely visual indicator, not an interactive button
  - **Smart Auto-Expand**: Panel automatically opens when browser session starts
  - **Smart Auto-Collapse**: Panel automatically closes when session ends
  - **Three-Column Header**: Left (sidebar toggle) | Center (thread title) | Right (status icon)
  - **Centered Title**: Thread title centered in header with balanced spacing
  - **Status Messages**: Shows "Browser is not working" when no active session
  - **Live Streaming**: WebSocket-based real-time browser viewport when active
  - **No False Errors**: Fixed closure issue causing false error logs
- ✅ **Interactive Approvals**: Review and approve browser actions before execution
- 📋 **Task Management**: Visual todo list showing agent's task breakdown
- 📁 **File Viewer**: View and edit files created by the agent
- 🔄 **Streaming Updates**: Real-time updates via Server-Sent Events (SSE)
- ⚙️ **Ralph Mode Configuration**: Enable iterative refinement with configurable max iterations
- 🔧 **Environment Variable Support**: Pre-configure settings via `.env.local`
- 🎯 **Claude-Inspired Sidebar**: New chat button at top, settings at bottom, streamlined layout
- 📝 **Smart Tool Display**: Browser/file tools show simplified `key: value` format, others expandable
- 📚 **Skills Management**: View and toggle skills in Settings dialog
- 🔌 **Skills API**: `/api/skills` endpoint for fetching backend skills
- 📄 **File Artifacts**: View and download files presented by the agent with inline preview
- 🗂️ **Multi-Format Preview**: Native preview for PDF, Markdown, images, text, JSON, CSV, HTML, DOCX, and XLSX files

### Backend Features
- ⏱️ **Automatic Browser Timeout**: Sessions auto-close after 5 minutes of inactivity
- 🔗 **Consistent Stream URLs**: Same thread always gets same WebSocket port (deterministic hash)
  - **No Port Spawning**: Multiple `browser_navigate` calls reuse same port
  - **Cache-First Strategy**: Instant port lookup for active sessions
  - **Hash-Based Assignment**: MD5(thread_id) ensures consistent ports even after timeout
  - **Logging**: Verify port reuse with `[StreamManager]` console logs
- 🔄 **Session Management**: Thread-safe browser session tracking with activity monitoring
- 🧹 **Background Cleanup**: Daemon thread automatically closes inactive sessions
- 📊 **Activity Tracking**: All browser interactions update last activity timestamp

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **UI Library**: React 19
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **State Management**: React Context API
- **Real-time**: WebSocket + SSE (Server-Sent Events)
- **Type Safety**: TypeScript

## Architecture

```
deep-agents-ui/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── api/               # API routes
│   │   │   └── skills/        # Skills API
│   │   │       └── route.ts   # GET /api/skills
│   │   ├── components/        # UI components
│   │   │   ├── BrowserCommandApproval.tsx   # Approval dialog
│   │   │   ├── BrowserPanel.tsx             # Persistent browser panel
│   │   │   ├── BrowserPreview.tsx           # WebSocket browser stream
│   │   │   ├── ChatInterface.tsx            # Main chat UI
│   │   │   ├── ChatMessage.tsx              # Message renderer
│   │   │   ├── ConfigDialog.tsx             # Settings + skills display
│   │   │   ├── ReasoningDisplay.tsx         # OpenAI reasoning summary
│   │   │   ├── ThoughtProcess.tsx           # Waterfall thinking display
│   │   │   ├── ThreadList.tsx               # Thread sidebar
│   │   │   └── ...
│   │   ├── hooks/             # React hooks
│   │   │   ├── useChat.ts                   # Chat state management
│   │   │   └── useThreads.ts                # Thread management
│   │   ├── types/             # TypeScript definitions
│   │   │   └── types.ts
│   │   ├── utils/             # Utility functions
│   │   │   └── utils.ts
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # 3-panel resizable layout
│   │   └── globals.css        # Claude-inspired theme
│   ├── components/            # shadcn/ui components
│   │   └── ui/
│   ├── lib/                   # Libraries
│   │   ├── config.ts          # Config with env support
│   │   └── utils.ts           # Utility functions
│   └── providers/             # Context providers
│       ├── ChatProvider.tsx   # Chat state provider
│       └── ClientProvider.tsx # Client-side wrapper
├── public/                    # Static assets
├── .env.local.example         # Environment variables template
├── .env.local                 # Local configuration (gitignored)
├── components.json            # shadcn/ui config
├── next.config.ts            # Next.js config
├── tailwind.config.mjs       # Tailwind config
├── tsconfig.json             # TypeScript config
└── package.json              # Dependencies
```

## Installation

### Prerequisites

- Node.js 18+ or 20+
- Yarn or npm
- Running Browser Use Agent backend (see `../browser-use-agent/README.md`)

### Setup

1. **Navigate to the frontend directory**:
```bash
cd deep-agents-ui
```

2. **Configure environment variables** (optional but recommended):
```bash
cp .env.local.example .env.local
# Edit .env.local with your settings
```

3. **Install dependencies**:
```bash
yarn install
# or
npm install
```

4. **Start development server**:
```bash
yarn dev
# or
npm run dev
```

5. **Open in browser**:
```
http://localhost:3000
```

## Configuration

### Environment Variables (Recommended)

Create `.env.local` from the example template:

```bash
cp .env.local.example .env.local
```

**Available Variables**:

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

These values serve as defaults and can be overridden in the Settings dialog.

### Settings Dialog

Click the **Settings** button in the sidebar (bottom left) to configure:

**Deployment Settings**:
- **Deployment URL**: Backend LangGraph server (`http://127.0.0.1:2024`)
- **Assistant ID**: Graph ID from langgraph.json (`browser-agent`)

**LangSmith** (Optional):
- **API Key**: For observability (`lsv2_pt_...`)

**Agent Behavior**:
- **Enable Ralph Mode**: Toggle iterative refinement
- **Max Iterations**: Number of refinement passes (1-20)
- **Recursion Limit**: Maximum agent reasoning steps (50-500, default: 200)

**Browser Streaming**:
- **Stream Port**: WebSocket port for browser viewport (1024-65535)

Settings override environment variables and are saved to localStorage.

## Usage

### Creating a Thread

1. Click **New chat** button at the top of the sidebar (Claude-style)
2. Type your task in the input box
3. Press Enter or click Send

The sidebar now follows Claude's design pattern with:
- **New chat** button prominently placed at the top
- **Recents** section showing your conversation threads
- **Settings** button at the bottom left corner
- Streamlined, minimal interface

### Example Tasks

**Simple Navigation**:
```
Navigate to example.com and tell me the page title
```

**Form Interaction**:
```
Go to https://www.w3schools.com/html/html_forms.asp, 
fill in the first name as "John" and submit the form
```

**Research Task**:
```
Research the top 3 features of Next.js 15 and create a summary
```

### Approving Browser Actions

When the agent wants to perform sensitive actions (click, fill, navigate), an approval dialog will appear:

1. **Review** the command and arguments
2. Click **Approve** to allow execution
3. Or click **Reject** to deny

**Auto-approved actions** (read-only):
- Taking snapshots
- Getting element info
- Taking screenshots
- Checking element visibility

### Viewing Agent's Thought Process

The agent's thinking appears in a collapsible section with intelligent summaries:

- **Smart Summaries**: When collapsed, shows first meaningful sentence (up to 70 characters)
- **Waterfall Pattern**: Hierarchical display of reasoning steps when expanded
- **Nested Steps**: Sub-tasks indented with visual indicators
- **Expand/Collapse**: Click anywhere on the thought header to toggle
- **Character Streaming**: Text streams in character-by-character for active thoughts
- **Step Hierarchy**: Numbered lists, bullet points, and indented sub-steps

**Collapsed View**:
```
🧠 Thought process   "Analyzing the request and identifying browser actions..."   ▼
```

**Expanded View**:
```
🧠 Thought process   ▲
Let me analyze the request...
├─ Breaking down the task
│  └─ Identifying browser actions
└─ Planning navigation steps
```

### Live Browser Preview (Header-Integrated Status Indicator)

The browser monitor is **always visible** as a status indicator with fully automatic panel management:

**Header Icon (Status Indicator Only)**:
1. **Idle State**: 🔴 Red monitor icon in top-right corner, disabled (not clickable, 50% opacity)
2. **Active State**: 🟢 Green monitor icon when browser session running
3. **Non-Interactive**: Icon is purely visual status, cannot be clicked
4. **Always Visible**: Present in header at all times as status indicator

**Panel Behavior (Fully Automatic)**:
1. **Auto-Open**: Panel automatically appears (right side) when browser session starts
2. **Auto-Close**: Panel automatically closes when session ends or thread changes
3. **No Manual Control**: Users cannot manually toggle - it's 100% session-driven
4. **Expanded - Not Working**: Shows "Browser is not working" message when no session
5. **Expanded - Active**: Shows live browser stream when session running
6. **Resizable**: Drag handle to adjust width (20-50%) when expanded

**Features**:
- **Always Visible**: Monitor icon always present in header (Claude-style)
- **Status Colors**: Red = idle/disabled, Green = active session
- **Smart Auto-Management**: Panel opens/closes automatically based on session state
- **Responsive Header**: Header layout adapts to sidebar and panel states (not fixed width)
- **Responsive Layout**: Chat panel expands from 65% to 100% when browser panel closed
- **Resizable**: Drag handle to adjust panel width (20-50%) when expanded
- **Live Streaming**: Real-time WebSocket viewport updates from browser
- **Consistent URLs**: Same thread always uses same stream port (deterministic)
- **Auto-Reconnect**: Exponential backoff with manual retry (up to 5 attempts)
- **No False Errors**: Fixed closure issue - no more false "connection failed" logs
- **Smart Error Messages**: Actionable troubleshooting steps for real connection issues
- **Auto-Timeout**: Sessions automatically close after 5 minutes of inactivity (backend)

### Managing Threads

- **Switch threads**: Click any thread in the sidebar
- **Rename thread**: Long press or right-click → Rename
- **Delete thread**: Long press or right-click → Delete
- **Mark resolved**: ✓ button in thread list

## Claude-Style Design System

The UI follows Anthropic's Claude design philosophy with a faithful sidebar recreation:

### Complete Claude UI Match

The interface now fully replicates Claude's design:

**Header** (Three-column layout with centered title):
```
┌─────────────────────────────────────────────────────────┐
│ [☰]           Full Chat Title (Centered)           [🖥] │
│                  Can Wrap To Two Lines...               │
└─────────────────────────────────────────────────────────┘

Left: Sidebar toggle button (with notification badge for interrupts)
Center: Thread title (centered, max 600px width, truncated with ellipsis)
Right: Browser status icon (RED = idle/disabled, GREEN = active)
```

**Browser Status Icon Behavior**:
- **Red (Idle)**: No browser session, icon disabled and not clickable
- **Green (Active)**: Browser session running, but still not clickable
- **Fully Automatic**: Panel opens/closes based on session state only
- **No Manual Control**: Icon is a status indicator, not an interactive button
```

**Sidebar**:
```
┌─────────────────────┐
│  [New chat] ⊕       │  ← Top: New chat button
├─────────────────────┤
│  Filter: All ▼      │  ← Filters
├─────────────────────┤
│  RECENTS            │  ← Section header
│  💬 Thread 1        │
│  💬 Thread 2        │  ← Thread list
│  💬 Thread 3        │
│  ...                │
├─────────────────────┤
│  [Settings] ⚙️      │  ← Bottom: Settings
└─────────────────────┘
```

**Key Features**:
- **Dynamic header** shows current chat title (not static "Deep Agent UI")
- **Full title display** shows up to 30 words with multi-line support (line-clamp-2)
- **Hamburger menu** (☰) icon to open sidebar when closed
- **Close icon** (⟨) to collapse sidebar when open
- **Interrupt badge** appears on menu icon when attention needed
- **Enhanced error handling** for WebSocket connections with helpful messages
- Clean, minimal design with rounded buttons
- Settings moved to bottom left (no longer in top header)
- New chat button prominently placed at top
- Consistent spacing and typography matching Claude

### Color Palette

**Light Mode**:
- Background: `#ffffff` (Pure white)
- Surface: `#f5f5f5` (Light gray cards)
- Border: `#e5e5e5` (Subtle borders)
- Primary: `#2f6868` (Teal)
- Text: `#1a1a1a` / `#666666`

**Dark Mode**:
- Background: `#1a1a1a`
- Surface: `#2a2a2a`
- Border: `#404040`
- Primary: `#4db6ac`
- Text: `#f0f0f0` / `#a0a0a0`

### Typography

- **Font**: System font stack (SF Pro, Segoe UI, Roboto)
- **Base size**: 16px
- **Line height**: 1.5 (normal), 1.75 (relaxed for chat)

### Animations

- **Smooth transitions**: 200ms ease-in-out
- **Thought process streaming**: Character-by-character (20ms/char)
- **Loading states**: Subtle pulse animations

## Development

### Project Structure

- **`components/`**: Reusable UI components following atomic design
- **`hooks/`**: Custom React hooks for state and side effects
- **`providers/`**: Context providers for global state
- **`types/`**: TypeScript type definitions
- **`utils/`**: Utility functions and helpers

### Adding New Components

```bash
# Using shadcn/ui CLI
npx shadcn@latest add [component-name]

# Example: Add a new button variant
npx shadcn@latest add button
```

### Code Style

- **TypeScript**: Strict mode enabled
- **ESLint**: Configured for Next.js and React
- **Prettier**: Auto-formatting on save
- **Components**: Use functional components with hooks
- **Naming**: PascalCase for components, camelCase for functions

### Building for Production

```bash
# Build optimized production bundle
yarn build

# Start production server
yarn start

# Export static site (if needed)
yarn build && yarn export
```

## Key Components

### `ChatInterface.tsx`
Main chat interface orchestrating:
- Message display
- Input handling
- Approval dialogs
- Task and file management

### `BrowserPanel.tsx` (New!)
Persistent right-side browser panel:
- Resizable panel with drag handles
- WebSocket connection management
- Exponential backoff reconnection
- Fullscreen mode toggle
- Connection status display
- Session information footer

### `ThoughtProcess.tsx` (Enhanced)
Waterfall thought process display:
- Parses content into hierarchical steps
- Nested structure with indentation
- Expandable/collapsible sub-steps
- Character-by-character streaming
- Visual hierarchy indicators
- Smooth animations

### `ConfigDialog.tsx` (Enhanced)
Comprehensive settings modal:
- Deployment configuration
- LangSmith integration
- Ralph Mode toggle and iterations
- Browser streaming port
- Input validation
- Organized sections

### `BrowserPreview.tsx`
WebSocket client for browser streaming:
- Connects to `ws://localhost:{port}`
- Renders base64 JPEG frames
- Shows connection status
- Auto-reconnect on disconnect

### `useChat.ts` Hook
Manages chat state:
- SSE streaming from backend
- Message history
- Browser session state
- Approval queue
- Thought process updates

## Troubleshooting

### WebSocket Connection Errors

If you see "WebSocket connection error - browser stream may not be running":

**Root Cause**: The backend is not configured to stream browser viewport data via WebSocket.

**Solution**: Set the `AGENT_BROWSER_STREAM_PORT` environment variable when starting the backend:

```bash
# Option 1: Set when starting the backend
AGENT_BROWSER_STREAM_PORT=9223 langgraph dev --port 2024

# Option 2: Add to backend .env file
echo "AGENT_BROWSER_STREAM_PORT=9223" >> browser-use-agent/.env
langgraph dev --port 2024
```

**Verification Steps**:
1. **Ensure browser session is active**: The agent must have called `browser_navigate` to start a session
2. **Check browser stream port matches**: 
   - Frontend setting (default: 9223) in Settings dialog
   - Backend `AGENT_BROWSER_STREAM_PORT` environment variable
3. **Verify WebSocket server is running**: Check backend logs for streaming initialization
4. **Check console logs**: Look for "Attempting to connect to browser stream: ws://localhost:XXXX"

The browser panel will automatically attempt to reconnect with exponential backoff (up to 5 attempts).

### Browser Session Auto-Timeout

**Feature**: Browser sessions automatically close after 60 seconds of inactivity to prevent resource leaks.

**How It Works**:
1. A background cleanup thread monitors all active browser sessions
2. Each browser interaction (`browser_click`, `browser_fill`, `browser_type`, etc.) updates the last activity timestamp
3. Sessions inactive for more than 60 seconds are automatically closed
4. The cleanup thread checks every 10 seconds
5. Session state is properly cleaned up on timeout

**Activity Tracking**:
- ✅ `browser_click` - Updates activity
- ✅ `browser_fill` - Updates activity
- ✅ `browser_type` - Updates activity
- ✅ `browser_press_key` - Updates activity
- ✅ `browser_navigate` - Updates activity (and resets timeout)
- ❌ `browser_snapshot` - Read-only, does not update activity
- ❌ `browser_screenshot` - Read-only, does not update activity

**Configuration**:
The timeout duration is configurable in `browser_use_agent/tools.py`:
```python
BROWSER_TIMEOUT_SECONDS = 60  # Default: 1 minute
```

**Logs**:
Backend will log timeout events:
```
[Browser Timeout] Session thread-123 inactive for 62s
[Browser Timeout] Auto-closing session thread-123
[Browser Timeout] Session thread-123 closed successfully
```

### Can't Connect to Backend

**Error**: "Failed to fetch" or "Network error"

**Solutions**:
1. Verify backend is running: `langgraph dev --port 2024`
2. Check Deployment URL in settings
3. Ensure no CORS issues (backend should allow `localhost:3000`)

### Browser Panel Not Showing

**Issue**: Right panel doesn't appear when browser session starts

**Solutions**:
1. Check `agent-browser` is installed: `agent-browser --version`
2. Verify backend started a browser session
3. Check browser session is active in chat context
4. Verify WebSocket port matches backend: `lsof -i :9223`

**WebSocket Connection Failed**:
1. **Port mismatch**: Ensure frontend `NEXT_PUBLIC_BROWSER_STREAM_PORT` matches backend `AGENT_BROWSER_STREAM_PORT`
2. **Backend not configured**: Set `AGENT_BROWSER_STREAM_PORT=9223` when starting backend (see above)
3. **Firewall blocking**: Check firewall isn't blocking WebSocket connections on port 9223
4. **Manual retry**: Use the "Try Again" button in the browser panel after reconfiguring the backend

### Tool Call Arguments Display

**Browser Tools** (simplified format):
Browser-related tools show arguments in a clean `key: value` format:
```
browser_navigate
  url: https://example.com
  thread_id: thread-123
```

**Other Tools** (expandable format):
Non-browser tools retain the expandable JSON format for detailed inspection:
```
custom_tool
  ▼ complex_arg
    { "nested": "data" }
  ▼ another_arg
    ["array", "values"]
```

This makes browser automation logs more readable while preserving detailed views for complex tools.

### Thought Process Not Streaming

**Issue**: Thought process appears instantly instead of streaming

**Solution**: This is normal for cached/fast responses. Streaming effect appears during longer processing.

### TypeScript Errors

**Error**: Type errors in components

**Solutions**:
```bash
# Regenerate types
yarn build

# Check TypeScript errors
yarn tsc --noEmit
```

## Performance Optimization

### Image Optimization
- Browser frames are JPEG-encoded for efficiency
- Automatic frame rate limiting (client-side)

### Code Splitting
- Lazy load heavy components
- Dynamic imports for modals and dialogs

### Memoization
- `React.memo` for expensive components
- `useMemo` for computed values
- `useCallback` for event handlers

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Related Documentation

- [Backend README](../browser-use-agent/README.md)
- [Main Project README](../README.md)
- Skills: `../.browser-agent/skills/` - PDF, PPTX, DOCX, browser automation
- [agent-browser docs](https://agent-browser.dev/)
- [DeepAgents docs](https://docs.langchain.com/oss/python/deepagents/overview)

## License

MIT License - See LICENSE file for details
