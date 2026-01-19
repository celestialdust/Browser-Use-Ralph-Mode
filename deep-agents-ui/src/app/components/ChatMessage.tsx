"use client";

import React, { useMemo, useState, useCallback } from "react";
import { SubAgentIndicator } from "@/app/components/SubAgentIndicator";
import { ToolCallBox } from "@/app/components/ToolCallBox";
import { MarkdownContent } from "@/app/components/MarkdownContent";
import { ThoughtProcess } from "@/app/components/ThoughtProcess";
import { ReasoningDisplay } from "@/app/components/ReasoningDisplay";
import type {
  SubAgent,
  ToolCall,
  ActionRequest,
  ReviewConfig,
  ThoughtProcess as ThoughtProcessType,
} from "@/app/types/types";
import { Message } from "@langchain/langgraph-sdk";
import {
  extractSubAgentContent,
  extractStringFromMessageContent,
} from "@/app/utils/utils";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: Message;
  toolCalls: ToolCall[];
  isLoading?: boolean;
  actionRequestsMap?: Map<string, ActionRequest>;
  reviewConfigsMap?: Map<string, ReviewConfig>;
  ui?: any[];
  stream?: any;
  onResumeInterrupt?: (value: any) => void;
  graphId?: string;
  currentThought?: ThoughtProcessType | null;
}

/**
 * Content block types from OpenAI's Responses API.
 * The message.content can be an array of these blocks.
 */
interface ReasoningContentBlock {
  type: "reasoning";
  id?: string;
  summary?: Array<{ text: string; type: "summary_text" }>;
  encrypted_content?: string;
}

interface TextContentBlock {
  type: "text";
  text: string;
  id?: string;
  index?: number;
}

type ContentBlock = ReasoningContentBlock | TextContentBlock | string;

