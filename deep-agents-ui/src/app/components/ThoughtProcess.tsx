"use client";

import React, { useState, useEffect, useCallback } from "react";
import { ChevronDown, ChevronUp, Brain } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ThoughtStep } from "@/app/types/types";

interface ThoughtProcessProps {
  content: string;
  isStreaming?: boolean;
  isExpanded?: boolean;
  steps?: ThoughtStep[];
}

function BlinkingCursor() {
  return (
    <span className="inline-block w-1.5 h-4 bg-gray-600 dark:bg-gray-400 ml-0.5 animate-pulse" />
  );
}

function streamText(
  text: string,
  setter: (value: string) => void,
  onComplete?: () => void
) {
  let index = 0;
  const interval = setInterval(() => {
    if (index < text.length) {
      setter(text.slice(0, index + 1));
      index++;
    } else {
      clearInterval(interval);
      onComplete?.();
    }
  }, 10); // 10ms per character for smooth streaming

  return () => clearInterval(interval);
}

// Generate a concise summary from the thought content
function generateSummary(content: string, maxLength: number = 70): string {
  if (!content || content.trim() === "") {
    return "Agent is thinking...";
  }

  // Clean up the content
  const cleaned = content.trim();
  
  // Try to extract the first sentence
  const sentenceMatch = cleaned.match(/^[^.!?]+[.!?]/);
  if (sentenceMatch) {
    const firstSentence = sentenceMatch[0].trim();
    if (firstSentence.length <= maxLength) {
      return firstSentence;
    }
    return firstSentence.slice(0, maxLength - 3) + "...";
  }
  
  // If no sentence ending, take first line or truncate
  const firstLine = cleaned.split("\n")[0];
  if (firstLine.length <= maxLength) {
    return firstLine + "...";
  }
  
  return firstLine.slice(0, maxLength - 3) + "...";
}

// Parse content into steps if it contains numbered lists or bullet points
function parseSteps(content: string): ThoughtStep[] {
  const lines = content.split("\n");
  const steps: ThoughtStep[] = [];
  let currentStep: ThoughtStep | null = null;

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    
    // Match numbered lists (1., 2., etc.)
    const numberedMatch = trimmed.match(/^(\d+)\.\s+(.+)$/);
    if (numberedMatch) {
      currentStep = {
        id: `step-${index}`,
        content: numberedMatch[2],
        level: 0,
        status: "complete",
      };
      steps.push(currentStep);
      return;
    }

    // Match bullet points with different indentation levels
    const bulletMatch = trimmed.match(/^([•\-*])\s+(.+)$/);
    if (bulletMatch) {
      const indent = line.indexOf(bulletMatch[0]);
      const level = Math.floor(indent / 2);
      
      const step: ThoughtStep = {
        id: `step-${index}`,
        content: bulletMatch[2],
        level,
        status: "complete",
      };

      if (level === 0) {
        steps.push(step);
        currentStep = step;
      } else if (currentStep) {
        if (!currentStep.children) {
          currentStep.children = [];
        }
        currentStep.children.push(step);
      }
      return;
    }

    // Match sub-steps with indentation (└─, ├─)
    const subStepMatch = trimmed.match(/^[└├]─\s+(.+)$/);
    if (subStepMatch && currentStep) {
      if (!currentStep.children) {
        currentStep.children = [];
      }
      currentStep.children.push({
        id: `substep-${index}`,
        content: subStepMatch[1],
        level: 1,
        status: "complete",
      });
      return;
    }

    // Regular line - add to current step or create new
    if (trimmed && currentStep) {
      currentStep.content += " " + trimmed;
    } else if (trimmed) {
      steps.push({
        id: `step-${index}`,
        content: trimmed,
        level: 0,
        status: "complete",
      });
    }
  });

  return steps;
}

