"use client";

import React, { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { HelpCircle, KeyRound, AlertTriangle, Terminal, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface HumanLoopInterruptProps {
  type: "guidance" | "credentials" | "confirmation" | "bash_approval";
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
    command?: string;  // For bash_approval
  };
  subagentName?: string;
  onRespond: (response: any) => void;
}

export function HumanLoopInterrupt({ type, data, subagentName, onRespond }: HumanLoopInterruptProps) {
  const [response, setResponse] = useState("");
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [isExpanded, setIsExpanded] = useState(true);

  const toggleExpanded = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  const getTitle = () => {
    switch (type) {
      case "guidance":
        return subagentName ? `${subagentName} needs guidance` : "Agent needs guidance";
      case "credentials":
        return subagentName
          ? `${subagentName} needs credentials for ${data.service}`
          : `Credentials for ${data.service}`;
      case "confirmation":
        return subagentName ? `${subagentName} needs confirmation` : "Confirmation required";
      case "bash_approval":
        return subagentName ? `${subagentName} wants to run a command` : "Command approval";
      default:
        return "Input required";
    }
  };

  const getIcon = () => {
    switch (type) {
      case "guidance":
        return <HelpCircle size={14} className="text-muted-foreground" />;
      case "credentials":
        return <KeyRound size={14} className="text-muted-foreground" />;
      case "confirmation":
        return <AlertTriangle size={14} className="text-muted-foreground" />;
      case "bash_approval":
        return <Terminal size={14} className="text-muted-foreground" />;
      default:
        return <HelpCircle size={14} className="text-muted-foreground" />;
    }
  };

  const getSummary = () => {
    switch (type) {
      case "guidance":
        return data.question?.slice(0, 60) + (data.question && data.question.length > 60 ? "..." : "");
      case "credentials":
        return data.reason?.slice(0, 60) + (data.reason && data.reason.length > 60 ? "..." : "");
      case "confirmation":
        return data.action?.slice(0, 60) + (data.action && data.action.length > 60 ? "..." : "");
      case "bash_approval":
        return data.command?.slice(0, 60) + (data.command && data.command.length > 60 ? "..." : "");
      default:
        return "";
    }
  };

  return (
    <div
      className={cn(
        "w-full overflow-hidden rounded-lg border-none shadow-none outline-none transition-colors duration-200 hover:bg-accent",
        isExpanded && "bg-accent"
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
      >
        <div className="flex w-full items-center gap-2 min-w-0">
          <div className="flex items-center gap-2 flex-shrink-0">
            {getIcon()}
            <span className="text-[15px] font-medium tracking-[-0.6px] text-foreground">
              {getTitle()}
            </span>
          </div>
          {!isExpanded && (
            <span className="text-sm text-muted-foreground truncate flex-1 min-w-0">
              {getSummary()}
            </span>
          )}
          <div className="flex-shrink-0 ml-auto">
            {isExpanded ? (
              <ChevronUp size={14} className="text-muted-foreground" />
            ) : (
              <ChevronDown size={14} className="text-muted-foreground" />
            )}
          </div>
        </div>
      </Button>

      {isExpanded && (
        <div className="px-4 pb-4">
          {type === "guidance" && (
            <>
              <p className="text-sm text-foreground">{data.question}</p>
              {(data.context || data.attempted_approaches) && (
                <details className="mt-2 text-xs text-muted-foreground">
                  <summary className="cursor-pointer hover:underline">Show details</summary>
                  <div className="mt-1 pl-2 border-l-2 border-border">
                    {data.context && <p>{data.context}</p>}
                    {data.attempted_approaches && <p className="mt-1">Tried: {data.attempted_approaches}</p>}
                  </div>
                </details>
              )}
              <div className="mt-3 flex gap-2 items-end">
                <input
                  type="text"
                  value={response}
                  onChange={(e) => setResponse(e.target.value)}
                  placeholder="Your guidance..."
                  className="flex-1 p-2 border border-border rounded text-sm bg-background"
                  onKeyDown={(e) => e.key === "Enter" && response.trim() && onRespond(response)}
                />
                <Button
                  onClick={() => onRespond(response)}
                  disabled={!response.trim()}
                  size="sm"
                >
                  Send
                </Button>
              </div>
            </>
          )}

          {type === "credentials" && (
            <>
              {data.reason && (
                <p className="text-sm text-muted-foreground">{data.reason}</p>
              )}
              <div className="mt-3 flex flex-col gap-2">
                <input
                  type="text"
                  value={credentials.username}
                  onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                  placeholder="Username or email"
                  className="w-full p-2 border border-border rounded text-sm bg-background"
                />
                <input
                  type="password"
                  value={credentials.password}
                  onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                  placeholder="Password"
                  className="w-full p-2 border border-border rounded text-sm bg-background"
                />
                <Button
                  onClick={() => onRespond(credentials)}
                  disabled={!credentials.username || !credentials.password}
                  size="sm"
                  className="self-end"
                >
                  Submit
                </Button>
              </div>
            </>
          )}

          {type === "confirmation" && (
            <>
              <p className="text-sm text-foreground">{data.action}</p>
              {data.risks && (
                <p className="text-xs text-muted-foreground mt-1">
                  <span className="font-medium">Risks:</span> {data.risks}
                </p>
              )}
              <div className="flex gap-2 mt-3">
                <Button
                  onClick={() => onRespond("approved")}
                  size="sm"
                  variant="destructive"
                >
                  Approve
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRespond("rejected")}
                >
                  Reject
                </Button>
              </div>
            </>
          )}

          {type === "bash_approval" && (
            <>
              <pre className="bg-muted/40 text-foreground p-2 rounded mt-1 max-h-[200px] overflow-auto text-xs font-mono border border-border whitespace-pre-wrap break-all">
                $ {data.command}
              </pre>
              <div className="flex gap-2 mt-3">
                <Button
                  onClick={() => onRespond("approved")}
                  size="sm"
                >
                  Allow
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRespond("rejected")}
                >
                  Deny
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
