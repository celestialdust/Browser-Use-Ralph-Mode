# Help Message Surfacing in UI Design

**Date:** 2026-01-20
**Status:** Approved
**Issue:** Human-loop interrupts only show in backend terminal, not in frontend UI

## Problem

When the agent calls human-loop tools (`request_human_guidance`, `request_credentials`, `request_confirmation`), the messages only appear in the backend terminal. The frontend doesn't render these interrupts, so users can't respond.

**Backend interrupt structure:**
```python
# request_human_guidance
interrupt({
    "type": "guidance",
    "thread_id": thread_id,
    "context": context,
    "question": question,
    "attempted_approaches": attempted_approaches,
})

# request_credentials
interrupt({
    "type": "credentials",
    "thread_id": thread_id,
    "service": service,
    "credential_types": credential_types,
    "reason": reason,
    "question": f"Please provide {credential_types} for {service}",
})

# request_confirmation
interrupt({
    "type": "confirmation",
    "thread_id": thread_id,
    "action": action,
    "risks": risks,
    "alternatives": alternatives,
    "question": f"Should I proceed with: {action}?",
    "options": ["Approve", "Reject", "Suggest alternative"],
})
```

**Frontend currently only handles:** `interrupt.value.action_requests` (tool approval)

## Solution

### Part 1: New Component

**File:** `deep-agents-ui/src/app/components/HumanLoopInterrupt.tsx`

```typescript
"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpCircle, KeyRound, AlertTriangle } from "lucide-react";

interface HumanLoopInterruptProps {
  type: "guidance" | "credentials" | "confirmation";
  data: {
    question?: string;
    context?: string;
    attempted_approaches?: string;
    service?: string;
    credential_types?: string;
    reason?: string;
    action?: string;
    risks?: string;
    alternatives?: string;
    options?: string[];
  };
  onRespond: (response: any) => void;
}

export function HumanLoopInterrupt({ type, data, onRespond }: HumanLoopInterruptProps) {
  const [response, setResponse] = useState("");
  const [credentials, setCredentials] = useState({ username: "", password: "" });

  if (type === "guidance") {
    return (
      <div className="border rounded-lg p-4 bg-amber-50 border-amber-200 dark:bg-amber-950 dark:border-amber-800">
        <div className="flex items-center gap-2 mb-2">
          <HelpCircle size={20} className="text-amber-600 dark:text-amber-400" />
          <h3 className="font-semibold text-amber-800 dark:text-amber-200">Agent needs guidance</h3>
        </div>
        {data.context && (
          <p className="text-sm text-amber-700 dark:text-amber-300 mt-2">{data.context}</p>
        )}
        <p className="font-medium mt-3 text-amber-900 dark:text-amber-100">{data.question}</p>
        {data.attempted_approaches && (
          <details className="mt-2 text-xs text-amber-600 dark:text-amber-400">
            <summary className="cursor-pointer">What I've tried</summary>
            <p className="mt-1 pl-2 border-l-2 border-amber-300">{data.attempted_approaches}</p>
          </details>
        )}
        <div className="mt-4 flex flex-col gap-2">
          <textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            placeholder="Your guidance..."
            className="w-full p-2 border rounded text-sm min-h-[80px] bg-white dark:bg-gray-900"
          />
          <Button
            onClick={() => onRespond(response)}
            disabled={!response.trim()}
            className="self-end"
          >
            Send Guidance
          </Button>
        </div>
      </div>
    );
  }

  if (type === "credentials") {
    return (
      <div className="border rounded-lg p-4 bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800">
        <div className="flex items-center gap-2 mb-2">
          <KeyRound size={20} className="text-blue-600 dark:text-blue-400" />
          <h3 className="font-semibold text-blue-800 dark:text-blue-200">
            Credentials needed for {data.service}
          </h3>
        </div>
        <p className="text-sm text-blue-700 dark:text-blue-300">{data.reason}</p>
        <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
          Required: {data.credential_types}
        </p>
        <div className="mt-4 flex flex-col gap-3">
          <input
            type="text"
            value={credentials.username}
            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            placeholder="Username or email"
            className="w-full p-2 border rounded text-sm bg-white dark:bg-gray-900"
          />
          <input
            type="password"
            value={credentials.password}
            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            placeholder="Password"
            className="w-full p-2 border rounded text-sm bg-white dark:bg-gray-900"
          />
          <Button
            onClick={() => onRespond(credentials)}
            disabled={!credentials.username || !credentials.password}
            className="self-end"
          >
            Submit Credentials
          </Button>
        </div>
      </div>
    );
  }

  if (type === "confirmation") {
    return (
      <div className="border rounded-lg p-4 bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle size={20} className="text-red-600 dark:text-red-400" />
          <h3 className="font-semibold text-red-800 dark:text-red-200">Confirmation required</h3>
        </div>
        <p className="font-medium text-red-900 dark:text-red-100">{data.action}</p>
        <p className="text-sm text-red-700 dark:text-red-300 mt-2">
          <strong>Risks:</strong> {data.risks}
        </p>
        {data.alternatives && data.alternatives !== "None" && (
          <p className="text-sm text-red-600 dark:text-red-400 mt-1">
            <strong>Alternatives:</strong> {data.alternatives}
          </p>
        )}
        <div className="flex gap-2 mt-4">
          <Button
            variant="destructive"
            onClick={() => onRespond("approved")}
          >
            Approve
          </Button>
          <Button
            variant="outline"
            onClick={() => onRespond("rejected")}
          >
            Reject
          </Button>
        </div>
      </div>
    );
  }

  return null;
}
```

### Part 2: Integration into ChatInterface

**File:** `deep-agents-ui/src/app/components/ChatInterface.tsx`

**Changes:**

1. Add import:
```typescript
import { HumanLoopInterrupt } from "@/app/components/HumanLoopInterrupt";
```

2. Add detection logic (after `reviewConfigsMap`):
```typescript
const humanLoopInterrupt = useMemo(() => {
  const value = interrupt?.value as any;
  if (!value?.type) return null;
  if (['guidance', 'credentials', 'confirmation'].includes(value.type)) {
    return value;
  }
  return null;
}, [interrupt]);
```

3. Render component (after ErrorBanner, before input form div):
```typescript
{humanLoopInterrupt && (
  <div className="mx-auto w-[calc(100%-32px)] max-w-[1024px] mb-4">
    <HumanLoopInterrupt
      type={humanLoopInterrupt.type}
      data={humanLoopInterrupt}
      onRespond={resumeInterrupt}
    />
  </div>
)}
```

## Visual Placement

```
┌─────────────────────────────┐
│     Chat messages           │
│                             │
├─────────────────────────────┤
│  [Error Banner if any]      │
│  [HumanLoopInterrupt if any]│  ← NEW
├─────────────────────────────┤
│  [Tasks/Files bar]          │
│  [Input form]               │
└─────────────────────────────┘
```

## Files to Create/Modify

1. `deep-agents-ui/src/app/components/HumanLoopInterrupt.tsx` - New component (create)
2. `deep-agents-ui/src/app/components/ChatInterface.tsx` - Add detection and rendering (modify)

## Testing

1. Trigger `request_human_guidance` from agent - verify guidance form appears
2. Submit guidance - verify agent receives response and continues
3. Trigger `request_credentials` - verify credentials form appears
4. Submit credentials - verify agent receives them (check securely, don't log)
5. Trigger `request_confirmation` - verify approve/reject buttons appear
6. Click approve/reject - verify agent receives decision
