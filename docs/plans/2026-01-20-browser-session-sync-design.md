# Browser Session Sync Design

**Date:** 2026-01-20
**Status:** Approved
**Issue:** Frontend shows browser as active when backend has closed the session via timeout

## Problem

When the backend closes a browser session due to inactivity timeout (5 minutes), the frontend continues to show the browser as "active" with a green indicator. This happens because:

1. The cleanup thread in `tools.py` updates a local in-memory dict (`_browser_sessions`)
2. The LangGraph thread state is never updated
3. The frontend only receives state via LangGraph streaming, so it never learns about the timeout closure

**Current flow (broken):**
```
Backend cleanup thread → _browser_sessions dict (local) → Frontend never knows
```

## Solution

Two-part solution to ensure frontend stays in sync:

### Part 1: Backend State Update

Use the LangGraph SDK client from the cleanup thread to update the thread state when a session is closed.

**File:** `browser-use-agent/browser_use_agent/tools.py`

**Changes:**

1. Add LangGraph SDK client (lazy initialized):

```python
from langgraph_sdk import get_client

_langgraph_client = None

def _get_langgraph_client():
    global _langgraph_client
    if _langgraph_client is None:
        _langgraph_client = get_client(url=f"http://localhost:{Config.LANGGRAPH_PORT}")
    return _langgraph_client
```

2. Add function to update thread state:

```python
def _update_thread_browser_session(thread_id: str, is_active: bool):
    """Update browser_session in LangGraph thread state."""
    try:
        client = _get_langgraph_client()
        client.threads.update_state(
            thread_id,
            values={
                "browser_session": {
                    "sessionId": thread_id,
                    "streamUrl": None if not is_active else stream_manager.get_stream_url(thread_id),
                    "isActive": is_active
                }
            },
            as_node="tools"  # Required: use "tools" node (from create_deep_agent graph structure)
        )
        print(f"[Browser Timeout] Updated LangGraph state for {thread_id}")
    except Exception as e:
        print(f"[Browser Timeout] Failed to update LangGraph state: {e}")
```

3. Call from `_cleanup_inactive_sessions()` after closing session:

```python
for thread_id in inactive_threads:
    result = _run_browser_command(thread_id, ["close"])
    stream_manager.release_port(thread_id)
    _update_browser_session(thread_id, is_active=False)
    _update_thread_browser_session(thread_id, is_active=False)  # NEW
```

### Part 2: Frontend Polling Fallback

Add polling to detect session closure when the stream is idle.

**File:** `deep-agents-ui/src/app/hooks/useChat.ts`

**Changes:**

Add useEffect for polling:

```typescript
const BROWSER_SESSION_POLL_INTERVAL = 30000; // 30 seconds

useEffect(() => {
  // Only poll if we think browser is active but stream is idle
  if (!browserSession?.isActive || stream.isLoading || !threadId) {
    return;
  }

  const pollSessionStatus = async () => {
    try {
      const state = await client.threads.getState(threadId);
      const backendSession = state.values?.browser_session;

      if (backendSession && !backendSession.isActive && browserSession?.isActive) {
        console.log("[useChat] Polling detected session closed, syncing state");
        setBrowserSession(backendSession);
      }
    } catch (error) {
      console.error("[useChat] Failed to poll session status:", error);
    }
  };

  const intervalId = setInterval(pollSessionStatus, BROWSER_SESSION_POLL_INTERVAL);

  return () => clearInterval(intervalId);
}, [browserSession?.isActive, stream.isLoading, threadId, client]);
```

## Configuration

Add `LANGGRAPH_PORT` to `configuration.py` (default: 2024) to ensure the cleanup thread connects to the correct LangGraph server.

## Files to Modify

1. `browser-use-agent/browser_use_agent/tools.py` - Add LangGraph client and state update
2. `browser-use-agent/browser_use_agent/configuration.py` - Add LANGGRAPH_PORT config
3. `deep-agents-ui/src/app/hooks/useChat.ts` - Add polling fallback

## Testing

1. Start a browser session via the agent
2. Wait for 5+ minutes without interaction
3. Verify frontend shows browser as inactive after timeout
4. Verify polling catches the state change within 30 seconds if stream is idle
