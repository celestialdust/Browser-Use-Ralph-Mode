"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Monitor, RefreshCw } from "lucide-react";
import type { BrowserSession } from "@/app/types/types";

// WebSocket connection constants
const INITIAL_RETRY_DELAY = 1000;  // 1s
const MAX_RETRY_DELAY = 16000;     // 16s max backoff
const MAX_RETRIES = 5;
const SILENT_RETRY_ATTEMPTS = 4;  // Grace period for backend startup

interface BrowserPanelProps {
  browserSession: BrowserSession | null;
  isExpanded: boolean;
  onToggleExpand: (expanded: boolean) => void;
}

interface FrameMessage {
  type: "frame";
  data: string; // base64-encoded JPEG
  metadata: {
    deviceWidth: number;
    deviceHeight: number;
    pageScaleFactor: number;
    offsetTop: number;
    scrollOffsetX: number;
    scrollOffsetY: number;
  };
}

interface StatusMessage {
  type: "status";
  connected: boolean;
  screencasting: boolean;
  viewportWidth: number;
  viewportHeight: number;
}

type WebSocketMessage = FrameMessage | StatusMessage;

export function BrowserPanel({ browserSession, isExpanded, onToggleExpand }: BrowserPanelProps) {
  // Auto-expand logic is now handled in page.tsx's ChatWithBrowserPanel component
  // to avoid duplicate effects that could cause infinite loops.
  // This component is kept for API compatibility but does nothing.
  return null;
}

// Connection status message helper
function getConnectionStatusMessage(
  reconnectAttempts: number,
  hasConnectedOnce: boolean,
  isConnecting: boolean
): string {
  if (isConnecting && reconnectAttempts === 0) {
    return "Connecting to browser...";
  }

  if (reconnectAttempts > 0 && reconnectAttempts < MAX_RETRIES) {
    const nextDelay = Math.min(INITIAL_RETRY_DELAY * Math.pow(2, reconnectAttempts), MAX_RETRY_DELAY);
    if (reconnectAttempts < SILENT_RETRY_ATTEMPTS) {
      return "Connecting to browser...";
    }
    return `Reconnecting in ${Math.round(nextDelay / 1000)}s... (${reconnectAttempts}/${MAX_RETRIES})`;
  }

  if (reconnectAttempts >= MAX_RETRIES) {
    return hasConnectedOnce
      ? "Connection lost. Click to retry."
      : "Unable to connect to browser stream.";
  }

  return "Waiting for frames...";
}