function ThoughtStepItem({ step, isStreaming }: { step: ThoughtStep; isStreaming: boolean }) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = step.children && step.children.length > 0;
  const indent = step.level * 24;

  const toggleExpanded = useCallback(() => {
    setExpanded((prev) => !prev);
  }, []);

  return (
    <div style={{ marginLeft: `${indent}px` }}>
      <div className="flex items-start gap-2 py-1">
        {hasChildren && (
          <button
            onClick={toggleExpanded}
            className="flex-shrink-0 mt-0.5 hover:opacity-70 transition-opacity"
            aria-label={expanded ? "Collapse" : "Expand"}
          >
            {expanded ? (
              <ChevronDown className="w-3 h-3 text-muted-foreground" />
            ) : (
              <ChevronUp className="w-3 h-3 text-muted-foreground" />
            )}
          </button>
        )}
        <div className={cn("flex-1", step.level > 0 && "border-l-2 border-border pl-3")}>
          <span className="text-sm text-muted-foreground prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{step.content}</ReactMarkdown>
            {isStreaming && step.status === "streaming" && <BlinkingCursor />}
          </span>
        </div>
      </div>
      {hasChildren && expanded && (
        <div className="mt-1">
          {step.children!.map((child) => (
            <ThoughtStepItem key={child.id} step={child} isStreaming={isStreaming} />
          ))}
        </div>
      )}
    </div>
  );
}

export function ThoughtProcess({
  content,
  isStreaming = false,
  isExpanded = true,
  steps,
}: ThoughtProcessProps) {
  const [expanded, setExpanded] = useState(isExpanded);
  const [displayedContent, setDisplayedContent] = useState("");
  const [streamComplete, setStreamComplete] = useState(!isStreaming);
  const [parsedSteps, setParsedSteps] = useState<ThoughtStep[]>([]);
  const [summary, setSummary] = useState<string>("");

  useEffect(() => {
    if (isStreaming && content) {
      const cleanup = streamText(content, (text) => {
        setDisplayedContent(text);
        // Re-parse steps as content streams in
        const newSteps = parseSteps(text);
        setParsedSteps(newSteps);
        // Update summary as content streams
        setSummary(generateSummary(text));
      }, () => {
        setStreamComplete(true);
      });
      return cleanup;
    } else {
      setDisplayedContent(content);
      setStreamComplete(true);
      setSummary(generateSummary(content));
      // Parse final content into steps
      if (steps) {
        setParsedSteps(steps);
      } else {
        const newSteps = parseSteps(content);
        setParsedSteps(newSteps);
      }
    }
  }, [content, isStreaming, steps]);

  const toggleExpanded = useCallback(() => {
    setExpanded((prev) => !prev);
  }, []);

  if (!content) {
    return null;
  }

  const useWaterfallDisplay = parsedSteps.length > 0;
  const hasContent = content && content.trim() !== "";

  return (
    <div
      className={cn(
        "w-full overflow-hidden rounded-lg border-none shadow-none outline-none transition-colors duration-200 hover:bg-accent",
        expanded && hasContent && "bg-accent"
      )}
    >
      <Button
        variant="ghost"
        size="sm"
        onClick={toggleExpanded}
        className={cn(
          "flex w-full items-center justify-between gap-2 border-none px-2 py-2 text-left shadow-none outline-none focus-visible:ring-0 focus-visible:ring-offset-0",
          "cursor-pointer"
        )}
        disabled={false}
      >
        <div className="flex w-full items-center gap-2 min-w-0">
          <div className="flex items-center gap-2 flex-shrink-0">
            <Brain size={14} className="text-muted-foreground" />
            <span className="text-[15px] font-medium tracking-[-0.6px] text-foreground">
              Thought process
            </span>
          </div>
          {!expanded && summary && (
            <span className="text-sm text-muted-foreground truncate flex-1 min-w-0">
              {summary}
            </span>
          )}
          <div className="flex-shrink-0 ml-auto">
            {expanded ? (
              <ChevronUp size={14} className="text-muted-foreground" />
            ) : (
              <ChevronDown size={14} className="text-muted-foreground" />
            )}
          </div>
        </div>
      </Button>

      {expanded && hasContent && (
        <div className="px-4 pb-4">
          {useWaterfallDisplay ? (
            <div className="space-y-1">
              {parsedSteps.map((step) => (
                <ThoughtStepItem key={step.id} step={step} isStreaming={isStreaming && !streamComplete} />
              ))}
            </div>
          ) : (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{displayedContent}</ReactMarkdown>
              {isStreaming && !streamComplete && <BlinkingCursor />}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
