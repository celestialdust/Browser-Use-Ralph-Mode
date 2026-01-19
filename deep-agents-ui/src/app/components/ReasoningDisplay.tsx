"use client";

import React, { useState } from "react";
import { Brain, ChevronDown, ChevronUp } from "lucide-react";
import ReactMarkdown from "react-markdown";

/**
 * Summary item from the reasoning API response.
 * Each summary block contains a text field with a step in the reasoning process.
 */
interface SummaryItem {
  text: string;
  type: "summary_text";
}

interface ReasoningDisplayProps {
  /**
   * Array of summary items from the reasoning content block.
   * Each item represents a step in the model's thinking process.
   */
  summaries: SummaryItem[];
}

/**
 * Displays the reasoning summary from GPT-5/o4-mini responses.
 *
 * The reasoning content from OpenAI's responses API is encrypted and not accessible,
 * but the summary is provided as an array of summary_text items that describe
 * the model's thinking process.
 *
 * This component displays the summaries in a collapsible format similar to
 * Claude's "thinking" display.
 */
export function ReasoningDisplay({ summaries }: ReasoningDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Don't render if no summaries
  if (!summaries || summaries.length === 0) return null;

  // Get the first summary for preview (when collapsed)
  const firstSummary = summaries[0]?.text || "";
  // Extract just the first line/heading for compact preview
  const previewText = firstSummary.split("\n")[0].replace(/^\*\*|\*\*$/g, "");

  return (
    <div className="reasoning-container bg-muted/50 border border-border rounded-lg p-4 my-2">
      <div
        className="flex items-center gap-2 cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Brain className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        <span className="text-sm font-medium flex-1">
          Thought process
        </span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        )}
      </div>

      {/* Preview when collapsed */}
      {!isExpanded && previewText && (
        <p className="text-xs text-muted-foreground italic mt-2 truncate">
          {previewText}
        </p>
      )}

      {/* Full content when expanded */}
      {isExpanded && (
        <div className="mt-3 space-y-3 animate-in fade-in-0 duration-200">
          {summaries.map((summary, index) => (
            <div
              key={index}
              className="text-sm text-foreground/90 border-l-2 border-primary/30 pl-3 prose prose-sm max-w-none dark:prose-invert"
            >
              <ReactMarkdown>{summary.text}</ReactMarkdown>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
