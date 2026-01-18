"use client";

import { useCallback, useState, useEffect } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import {
  type Message,
  type Assistant,
  type Checkpoint,
} from "@langchain/langgraph-sdk";
import { v4 as uuidv4 } from "uuid";
import type { UseStreamThread } from "@langchain/langgraph-sdk/react";
import type { TodoItem, BrowserSession, BrowserCommand, ThoughtProcess } from "@/app/types/types";
import { useClient } from "@/providers/ClientProvider";
import { useQueryState } from "nuqs";

export type StateType = {
  messages: Message[];
  todos: TodoItem[];
  files: Record<string, string>;
  email?: {
    id?: string;
    subject?: string;
    page_content?: string;
  };
  ui?: any;
  browser_session?: BrowserSession | null;
  approval_queue?: BrowserCommand[];
  current_thought?: ThoughtProcess | null;
};

export function useChat({
  activeAssistant,
  onHistoryRevalidate,
  thread,
  recursionLimit = 200,
  browserStreamPort = 9223,
}: {
  activeAssistant: Assistant | null;
  onHistoryRevalidate?: () => void;
  thread?: UseStreamThread<StateType>;
  recursionLimit?: number;
  browserStreamPort?: number;
}) {
  const [threadId, setThreadId] = useQueryState("threadId");
  const client = useClient();
  const [browserSession, setBrowserSession] = useState<BrowserSession | null>(null);

  const stream = useStream<StateType>({
    assistantId: activeAssistant?.assistant_id || "",
    client: client ?? undefined,
    reconnectOnMount: true,
    threadId: threadId ?? null,
    onThreadId: setThreadId,
    defaultHeaders: { "x-auth-scheme": "langsmith" },
    // Enable fetching state history when switching to existing threads
    fetchStateHistory: true,
    // Revalidate thread list when stream finishes, errors, or creates new thread
    onFinish: onHistoryRevalidate,
    onError: onHistoryRevalidate,
    onCreated: onHistoryRevalidate,
    experimental_thread: thread,
  });

  // Detect browser tool calls and manage browser session state
  useEffect(() => {
    // Prioritize backend-provided browser_session
    if (stream.values.browser_session) {
      setBrowserSession(stream.values.browser_session);
      return;
    }
    
    // Fallback: Check if any recent messages contain browser tool calls
    const messages = stream.messages || [];
    const lastAiMessage = [...messages].reverse().find((m) => m.type === "ai");
    
    if (lastAiMessage) {
      let toolCalls: any[] = [];
      
      if (Array.isArray(lastAiMessage.tool_calls)) {
        toolCalls = lastAiMessage.tool_calls;
      } else if (Array.isArray(lastAiMessage.additional_kwargs?.tool_calls)) {
        toolCalls = lastAiMessage.additional_kwargs.tool_calls;
      } else if (Array.isArray(lastAiMessage.content)) {
        toolCalls = lastAiMessage.content.filter((b: any) => b.type === "tool_use");
      }
      
      const hasBrowserNavigate = toolCalls.some((tc: any) => {
        const name = tc.name || tc.function?.name || tc.type;
        return name === "browser_navigate";
      });
      
      const hasBrowserClose = toolCalls.some((tc: any) => {
        const name = tc.name || tc.function?.name || tc.type;
        return name === "browser_close";
      });
      
      if (hasBrowserNavigate && threadId) {
        // Extract actual stream URL from browser_navigate tool result
        let streamUrl = `ws://localhost:${browserStreamPort}`; // Default fallback
        
        // Look for the MOST RECENT browser_navigate tool result message
        // Use reverse to find the last occurrence, not the first
        const navigateResult = [...messages].reverse().find((m: any) => 
          m.type === "tool" && 
          m.name === "browser_navigate"
        );
        
        if (navigateResult && typeof navigateResult.content === 'string') {
          const urlMatch = navigateResult.content.match(/Browser stream available at (ws:\/\/[^\s]+)/);
          if (urlMatch && urlMatch[1]) {
            streamUrl = urlMatch[1];
            console.log("[Browser Session] Extracted stream URL from most recent browser_navigate:", streamUrl);
          }
        }
        
        // Browser session started with extracted or fallback URL
        // Always update to ensure we're using the latest stream URL
        setBrowserSession((prev) => {
          if (prev && prev.streamUrl !== streamUrl) {
            console.log("[Browser Session] Stream URL changed:", prev.streamUrl, "->", streamUrl);
          }
          return {
            sessionId: threadId,
            streamUrl: streamUrl,
            isActive: true,
          };
        });
      } else if (hasBrowserClose) {
        // Browser session closed
        setBrowserSession((prev) => prev ? { ...prev, isActive: false } : null);
      }
    }
  }, [stream.messages, stream.values.browser_session, threadId, browserStreamPort]);

  const sendMessage = useCallback(
    (content: string) => {
      const newMessage: Message = { id: uuidv4(), type: "human", content };
      stream.submit(
        { messages: [newMessage] },
        {
          optimisticValues: (prev) => ({
            messages: [...(prev.messages ?? []), newMessage],
          }),
          config: { ...(activeAssistant?.config ?? {}), recursion_limit: recursionLimit },
        }
      );
      // Update thread list immediately when sending a message
      onHistoryRevalidate?.();
    },
    [stream, activeAssistant?.config, onHistoryRevalidate, recursionLimit]
  );

  const runSingleStep = useCallback(
    (
      messages: Message[],
      checkpoint?: Checkpoint,
      isRerunningSubagent?: boolean,
      optimisticMessages?: Message[]
    ) => {
      if (checkpoint) {
        stream.submit(undefined, {
          ...(optimisticMessages
            ? { optimisticValues: { messages: optimisticMessages } }
            : {}),
          config: activeAssistant?.config,
          checkpoint: checkpoint,
          ...(isRerunningSubagent
            ? { interruptAfter: ["tools"] }
            : { interruptBefore: ["tools"] }),
        });
      } else {
        stream.submit(
          { messages },
          { config: activeAssistant?.config, interruptBefore: ["tools"] }
        );
      }
    },
    [stream, activeAssistant?.config]
  );

  const setFiles = useCallback(
    async (files: Record<string, string>) => {
      if (!threadId) return;
      // TODO: missing a way how to revalidate the internal state
      // I think we do want to have the ability to externally manage the state
      await client.threads.updateState(threadId, { values: { files } });
    },
    [client, threadId]
  );

  const continueStream = useCallback(
    (hasTaskToolCall?: boolean) => {
      stream.submit(undefined, {
        config: {
          ...(activeAssistant?.config || {}),
          recursion_limit: recursionLimit,
        },
        ...(hasTaskToolCall
          ? { interruptAfter: ["tools"] }
          : { interruptBefore: ["tools"] }),
      });
      // Update thread list when continuing stream
      onHistoryRevalidate?.();
    },
    [stream, activeAssistant?.config, onHistoryRevalidate, recursionLimit]
  );

  const markCurrentThreadAsResolved = useCallback(() => {
    stream.submit(null, { command: { goto: "__end__", update: null } });
    // Update thread list when marking thread as resolved
    onHistoryRevalidate?.();
  }, [stream, onHistoryRevalidate]);

  const resumeInterrupt = useCallback(
    (value: any) => {
      stream.submit(null, { command: { resume: value } });
      // Update thread list when resuming from interrupt
      onHistoryRevalidate?.();
    },
    [stream, onHistoryRevalidate]
  );

  const stopStream = useCallback(() => {
    stream.stop();
  }, [stream]);

  return {
    stream,
    todos: stream.values.todos ?? [],
    files: stream.values.files ?? {},
    email: stream.values.email,
    ui: stream.values.ui,
    browserSession: browserSession ?? stream.values.browser_session ?? null,
    approvalQueue: stream.values.approval_queue ?? [],
    currentThought: stream.values.current_thought ?? null,
    setFiles,
    messages: stream.messages,
    isLoading: stream.isLoading,
    isThreadLoading: stream.isThreadLoading,
    interrupt: stream.interrupt,
    getMessagesMetadata: stream.getMessagesMetadata,
    sendMessage,
    runSingleStep,
    continueStream,
    stopStream,
    markCurrentThreadAsResolved,
    resumeInterrupt,
  };
}
