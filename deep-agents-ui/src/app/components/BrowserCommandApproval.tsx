"use client";

import React from "react";
import { Check, X, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { BrowserCommand } from "@/app/types/types";

interface BrowserCommandApprovalProps {
  commands: BrowserCommand[];
  onApprove: (commandId: string) => void;
  onReject: (commandId: string) => void;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export function BrowserCommandApproval({
  commands,
  onApprove,
  onReject,
  isOpen,
  onOpenChange,
}: BrowserCommandApprovalProps) {
  if (commands.length === 0) {
    return null;
  }

  const currentCommand = commands[0]; // Show first command in queue

  const formatArgs = (args: any): string => {
    if (typeof args === "object" && args !== null) {
      const { thread_id, ...relevantArgs } = args;
      return Object.entries(relevantArgs)
        .map(([key, value]) => {
          if (typeof value === "string") {
            return `${key}="${value}"`;
          }
          return `${key}=${JSON.stringify(value)}`;
        })
        .join(" ");
    }
    return "";
  };

  const getCommandDescription = (command: BrowserCommand): string => {
    const commandName = command.command.replace("browser_", "");
    const args = formatArgs(command.args);

    switch (command.command) {
      case "browser_click":
        return `Click on element ${command.args.ref || ""}`;
      case "browser_fill":
        return `Fill element ${command.args.ref || ""} with text`;
      case "browser_type":
        return `Type into element ${command.args.ref || ""}`;
      case "browser_navigate":
        return `Navigate to ${command.args.url || "a URL"}`;
      case "browser_press_key":
        return `Press ${command.args.key || "a key"}`;
      case "browser_eval":
        return "Execute JavaScript code";
      default:
        return `Execute ${commandName} ${args}`;
    }
  };

  const getCommandRisk = (command: BrowserCommand): string => {
    switch (command.command) {
      case "browser_click":
      case "browser_fill":
      case "browser_type":
        return "This action will interact with the web page.";
      case "browser_navigate":
        return "This will navigate to a new URL.";
      case "browser_eval":
        return "⚠️ This will execute arbitrary JavaScript code.";
      default:
        return "This action will modify the browser state.";
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Terminal className="w-5 h-5" />
            Browser Command Approval
          </DialogTitle>
          <DialogDescription>
            The agent wants to execute a browser command. Please review and
            approve or reject.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Action:
              </label>
              <p className="mt-1 text-base font-semibold text-gray-900 dark:text-gray-100">
                {getCommandDescription(currentCommand)}
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Command:
              </label>
              <div className="mt-1 rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-2 font-mono text-sm border border-gray-200 dark:border-gray-700">
                agent-browser {currentCommand.command.replace("browser_", "")}{" "}
                {formatArgs(currentCommand.args)}
              </div>
            </div>

            <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 px-3 py-2 text-sm text-blue-800 dark:text-blue-200">
              {getCommandRisk(currentCommand)}
            </div>

            {commands.length > 1 && (
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {commands.length - 1} more command
                {commands.length - 1 > 1 ? "s" : ""} waiting in queue
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              onReject(currentCommand.id);
              if (commands.length === 1) {
                onOpenChange(false);
              }
            }}
            className="flex items-center gap-2"
          >
            <X className="w-4 h-4" />
            Reject
          </Button>
          <Button
            onClick={() => {
              onApprove(currentCommand.id);
              if (commands.length === 1) {
                onOpenChange(false);
              }
            }}
            className="flex items-center gap-2 bg-[#2f6868] hover:bg-[#254f4f]"
          >
            <Check className="w-4 h-4" />
            Approve
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
