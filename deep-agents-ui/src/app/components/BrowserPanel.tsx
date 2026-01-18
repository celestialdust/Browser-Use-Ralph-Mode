"use client";

import React, { useState, useEffect, useRef } from "react";
import { Monitor, Wifi, WifiOff, Maximize2, Minimize2, X } from "lucide-react";
import type { BrowserSession } from "@/app/types/types";

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
  const hasConnectedOnceRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;

  const streamUrl = browserSession?.streamUrl;
  const isActive = browserSession?.isActive ?? false;

  // Auto-expand when browser session becomes active
  useEffect(() => {
    if (isActive && streamUrl && !isExpanded) {
      onToggleExpand(true);
    }
  }, [isActive, streamUrl, isExpanded, onToggleExpand]);

  // Reset connection state when streamUrl changes
  useEffect(() => {
    setReconnectAttempts(0);
    hasConnectedOnceRef.current = false;
  }, [streamUrl]);

  useEffect(() => {
    if (!streamUrl || !isActive) {
      // Clean up connection if not active
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setConnectionStatus({ connected: false, screencasting: false });
      setImageSrc("");
      return;
    }

    const connectWebSocket = () => {
      try {
        // Validate WebSocket URL
        if (!streamUrl.startsWith('ws://') && !streamUrl.startsWith('wss://')) {
          console.error("Invalid WebSocket URL:", streamUrl);
          return;
        }

        console.log("Attempting to connect to browser stream:", streamUrl);
        const ws = new WebSocket(streamUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("Browser stream connected successfully");
          setConnectionStatus((prev) => ({ ...prev, connected: true }));
          setReconnectAttempts(0);
          setConnectionError(null);
          hasConnectedOnceRef.current = true;
        };

        ws.onmessage = (event) => {
          try {
            const msg: WebSocketMessage = JSON.parse(event.data);

            if (msg.type === "frame") {
              // Update image with base64 data
              setImageSrc(`data:image/jpeg;base64,${msg.data}`);
              // Update viewport dimensions from metadata
              if (msg.metadata) {
                setViewport({
                  width: msg.metadata.deviceWidth,
                  height: msg.metadata.deviceHeight,
                });
              }
            } else if (msg.type === "status") {
              setConnectionStatus({
                connected: msg.connected,
                screencasting: msg.screencasting,
              });
              if (msg.viewportWidth && msg.viewportHeight) {
                setViewport({
                  width: msg.viewportWidth,
                  height: msg.viewportHeight,
                });
              }
            }
          } catch (error) {
            console.error("Failed to parse WebSocket message:", error);
          }
        };

        ws.onerror = (event) => {
          // WebSocket onerror fires during normal connection handshake
          // Only handle errors in onclose where we have more context
        };

        ws.onclose = (event) => {
          setConnectionStatus({ connected: false, screencasting: false });
          
          // Check if this was an abnormal closure (not a clean disconnect)
          const wasAbnormal = event.code !== 1000 && event.code !== 1001;
          
          setReconnectAttempts((currentAttempts) => {
            // Attempt to reconnect if still active and haven't exceeded max attempts
            if (isActive && streamUrl && currentAttempts < maxReconnectAttempts) {
              // Only log initial connection failure if we never connected
              if (currentAttempts === 0 && !hasConnectedOnceRef.current && wasAbnormal) {
                console.error("WebSocket connection failed - browser stream may not be running");
                const port = streamUrl.match(/:(\d+)/)?.[1] || "9223";
                setConnectionError(`Unable to connect to browser stream at ${streamUrl}. Ensure AGENT_BROWSER_STREAM_PORT=${port} is set when starting the backend.`);
              } else if (hasConnectedOnceRef.current) {
                console.log("WebSocket connection lost, attempting to reconnect...");
              }
              
              const backoffTime = Math.min(1000 * Math.pow(2, currentAttempts), 10000);
              reconnectTimeoutRef.current = setTimeout(() => {
                connectWebSocket();
              }, backoffTime);
              
              return currentAttempts + 1;
            } else if (currentAttempts >= maxReconnectAttempts) {
              if (hasConnectedOnceRef.current) {
                console.log("Browser session ended (possibly due to inactivity timeout)");
                setConnectionError("Browser session ended. The session may have timed out due to inactivity.");
              } else {
                console.error("Failed to connect to browser stream after multiple attempts");
                const port = streamUrl.match(/:(\d+)/)?.[1] || "9223";
                setConnectionError(`Unable to connect to browser stream at ${streamUrl}. Ensure AGENT_BROWSER_STREAM_PORT=${port} is set when starting the backend.`);
              }
            }
            return currentAttempts;
          });
        };
      } catch (error) {
        console.error("Failed to connect to browser stream:", error);
      }
    };

    connectWebSocket();

    // Cleanup on unmount or when streamUrl changes
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [streamUrl, isActive, reconnectAttempts]);

  const handleReconnect = () => {
    setReconnectAttempts(0);
    setConnectionError(null);
    hasConnectedOnceRef.current = false;
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  // This component handles WebSocket connection only
  // UI is rendered separately via BrowserPanelContent
  return null;
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
  const hasConnectedOnceRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;

  const streamUrl = browserSession?.streamUrl;
  const isActive = browserSession?.isActive ?? false;

  // Reset connection state when streamUrl changes
  useEffect(() => {
    setReconnectAttempts(0);
    hasConnectedOnceRef.current = false;
  }, [streamUrl]);

  useEffect(() => {
    if (!streamUrl || !isActive) {
      // Clean up connection if not active
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setConnectionStatus({ connected: false, screencasting: false });
      setImageSrc("");
      return;
    }

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(streamUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("Browser stream connected");
          setConnectionStatus((prev) => ({ ...prev, connected: true }));
          setConnectionError(null);
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
            console.error("Failed to parse WebSocket message:", error);
          }
        };

        ws.onerror = (error) => {
          // Only log errors if we're sure it's a problem (not during initial connection handshake)
          // The onerror event fires during normal connection establishment, so we wait for onclose
        };

        ws.onclose = (event) => {
          setConnectionStatus({ connected: false, screencasting: false });
          
          // Check if this was an abnormal closure (not a clean disconnect)
          const wasAbnormal = event.code !== 1000 && event.code !== 1001;
          
          setReconnectAttempts((currentAttempts) => {
            // Attempt to reconnect if still active and haven't exceeded max attempts
            if (isActive && streamUrl && currentAttempts < maxReconnectAttempts) {
              // Only log initial connection failure if we never connected
              if (currentAttempts === 0 && !hasConnectedOnceRef.current && wasAbnormal) {
                console.error("WebSocket connection failed - browser stream may not be running");
                const port = streamUrl.split(":").pop();
                setConnectionError(`Unable to connect to browser stream at ${streamUrl}. Ensure AGENT_BROWSER_STREAM_PORT=${port} is set when starting the backend.`);
              } else if (hasConnectedOnceRef.current) {
                console.log("WebSocket connection lost, attempting to reconnect...");
              }
              
              const backoffTime = Math.min(1000 * Math.pow(2, currentAttempts), 10000);
              reconnectTimeoutRef.current = setTimeout(() => {
                connectWebSocket();
              }, backoffTime);
              
              return currentAttempts + 1;
            } else if (currentAttempts >= maxReconnectAttempts) {
              if (hasConnectedOnceRef.current) {
                console.log("Browser session ended (possibly due to inactivity timeout)");
                setConnectionError("Browser session ended. The session may have timed out due to inactivity.");
              } else {
                console.error("Failed to connect to browser stream after multiple attempts");
                const port = streamUrl.split(":").pop();
                setConnectionError(`Unable to connect to browser stream at ${streamUrl}. Ensure AGENT_BROWSER_STREAM_PORT=${port} is set when starting the backend.`);
              }
            }
            return currentAttempts;
          });
        };
      } catch (error) {
        console.error("Failed to connect to browser stream:", error);
      }
    };

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
  }, [streamUrl, isActive]);

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
              : reconnectAttempts >= maxReconnectAttempts
              ? "Connection failed"
              : "Connecting to browser..."}
          </p>
          {connectionError && reconnectAttempts >= maxReconnectAttempts && (
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
          {reconnectAttempts >= maxReconnectAttempts && (
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
