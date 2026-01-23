"use client";

import React from "react";
import { Bot, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import type { SubagentStatus } from "@/app/types/types";
import { cn } from "@/lib/utils";

interface SubagentStatusCardProps {
  subagent: SubagentStatus;
  className?: string;
}

/**
 * SubagentStatusCard displays the status of a running or completed subagent.
 * Used for polling-based subagent visibility in the chat interface.
 *
 * Features:
 * - Shows subagent type and current status with appropriate icon
 * - Displays the prompt given to the subagent
 * - Shows last activity when running
 * - Shows tool call count
 * - Shows result summary when completed
 * - Shows error message if failed
 * - Uses border-left indentation to show hierarchy
 */
export const SubagentStatusCard: React.FC<SubagentStatusCardProps> = ({
  subagent,
  className,
}) => {
  const statusConfig = {
    pending: {
      icon: Clock,
      color: "text-muted-foreground",
      label: "Pending",
      spin: false,
    },
    running: {
      icon: Loader2,
      color: "text-blue-500",
      label: "Running",
      spin: true,
    },
    completed: {
      icon: CheckCircle,
      color: "text-green-500",
      label: "Completed",
      spin: false,
    },
    error: {
      icon: XCircle,
      color: "text-red-500",
      label: "Error",
      spin: false,
    },
    cancelled: {
      icon: XCircle,
      color: "text-orange-500",
      label: "Cancelled",
      spin: false,
    },
  };

  const config = statusConfig[subagent.status];
  const StatusIcon = config.icon;

  // Format the subagent type for display (e.g., "research" -> "Research")
  const formattedType = subagent.subagent_type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  return (
    <div
      className={cn(
        "border-l-2 border-blue-200 dark:border-blue-800 ml-4 pl-4 py-2 transition-all duration-200",
        subagent.status === "running" && "border-blue-400 dark:border-blue-600",
        subagent.status === "completed" && "border-green-300 dark:border-green-700",
        subagent.status === "error" && "border-red-300 dark:border-red-700",
        className
      )}
    >
      {/* Header row with type and status */}
      <div className="flex items-center gap-2 mb-1">
        <Bot size={14} className="text-blue-500 flex-shrink-0" />
        <span className="font-medium text-sm text-foreground">
          {formattedType}
        </span>
        <StatusIcon
          size={14}
          className={cn(config.color, config.spin && "animate-spin", "flex-shrink-0")}
        />
        <span className="text-xs text-muted-foreground">{config.label}</span>
      </div>

      {/* Prompt - truncated to show context */}
      <p className="text-xs text-muted-foreground truncate max-w-md mb-1">
        {subagent.prompt}
      </p>

      {/* Last activity (shown when running) */}
      {subagent.last_activity && subagent.status === "running" && (
        <p className="text-xs text-blue-500 dark:text-blue-400 mt-1 italic">
          {subagent.last_activity}
        </p>
      )}

      {/* Tool calls count */}
      {subagent.tool_calls_count > 0 && (
        <p className="text-xs text-muted-foreground mt-1">
          {subagent.tool_calls_count} tool call{subagent.tool_calls_count !== 1 ? "s" : ""}
        </p>
      )}

      {/* Result summary (shown when completed) */}
      {subagent.result_summary && subagent.status === "completed" && (
        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
          {subagent.result_summary}
        </p>
      )}

      {/* Error message (shown when error) */}
      {subagent.error && subagent.status === "error" && (
        <p className="text-xs text-red-500 dark:text-red-400 mt-1">
          Error: {subagent.error}
        </p>
      )}
    </div>
  );
};

SubagentStatusCard.displayName = "SubagentStatusCard";
