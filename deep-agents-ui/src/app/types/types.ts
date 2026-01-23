export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: string;
  status: "pending" | "completed" | "error" | "interrupted";
}

export interface SubAgent {
  id: string;
  name: string;
  subAgentName: string;
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  status: "pending" | "active" | "completed" | "error";
}

export interface FileItem {
  path: string;
  content: string;
}

export interface TodoItem {
  id: string;
  content: string;
  status: "pending" | "in_progress" | "completed";
  updatedAt?: Date;
}

export interface Thread {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface InterruptData {
  value: any;
  ns?: string[];
  scope?: string;
}

export interface ActionRequest {
  name: string;
  args: Record<string, unknown>;
  description?: string;
}

export interface ReviewConfig {
  actionName: string;
  allowedDecisions?: string[];
}

export interface ToolApprovalInterruptData {
  action_requests: ActionRequest[];
  review_configs?: ReviewConfig[];
}

export interface BrowserSession {
  sessionId: string;
  streamUrl: string | null;
  isActive: boolean;
}

export interface BrowserCommand {
  id: string;
  command: string;
  args: any;
  requiresApproval: boolean;
}

export interface ThoughtStep {
  id: string;
  content: string;
  level: number; // 0 = top-level, 1 = nested, etc.
  status?: "streaming" | "complete";
  children?: ThoughtStep[];
}

export interface ThoughtProcess {
  content: string;
  timestamp: number;
  isComplete: boolean;
  steps?: ThoughtStep[]; // For waterfall/nested structure
}

export interface SubagentInterrupt {
  id: string;
  subagent_id: string;
  subagent_name: string;
  interrupt_type: "guidance" | "credentials" | "confirmation";
  interrupt_data: {
    type: string;
    question?: string;
    context?: string;
    attempted_approaches?: string;
    service?: string;
    credential_types?: string;
    reason?: string;
    action?: string;
    risks?: string;
    alternatives?: string;
    [key: string]: any;
  };
  response?: any;
  created_at: number;
  status: "pending" | "responded" | "resumed";
}

export interface PresentedFile {
  id: string;
  file_path: string;
  display_name: string;
  description?: string;
  file_type: string;
  file_size: number;
  presented_at: string;
  tool_call_id?: string;
}

/**
 * Status of a running or completed subagent.
 * Used for polling-based subagent visibility in the UI.
 */
export interface SubagentStatus {
  subagent_id: string;
  subagent_type: string;
  prompt: string;
  status: "pending" | "running" | "completed" | "error" | "cancelled";
  started_at: string;
  completed_at?: string;
  tool_calls_count: number;
  last_activity?: string;
  result_summary?: string;
  error?: string;
}
