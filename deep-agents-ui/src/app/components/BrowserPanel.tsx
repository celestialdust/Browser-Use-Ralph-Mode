"use client";

import React, { useState, useEffect, useRef } from "react";
import { Monitor, Wifi, WifiOff, Maximize2, Minimize2, X } from "lucide-react";
import type { BrowserSession } from "@/app/types/types";

interface BrowserPanelProps {
  browserSession: BrowserSession | null;
  onClose?: () => void;
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

export function BrowserPanel({ browserSession, onClose }: BrowserPanelProps) {
  const [imageSrc, setImageSrc] = useState<string>("");
  const [connectionStatus, setConnectionStatus] = useState<{
    connected: boolean;
    screencasting: boolean;
  }>({ connected: false, screencasting: false });
  const [viewport, setViewport] = useState<{
    width: number;
    height: number;
  }>({ width: 0, height: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;

  const streamUrl = browserSession?.streamUrl;
  const isActive = browserSession?.isActive ?? false;

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
          console.error("WebSocket connection error - browser stream may not be running");
          console.log("Stream URL:", streamUrl);
          console.log("Make sure the browser session is active and streaming");
        };

        ws.onclose = () => {
          console.log("Browser stream disconnected");
          setConnectionStatus({ connected: false, screencasting: false });

          // Attempt to reconnect if still active and haven't exceeded max attempts
          if (isActive && streamUrl && reconnectAttempts < maxReconnectAttempts) {
            const backoffTime = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
            reconnectTimeoutRef.current = setTimeout(() => {
              console.log(`Attempting to reconnect... (attempt ${reconnectAttempts + 1})`);
              setReconnectAttempts((prev) => prev + 1);
              connectWebSocket();
            }, backoffTime);
          }
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
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  if (!isActive || !streamUrl) {
    return null;
  }

  return (
    <div
      className={`flex flex-col h-full bg-background border-l border-border ${
        isFullscreen ? "fixed inset-0 z-50" : ""
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-card">
        <div className="flex items-center gap-3">
          <Monitor className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Browser Preview</span>
          {connectionStatus.connected ? (
            <>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <Wifi className="w-3.5 h-3.5 text-green-600 dark:text-green-500" />
              </div>
              {viewport.width > 0 && (
                <span className="text-xs text-muted-foreground">
                  {viewport.width} × {viewport.height}
                </span>
              )}
            </>
          ) : (
            <div className="flex items-center gap-1.5">
              <WifiOff className="w-3.5 h-3.5 text-red-600 dark:text-red-500" />
              <span className="text-xs text-muted-foreground">Disconnected</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!connectionStatus.connected && reconnectAttempts < maxReconnectAttempts && (
            <button
              onClick={handleReconnect}
              className="px-2 py-1 text-xs rounded hover:bg-accent transition-colors"
              title="Reconnect"
            >
              Reconnect
            </button>
          )}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 hover:bg-accent rounded transition-colors"
            title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>
          {onClose && !isFullscreen && (
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-accent rounded transition-colors"
              title="Close panel"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Browser Stream Display */}
      <div className="flex-1 overflow-auto bg-muted">
        {imageSrc ? (
          <div className="flex items-center justify-center min-h-full p-4">
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
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <Monitor className="w-12 h-12 mb-4 opacity-50" />
            <p className="text-sm">
              {connectionStatus.connected
                ? "Waiting for frames..."
                : reconnectAttempts >= maxReconnectAttempts
                ? "Connection failed"
                : "Connecting to browser..."}
            </p>
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
      </div>

      {/* Footer with session info */}
      {browserSession?.sessionId && (
        <div className="px-4 py-2 border-t border-border bg-card">
          <p className="text-xs text-muted-foreground">
            Session: <span className="font-mono">{browserSession.sessionId}</span>
          </p>
        </div>
      )}
    </div>
  );
}