// Separate component for expanded browser panel content
export function BrowserPanelContent({ browserSession }: { browserSession: BrowserSession | null }) {
  const [imageSrc, setImageSrc] = useState<string>("");
  const [connectionStatus, setConnectionStatus] = useState<{
    connected: boolean;
    screencasting: boolean;
  }>({ connected: false, screencasting: false });
  const [viewport, setViewport] = useState<{
    width: number;
    height: number;
  }>({ width: 0, height: 0 });
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const hasConnectedOnceRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const streamUrl = browserSession?.streamUrl;
  const isActive = browserSession?.isActive ?? false;
  
  // Store props in refs to prevent stale closures
  const streamUrlRef = useRef(streamUrl);
  const isActiveRef = useRef(isActive);

  // Update refs when props change
  useEffect(() => {
    streamUrlRef.current = streamUrl;
    isActiveRef.current = isActive;
  }, [streamUrl, isActive]);

  // Reset connection state when streamUrl changes
  useEffect(() => {
    setReconnectAttempts(0);
    hasConnectedOnceRef.current = false;
  }, [streamUrl]);

  // Explicit cleanup when session becomes inactive
  useEffect(() => {
    if (!isActive && wsRef.current) {
      console.log("[BrowserPanelContent] Session ended, closing WebSocket");
      wsRef.current.close(1000, "Session ended");
      wsRef.current = null;
      // Cancel any pending reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      setReconnectAttempts(0);
      setConnectionStatus({ connected: false, screencasting: false });
      setImageSrc("");
    }
  }, [isActive]);

  // Memoized connectWebSocket to avoid recreation on each render
  const connectWebSocket = useCallback(() => {
    const currentStreamUrl = streamUrlRef.current;
    const currentIsActive = isActiveRef.current;

    if (!currentStreamUrl || !currentIsActive) {
      return;
    }

    try {
      setIsConnecting(true);
      const ws = new WebSocket(currentStreamUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[BrowserPanel] Stream connected");
        setConnectionStatus((prev) => ({ ...prev, connected: true }));
        setConnectionError(null);
        setReconnectAttempts(0);
        setIsConnecting(false);
        hasConnectedOnceRef.current = true;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "frame") {
            setImageSrc(`data:image/jpeg;base64,${message.data}`);
            setConnectionStatus((prev) => ({ ...prev, screencasting: true }));
          } else if (message.type === "status") {
            setConnectionStatus({
              connected: message.connected,
              screencasting: message.screencasting,
            });
            setViewport({
              width: message.viewportWidth,
              height: message.viewportHeight,
            });
          }
        } catch (error) {
          console.error("[BrowserPanel] Failed to parse message:", error);
        }
      };

      ws.onerror = () => {
        // Error logging deferred to onclose for more complete information
      };

      ws.onclose = (event) => {
        setConnectionStatus({ connected: false, screencasting: false });
        setIsConnecting(false);

        const wasAbnormal = event.code !== 1000 && event.code !== 1001;

        setReconnectAttempts((currentAttempts) => {
          const latestStreamUrl = streamUrlRef.current;
          const latestIsActive = isActiveRef.current;

          if (latestIsActive && latestStreamUrl && currentAttempts < MAX_RETRIES) {
            // Calculate exponential backoff delay
            const backoffDelay = Math.min(
              INITIAL_RETRY_DELAY * Math.pow(2, currentAttempts),
              MAX_RETRY_DELAY
            );

            // Only show error after grace period
            if (currentAttempts >= SILENT_RETRY_ATTEMPTS && !hasConnectedOnceRef.current && wasAbnormal) {
              console.error("[BrowserPanel] Connection failed after grace period");
              const port = latestStreamUrl.split(":").pop();
              setConnectionError(
                `Unable to connect to browser stream at ${latestStreamUrl}. Ensure AGENT_BROWSER_STREAM_PORT=${port} is set when starting the backend.`
              );
            } else if (hasConnectedOnceRef.current) {
              console.log(`[BrowserPanel] Connection lost, reconnecting in ${backoffDelay}ms...`);
            } else if (currentAttempts < SILENT_RETRY_ATTEMPTS) {
              console.log(`[BrowserPanel] Retry ${currentAttempts + 1}/${SILENT_RETRY_ATTEMPTS} (grace period)`);
            }

            reconnectTimeoutRef.current = setTimeout(() => {
              connectWebSocket();
            }, backoffDelay);

            return currentAttempts + 1;
          } else if (currentAttempts >= MAX_RETRIES) {
            if (hasConnectedOnceRef.current) {
              console.log("[BrowserPanel] Session ended (possibly timed out)");
              setConnectionError("Browser session ended. The session may have timed out due to inactivity.");
            } else {
              console.error("[BrowserPanel] Failed to connect after max retries");
              const port = latestStreamUrl?.split(":").pop() || "9223";
              setConnectionError(
                `Unable to connect to browser stream at ${latestStreamUrl}. Ensure AGENT_BROWSER_STREAM_PORT=${port} is set when starting the backend.`
              );
            }
          }
          return currentAttempts;
        });
      };
    } catch (error) {
      console.error("[BrowserPanel] Failed to create WebSocket:", error);
      setIsConnecting(false);
    }
  }, []);

  useEffect(() => {
    if (!streamUrl || !isActive) {
      // Clean up connection if not active
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setConnectionStatus({ connected: false, screencasting: false });
      setImageSrc("");
      setIsConnecting(false);
      return;
    }

    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [streamUrl, isActive, connectWebSocket]);

  const handleReconnect = () => {
    setReconnectAttempts(0);
    setConnectionError(null);
    hasConnectedOnceRef.current = false;
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  return (
    <>
      {!isActive || !streamUrl ? (
        // No active session - show "not working" message
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground px-8">
          <Monitor className="w-12 h-12 mb-4 opacity-30" />
          <p className="text-sm text-center font-medium text-foreground mb-1">
            Browser is not working
          </p>
          <p className="text-xs text-center text-muted-foreground">
            No active browser session. Start a task that requires browser automation.
          </p>
        </div>
      ) : imageSrc ? (
        // Active session with frames
        <div className="flex items-center justify-center min-h-full p-4 bg-muted">
          <img
            src={imageSrc}
            alt="Browser viewport"
            className="max-w-full h-auto rounded border border-border shadow-lg"
            style={{
              imageRendering: "crisp-edges",
            }}
          />
        </div>
      ) : (
        // Active session but no frames yet
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground px-8 bg-muted">
          <Monitor className="w-12 h-12 mb-4 opacity-50" />
          <p className="text-sm text-center mb-2">
            {connectionStatus.connected
              ? "Waiting for frames..."
              : getConnectionStatusMessage(reconnectAttempts, hasConnectedOnceRef.current, isConnecting)}
          </p>
          {/* Show spinner while reconnecting */}
          {isConnecting && reconnectAttempts > 0 && reconnectAttempts < MAX_RETRIES && (
            <RefreshCw className="w-5 h-5 mb-4 animate-spin opacity-50" />
          )}
          {connectionError && reconnectAttempts >= MAX_RETRIES && (
            <div className="mt-4 p-4 max-w-lg bg-background/50 border border-border rounded-lg text-left">
              <p className="text-sm font-medium mb-3 text-foreground">
                Browser Stream Configuration Issue
              </p>
              <p className="text-xs text-muted-foreground mb-3">
                {connectionError}
              </p>
              <div className="text-xs space-y-2 text-muted-foreground">
                <p className="font-medium text-foreground">To fix this:</p>
                <ol className="list-decimal list-inside space-y-1 ml-2">
                  <li>Stop your backend server</li>
                  <li>Restart with the stream port environment variable:</li>
                </ol>
                <pre className="mt-2 p-2 bg-card border border-border rounded text-xs overflow-x-auto">
                  <code>AGENT_BROWSER_STREAM_PORT={streamUrl?.match(/:(\d+)/)?.[1] || "9223"} langgraph dev</code>
                </pre>
                <p className="mt-2">
                  Or set it in your <code className="px-1 py-0.5 bg-card border border-border rounded">.env</code> file
                </p>
              </div>
            </div>
          )}
          {reconnectAttempts >= MAX_RETRIES && (
            <button
              onClick={handleReconnect}
              className="mt-4 px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      )}
    </>
  );
}
