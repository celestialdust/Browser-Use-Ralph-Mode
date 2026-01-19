"use client";

import React, { useState } from "react";
import { AlertCircle, AlertTriangle, Info, X, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

export type ErrorType = "warning" | "error" | "info";

interface ErrorBannerProps {
  type: ErrorType;
  message: string;
  details?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

const typeConfig = {
  warning: {
    bgColor: "bg-yellow-50 dark:bg-yellow-950",
    borderColor: "border-yellow-200 dark:border-yellow-800",
    textColor: "text-yellow-800 dark:text-yellow-200",
    iconColor: "text-yellow-500 dark:text-yellow-400",
    icon: AlertTriangle,
  },
  error: {
    bgColor: "bg-red-50 dark:bg-red-950",
    borderColor: "border-red-200 dark:border-red-800",
    textColor: "text-red-800 dark:text-red-200",
    iconColor: "text-red-500 dark:text-red-400",
    icon: AlertCircle,
  },
  info: {
    bgColor: "bg-blue-50 dark:bg-blue-950",
    borderColor: "border-blue-200 dark:border-blue-800",
    textColor: "text-blue-800 dark:text-blue-200",
    iconColor: "text-blue-500 dark:text-blue-400",
    icon: Info,
  },
};

export function ErrorBanner({
  type,
  message,
  details,
  onRetry,
  onDismiss,
  className,
}: ErrorBannerProps) {
  const [showDetails, setShowDetails] = useState(false);
  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "p-3 border rounded-lg",
        config.bgColor,
        config.borderColor,
        config.textColor,
        className
      )}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <Icon className={cn("w-5 h-5 flex-shrink-0 mt-0.5", config.iconColor)} />

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{message}</p>

          {details && showDetails && (
            <pre className="mt-2 text-xs whitespace-pre-wrap break-all opacity-75 font-mono bg-black/5 dark:bg-white/5 p-2 rounded">
              {details}
            </pre>
          )}
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          {details && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-1.5 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
              aria-label={showDetails ? "Hide details" : "View details"}
              title={showDetails ? "Hide details" : "View details"}
            >
              {showDetails ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          )}

          {onRetry && (
            <button
              onClick={onRetry}
              className="p-1.5 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
              aria-label="Retry"
              title="Retry"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}

          {onDismiss && (
            <button
              onClick={onDismiss}
              className="p-1.5 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
              aria-label="Dismiss"
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
