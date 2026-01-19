"use client";

import { useCallback, useState, useEffect, useRef, useMemo } from "react";
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
import { RECURSION_LIMIT } from "@/lib/config";

// Error types for user-friendly messages
export type ErrorType = "warning" | "error" | "info";

export interface ChatError {
  type: ErrorType;
  message: string;
  details?: string;
  retryable: boolean;
}

// Helper to parse and categorize errors
function parseError(error: Error | string): ChatError {
  const errorMessage = typeof error === "string" ? error : error.message || String(error);

  // Recursion limit errors
  if (errorMessage.includes("recursion") || errorMessage.includes("limit") || errorMessage.includes("maximum") || errorMessage.includes("exceeded")) {
    return {
      type: "warning",
      message: "Agent reached maximum iterations. You can retry or provide more guidance.",
      details: errorMessage,
      retryable: true,
    };
  }

  // Authentication errors
  if (errorMessage.includes("401") || errorMessage.includes("unauthorized") || errorMessage.includes("authentication")) {
    return {
      type: "error",
      message: "Authentication failed. Please check your API key.",
      details: errorMessage,
      retryable: false,
    };
  }

  // Server errors
  if (errorMessage.includes("500") || errorMessage.includes("internal server")) {
    return {
      type: "error",
      message: "Server error occurred. Please try again.",
      details: errorMessage,
      retryable: true,
    };
  }

  // Service unavailable (transient)
  if (errorMessage.includes("503") || errorMessage.includes("service unavailable")) {
    return {
      type: "warning",
      message: "Service temporarily unavailable. Retrying...",
      details: errorMessage,
      retryable: true,
    };
  }

  // Network/timeout errors
  if (errorMessage.includes("timeout") || errorMessage.includes("network") || errorMessage.includes("ECONNREFUSED") || errorMessage.includes("fetch")) {
    return {
      type: "error",
      message: "Connection error. Please check your network and try again.",
      details: errorMessage,
      retryable: true,
    };
  }

  // Default error
  return {
    type: "error",
    message: errorMessage || "An unexpected error occurred.",
    details: errorMessage,
    retryable: true,
  };
}

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
  recursionLimit = RECURSION_LIMIT,
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
  const [chatError, setChatError] = useState<ChatError | null>(null);
  const retryCountRef = useRef(0);
  const lastInputRef = useRef<string | null>(null);

  // Error handler - stops stream and displays error to user
  const handleStreamError = useCallback((error: unknown) => {
    console.error("[useChat] Stream error:", error);

    // Convert unknown to Error or string for parseError
    const errorValue = error instanceof Error ? error : String(error);
    const parsedError = parseError(errorValue);
    setChatError(parsedError);

    // Don't auto-retry here - let user manually retry via ErrorBanner
    // This avoids circular dependency issues and gives user control
    retryCountRef.current = 0;

    onHistoryRevalidate?.();
  }, [onHistoryRevalidate]);

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
    onFinish: () => {
      retryCountRef.current = 0; // Reset retry count on successful finish
      onHistoryRevalidate?.();
    },
    onError: handleStreamError,
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

  // ChatContent can be a string or an array of content blocks (for multimodal messages with images)
  type ChatContent = string | Array<{ type: string; text?: string; image_url?: { url: string } }>;

  const sendMessage = useCallback(
    (content: ChatContent) => {
      // Clear any previous errors
      setChatError(null);
      retryCountRef.current = 0;
      lastInputRef.current = typeof content === "string" ? content : JSON.stringify(content);

      // Cast to any to allow multimodal content - the SDK handles various content types
      const newMessage: Message = { id: uuidv4(), type: "human", content: content as any };
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

  const clearError = useCallback(() => {
    setChatError(null);
    retryCountRef.current = 0;
  }, []);

  const retryLastMessage = useCallback(() => {
    if (lastInputRef.current) {
      setChatError(null);
      retryCountRef.current = 0;
      sendMessage(lastInputRef.current);
    }
  }, [sendMessage]);

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

  // Memoize fallback values to prevent creating new objects on each render
  // which could cause infinite re-renders in dependent components
  const emptyTodos: TodoItem[] = useMemo(() => [], []);
  const emptyFiles: Record<string, string> = useMemo(() => ({}), []);
  const emptyApprovalQueue: BrowserCommand[] = useMemo(() => [], []);

  const todos = stream.values.todos ?? emptyTodos;
  const files = stream.values.files ?? emptyFiles;
  const approvalQueue = stream.values.approval_queue ?? emptyApprovalQueue;
  const resolvedBrowserSession = browserSession ?? stream.values.browser_session ?? null;
  const currentThought = stream.values.current_thought ?? null;

  return {
    stream,
    todos,
    files,
    email: stream.values.email,
    ui: stream.values.ui,
    browserSession: resolvedBrowserSession,
    approvalQueue,
    currentThought,
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
    // Error handling
    chatError,
    clearError,
    retryLastMessage,
  };
}
