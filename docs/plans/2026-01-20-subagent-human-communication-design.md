# Subagent Human Communication Design

**Date:** 2026-01-20
**Status:** Approved
**Issue:** Subagent interrupts don't bubble up to parent, leaving subagents stuck when requesting human help

## Problem

When the main agent spawns a subagent via the DeepAgents `task` tool, and that subagent calls `request_human_guidance()`:

1. The subagent raises `GraphInterrupt` with the guidance request
2. The interrupt does NOT bubble up to the parent agent
3. The subagent is stuck waiting for a response that never comes
4. The frontend never sees the interrupt

**Evidence from LangSmith:**
```
GraphInterrupt((Interrupt(value={'type': 'guidance', 'thread_id': '...',
'context': '...', 'question': '...', 'attempted_approaches': '...'}),))
```

The interrupt is raised but not forwarded to the parent level.

## Root Cause

DeepAgents' `task` tool runs subagents as **independent invocations** rather than **nested subgraphs**. In LangGraph:
- Nested subgraph: Interrupt bubbles up automatically
- Independent invocation: Interrupt stops the subagent but doesn't reach parent

## Solution: Interrupt Forwarding Layer

Create a mechanism to catch subagent interrupts, store them in shared state, let the frontend surface them, then resume the subagent with the response.

### Part 1: State Changes

**File:** `browser-use-agent/browser_use_agent/state.py`

```python
class SubagentInterrupt(TypedDict, total=False):
    """Pending interrupt from a subagent."""
    id: str                    # Unique interrupt ID
    subagent_id: str           # Which subagent is waiting
    subagent_name: str         # Human-readable name
    interrupt_type: str        # guidance, credentials, confirmation
    interrupt_data: Dict       # Full interrupt value
    response: Any              # Human's response (when responded)
    created_at: int            # Timestamp
    status: str                # pending, responded, resumed


class AgentState(TypedDict, total=False):
    """State for the browser automation agent."""
    messages: List[BaseMessage]
    todos: List[TodoItem]
    files: Dict[str, str]
    browser_session: Optional[BrowserSession]
    approval_queue: List[BrowserCommand]
    current_thought: Optional[ThoughtProcess]
    thread_id: str
    pending_subagent_interrupts: List[SubagentInterrupt]  # NEW
```

### Part 2: Interrupt Capture

**File:** `browser-use-agent/browser_use_agent/subagent_interrupt.py` (new file)

```python
"""Subagent interrupt forwarding layer.

Catches GraphInterrupt from subagents and stores them in parent state
so they can be surfaced to the frontend for human response.
"""

import time
import uuid
from typing import Any, Dict, Optional
from langgraph.types import GraphInterrupt


def execute_subagent_with_interrupt_capture(
    subagent,
    input_data: Dict[str, Any],
    parent_state: Dict[str, Any],
    subagent_name: str = "Subagent"
) -> Dict[str, Any]:
    """Execute subagent and capture any interrupts.

    Args:
        subagent: The subagent graph to execute
        input_data: Input for the subagent
        parent_state: Parent agent's state (will be modified)
        subagent_name: Human-readable name for the subagent

    Returns:
        Dict with success status and either result or interrupt info
    """
    subagent_id = str(uuid.uuid4())

    try:
        result = subagent.invoke(input_data)
        return {"success": True, "result": result}

    except GraphInterrupt as e:
        # Extract interrupt data from the exception
        interrupt_value = e.args[0].value if e.args else {}

        interrupt_info = {
            "id": str(uuid.uuid4()),
            "subagent_id": subagent_id,
            "subagent_name": subagent_name,
            "interrupt_type": interrupt_value.get("type", "guidance"),
            "interrupt_data": interrupt_value,
            "created_at": int(time.time()),
            "status": "pending"
        }

        # Initialize list if needed
        if "pending_subagent_interrupts" not in parent_state:
            parent_state["pending_subagent_interrupts"] = []

        # Store in parent state
        parent_state["pending_subagent_interrupts"].append(interrupt_info)

        return {
            "success": False,
            "waiting_for_human": True,
            "interrupt_id": interrupt_info["id"],
            "message": f"Subagent '{subagent_name}' needs human assistance: {interrupt_value.get('question', 'Unknown question')}"
        }


def check_and_resume_subagents(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Check for responded subagent interrupts and prepare resume info.

    Args:
        state: Current agent state

    Returns:
        Dict with resume info if a subagent should be resumed, None otherwise
    """
    for interrupt in state.get("pending_subagent_interrupts", []):
        if interrupt.get("status") == "responded":
            # Mark as resumed
            interrupt["status"] = "resumed"

            return {
                "resume_subagent_id": interrupt["subagent_id"],
                "resume_value": interrupt.get("response"),
                "interrupt_id": interrupt["id"]
            }

    return None


def respond_to_subagent_interrupt(
    state: Dict[str, Any],
    interrupt_id: str,
    response: Any
) -> bool:
    """Store response for a subagent interrupt.

    Args:
        state: Current agent state
        interrupt_id: ID of the interrupt to respond to
        response: Human's response

    Returns:
        True if interrupt was found and updated, False otherwise
    """
    for interrupt in state.get("pending_subagent_interrupts", []):
        if interrupt["id"] == interrupt_id:
            interrupt["status"] = "responded"
            interrupt["response"] = response
            return True

    return False
```

### Part 3: Frontend State Types

**File:** `deep-agents-ui/src/app/types/types.ts`

