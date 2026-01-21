"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpCircle, KeyRound, AlertTriangle, Terminal } from "lucide-react";

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

  if (type === "guidance") {
    return (
      <div className="border rounded-lg p-4 bg-amber-50 border-amber-200 dark:bg-amber-950 dark:border-amber-800">
        <div className="flex items-center gap-2 mb-2">
          <HelpCircle size={20} className="text-amber-600 dark:text-amber-400" />
          <h3 className="font-semibold text-amber-800 dark:text-amber-200">
            {subagentName ? `${subagentName} needs guidance` : "Agent needs guidance"}
          </h3>
        </div>
        {data.context && (
          <p className="text-sm text-amber-700 dark:text-amber-300 mt-2">{data.context}</p>
        )}
        <p className="font-medium mt-3 text-amber-900 dark:text-amber-100">{data.question}</p>
        {data.attempted_approaches && (
          <details className="mt-2 text-xs text-amber-600 dark:text-amber-400">
            <summary className="cursor-pointer">What I've tried</summary>
            <p className="mt-1 pl-2 border-l-2 border-amber-300">{data.attempted_approaches}</p>
          </details>
        )}
        <div className="mt-4 flex flex-col gap-2">
          <textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            placeholder="Your guidance..."
            className="w-full p-2 border rounded text-sm min-h-[80px] bg-white dark:bg-gray-900"
          />
          <Button
            onClick={() => onRespond(response)}
            disabled={!response.trim()}
            className="self-end"
          >
            Send Guidance
          </Button>
        </div>
      </div>
    );
  }

  if (type === "credentials") {
    return (
      <div className="border rounded-lg p-4 bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800">
        <div className="flex items-center gap-2 mb-2">
          <KeyRound size={20} className="text-blue-600 dark:text-blue-400" />
          <h3 className="font-semibold text-blue-800 dark:text-blue-200">
            {subagentName
              ? `${subagentName} needs credentials for ${data.service}`
              : `Credentials needed for ${data.service}`}
          </h3>
        </div>
        <p className="text-sm text-blue-700 dark:text-blue-300">{data.reason}</p>
        <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
          Required: {data.credential_types}
        </p>
        <div className="mt-4 flex flex-col gap-3">
          <input
            type="text"
            value={credentials.username}
            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            placeholder="Username or email"
            className="w-full p-2 border rounded text-sm bg-white dark:bg-gray-900"
          />
          <input
            type="password"
            value={credentials.password}
            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            placeholder="Password"
            className="w-full p-2 border rounded text-sm bg-white dark:bg-gray-900"
          />
          <Button
            onClick={() => onRespond(credentials)}
            disabled={!credentials.username || !credentials.password}
            className="self-end"
          >
            Submit Credentials
          </Button>
        </div>
      </div>
    );
  }

  if (type === "confirmation") {
    return (
      <div className="border rounded-lg p-4 bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle size={20} className="text-red-600 dark:text-red-400" />
          <h3 className="font-semibold text-red-800 dark:text-red-200">
            {subagentName ? `${subagentName} needs confirmation` : "Confirmation required"}
          </h3>
        </div>
        <p className="font-medium text-red-900 dark:text-red-100">{data.action}</p>
        <p className="text-sm text-red-700 dark:text-red-300 mt-2">
          <strong>Risks:</strong> {data.risks}
        </p>
        {data.alternatives && data.alternatives !== "None" && (
          <p className="text-sm text-red-600 dark:text-red-400 mt-1">
            <strong>Alternatives:</strong> {data.alternatives}
          </p>
        )}
        <div className="flex gap-2 mt-4">
          <Button
            variant="destructive"
            onClick={() => onRespond("approved")}
          >
            Approve
          </Button>
          <Button
            variant="outline"
            onClick={() => onRespond("rejected")}
          >
            Reject
          </Button>
        </div>
      </div>
    );
  }

  if (type === "bash_approval") {
    return (
      <div className="border rounded-lg p-4 bg-orange-50 border-orange-200 dark:bg-orange-950 dark:border-orange-800">
        <div className="flex items-center gap-2 mb-2">
          <Terminal size={20} className="text-orange-600 dark:text-orange-400" />
          <h3 className="font-semibold text-orange-800 dark:text-orange-200">
            {subagentName ? `${subagentName} wants to run a command` : "Command approval needed"}
          </h3>
        </div>
        <pre className="bg-gray-900 text-green-400 p-3 rounded mt-3 overflow-x-auto text-sm font-mono">
          $ {data.command}
        </pre>
        <div className="flex gap-2 mt-4">
          <Button
            onClick={() => onRespond("approved")}
            className="bg-orange-600 hover:bg-orange-700"
          >
            Allow
          </Button>
          <Button
            variant="outline"
            onClick={() => onRespond("rejected")}
          >
            Deny
          </Button>
        </div>
      </div>
    );
  }

  return null;
}
