# Deep Agents UI - Browser Automation Frontend

A modern, Claude-inspired interface for interacting with the Browser Use Agent. Built with Next.js 15, React 19, and Tailwind CSS.

## What's New (Latest Update)

### Claude UI Complete Match 🎨

The interface now matches Claude's design exactly:

**Latest Changes** (v2.0):
- 📝 **Full title display** - Shows up to 30 words of chat title with ellipsis
- 📏 **Multi-line title support** - Title can wrap to 2 lines using line-clamp-2
- 🔧 **WebSocket error handling** - Better error messages for browser stream connection issues
- ✅ **URL validation** - WebSocket connections validated before attempting to connect

**Previous Changes** (v1.0):
- 🔄 **Dynamic header** - Shows current chat title (like Claude)
- 🍔 **Hamburger menu icon** - Toggle sidebar open/closed with Menu icon
- ✕ **Close sidebar icon** - PanelLeftClose icon when sidebar is open
- 📝 **Centered chat title** - Current thread name displayed in header center
- 🎯 **Flexible layout** - Header adapts based on sidebar state

**Previous Changes**:
- ✨ **New chat button** moved to top of sidebar (from top-right header)
- ⚙️ **Settings button** relocated to bottom left corner (from top-right header)
- 🧹 **Cleaner header** with just sidebar toggle and app title
- 📋 **Recents section** with streamlined thread display
- 💬 **Thread items** now show message icon and simplified layout
- 🎯 **Consistent spacing** matching Claude's design language

**Result**: Complete Claude UI replica with dynamic header and proper sidebar controls

---

## Features

- 🎨 **Claude-Style Aesthetic**: Clean, minimal design with Anthropic-inspired color palette and sidebar
- 💬 **Multi-Thread Chat**: Create and manage multiple conversation threads
- 🧠 **Waterfall Thought Process**: Nested, cascading display of agent's reasoning steps
- 🌐 **Persistent Browser Panel**: Resizable right-side panel with live WebSocket streaming
- ✅ **Interactive Approvals**: Review and approve browser actions before execution
- 📋 **Task Management**: Visual todo list showing agent's task breakdown
- 📁 **File Viewer**: View and edit files created by the agent
- 🔄 **Streaming Updates**: Real-time updates via Server-Sent Events (SSE)
- ⚙️ **Ralph Mode Configuration**: Enable iterative refinement with configurable max iterations
- 🔧 **Environment Variable Support**: Pre-configure settings via `.env.local`
- 🎯 **Claude-Inspired Sidebar**: New chat button at top, settings at bottom, streamlined layout

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
│   │   ├── components/        # UI components
│   │   │   ├── BrowserCommandApproval.tsx   # Approval dialog
│   │   │   ├── BrowserPanel.tsx             # Persistent browser panel (NEW)
│   │   │   ├── BrowserPreview.tsx           # WebSocket browser stream
│   │   │   ├── ChatInterface.tsx            # Main chat UI
│   │   │   ├── ChatMessage.tsx              # Message renderer
│   │   │   ├── ConfigDialog.tsx             # Enhanced settings modal
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

### Viewing Agent's Thought Process (Waterfall Display)

The agent's thinking appears in a collapsible section with nested structure:

- **Waterfall Pattern**: Hierarchical display of reasoning steps
- **Nested Steps**: Sub-tasks indented with visual indicators
- **Expand/Collapse**: Click chevron to show/hide details
- **Character Streaming**: Text streams in character-by-character
- **Step Hierarchy**: Numbered lists, bullet points, and indented sub-steps

**Example Structure**:
```
[Thought Process] ▼
Let me analyze the request...
├─ Breaking down the task
│  └─ Identifying browser actions
└─ Planning navigation steps
```

### Live Browser Preview (Persistent Panel)

When the agent opens a browser session, a resizable panel appears on the right:

- **Persistent Display**: Panel stays visible across messages
- **Resizable**: Drag the handle to adjust panel width
- **Live Streaming**: Real-time WebSocket viewport updates
- **Connection Status**: Visual indicator (green dot = connected)
- **Auto-Reconnect**: Exponential backoff with manual retry
- **Session Info**: Display current browser session ID
- **Fullscreen Mode**: Toggle for larger view

### Managing Threads

- **Switch threads**: Click any thread in the sidebar
- **Rename thread**: Long press or right-click → Rename
- **Delete thread**: Long press or right-click → Delete
- **Mark resolved**: ✓ button in thread list

## Claude-Style Design System

The UI follows Anthropic's Claude design philosophy with a faithful sidebar recreation:

### Complete Claude UI Match

The interface now fully replicates Claude's design:

**Header** (Dynamic with full title):
```
┌──────────────────────────────────────────┐
│ [☰]   Full Chat Title Up To 30 Words    │  ← Sidebar closed
│       Can Wrap To Two Lines...           │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ [⟨]   Full Chat Title Up To 30 Words    │  ← Sidebar open
│       Can Wrap To Two Lines...           │
└──────────────────────────────────────────┘
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

1. **Ensure browser session is active**: The agent must have called `browser_navigate` to start a session
2. **Check browser stream port**: Default is 9223, verify in Settings
3. **Verify agent-browser CLI**: Make sure the browser automation backend is running
4. **Check console logs**: Look for "Attempting to connect to browser stream: ws://localhost:XXXX"

The browser panel will automatically attempt to reconnect with exponential backoff.

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
1. Ensure `NEXT_PUBLIC_BROWSER_STREAM_PORT` matches backend
2. Check firewall isn't blocking WebSocket connections
3. Verify backend set `AGENT_BROWSER_STREAM_PORT` environment variable
4. Try manual reconnect button in browser panel

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

## What's New in This Version

### ✨ Major Updates

**Waterfall Thought Process**:
- Hierarchical display of agent's reasoning
- Nested steps with visual indentation
- Expandable/collapsible sections
- Character-by-character streaming

**Persistent Browser Panel**:
- Resizable right-side panel (20-50% width)
- Panel persists across all messages
- Auto-reconnection with exponential backoff
- Fullscreen mode for detailed viewing

**Enhanced Configuration**:
- Environment variable support (`.env.local`)
- Ralph Mode toggle and iteration control
- Browser stream port configuration
- Settings override env defaults

**Claude-Inspired Aesthetic**:
- Updated color palette (light/dark modes)
- Smooth transitions (200ms cubic-bezier)
- Improved typography and spacing
- Minimal, clean design

**3-Panel Resizable Layout**:
- Thread sidebar (15-30%)
- Chat area (50-80%, dynamic)
- Browser panel (20-50%, conditional)
- Panel sizes persist via localStorage

## Related Documentation

- [Backend README](../browser-use-agent/README.md)
- [Main Project README](../README.md)
- [Implementation Notes](./IMPLEMENTATION_NOTES.md)
- [agent-browser docs](https://agent-browser.dev/)
- [DeepAgents docs](https://docs.langchain.com/oss/python/deepagents/overview)

## License

MIT License - See LICENSE file for details
