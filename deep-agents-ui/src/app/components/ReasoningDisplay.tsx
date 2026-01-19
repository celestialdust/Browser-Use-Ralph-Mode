"use client";

import React, { useState } from "react";
import { Sparkles } from "lucide-react";

interface ReasoningDisplayProps {
  reasoning: string;
  summary?: string;
}

export function ReasoningDisplay({ reasoning, summary }: ReasoningDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!reasoning) return null;

  return (
    <div className="reasoning-container bg-muted/50 border border-border rounded-lg p-4 my-2">
      <div
        className="flex items-center gap-2 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Sparkles className="w-4 h-4 text-primary" />
        <span className="text-sm font-medium">
          {isExpanded ? "Hide" : "Show"} thinking process
        </span>
      </div>

      {!isExpanded && summary && (
        <p className="text-xs text-muted-foreground italic mt-2">
          {summary}
        </p>
      )}

      {isExpanded && (
        <div className="mt-3 text-sm text-foreground/90 whitespace-pre-wrap animate-in fade-in-0">
          {reasoning}
        </div>
      )}
    </div>
  );
}