```typescript
export interface SubagentInterrupt {
  id: string;
  subagent_id: string;
  subagent_name: string;
  interrupt_type: "guidance" | "credentials" | "confirmation";
  interrupt_data: {
    type: string;
    question?: string;
    context?: string;
    attempted_approaches?: string;
    service?: string;
    credential_types?: string;
    reason?: string;
    action?: string;
    risks?: string;
    alternatives?: string;
    [key: string]: any;
  };
  response?: any;
  created_at: number;
  status: "pending" | "responded" | "resumed";
}
```

**File:** `deep-agents-ui/src/app/hooks/useChat.ts`

```typescript
// Add to StateType
export type StateType = {
  messages: Message[];
  todos: TodoItem[];
  files: Record<string, string>;
  email?: { /* ... */ };
  ui?: any;
  browser_session?: BrowserSession | null;
  approval_queue?: BrowserCommand[];
  current_thought?: ThoughtProcess | null;
  pending_subagent_interrupts?: SubagentInterrupt[];  // NEW
};

// Add response function
const respondToSubagentInterrupt = useCallback(
  async (interruptId: string, response: any) => {
    if (!threadId) return;

    // Update state with response
    const updatedInterrupts = (stream.values.pending_subagent_interrupts || []).map(
      i => i.id === interruptId
        ? { ...i, status: "responded" as const, response }
        : i
    );

    await client.threads.updateState(threadId, {
      values: {
        pending_subagent_interrupts: updatedInterrupts
      },
      asNode: "tools"  // Required: use "tools" node (from create_deep_agent graph structure)
    });

    // Continue the stream to let parent agent resume subagent
    continueStream();
  },
  [threadId, client, stream.values.pending_subagent_interrupts, continueStream]
);

// Export in return
return {
  // ... existing exports ...
  pendingSubagentInterrupts: stream.values.pending_subagent_interrupts || [],
  respondToSubagentInterrupt,
};
```

### Part 4: Frontend UI Integration

**File:** `deep-agents-ui/src/app/components/ChatInterface.tsx`

```typescript
// Add to useChatContext destructuring
const {
  // ... existing ...
  pendingSubagentInterrupts,
  respondToSubagentInterrupt,
} = useChatContext();

// Detect pending subagent interrupt
const pendingSubagentInterrupt = useMemo(() => {
  return pendingSubagentInterrupts.find(i => i.status === "pending") || null;
}, [pendingSubagentInterrupts]);

// Render in JSX (after humanLoopInterrupt, before input form)
{pendingSubagentInterrupt && (
  <div className="mx-auto w-[calc(100%-32px)] max-w-[1024px] mb-4">
    <HumanLoopInterrupt
      type={pendingSubagentInterrupt.interrupt_type}
      data={pendingSubagentInterrupt.interrupt_data}
      subagentName={pendingSubagentInterrupt.subagent_name}
      onRespond={(response) => respondToSubagentInterrupt(
        pendingSubagentInterrupt.id,
        response
      )}
    />
  </div>
)}
```

### Part 5: Update HumanLoopInterrupt Component

**File:** `deep-agents-ui/src/app/components/HumanLoopInterrupt.tsx`

Add `subagentName` prop to show which subagent is asking:

```typescript
interface HumanLoopInterruptProps {
  type: "guidance" | "credentials" | "confirmation";
  data: { /* ... */ };
  subagentName?: string;  // NEW - optional, shows subagent context
  onRespond: (response: any) => void;
}

export function HumanLoopInterrupt({ type, data, subagentName, onRespond }: HumanLoopInterruptProps) {
  // In each section, show subagent context if provided

  if (type === "guidance") {
    return (
      <div className="border rounded-lg p-4 bg-amber-50 border-amber-200">
        <div className="flex items-center gap-2 mb-2">
          <HelpCircle size={20} className="text-amber-600" />
          <h3 className="font-semibold text-amber-800">
            {subagentName ? `${subagentName} needs guidance` : "Agent needs guidance"}
          </h3>
        </div>
        {/* ... rest of component ... */}
      </div>
    );
  }

  // Similar changes for credentials and confirmation types
}
```

## Integration with DeepAgents Task Tool

The interrupt capture needs to be integrated with how DeepAgents runs subagents. Options:

1. **Monkey-patch the task tool** - Wrap the existing tool's execution
2. **Custom middleware** - Add a LangGraph middleware that catches interrupts
3. **Fork/modify DeepAgents** - If needed for deeper integration

Recommended approach: Start with monkey-patching to test the concept, then consider cleaner integration.

## Files to Create/Modify

**Create:**
1. `browser-use-agent/browser_use_agent/subagent_interrupt.py` - Interrupt capture logic

**Modify:**
1. `browser-use-agent/browser_use_agent/state.py` - Add SubagentInterrupt type and field
2. `deep-agents-ui/src/app/types/types.ts` - Add SubagentInterrupt interface
3. `deep-agents-ui/src/app/hooks/useChat.ts` - Add state, response function
4. `deep-agents-ui/src/app/components/ChatInterface.tsx` - Detect and render
5. `deep-agents-ui/src/app/components/HumanLoopInterrupt.tsx` - Add subagentName prop

## Testing

1. Spawn a subagent that will need human guidance (e.g., navigate to a page that requires login)
2. Verify the interrupt appears in `pending_subagent_interrupts` state
3. Verify frontend detects and renders the interrupt
4. Submit a response
5. Verify the subagent resumes with the response
6. Verify the interrupt status changes to "resumed"

## Future Enhancements

- Track multiple concurrent subagent interrupts
- Show interrupt history
- Timeout handling for unresponsive interrupts
- Cancel/abort stuck subagents
- **Investigate DeepAgents nested subgraph support**: According to LangGraph docs, `GraphInterrupt` should bubble up automatically from nested subgraphs. If DeepAgents can be configured to use nested subgraphs instead of independent invocations, this interrupt forwarding layer may become unnecessary.