export const ChatMessage = React.memo<ChatMessageProps>(
  ({
    message,
    toolCalls,
    isLoading,
    actionRequestsMap,
    reviewConfigsMap,
    ui,
    stream,
    onResumeInterrupt,
    graphId,
    currentThought,
  }) => {
    const isUser = message.type === "human";
    const messageContent = extractStringFromMessageContent(message);
    const hasContent = messageContent && messageContent.trim() !== "";
    const hasToolCalls = toolCalls.length > 0;

    /**
     * Extract reasoning summaries from message content blocks.
     *
     * When using OpenAI's Responses API with reasoning enabled, the message.content
     * is an array of content blocks. The first block is typically a "reasoning" block
     * with an encrypted reasoning field and an optional summary array.
     *
     * Example content structure:
     * [
     *   {
     *     "type": "reasoning",
     *     "id": "rs_...",
     *     "summary": [
     *       { "text": "**Step 1**\n\nThinking about...", "type": "summary_text" },
     *       { "text": "**Step 2**\n\nConsidering...", "type": "summary_text" }
     *     ]
     *   },
     *   {
     *     "type": "text",
     *     "text": "The actual response content...",
     *     "id": "msg_..."
     *   }
     * ]
     */
    const reasoningSummaries = useMemo(() => {
      const content = message.content;

      // If content is an array, look for reasoning blocks
      if (Array.isArray(content)) {
        for (const block of content as ContentBlock[]) {
          if (
            typeof block === "object" &&
            block !== null &&
            "type" in block &&
            block.type === "reasoning"
          ) {
            const reasoningBlock = block as ReasoningContentBlock;
            if (reasoningBlock.summary && reasoningBlock.summary.length > 0) {
              return reasoningBlock.summary;
            }
          }
        }
      }

      return null;
    }, [message.content]);

    const subAgents = useMemo(() => {
      return toolCalls
        .filter((toolCall: ToolCall) => {
          return (
            toolCall.name === "task" &&
            toolCall.args["subagent_type"] &&
            toolCall.args["subagent_type"] !== "" &&
            toolCall.args["subagent_type"] !== null
          );
        })
        .map((toolCall: ToolCall) => {
          const subagentType = (toolCall.args as Record<string, unknown>)[
            "subagent_type"
          ] as string;
          return {
            id: toolCall.id,
            name: toolCall.name,
            subAgentName: subagentType,
            input: toolCall.args,
            output: toolCall.result ? { result: toolCall.result } : undefined,
            status: toolCall.status,
          } as SubAgent;
        });
    }, [toolCalls]);

    const [expandedSubAgents, setExpandedSubAgents] = useState<
      Record<string, boolean>
    >({});
    const isSubAgentExpanded = useCallback(
      (id: string) => expandedSubAgents[id] ?? true,
      [expandedSubAgents]
    );
    const toggleSubAgent = useCallback((id: string) => {
      setExpandedSubAgents((prev) => ({
        ...prev,
        [id]: prev[id] === undefined ? false : !prev[id],
      }));
    }, []);

    return (
      <div
        className={cn(
          "flex w-full max-w-full overflow-x-hidden message-enter",
          isUser && "flex-row-reverse"
        )}
      >
        <div
          className={cn(
            "min-w-0 max-w-full",
            isUser ? "max-w-[70%]" : "w-full"
          )}
        >
          {/* Thought Process for assistant messages */}
          {!isUser && currentThought && currentThought.content && (
            <ThoughtProcess
              content={currentThought.content}
              isStreaming={!currentThought.isComplete}
              isExpanded={true}
            />
          )}

          {/* Reasoning Summary Display for assistant messages */}
          {!isUser && reasoningSummaries && reasoningSummaries.length > 0 && (
            <ReasoningDisplay summaries={reasoningSummaries} />
          )}

          {hasContent && (
            <div className={cn("relative flex items-end gap-0")}>
              <div
                className={cn(
                  "mt-4 overflow-hidden break-words text-sm font-normal",
                  isUser
                    ? "rounded-xl rounded-br-none border border-border px-3 py-2 text-foreground leading-[150%]"
                    : "text-primary rounded-lg bg-gray-50 dark:bg-gray-800 px-6 py-4 leading-[175%]"
                )}
                style={
                  isUser
                    ? { backgroundColor: "var(--color-user-message-bg)" }
                    : undefined
                }
              >
                {isUser ? (
                  <p className="m-0 whitespace-pre-wrap break-words text-sm leading-relaxed">
                    {messageContent}
                  </p>
                ) : hasContent ? (
                  <MarkdownContent content={messageContent} />
                ) : null}
              </div>
            </div>
          )}
          {hasToolCalls && (
            <div className="mt-4 flex w-full flex-col">
              {toolCalls.map((toolCall: ToolCall) => {
                if (toolCall.name === "task") return null;
                const toolCallGenUiComponent = ui?.find(
                  (u) => u.metadata?.tool_call_id === toolCall.id
                );
                const actionRequest = actionRequestsMap?.get(toolCall.name);
                const reviewConfig = reviewConfigsMap?.get(toolCall.name);
                return (
                  <ToolCallBox
                    key={toolCall.id}
                    toolCall={toolCall}
                    uiComponent={toolCallGenUiComponent}
                    stream={stream}
                    graphId={graphId}
                    actionRequest={actionRequest}
                    reviewConfig={reviewConfig}
                    onResume={onResumeInterrupt}
                    isLoading={isLoading}
                  />
                );
              })}
            </div>
          )}

          {!isUser && subAgents.length > 0 && (
            <div className="flex w-fit max-w-full flex-col gap-4">
              {subAgents.map((subAgent) => (
                <div key={subAgent.id} className="flex w-full flex-col gap-2">
                  <div className="flex items-end gap-2">
                    <div className="w-[calc(100%-100px)]">
                      <SubAgentIndicator
                        subAgent={subAgent}
                        onClick={() => toggleSubAgent(subAgent.id)}
                        isExpanded={isSubAgentExpanded(subAgent.id)}
                      />
                    </div>
                  </div>
                  {isSubAgentExpanded(subAgent.id) && (
                    <div className="w-full max-w-full">
                      <div className="bg-surface border-border-light rounded-md border p-4">
                        <h4 className="text-primary/70 mb-2 text-xs font-semibold uppercase tracking-wider">
                          Input
                        </h4>
                        <div className="mb-4">
                          <MarkdownContent
                            content={extractSubAgentContent(subAgent.input)}
                          />
                        </div>
                        {subAgent.output && (
                          <>
                            <h4 className="text-primary/70 mb-2 text-xs font-semibold uppercase tracking-wider">
                              Output
                            </h4>
                            <MarkdownContent
                              content={extractSubAgentContent(subAgent.output)}
                            />
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }
);

ChatMessage.displayName = "ChatMessage";
