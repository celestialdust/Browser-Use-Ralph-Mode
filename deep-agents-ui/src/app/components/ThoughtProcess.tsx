"use client";

import React, { useState, useEffect } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

interface ThoughtProcessProps {
  content: string;
  isStreaming?: boolean;
  isExpanded?: boolean;
}

function BlinkingCursor() {
  return (
    <span className="inline-block w-1.5 h-4 bg-gray-600 ml-0.5 animate-pulse" />
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

export function ThoughtProcess({
  content,
  isStreaming = false,
  isExpanded = true,
}: ThoughtProcessProps) {
  const [expanded, setExpanded] = useState(isExpanded);
  const [displayedContent, setDisplayedContent] = useState("");
  const [streamComplete, setStreamComplete] = useState(!isStreaming);

  useEffect(() => {
    if (isStreaming && content) {
      const cleanup = streamText(content, setDisplayedContent, () => {
        setStreamComplete(true);
      });
      return cleanup;
    } else {
      setDisplayedContent(content);
      setStreamComplete(true);
    }
  }, [content, isStreaming]);

  if (!content) {
    return null;
  }

  return (
    <div className="thought-process">
      <div
        className="thought-header"
        onClick={() => setExpanded(!expanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setExpanded(!expanded);
          }
        }}
        aria-expanded={expanded}
        aria-controls="thought-content"
      >
        <span className="flex items-center gap-2">
          {expanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
          Thought process
        </span>
      </div>
      {expanded && (
        <div
          id="thought-content"
          className="thought-content"
          role="region"
          aria-label="Agent thought process"
        >
          <div className="whitespace-pre-wrap">
            {displayedContent}
            {isStreaming && !streamComplete && <BlinkingCursor />}
          </div>
        </div>
      )}
    </div>
  );
}
